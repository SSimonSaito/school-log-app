
import gspread
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import streamlit as st
import traceback

def connect_to_sheet(sheet_name):
    try:
        creds_dict = st.secrets["gcp"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        credentials.refresh(Request())
        client = gspread.authorize(credentials)
        return client.open(sheet_name)
    except Exception as e:
        st.error(f"[接続エラー] Google Sheets にアクセスできませんでした: {e}")
        raise

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    try:
        jst = datetime.utcnow() + timedelta(hours=9)
        date_str = date_override.strftime('%Y-%m-%d') if date_override else jst.strftime("%Y-%m-%d")
        timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")
        row_data = [date_str, timestamp, class_name, student_id, student_name, status, entered_by]
        sheet.append_row(row_data)
    except Exception as e:
        st.error(f"[書き込みエラー] 出欠データの書き込みに失敗しました: {e}")
        st.code(traceback.format_exc())
        raise

def overwrite_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    try:
        df = pd.DataFrame(sheet.get_all_records())
        jst = datetime.utcnow() + timedelta(hours=9)
        date_str = date_override.strftime('%Y-%m-%d') if date_override else jst.strftime("%Y-%m-%d")
        timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")
        mask = (
            (df["date"] == date_str) &
            (df["class"] == class_name) &
            (df["student_id"] == student_id) &
            (df["entered_by"] == entered_by)
        )
        indices = df[mask].index.tolist()
        if indices:
            sheet.delete_rows([i + 2 for i in indices])  # header is row 1
        row_data = [date_str, timestamp, class_name, student_id, student_name, status, entered_by]
        sheet.append_row(row_data)
    except Exception as e:
        st.error(f"[上書きエラー] データ上書きに失敗しました: {e}")
        st.code(traceback.format_exc())
        raise

def get_latest_attendance(sheet, class_name, date_str):
    df = load_master_dataframe(connect_to_sheet(st.session_state.get("sheet_name", "attendance-shared")), "attendance_log")
    df = df[(df["class"] == class_name) & (df["date"] == date_str)]
    latest = {}
    for _, r in df.iterrows():
        sid = r["student_id"]
        ts = r["timestamp"]
        if sid not in latest or ts > latest[sid][1]:
            latest[sid] = (r["status"], ts)
    return {sid: st for sid, (st, _) in latest.items()}
