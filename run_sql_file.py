import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "sample" / "retail_sample.db"
SQL_DIR = ROOT / "sql"


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_sql_file.py <sql_filename>")
        sys.exit(1)

    filename = sys.argv[1]

    # Only allow SQL files from the project's sql directory.
    if Path(filename).name != filename or not filename.endswith(".sql"):
        print("Error: provide a SQL filename such as 04_inventory_kpis.sql")
        sys.exit(1)

    sql_path = SQL_DIR / filename

    if not sql_path.is_file():
        print(f"Error: SQL file not found: {sql_path}")
        sys.exit(1)

    if not DB_PATH.is_file():
        print("Sample database not found. Run: python run_sql.py")
        sys.exit(1)

    sql_text = sql_path.read_text(encoding="utf-8-sig")

    # Split on semicolons and execute each query separately.
    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip() and not statement.strip().startswith("--")
    ]

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()

        for number, statement in enumerate(statements, start=1):
            print(f"\n{'=' * 60}")
            print(f"Query {number}")
            print("=" * 60)

            try:
                cursor.execute(statement)
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
                print(f"SQL error: {error}")
                sys.exit(1)


if __name__ == "__main__":
    main()
