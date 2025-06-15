import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def connect_to_sheet(sheet_url, sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_url(sheet_url).worksheet(sheet_name)

def get_existing_attendance(sheet):
    df = pd.DataFrame(sheet.get_all_records())
    df.columns = df.columns.str.strip()
    return df
