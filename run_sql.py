import sqlite3
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parent
csv_path = root / "data" / "sample" / "inventory_sample.csv"
sql_path = root / "sql" / "01_inventory_overview.sql"
db_path = root / "data" / "sample" / "retail_sample.db"

df = pd.read_csv(csv_path, encoding="utf-8-sig")

with sqlite3.connect(db_path) as connection:
    df.to_sql("inventory", connection, if_exists="replace", index=False)

    sql = sql_path.read_text(encoding="utf-8-sig")
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]

    for index, statement in enumerate(statements, start=1):
        print(f"\n--- Query {index} ---")
        print(pd.read_sql_query(statement, connection).to_string(index=False))

print(f"\nSQLite database created at: {db_path}")
