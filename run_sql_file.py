import sqlite3
import sys
from pathlib import Path

from sql_utils import split_sql_statements

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "sample" / "retail_sample.db"
SQL_DIR = ROOT / "sql"


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_sql_file.py <sql_filename>")
        sys.exit(1)

    filename = sys.argv[1]

    if Path(filename).name != filename or not filename.endswith(".sql"):
        print("Error: provide a SQL filename such as 04_inventory_kpis.sql")
        sys.exit(1)

    sql_path = SQL_DIR / filename

    if not sql_path.is_file():
        print(f"Error: SQL file not found: {sql_path}")
        sys.exit(1)

    if not DB_PATH.is_file():
        print(f"Sample database not found: {DB_PATH}")
        sys.exit(1)

    sql_text = sql_path.read_text(encoding="utf-8-sig")

    try:
        statements = split_sql_statements(sql_text)
    except ValueError as error:
        print(f"SQL parsing error: {error}")
        sys.exit(1)

    if not statements:
        print("No SQL statements found.")
        return

    try:
        with sqlite3.connect(DB_PATH) as connection:
            for number, statement in enumerate(statements, start=1):
                print(f"\n{'=' * 60}")
                print(f"Query {number}")
                print("=" * 60)

                cursor = connection.execute(statement)

                if cursor.description:
                    columns = [item[0] for item in cursor.description]
                    rows = cursor.fetchall()
                    print(" | ".join(columns))
                    print("-" * 60)

                    for row in rows:
                        print(" | ".join(str(value) for value in row))

                    print(f"\nRows returned: {len(rows)}")
                else:
                    print(f"Rows affected: {cursor.rowcount}")

    except sqlite3.Error as error:
        print(f"SQL execution error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
