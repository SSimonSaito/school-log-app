import streamlit as st
import pandas as pd
from google_sheets_utils import connect_to_sheet

st.set_page_config(page_title="Teaching Log", page_icon="📒", layout="wide")
st.title("📒 Teaching Log - 出欠入力")

sheet_id = "1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
sheet = connect_to_sheet(sheet_id, "attendance_log")

# 残りのロジックは前述の通り。省略。
