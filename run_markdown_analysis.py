import sqlite3
from pathlib import Path

import pandas as pd

from sql_utils import split_sql_statements

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "sample" / "retail_sample.db"
SQL_PATH = ROOT / "sql" / "02_markdown_analysis.sql"


def main():
    if not DB_PATH.is_file():
        raise SystemExit(f"Database not found: {DB_PATH}")

    if not SQL_PATH.is_file():
        raise SystemExit(f"SQL file not found: {SQL_PATH}")

    sql_text = SQL_PATH.read_text(encoding="utf-8-sig")
    statements = split_sql_statements(sql_text)

    with sqlite3.connect(DB_PATH) as connection:
        for number, statement in enumerate(statements, start=1):
            print(f"\n--- Markdown analysis: Query {number} ---")
            print(
                pd.read_sql_query(statement, connection).to_string(index=False)
            )


if __name__ == "__main__":
    main()
