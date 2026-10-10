from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time

import pytest

from generator.__main__ import generate

START, END = date(2024, 1, 1), date(2024, 12, 31)
END_DT = datetime.combine(END, time(23, 59, 59))


@pytest.fixture(scope="module")
def world():
    return generate(seed=7, start=START, end=END, scale=0.5)


def test_same_seed_gives_same_data(world):
    again = generate(seed=7, start=START, end=END, scale=0.5)
    assert again.invoices == world.invoices
    assert again.affiliate_pulls == world.affiliate_pulls


def test_nothing_is_dated_after_the_extract(world):
    assert max(a["created_at"] for a in world.accounts) <= END_DT
    assert max(i["issued_at"] for i in world.invoices) <= END_DT
    assert max(e["received_at"] for e in world.subscription_events) <= END_DT


def test_invoices_and_events_reference_known_subscriptions(world):
    subscription_ids = {s["subscription_id"] for s in world.subscriptions}
    assert {i["subscription_id"] for i in world.invoices} <= subscription_ids
    assert {e["subscription_id"] for e in world.subscription_events} <= subscription_ids


def test_every_subscription_is_billed_from_its_start(world):
    first_invoice = {}
    for invoice in world.invoices:
        first_invoice.setdefault(invoice["subscription_id"], invoice)
    for sub in world.subscriptions:
        assert first_invoice[sub["subscription_id"]]["period_start"] == sub["started_at"]


def test_canceled_subscriptions_have_ended(world):
    for sub in world.subscriptions:
        if sub["status"] == "canceled":
            assert sub["ended_at"] is not None and sub["ended_at"] <= END_DT


def test_planted_data_problems_exist(world):
    event_ids = Counter(e["event_id"] for e in world.subscription_events)
    assert any(count > 1 for count in event_ids.values()), "expected duplicate webhook deliveries"
    assert any(a["country_code"] != a["country_code"].upper() for a in world.accounts)
    assert any(c["domain"].startswith(("www.", "https://")) for c in world.crm_companies)
    assert any(s["unit_amount"] == 0 for s in world.subscriptions), "expected internal QA subscriptions"
