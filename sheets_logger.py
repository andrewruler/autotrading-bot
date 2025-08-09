# sheets_logger.py
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SHEET_TITLE = os.getenv("GS_SHEET_TITLE", "Alpaca_Trades")
TAB_NAME = os.getenv("GS_TAB_NAME", "Trades")
GOOGLE_SA_PATH = os.getenv("GOOGLE_SA_PATH", "alpaca-sheets-key.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_client = None
_ws = None

def _init_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(GOOGLE_SA_PATH, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client

def _ensure_worksheet():
    global _ws
    if _ws is not None:
        return _ws
    gc = _init_client()
    try:
        sh = gc.open(SHEET_TITLE)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(SHEET_TITLE)
        # Share the sheet with the service account in Google Sheets UI if needed

    try:
        ws = sh.worksheet(TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=TAB_NAME, rows=1000, cols=20)

    headers = [
        "timestamp","symbol","side","qty","status",
        "submitted_at","filled_at","submitted_price",
        "filled_avg_price","order_id","notes"
    ]
    existing = ws.row_values(1)
    if existing != headers:
        if existing:
            ws.insert_row(headers, 1)
        else:
            ws.update("A1", [headers])
    _ws = ws
    return _ws

def log_trade_row(row: dict):
    """Append a single trade row to Google Sheets."""
    ws = _ensure_worksheet()
    cols = [
        "timestamp","symbol","side","qty","status",
        "submitted_at","filled_at","submitted_price",
        "filled_avg_price","order_id","notes"
    ]
    vals = [str(row.get(c, "")) for c in cols]
    ws.append_row(vals, value_input_option="USER_ENTERED")

def utcnow():
    return datetime.utcnow().isoformat()
