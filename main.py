import streamlit as st
import pandas as pd
from google_sheets_utils import connect_to_sheet

st.set_page_config(page_title="School Log App", page_icon="📘")

sheet_name = "teachers_master"
book = connect_to_sheet("attendance-shared")
teacher_df = pd.DataFrame(book.worksheet(sheet_name).get_all_records())

st.title("📅 教師と日付の選択")

teacher_df = teacher_df[teacher_df["teacher"].notna()]
teacher_df["teacher_id"] = teacher_df.index + 1
teacher_df = teacher_df.reset_index(drop=True)

teacher_input = st.text_input("👨‍🏫 教師IDを入力してください", "")
teacher_name = ""

if teacher_input.isdigit():
    teacher_id = int(teacher_input)
    if 1 <= teacher_id <= len(teacher_df):
        teacher_name = teacher_df.iloc[teacher_id - 1]["teacher"]

date = st.date_input("📅 日付を選択してください")

if teacher_name:
    st.session_state.teacher = teacher_name
    st.session_state.date = date.strftime("%Y-%m-%d")
    if st.button("➡️ 出欠入力へ"):
        st.switch_page("pages/1_Homeroom.py")
else:
    st.warning("正しい教師IDを入力してください")
