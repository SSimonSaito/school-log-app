import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def connect_to_gsheet(sheet_name):
    scopes = st.secrets["gcp"]["scopes"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp"], scopes
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(st.secrets["gcp"]["spreadsheet_id"])
    return spreadsheet.worksheet(sheet_name)
