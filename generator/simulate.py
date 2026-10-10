"""Clean simulation of Fieldcraft's business. Data-quality problems are added afterwards by messy.py."""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from generator import config as cfg

Row = dict[str, object]

COMPANY_PREFIXES = [
    "North", "Blue", "Iron", "Summit", "Harbor", "Cedar", "Bright", "Atlas", "Peak", "River",
    "Stone", "Silver", "Oak", "Pioneer", "Metro", "Swift", "Coastal", "Prime", "Evergreen", "Granite",
]
COMPANY_TRADES = [
    "Plumbing", "HVAC", "Electric", "Landscaping", "Roofing", "Cleaning", "Pest Control", "Solar",
    "Facilities", "Maintenance", "Builders", "Field Services", "Pool Care", "Security Systems",
]
COMPANY_SUFFIXES = ["", "", "", " Ltd", " LLC", " GmbH", " & Co", " Group"]
FIRST_NAMES = [
    "anna", "ben", "carla", "dimitris", "eva", "frank", "giulia", "hugo", "ines", "jonas",
    "katie", "liam", "maria", "nikos", "olivia", "pablo", "sofia", "tom",
]
TLD_BY_COUNTRY = {
    "US": "com", "CA": "ca", "AU": "com.au", "GB": "co.uk", "DE": "de", "FR": "fr",
    "NL": "nl", "ES": "es", "IT": "it", "IE": "ie", "GR": "gr", "SE": "se",
}
LONDON = ZoneInfo("Europe/London")


@dataclass
class World:
    accounts: list[Row] = field(default_factory=list)
    subscriptions: list[Row] = field(default_factory=list)
    subscription_events: list[Row] = field(default_factory=list)
    invoices: list[Row] = field(default_factory=list)
    fx_rates: list[Row] = field(default_factory=list)
    google_ads: list[Row] = field(default_factory=list)
    meta_ads: list[Row] = field(default_factory=list)
    linkedin_ads: list[Row] = field(default_factory=list)
    web_traffic: list[Row] = field(default_factory=list)
    crm_owners: list[Row] = field(default_factory=list)
    crm_companies: list[Row] = field(default_factory=list)
    crm_deals: list[Row] = field(default_factory=list)
    affiliate_pulls: dict[str, list[Row]] = field(default_factory=dict)


def add_months(moment: datetime, months: int) -> datetime:
    month_index = moment.month - 1 + months
    year = moment.year + month_index // 12
    month = month_index % 12 + 1
    next_month = date(year + month // 12, month % 12 + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    return moment.replace(year=year, month=month, day=min(moment.day, last_day))


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, round(rng.gauss(lam, math.sqrt(lam))))
    threshold, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= threshold:
            return k
        k += 1


def _pick(rng: random.Random, weights: dict[str, float]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _random_time(rng: random.Random, day: date, start_hour: int = 0, end_hour: int = 24) -> datetime:
    return datetime.combine(day, time()) + timedelta(seconds=rng.randrange(start_hour * 3600, end_hour * 3600))


def _daily_pull(moment: datetime) -> datetime:
    """Affiliate APIs are pulled once a day at 02:00 UTC; return the first pull after `moment`."""
    pull = datetime.combine(moment.date(), time(2))
    return pull if pull > moment else pull + timedelta(days=1)


class Simulator:
    def __init__(self, seed: int, start: date, end: date, scale: float = 1.0):
        self.rng = random.Random(seed)
        self.start, self.end, self.scale = start, end, scale
        self.end_dt = datetime.combine(end, time(23, 59, 59))
        self.world = World()
        self._domains: set[str] = set()
        self._fx: dict[tuple[date, str], float] = {}
        self._sub_seq = 0
        self._inv_seq = 0

    def run(self) -> World:
        self._fx_rates()
        self._accounts()
        self._marketing()
        self._crm()
        self._affiliates()
        return self.world

    # --- finance -------------------------------------------------------------------------------

    def _fx_rates(self) -> None:
        rates = {"EUR": 1.09, "GBP": 1.27}
        volatility = {"EUR": 0.004, "GBP": 0.005}
        day = self.start - timedelta(days=7)
        while day <= self.end:
            for currency in rates:
                rates[currency] *= math.exp(self.rng.gauss(0, volatility[currency]))
            if day.weekday() < 5:  # rates are only published on business days
                for currency, rate in rates.items():
                    self._fx[(day, currency)] = rate
                    self.world.fx_rates.append({"rate_date": day, "currency": currency, "usd_per_unit": round(rate, 6)})
            day += timedelta(days=1)

    def _usd_per_unit(self, currency: str, on: date) -> float:
        if currency == "USD":
            return 1.0
        while (on, currency) not in self._fx:
            on -= timedelta(days=1)
        return self._fx[(on, currency)]

    # --- accounts and billing ------------------------------------------------------------------

    def _accounts(self) -> None:
        total_days = (self.end - self.start).days + 1
        seq = 0
        for offset in range(total_days):
            day = self.start + timedelta(days=offset)
            daily_rate = (6 + 8 * offset / total_days) * (0.6 if day.weekday() >= 5 else 1.1) * self.scale
            for _ in range(_poisson(self.rng, daily_rate)):
                seq += 1
                account = self._new_account(seq, day)
                self.world.accounts.append(account)
                self._maybe_convert(account)

    def _new_account(self, seq: int, day: date) -> Row:
        rng = self.rng
        internal = rng.random() < 0.005
        country = _pick(rng, {code: weight for code, (_, weight) in cfg.COUNTRIES.items()})
        size = _pick(rng, {name: values[0] for name, values in cfg.COMPANY_SIZES.items()})
        channel = "direct" if internal else _pick(rng, {name: values[0] for name, values in cfg.CHANNELS.items()})

        campaign_id = None
        if channel in cfg.CAMPAIGNS:
            campaigns = cfg.CAMPAIGNS[channel]
            campaign_id = rng.choices([c[0] for c in campaigns], weights=[c[2] for c in campaigns])[0]

        utm_source, utm_medium = cfg.UTM_BY_CHANNEL[channel]
        network = click_ref = None
        if channel == "partner":
            network = _pick(rng, cfg.AFFILIATE_NETWORKS)
            utm_source = network
            click_ref = f"clk_{rng.getrandbits(40):010x}"

        name, slug = self._company_name()
        domain = cfg.INTERNAL_DOMAIN if internal else self._unique_domain(slug, country)
        email = f"qa+{seq}@{domain}" if internal else f"{rng.choice(FIRST_NAMES)}@{domain}"
        created_at = _random_time(rng, day, 6, 23)
        return {
            "account_id": f"acc_{seq:06d}",
            "company_name": name,
            "email": email,
            "country_code": country,
            "company_size": size,
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": campaign_id,
            "affiliate_click_ref": click_ref,
            "created_at": created_at,
            "trial_ends_at": created_at + timedelta(days=cfg.TRIAL_DAYS),
            "_internal": internal,
            "_channel": channel,
            "_network": network,
            "_domain": domain,
            "_subs": [],
        }

    def _company_name(self) -> tuple[str, str]:
        prefix, trade = self.rng.choice(COMPANY_PREFIXES), self.rng.choice(COMPANY_TRADES)
        name = f"{prefix} {trade}{self.rng.choice(COMPANY_SUFFIXES)}"
        return name, re.sub(r"[^a-z0-9]", "", f"{prefix}{trade}".lower())

    def _unique_domain(self, slug: str, country: str) -> str:
        domain = f"{slug}.{TLD_BY_COUNTRY[country]}"
        while domain in self._domains:
            domain = f"{slug}{self.rng.randrange(2, 999)}.{TLD_BY_COUNTRY[country]}"
        self._domains.add(domain)
        return domain

    def _maybe_convert(self, account: Row) -> None:
        rng = self.rng
        size = account["company_size"]
        channel_rate = cfg.CHANNELS[account["_channel"]][1]
        probability = 0.6 if account["_internal"] else channel_rate * cfg.COMPANY_SIZES[size][1]
        if rng.random() >= probability:
            return

        converted_at = account["created_at"] + timedelta(days=rng.triangular(1, 21, 13))
        if converted_at > self.end_dt:
            return
        plan_id = rng.choices(list(cfg.PLANS), weights=cfg.COMPANY_SIZES[size][2])[0]
        period = "annual" if rng.random() < cfg.ANNUAL_SHARE else "monthly"
        currency = cfg.COUNTRIES[account["country_code"]][0]

        first = self._run_subscription(account, converted_at, plan_id, period, currency)
        if first["ended_at"] and rng.random() < cfg.REACTIVATION_RATE:
            restart = first["ended_at"] + timedelta(days=rng.uniform(30, 180))
            if restart <= self.end_dt:
                self._run_subscription(account, restart, plan_id, period, currency)

    def _unit_amount(self, plan_id: str, currency: str, period: str, on: date) -> int:
        if plan_id == "pro" and on >= cfg.PRO_PRICE_CHANGE_DATE:
            monthly = cfg.PRO_NEW_PRICES[currency]
        else:
            monthly = cfg.PLANS[plan_id].prices[currency]
        return monthly * cfg.ANNUAL_MONTHS_CHARGED if period == "annual" else monthly

    def _run_subscription(self, account: Row, started_at: datetime, plan_id: str, period: str, currency: str) -> Row:
        rng = self.rng
        internal = account["_internal"]
        self._sub_seq += 1
        sub: Row = {
            "subscription_id": f"sub_{self._sub_seq:06d}",
            "account_id": account["account_id"],
            "billing_period": period,
            "currency": currency,
            "started_at": started_at,
            "cancel_requested_at": None,
            "ended_at": None,
            "cancel_reason": None,
        }
        unit = 0 if internal else self._unit_amount(plan_id, currency, period, started_at.date())
        self._event(sub, "subscription_created", started_at, plan_id, None, unit)

        months = 12 if period == "annual" else 1
        period_start, tenure = started_at, 0
        cancel: tuple[datetime, datetime, str] | None = None
        while period_start <= self.end_dt:
            period_end = add_months(period_start, months)
            reason = "subscription_create" if tenure == 0 else "subscription_cycle"
            invoice = self._invoice(sub, reason, unit, period_start, period_end, period_start)
            if tenure == 0:
                sub["_first_invoice"] = invoice
            if invoice["status"] == "uncollectible":
                ended = period_start + timedelta(days=21)
                cancel = (ended, ended, "payment_failed")
                break
            if tenure == 0 and invoice["refunded_at"] is not None:
                cancel = (invoice["refunded_at"], invoice["refunded_at"], "refund")
                break

            tier = cfg.PLANS[plan_id].tier
            roll = rng.random()
            if period == "monthly":
                churn = cfg.MONTHLY_CHURN[plan_id] * (cfg.EARLY_TENURE_CHURN_MULTIPLIER if tenure < 3 else 1.0)
                fraction = rng.random()
                changed_at = period_start + (period_end - period_start) * fraction
                if roll < churn:
                    cancel = (changed_at, period_end, "customer_request")
                    break
                upgrade = roll < churn + cfg.MONTHLY_UPGRADE and tier < 3
                downgrade = not upgrade and roll < churn + cfg.MONTHLY_UPGRADE + cfg.MONTHLY_DOWNGRADE and tier > 1
                if (upgrade or downgrade) and not internal and changed_at <= self.end_dt:
                    new_plan = cfg.PLAN_BY_TIER[tier + (1 if upgrade else -1)].plan_id
                    new_unit = self._unit_amount(new_plan, currency, period, changed_at.date())
                    self._event(sub, "plan_changed", changed_at, new_plan, plan_id, new_unit)
                    if upgrade:  # upgrades are prorated immediately; downgrades get no credit
                        proration = round((new_unit - unit) * (1 - fraction))
                        self._invoice(sub, "subscription_update", proration, changed_at, period_end, changed_at)
                    plan_id, unit = new_plan, new_unit
            else:
                # Annual plans only change at renewal.
                if roll < cfg.ANNUAL_RENEWAL_CHURN:
                    cancel = (period_end - timedelta(days=rng.uniform(1, 60)), period_end, "customer_request")
                    break
                if roll < cfg.ANNUAL_RENEWAL_CHURN + 0.12:
                    step = 1
                elif roll < cfg.ANNUAL_RENEWAL_CHURN + 0.16:
                    step = -1
                else:
                    step = 0
                if step and 1 <= tier + step <= 3 and not internal and period_end <= self.end_dt:
                    new_plan = cfg.PLAN_BY_TIER[tier + step].plan_id
                    new_unit = self._unit_amount(new_plan, currency, period, period_end.date())
                    self._event(sub, "plan_changed", period_end, new_plan, plan_id, new_unit)
                    plan_id, unit = new_plan, new_unit

            tenure += 1
            period_start = period_end

        status = "active"
        if cancel and cancel[0] <= self.end_dt:
            requested, ended, reason = cancel
            sub.update(cancel_requested_at=requested, ended_at=ended, cancel_reason=reason)
            self._event(sub, "subscription_cancelled", requested, plan_id, None, unit, effective_at=ended)
            status = "canceled" if ended <= self.end_dt else "active"
        elif cancel and cancel[2] == "payment_failed":
            status = "past_due"

        sub.update(
            status=status,
            plan_id=plan_id,
            unit_amount=unit,
            cancel_at_period_end=status == "active" and sub["ended_at"] is not None,
        )
        self.world.subscriptions.append(sub)
        account["_subs"].append(sub)
        return sub

    def _event(self, sub: Row, event_type: str, occurred_at: datetime, plan_id: str,
               previous_plan_id: str | None, unit: int, effective_at: datetime | None = None) -> None:
        sub["updated_at"] = occurred_at
        self.world.subscription_events.append({
            "event_id": f"evt_{self.rng.getrandbits(48):012x}",
            "subscription_id": sub["subscription_id"],
            "account_id": sub["account_id"],
            "event_type": event_type,
            "plan_id": plan_id,
            "previous_plan_id": previous_plan_id,
            "billing_period": sub["billing_period"],
            "currency": sub["currency"],
            "unit_amount": unit,
            "occurred_at": occurred_at,
            "effective_at": effective_at or occurred_at,
        })

    def _invoice(self, sub: Row, reason: str, amount: int, period_start: datetime, period_end: datetime,
                 issued_at: datetime) -> Row:
        rng = self.rng
        self._inv_seq += 1
        status, paid_at, refunded_at = "paid", issued_at + timedelta(minutes=rng.uniform(1, 90)), None
        if reason == "subscription_cycle" and amount > 0 and rng.random() < 0.015:
            status, paid_at = "uncollectible", None
        elif reason == "subscription_create" and amount > 0 and rng.random() < 0.03:
            refunded = issued_at + timedelta(days=rng.uniform(1, 14))
            refunded_at = refunded if refunded <= self.end_dt else None
        if paid_at and paid_at > self.end_dt:
            status, paid_at = "open", None
        invoice = {
            "invoice_id": f"in_{self._inv_seq:07d}",
            "subscription_id": sub["subscription_id"],
            "account_id": sub["account_id"],
            "billing_reason": reason,
            "currency": sub["currency"],
            "amount_due": amount,
            "amount_refunded": amount if refunded_at else 0,
            "period_start": period_start,
            "period_end": period_end,
            "issued_at": issued_at,
            "status": status,
            "paid_at": paid_at,
            "refunded_at": refunded_at,
        }
        self.world.invoices.append(invoice)
        return invoice

    # --- marketing -----------------------------------------------------------------------------

    def _marketing(self) -> None:
        rng = self.rng
        by_campaign: dict[tuple[date, str], int] = {}
        by_channel: dict[tuple[date, str], int] = {}
        for account in self.world.accounts:
            day = account["created_at"].date()
            group = cfg.WEB_CHANNEL_GROUPS[account["_channel"]][0]
            by_channel[(day, group)] = by_channel.get((day, group), 0) + 1
            if account["utm_campaign"]:
                key = (day, account["utm_campaign"])
                by_campaign[key] = by_campaign.get(key, 0) + 1

        names = {cid: name for campaigns in cfg.CAMPAIGNS.values() for cid, name, _ in campaigns}
        group_rates = {group: rate for group, rate in cfg.WEB_CHANNEL_GROUPS.values()}
        day = self.start
        while day <= self.end:
            for campaign_id, (cvr, ctr, cpc) in cfg.CAMPAIGN_ECONOMICS.items():
                signups = by_campaign.get((day, campaign_id), 0)
                clicks = max(1, round((signups + rng.uniform(0.2, 1.2)) / cvr * rng.uniform(0.85, 1.15)))
                impressions = round(clicks / ctr * rng.uniform(0.9, 1.1))
                cost = clicks * cpc * rng.uniform(0.85, 1.15)
                platform, number = campaign_id.split("_")
                if platform == "gads":
                    self.world.google_ads.append({
                        "segments_date": day, "campaign_id": number, "campaign_name": names[campaign_id],
                        "impressions": impressions, "clicks": clicks,
                        "cost_micros": round(cost * 1_000_000), "currency_code": "USD",
                    })
                elif platform == "meta":
                    self.world.meta_ads.append({
                        "date_start": day, "date_stop": day, "campaign_id": number,
                        "campaign_name": names[campaign_id], "impressions": impressions, "clicks": clicks,
                        "spend": f"{cost:.2f}", "account_currency": "EUR",
                    })
                else:
                    self.world.linkedin_ads.append({
                        "date_range_start": day, "campaign_urn": f"urn:li:sponsoredCampaign:{number}",
                        "campaign_name": names[campaign_id], "impressions": impressions, "clicks": clicks,
                        "cost_in_usd": f"{cost:.2f}",
                    })
            for group, rate in group_rates.items():
                signups = by_channel.get((day, group), 0)
                sessions = round((signups + rng.uniform(0.5, 2)) / rate * rng.uniform(0.9, 1.1))
                self.world.web_traffic.append({
                    "date": day, "session_default_channel_group": group, "sessions": sessions,
                    "engaged_sessions": round(sessions * rng.uniform(0.5, 0.65)),
                })
            day += timedelta(days=1)

    # --- CRM -----------------------------------------------------------------------------------

    def _crm(self) -> None:
        rng = self.rng
        owners_by_team: dict[str, list[str]] = {}
        for owner_id, name, team in cfg.CRM_OWNERS:
            first, last = name.lower().split()
            self.world.crm_owners.append({
                "owner_id": owner_id, "full_name": name, "email": f"{first}.{last}@{cfg.INTERNAL_DOMAIN}", "team": team,
            })
            owners_by_team.setdefault(team, []).append(owner_id)

        for account in self.world.accounts:
            if account["_internal"]:
                continue
            size, subs = account["company_size"], account["_subs"]
            if size not in ("51-200", "201+") and not (subs and subs[0]["plan_id"] == "business"):
                continue
            created_at = account["created_at"] + timedelta(hours=rng.uniform(0.1, 48))
            if created_at > self.end_dt:
                continue
            team = {"51-200": "mid_market", "201+": "enterprise"}.get(size, "smb")
            company = self._company(
                name=account["company_name"], domain=account["_domain"], country=account["country_code"],
                owner_id=rng.choice(owners_by_team[team]), created_at=created_at,
                account_id=account["account_id"] if rng.random() < 0.85 else None,
            )
            deal = None
            if size in ("51-200", "201+") and rng.random() < 0.7:
                deal = self._deal_for_account(company, account)
            active = any(s["status"] != "canceled" for s in subs)
            company["lifecycle_stage"] = (
                "customer" if active else "former_customer" if subs
                else "opportunity" if deal and deal["deal_stage"] not in ("closed_won", "closed_lost") else "lead"
            )

        # Outbound prospects that never signed up.
        for _ in range(len(self.world.crm_companies) // 4):
            country = _pick(rng, {code: weight for code, (_, weight) in cfg.COUNTRIES.items()})
            name, slug = self._company_name()
            day = self.start + timedelta(days=rng.randrange((self.end - self.start).days))
            created_at = _random_time(rng, day, 8, 18)
            company = self._company(
                name=name, domain=self._unique_domain(slug, country), country=country,
                owner_id=rng.choice(owners_by_team["enterprise"] + owners_by_team["mid_market"]),
                created_at=created_at, account_id=None,
            )
            company["lifecycle_stage"] = "lead"
            if rng.random() < 0.3:
                deal_created = created_at + timedelta(days=rng.uniform(1, 20))
                close = deal_created + timedelta(days=rng.uniform(10, 60))
                if deal_created <= self.end_dt:
                    is_open = close > self.end_dt
                    stage = rng.choice(["qualified", "demo_scheduled"]) if is_open else "closed_lost"
                    amount = cfg.PLANS["business"].prices["USD"] * 12
                    self._deal(company, deal_created, stage, None if is_open else close.date(), amount, "USD")
                    if is_open:
                        company["lifecycle_stage"] = "opportunity"

    def _company(self, name: str, domain: str, country: str, owner_id: str, created_at: datetime,
                 account_id: str | None) -> Row:
        company = {
            "company_id": str(self.rng.randrange(10**9, 10**10)),
            "name": name,
            "domain": domain,
            "country": country,
            "fieldcraft_account_id": account_id,
            "owner_id": owner_id,
            "lifecycle_stage": None,
            "created_at": created_at,
            "updated_at": created_at,
        }
        self.world.crm_companies.append(company)
        return company

    def _deal_for_account(self, company: Row, account: Row) -> Row | None:
        rng = self.rng
        currency = cfg.COUNTRIES[account["country_code"]][0]
        created_at = company["created_at"] + timedelta(days=rng.uniform(1, 5))
        subs = account["_subs"]
        if subs:
            first = subs[0]
            created_at = min(created_at, first["started_at"] - timedelta(hours=rng.uniform(2, 48)))
            amount = first["_first_invoice"]["amount_due"] * (12 if first["billing_period"] == "monthly" else 1)
            return self._deal(company, created_at, "closed_won", first["started_at"].date(), amount, currency)
        if created_at > self.end_dt:
            return None
        amount = cfg.PLANS["business"].prices[currency] * 12
        lost_at = account["trial_ends_at"] + timedelta(days=rng.uniform(0, 20))
        if lost_at > self.end_dt:
            return self._deal(company, created_at, rng.choice(["qualified", "demo_scheduled", "proposal_sent"]),
                              None, amount, currency)
        return self._deal(company, created_at, "closed_lost", lost_at.date(), amount, currency)

    def _deal(self, company: Row, created_at: datetime, stage: str, close_date: date | None, amount_minor: int,
              currency: str) -> Row:
        deal = {
            "deal_id": str(self.rng.randrange(10**10, 10**11)),
            "company_id": company["company_id"],
            "owner_id": company["owner_id"],
            "pipeline": "new_business",
            "deal_stage": stage,
            "amount": f"{amount_minor / 100:.2f}",
            "deal_currency_code": currency,
            "created_at": created_at,
            "close_date": close_date,
        }
        if close_date:
            closed = datetime.combine(close_date, time(12))
            company["updated_at"] = min(max(company["updated_at"], closed), self.end_dt)
        self.world.crm_deals.append(deal)
        return deal

    # --- affiliates ----------------------------------------------------------------------------

    def _affiliates(self) -> None:
        rng = self.rng
        self.world.affiliate_pulls = {network: [] for network in cfg.AFFILIATE_NETWORKS}
        for account in self.world.accounts:
            if account["_channel"] != "partner" or not account["_subs"]:
                continue
            sub = account["_subs"][0]
            invoice = sub["_first_invoice"]
            decided_at = sub["started_at"] + timedelta(days=30)
            ended = sub["ended_at"]
            reversed_ = (ended is not None and ended <= decided_at) or invoice["refunded_at"] is not None
            self._emit_conversion(
                network=account["_network"], click_ref=account["affiliate_click_ref"],
                converted_at=sub["started_at"], decided_at=decided_at,
                final_status="reversed" if reversed_ else "approved",
                commission_minor=round(invoice["amount_due"] * cfg.AFFILIATE_COMMISSION_RATE),
                currency=invoice["currency"],
            )

        # Conversions the networks attribute to clicks we never saw a signup for.
        orphans = max(1, sum(len(v) for v in self.world.affiliate_pulls.values()) // 100)
        for _ in range(orphans):
            converted_at = _random_time(rng, self.start + timedelta(days=rng.randrange((self.end - self.start).days)))
            self._emit_conversion(
                network=_pick(rng, cfg.AFFILIATE_NETWORKS), click_ref=f"clk_{rng.getrandbits(40):010x}",
                converted_at=converted_at, decided_at=converted_at + timedelta(days=30), final_status="reversed",
                commission_minor=rng.choice([580, 1580, 3980]), currency="USD",
            )

    def _emit_conversion(self, network: str, click_ref: str, converted_at: datetime, decided_at: datetime,
                         final_status: str, commission_minor: int, currency: str) -> None:
        rng = self.rng
        conversion_key = rng.getrandbits(64)
        pulls = [(_daily_pull(converted_at + timedelta(hours=rng.uniform(1, 30))), "pending")]
        if rng.random() < 0.5:
            pulls.append((pulls[0][0] + timedelta(days=rng.randrange(3, 15)), "pending"))
        pulls.append((_daily_pull(decided_at + timedelta(hours=rng.uniform(0, 72))), final_status))

        for pulled_at, status in pulls:
            if pulled_at > self.end_dt:
                continue
            decided = status != "pending"
            if network == "affinet":
                payload = {
                    "id": f"afn-{conversion_key:016x}",
                    "click_ref": click_ref,
                    "commission": {"amount": f"{commission_minor / 100:.2f}", "currency": currency},
                    "status": {"pending": "pending", "approved": "approved", "reversed": "declined"}[status],
                    "event_date": converted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated": (decided_at if decided else converted_at).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            elif network == "linkloop":
                usd = commission_minor / 100 * self._usd_per_unit(currency, converted_at.date())
                local = converted_at.replace(tzinfo=UTC).astimezone(LONDON)
                payload = {
                    "transactionId": conversion_key % 10**9,
                    "subId": click_ref,
                    "commissionAmount": round(usd, 2),
                    "currency": "USD",
                    "state": {"pending": "PENDING", "approved": "CONFIRMED", "reversed": "DECLINED"}[status],
                    "date": local.strftime("%d/%m/%Y %H:%M"),
                }
            else:
                usd = commission_minor / 100 * self._usd_per_unit(currency, converted_at.date())
                gbp = usd / self._usd_per_unit("GBP", converted_at.date())
                payload = {
                    "conversion": {
                        "uuid": f"{conversion_key:016x}",
                        "reference": click_ref,
                        "created": int(converted_at.replace(tzinfo=UTC).timestamp() * 1000),
                    },
                    "payout_cents": round(gbp * 100),
                    "payout_currency": "GBP",
                    "approval": {
                        "status": {"pending": "pending", "approved": "accepted", "reversed": "rejected"}[status],
                        "at": decided_at.strftime("%Y-%m-%dT%H:%M:%SZ") if decided else None,
                    },
                }
            self.world.affiliate_pulls[network].append({"network": network, "pulled_at": pulled_at, "payload": payload})
