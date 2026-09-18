import json

import gspread
from google.oauth2.service_account import Credentials

from importer import RAW_HEADERS


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def credentials_ready(raw_json: str) -> bool:
    return bool(raw_json and raw_json not in {"__SET_ME__", "SET_ME", "CHANGEME"})


def open_sheet(sheet_id: str, service_account_json: str):
    info = json.loads(service_account_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(sheet_id)


def upsert_fn_raw(sheet_id: str, service_account_json: str, rows: list[dict]) -> dict:
    sh = open_sheet(sheet_id, service_account_json)
    ws = sh.worksheet("FN_RAW")

    existing = ws.get_all_values()
    header = existing[0] if existing else []
    if header != RAW_HEADERS:
        raise RuntimeError("FN_RAW header mismatch")

    key_col = RAW_HEADERS.index("source_variant_id")
    existing_map = {}
    for i, row in enumerate(existing[1:], start=2):
        if len(row) > key_col and row[key_col]:
            existing_map[row[key_col]] = i

    updates = []
    appends = []
    updated = inserted = 0

    for item in rows:
        values = [item.get(h, "") for h in RAW_HEADERS]
        key = str(item.get("source_variant_id") or "")
        if key and key in existing_map:
            row_num = existing_map[key]
            updates.append({
                "range": f"A{row_num}:AC{row_num}",
                "values": [values],
            })
            updated += 1
        else:
            appends.append(values)
            inserted += 1

    if updates:
        ws.batch_update(updates, value_input_option="RAW")
    if appends:
        ws.append_rows(appends, value_input_option="RAW", insert_data_option="INSERT_ROWS")

    return {"inserted": inserted, "updated": updated, "total": len(rows)}
