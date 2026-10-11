# Fieldcraft analytics

[![ci](https://github.com/marios-alexiou/analytics-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/marios-alexiou/analytics-portfolio/actions/workflows/ci.yml)

An end-to-end analytics stack for **Fieldcraft**, a fictional B2B SaaS company selling scheduling software to
field-service businesses. It covers the whole path: messy raw sources, ingestion, dbt modelling and tests,
and the dashboards people read.

The data pipeline and Evidence dashboards run locally on DuckDB with no credentials. A BigQuery target
is configured but has not yet been validated against BigQuery. Looker Studio reports are not built.

## The company and its data

Fieldcraft sells three plans (Starter, Pro, Business) monthly or annually in USD, EUR and GBP. Every signup
gets a 14-day trial. Customers come from organic search, paid search, Meta, LinkedIn, referrals and three
affiliate networks; larger accounts are worked by a sales team in the CRM.

`generator/` simulates three years of that business and writes the raw files each source system would
deliver. The data is deliberately imperfect, the way real sources are:

| Source | Problem planted | Handled in |
|---|---|---|
| Billing webhooks | At-least-once delivery (duplicate `event_id`s); some events arrive days late or not yet | `stg_billing__subscription_events` |
| Billing | Amounts in minor units; prorated upgrade invoices that are not MRR | `minor_units_to_amount`, invoice model docs |
| Signup form | Country typed as code, lower-case code or full name; stray whitespace; upper-case emails | `stg_app_db__accounts` |
| Signup form | Internal QA workspaces with free subscriptions | `is_internal` flag |
| FX rates | Business days only; no USD row | Downstream date spine |
| CRM | Hand-typed domains (`https://`, `www.`, upper case); missing workspace links | `normalize_domain` |
| Google Ads | Connector re-syncs a day by appending duplicates | `stg_marketing__google_ads` |
| Affiliate APIs | Three JSON schemas; local London time, epoch millis and ISO UTC; three currencies; one row per daily pull; conversions for unknown clicks | `stg_affiliates__*` |

## The models

```
staging/        one model per source table: types, renames, dedup, normalization
intermediate/   FX rates for every day, subscription price periods, unified ad spend and affiliate conversions
marts/core/     dim_dates, dim_accounts, fct_mrr_daily
marts/finance/  mart_mrr_monthly: MRR bridge by region and channel
marts/growth/   mart_trial_funnel, mart_acquisition_monthly (CAC, payback), mart_web_funnel_monthly
```

Some design choices:

- **MRR is rebuilt from billing events at daily grain**, then checked against the billing system's own
  current state on the extract date (`assert_mrr_matches_billing_state`). The monthly bridge must reconcile to the
  cent (`assert_mrr_bridge_reconciles`).
- **Exchange-rate movement is its own line in the bridge.** Customers are billed in USD, EUR and GBP; valuing each
  day's change at that day's rate and booking the remainder as `fx_effect_usd` keeps new/expansion/churn honest.
- **Marts hold counts and sums, not rates.** Conversion rates and CAC are ratios of sums in the BI tool, so
  they stay correct at any roll-up.
- **Silent row loss fails the build.** The first MRR numbers came out about 60% low: `dbt_utils.deduplicate` on DuckDB
  natural-joins on every column, so any row with a NULL disappeared. The reconciliation tests caught it; the fix is
  a `QUALIFY`-based macro and a test that every raw `event_id` reaches staging.

## Dashboard gallery

These PDF exports show the Evidence dashboards using synthetic Fieldcraft data. They are static snapshots,
not live reports; interactive filters are available in the local dashboard app.

| Dashboard | Business question | Preview |
|---|---|---|
| SaaS overview | How is recurring revenue growing, and what explains the monthly change? | [View PDF](dashboards/saas-overview.pdf) |
| Trial conversion | Which acquisition channels and signup cohorts convert to paid customers? | [View PDF](dashboards/trial-conversion.pdf) |
| Acquisition economics | How do paid channels compare on acquisition cost and revenue payback? | [View PDF](dashboards/acquisition.pdf) |

The PDFs retain the original browser print layout, including page breaks and localhost headers.

## Run it

### Local dashboards

The open-source Evidence trial lives in `dashboards/`. Each dashboard is a Markdown page with SQL,
charts and filters: SaaS overview, trial conversion and acquisition economics. They read only the synthetic
DuckDB marts; no Google Cloud account is needed. The reference screenshots are not included.

After building the dbt models, run `make dashboard-setup`, `make dashboard-build`, then
`make dashboard-preview` and open http://127.0.0.1:3001.

The legacy Evidence dependency tree has npm audit findings. This is a localhost trial, not an approved
public deployment. Stop the preview before rebuilding; Evidence regenerates its working directory.

### Data pipeline

```bash
make setup   # Python 3.12 virtualenv, dependencies, dbt packages
make data    # generate raw files and load them into data/fieldcraft.duckdb
make build   # dbt seeds, models and tests
make lint    # ruff + sqlfluff
make test    # generator unit tests
```

## Layout

```
generator/   Python simulation of the business, plus the data-quality problems
scripts/     Loads raw files into DuckDB, one raw_<source> schema per source system
transform/   dbt project (staging -> intermediate -> marts)
tests/       Generator unit tests
dashboards/  Evidence Markdown pages, shared components and DuckDB source queries
```
