"""Land the raw files in DuckDB as all-string tables, one schema per source: raw_<source>.<table>.

Types are enforced in dbt staging, not here, so the same staging SQL works on DuckDB and BigQuery.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def load(raw_dir: Path, database: Path) -> None:
    database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database))
    for path in sorted(raw_dir.glob("*/*")):
        schema, table = f"raw_{path.parent.name}", path.name.split(".")[0]
        con.execute(f"create schema if not exists {schema}")
        if path.suffix == ".csv":
            source = f"read_csv('{path}', all_varchar = true, header = true)"
        else:
            source = (
                f"(select network, pulled_at, payload::varchar as payload from read_json('{path}', "
                "format = 'newline_delimited', columns = {network: 'varchar', pulled_at: 'varchar', payload: 'json'}))"
            )
        con.execute(
            f"create or replace table {schema}.{table} as "
            f"select *, current_timestamp::timestamp as _loaded_at from {source}"
        )
        rows = con.execute(f"select count(*) from {schema}.{table}").fetchone()[0]
        print(f"{schema}.{table:<28} {rows:>8,}")
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/fieldcraft.duckdb"))
    args = parser.parse_args()
    load(args.raw_dir, args.database)


if __name__ == "__main__":
    main()
