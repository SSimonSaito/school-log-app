import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from gspread.exceptions import APIError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# 最大3回まで再試行、各2秒間隔、APIError発生時のみ
retry_gspread = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(APIError),
    reraise=True
)

@retry_gspread
def connect_to_sheet(sheet_name):
    scopes = st.secrets["gcp"]["scopes"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["gcp"]["spreadsheet_id"])

@retry_gspread
def get_teachers_df():
    book = connect_to_sheet("teachers_master")
    sheet = book.worksheet("teachers_master")
    return pd.DataFrame(sheet.get_all_records())

@retry_gspread
def get_existing_attendance(book, sheet_name="attendance_log"):
    sheet = book.worksheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df

@retry_gspread
def write_attendance_data(book, sheet_name, data):
    sheet = book.worksheet(sheet_name)
    sheet.append_rows(data)

@retry_gspread
def write_status_log(book, sheet_name, data):
    sheet = book.worksheet(sheet_name)
    sheet.append_rows(data)

@retry_gspread
def get_worksheet_df(book, sheet_name):
    sheet = book.worksheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df
