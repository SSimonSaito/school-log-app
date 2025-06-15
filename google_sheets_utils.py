
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def connect_to_gsheet():
    scopes = st.secrets["gcp"]["scopes"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet_id = st.secrets["gcp"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id)

def connect_to_sheet(sheet_name):
    return connect_to_gsheet().worksheet(sheet_name)

def get_existing_attendance(book, sheet_name="attendance_log"):
    sheet = book.worksheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df

def write_attendance_data(sheet, data):
    sheet.append_rows(data, value_input_option="USER_ENTERED")

def write_status_log(sheet, data):
    sheet.append_rows(data, value_input_option="USER_ENTERED")
