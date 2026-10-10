# Fieldcraft analytics

[![ci](https://github.com/marios-alexiou/analytics-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/marios-alexiou/analytics-portfolio/actions/workflows/ci.yml)

An end-to-end analytics stack for **Fieldcraft**, a fictional B2B SaaS company selling scheduling software to
field-service businesses. It covers the whole path: messy raw sources, ingestion, dbt modelling and tests,
and the dashboards people read.

Everything runs locally on DuckDB with no credentials. The same dbt project also targets BigQuery, which
backs the Looker Studio dashboards.

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

## Run it

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
```

## Roadmap

- [x] Synthetic sources with realistic data problems
- [x] Staging layer with tests and docs on every column, portable across DuckDB and BigQuery
- [x] CI: generator tests, dbt build, sqlfluff
- [ ] Intermediate and marts: daily MRR and MRR movements, cohorts, trial funnel, CAC by channel, affiliate commissions
- [ ] Snapshots for CRM ownership history
- [ ] PR impact report: CI comments every PR with row, key and column changes against `main`
- [ ] Ingestion: config-driven extractor for the affiliate APIs, Terraform module
- [ ] Dashboards: Looker Studio (BigQuery sandbox) and Evidence (dashboards as code)
- [ ] Decision records and case studies
