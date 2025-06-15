import streamlit as st
from google_sheets_utils import connect_to_sheet_by_url
from datetime import datetime
import pandas as pd

SHEET_URL = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
book = connect_to_sheet_by_url(SHEET_URL)
sheet = book.worksheet("teachers_master")

df = pd.DataFrame(sheet.get_all_records())
teacher_ids = df["teacher_id"].dropna().astype(str).tolist()

st.title("📅 教師と日付の選択")
teacher_id = st.text_input("🧑‍🏫 教師IDを入力してください")

if teacher_id in teacher_ids:
    teacher_name = df[df["teacher_id"] == teacher_id]["teacher"].values[0]
    st.success(f"教師名: {teacher_name}")
    selected_date = st.date_input("📅 日付を選択してください", datetime.now().date())
    if st.button("➡️ 出欠入力へ"):
        st.session_state.teacher_id = teacher_id
        st.session_state.teacher = teacher_name
        st.session_state.date = selected_date.strftime("%Y-%m-%d")
        st.switch_page("pages/1_Homeroom.py")
else:
    if teacher_id:
        st.warning("有効な教師IDを入力してください")