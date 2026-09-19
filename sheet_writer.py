import json

import gspread
from google.oauth2.service_account import Credentials

from importer import RAW_HEADERS
from master_builder import MASTER_HEADERS, build_master_row


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
    keys = [str(row.get("source_variant_id") or "").strip() for row in rows]
    if any(not key for key in keys):
        raise RuntimeError("FN_RAW write blocked: empty source_variant_id")
    if len(set(keys)) != len(keys):
        raise RuntimeError("FN_RAW write blocked: duplicate source_variant_id in input")

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


def sync_fn_master_from_raw(sheet_id: str, service_account_json: str) -> dict:
    sh = open_sheet(sheet_id, service_account_json)
    raw_ws = sh.worksheet("FN_RAW")
    master_ws = sh.worksheet("FN_MASTER")

    raw_values = raw_ws.get_all_values()
    if not raw_values or raw_values[0] != RAW_HEADERS:
        raise RuntimeError("FN_RAW header mismatch")
    master_values = master_ws.get_all_values()
    if not master_values or master_values[0] != MASTER_HEADERS:
        raise RuntimeError("FN_MASTER header mismatch")

    raw_rows = [dict(zip(RAW_HEADERS, row + [""] * (len(RAW_HEADERS) - len(row)))) for row in raw_values[1:]]
    key_col = MASTER_HEADERS.index("source_variant_id")
    existing_map = {}
    for i, row in enumerate(master_values[1:], start=2):
        padded = row + [""] * (len(MASTER_HEADERS) - len(row))
        key = str(padded[key_col] or "").strip()
        if key:
            existing_map[key] = (i, dict(zip(MASTER_HEADERS, padded)))

    keys = [str(r.get("source_variant_id") or "").strip() for r in raw_rows]
    if any(not k for k in keys):
        raise RuntimeError("FN_MASTER sync blocked: FN_RAW contains empty source_variant_id")
    if len(set(keys)) != len(keys):
        raise RuntimeError("FN_MASTER sync blocked: FN_RAW contains duplicate source_variant_id")

    updates = []
    appends = []
    inserted = updated = 0
    for raw in raw_rows:
        key = str(raw.get("source_variant_id") or "").strip()
        existing_entry = existing_map.get(key)
        existing = existing_entry[1] if existing_entry else {}
        item = build_master_row(raw, existing)
        values = [item.get(h, "") for h in MASTER_HEADERS]
        if existing_entry:
            row_num = existing_entry[0]
            updates.append({
                "range": f"A{row_num}:BB{row_num}",
                "values": [values],
            })
            updated += 1
        else:
            appends.append(values)
            inserted += 1

    if updates:
        master_ws.batch_update(updates, value_input_option="RAW")
    if appends:
        master_ws.append_rows(appends, value_input_option="RAW", insert_data_option="INSERT_ROWS")

    return {"inserted": inserted, "updated": updated, "total": len(raw_rows)}
