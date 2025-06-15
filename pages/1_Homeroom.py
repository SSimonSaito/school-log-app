import streamlit as st
from google_sheets_utils import connect_to_sheet, get_existing_attendance
import pandas as pd

st.title("🏫 Homeroom 出欠入力")

if "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.warning("⚠️ main画面から日付と教師を選択してください。")
    st.stop()

teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]

st.write(f"🧑‍🏫 教師: {teacher_name}")
st.write(f"📅 日付: {selected_date}")

book = connect_to_sheet("attendance-shared")
df_existing = get_existing_attendance(book)

if df_existing.empty:
    st.warning("⚠️ 出欠データが読み込めませんでした。")