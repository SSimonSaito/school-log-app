import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import connect_to_sheet, write_attendance

st.set_page_config(page_title="Homeroom 出欠入力", page_icon="🏫", layout="wide")
st.title("🏫 Homeroom 出欠入力")

sheet_id = "1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
sheet = connect_to_sheet(sheet_id, "attendance_log")

# 残りのロジックは前述の通り。省略。
