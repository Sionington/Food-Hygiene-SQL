import sqlite3
from pathlib import Path

HERE = Path(__file__).parent


def check_db():
    db_path = HERE / "hygiene.db"
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    text = (HERE / "checks.sql").read_text()
    queries = text.split(";")
    for query in queries:
        if not query.strip():
            continue
        for line in query.strip().splitlines():
            if line.startswith("--"):
                print(line)
        cursor = conn.execute(query)
        col_names = [col[0] for col in cursor.description]
        print(col_names)
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    conn.close()

def main():
    check_db()


if __name__ == "__main__":
    main()
