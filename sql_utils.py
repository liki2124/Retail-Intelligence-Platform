import re
import sqlite3


def split_sql_statements(sql_text):
    """Split SQL at statement-ending semicolons, preserving comments."""
    statements = []
    buffer = ""

    for character in sql_text:
        buffer += character

        if character == ";" and sqlite3.complete_statement(buffer):
            # Ignore sections containing only SQL comments.
            without_comments = re.sub(
                r"--[^\n]*|/\*.*?\*/",
                "",
                buffer,
                flags=re.DOTALL,
            ).strip()

            if without_comments:
                statements.append(buffer.strip())

            buffer = ""

    if buffer.strip():
        without_comments = re.sub(
            r"--[^\n]*|/\*.*?\*/",
            "",
            buffer,
            flags=re.DOTALL,
        ).strip()

        if without_comments:
            if not sqlite3.complete_statement(buffer):
                raise ValueError("SQL file ends with an incomplete statement.")
            statements.append(buffer.strip())

    return statements
