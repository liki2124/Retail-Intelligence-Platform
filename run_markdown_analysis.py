import sqlite3
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent
db_path = root / "data" / "sample" / "retail_sample.db"
sql_path = root / "sql" / "02_markdown_analysis.sql"

with sqlite3.connect(db_path) as connection:
    sql = sql_path.read_text(encoding="utf-8-sig")
    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]

    for number, statement in enumerate(statements, start=1):
        print(f"\n--- Markdown analysis: Query {number} ---")
        print(
            pd.read_sql_query(statement, connection)
            .to_string(index=False)
        )
