"""Write the simulated world as the raw files each source system would deliver."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path

from generator.simulate import World


def _format(value: object) -> object:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return str(value).lower()
    return "" if value is None else value


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [key for key in rows[0] if not key.startswith("_")]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: _format(row[key]) for key in columns} for row in rows)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps({**row, "pulled_at": _format(row["pulled_at"])}) + "\n")


def write(world: World, out: Path) -> dict[str, int]:
    tables = {
        "app_db/accounts.csv": world.accounts,
        "billing/subscriptions.csv": world.subscriptions,
        "billing/subscription_events.csv": world.subscription_events,
        "billing/invoices.csv": world.invoices,
        "finance/fx_rates.csv": world.fx_rates,
        "crm/owners.csv": world.crm_owners,
        "crm/companies.csv": world.crm_companies,
        "crm/deals.csv": world.crm_deals,
        "marketing/google_ads_campaign_stats.csv": world.google_ads,
        "marketing/meta_ads_insights.csv": world.meta_ads,
        "marketing/linkedin_ads_analytics.csv": world.linkedin_ads,
        "marketing/web_traffic_daily.csv": world.web_traffic,
    }
    counts = {}
    for name, rows in tables.items():
        _write_csv(out / name, rows)
        counts[name] = len(rows)
    for network, rows in world.affiliate_pulls.items():
        name = f"affiliates/{network}_conversions.jsonl"
        _write_jsonl(out / name, rows)
        counts[name] = len(rows)
    return counts
