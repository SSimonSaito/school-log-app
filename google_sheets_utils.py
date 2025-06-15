
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import streamlit as st

def connect_to_sheet(sheet_name):
    try:
        creds_dict = st.secrets["gcp"]
        credentials = Credentials.from_service_account_info(creds_dict)
        credentials.refresh(Request())  # 明示的にリフレッシュ
        client = gspread.authorize(credentials)
        return client.open(sheet_name)
    except Exception as e:
        st.error(f"[接続エラー] Google Sheets にアクセスできませんでした: {e}")
        raise

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    date_str = date_override.strftime('%Y-%m-%d') if date_override else datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([date_str, timestamp, class_name, student_id, student_name, status, entered_by])

def get_latest_attendance(sheet, class_name, date_str):
    df = load_master_dataframe(connect_to_sheet(st.session_state.get("sheet_name","attendance-shared")), "attendance-shared")
    df = df[(df["class"] == class_name) & (df["date"] == date_str)]
    latest = {}
    for _, r in df.iterrows():
        sid = r["student_id"]
        ts = r["timestamp"]
        if sid not in latest or ts > latest[sid][1]:
            latest[sid] = (r["status"], ts)
    return {sid: st for sid, (st, _) in latest.items()}
