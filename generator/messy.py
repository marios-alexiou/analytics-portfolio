"""Inject the data-quality problems real sources have. Every problem here is handled in dbt staging."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from generator.simulate import World

COUNTRY_NAMES = {"US": "United States", "GB": "United Kingdom", "DE": "Germany", "GR": "Greece", "FR": "France"}


def apply(world: World, seed: int, extracted_at: datetime) -> None:
    rng = random.Random(seed + 1)
    _accounts(world, rng)
    _subscription_events(world, rng, extracted_at)
    _crm_domains(world, rng)
    _google_ads_resync(world, rng)


def _accounts(world: World, rng: random.Random) -> None:
    """Free-text signup form: inconsistent country values, stray whitespace, upper-case emails."""
    for account in world.accounts:
        roll = rng.random()
        if roll < 0.03:
            account["country_code"] = account["country_code"].lower()
        elif roll < 0.04 and account["country_code"] in COUNTRY_NAMES:
            account["country_code"] = COUNTRY_NAMES[account["country_code"]]
        if rng.random() < 0.02:
            account["company_name"] = f" {account['company_name']}  "
        if rng.random() < 0.01:
            account["email"] = account["email"].upper()


def _subscription_events(world: World, rng: random.Random, extracted_at: datetime) -> None:
    """Webhooks: at-least-once delivery (duplicates), some arrive days late, some not yet at extract time."""
    delivered = []
    for event in world.subscription_events:
        event["received_at"] = event["occurred_at"] + timedelta(seconds=rng.uniform(1, 120))
        if rng.random() < 0.02:
            event["received_at"] += timedelta(days=rng.uniform(1, 5))
        delivered.append(event)
        if rng.random() < 0.01:
            delivered.append({**event, "received_at": event["received_at"] + timedelta(seconds=rng.uniform(5, 600))})
    world.subscription_events = sorted(
        (e for e in delivered if e["received_at"] <= extracted_at), key=lambda e: e["received_at"]
    )


def _crm_domains(world: World, rng: random.Random) -> None:
    """Sales reps type domains by hand."""
    for company in world.crm_companies:
        roll = rng.random()
        if roll < 0.08:
            company["domain"] = f"www.{company['domain']}"
        elif roll < 0.12:
            company["domain"] = f"https://{company['domain']}/"
        elif roll < 0.15:
            company["domain"] = company["domain"].upper()


def _google_ads_resync(world: World, rng: random.Random) -> None:
    """The connector re-syncs a few days and appends instead of replacing."""
    world.google_ads.extend([dict(row) for row in world.google_ads if rng.random() < 0.003])
