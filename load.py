import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def fetch(api_url, api):
    headers = {"Accept": "application/json", "x-api-version": "2"}
    response = requests.get(api_url, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json().get(api, [])
        return data
    else:
        print(f"Error: {response.status_code}")


def get_authorities():
    get_authorities_names = [
        "Vale of Glamorgan",
        "Bridgend",
        "Newport",
        "Bristol",
        "Cardiff",
    ]
    authorities = fetch(
        "https://api.ratings.food.gov.uk/Authorities/basic", "authorities"
    )
    chosen = [a for a in authorities if a["Name"] in get_authorities_names]
    return chosen


def pull_pages(chosen):
    id_authorities = [a["LocalAuthorityId"] for a in chosen]
    establishments = []
    fetched_any = False

    for authority_id in id_authorities:
        page_number = 1
        while True:
            path = RAW / f"{authority_id}_{page_number}.json"
            url = (
                f"https://api.ratings.food.gov.uk/Establishments?localAuthorityId={authority_id}"
                f"&sortOptionKey=alpha&pageNumber={page_number}&pageSize=200"
            )
            if path.exists():
                new_establishments = json.loads(path.read_text(encoding="utf-8"))
            else:
                new_establishments = fetch(url, "establishments")
                if not new_establishments:
                    break
                path.write_text(json.dumps(new_establishments), encoding="utf-8")
                fetched_any = True
                time.sleep(1)
            establishments.extend(new_establishments)
            if len(new_establishments) < 200:
                break
            page_number += 1
    return establishments, fetched_any


def write_pull_record(chosen):
    pull = {
        "pulled_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "counts": {a["Name"]: a["EstablishmentCount"] for a in chosen},
    }
    (RAW / "pull.json").write_text(json.dumps(pull, indent=2), encoding="utf-8")


def load_db(chosen, establishments):
    ids = [e["FHRSID"] for e in establishments]
    if len(ids) != len(set(ids)):
        raise SystemExit(
            f"{len(ids) - len(set(ids))} repeated businesses: re-pull before loading"
        )

    expected = sum(a["EstablishmentCount"] for a in chosen)
    if len(establishments) != expected:
        raise SystemExit(
            f"pulled {len(establishments)} of {expected} businesses:"
            f" re-pull before loading"
        )

    conn = sqlite3.connect(HERE / "hygiene.db")
    schema = (HERE / "schema.sql").read_text(encoding="utf-8")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema)

    rows = [
        (
            e["FHRSID"],
            e["LocalAuthorityCode"],
            e["BusinessName"],
            e["RatingValue"],
            e["BusinessType"],
            e["PostCode"],
            e["RatingDate"],
        )
        for e in establishments
    ]
    conn.executemany(
        "INSERT INTO authorities VALUES (?, ?, ?, ?)",
        [
            (
                a["LocalAuthorityId"],
                a["Name"],
                a["EstablishmentCount"],
                a["LocalAuthorityIdCode"],
            )
            for a in chosen
        ],
    )
    conn.executemany("INSERT INTO establishments VALUES (?, ?, ?, ?, ?, ?, ?)", rows)

    conn.commit()
    conn.close()


def main():
    chosen = get_authorities()
    establishments, fetched_any = pull_pages(chosen)
    if fetched_any:
        write_pull_record(chosen)
    load_db(chosen, establishments)


if __name__ == "__main__":
    main()
