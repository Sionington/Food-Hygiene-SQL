from pathlib import Path
import json
import requests
import time
import sqlite3
from datetime import datetime, timezone


RAW =  Path(__file__).parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).parent
conn = sqlite3.connect(HERE / "hygiene.db")
schema = (HERE / "schema.sql").read_text(encoding="utf-8")

get_authorities = ["Vale of Glamorgan", "Bridgend", "Newport", "Bristol", "Cardiff"]

def fetch(api_url, api):
    headers = {"Accept": "application/json", "x-api-version": "2"}
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        response = response.json().get(api, [])
        
        #for index, article in enumerate(response[:1], start=1):
            #print(f"Article {index}:\n{json.dumps(article, sort_keys=True, indent=4)}\n")
        return response
    else:
        print(f"Error: {response.status_code}")


def jprint(obj):
    print(json.dumps(obj, sort_keys=True, indent=4))


authorities = fetch(f"https://api.ratings.food.gov.uk/Authorities/basic", "authorities")

chosen = [a for a in authorities if a["Name"] in get_authorities]
id_authorities = [a["LocalAuthorityId"] for a in chosen]

print(id_authorities)

establishments = []
fetched_any = False

for authority_id in id_authorities:
    pageNumber = 1
    while True:
        path = RAW / f"{authority_id}_{pageNumber}.json"
        url = (f"https://api.ratings.food.gov.uk/Establishments?localAuthorityId={authority_id}"
            f"&sortOptionKey=alpha&pageNumber={pageNumber}&pageSize=200")
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
        pageNumber += 1

if fetched_any:
    pull = {"pulled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": {a["Name"]: a["EstablishmentCount"] for a in chosen}}
    (RAW / "pull.json").write_text(json.dumps(pull, indent=2), encoding="utf-8")

ids = [e["FHRSID"] for e in establishments]
if len(ids) != len(set(ids)):
    raise SystemExit(f"{len(ids) - len(set(ids))} repeated businesses: re-pull before loading")

conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(schema)

rows = [(e["FHRSID"], e["LocalAuthorityCode"], e["BusinessName"], e["RatingValue"],
         e["BusinessType"], e["PostCode"], e["RatingDate"]) for e in establishments]
conn.executemany("INSERT INTO authorities VALUES (?, ?, ?, ?)",
                 [(a["LocalAuthorityId"], a["Name"], a["EstablishmentCount"], a["LocalAuthorityIdCode"]) for a in chosen])
conn.executemany("INSERT INTO establishments VALUES (?, ?, ?, ?, ?, ?, ?)", rows)

conn.commit()
conn.close()
