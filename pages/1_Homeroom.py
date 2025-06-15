import streamlit as st
from google_sheets_utils import connect_to_sheet_by_url, get_existing_attendance
from datetime import datetime
import pandas as pd

st.title("🏫 Homeroom 出欠入力")
st.markdown(f"🧑‍🏫 教師: {st.session_state.teacher}")
st.markdown(f"📅 日付: {st.session_state.date}")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
book = connect_to_sheet_by_url(SHEET_URL)
df_existing = get_existing_attendance(book)

# 必要に応じてこの下に出欠入力のUI処理を追加
st.info("※ 出欠入力UIはここに追加可能です。")