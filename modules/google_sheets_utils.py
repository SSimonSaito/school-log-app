
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz

def connect_to_sheet(sheet_name):
    scopes = st.secrets["gcp"]["scopes"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["gcp"]["spreadsheet_id"]).worksheet(sheet_name)

def get_existing_attendance(book, sheet_name="attendance_log"):
    sheet = book.worksheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df

def write_attendance_data(book, sheet_name, data):
    sheet = book.worksheet(sheet_name)
    sheet.append_rows(data)

def write_status_log(book, sheet_name, data):
    sheet = book.worksheet(sheet_name)
    sheet.append_rows(data)

def get_worksheet_df(book, sheet_name):
    sheet = book.worksheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df
