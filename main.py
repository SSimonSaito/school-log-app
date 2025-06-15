import streamlit as st
import pandas as pd
from google_sheets_utils import connect_to_gsheet
from datetime import datetime

st.title("出欠入力アプリ")

sheet = connect_to_gsheet("teachers_master")
df = pd.DataFrame(sheet.get_all_records())

teacher_id = st.text_input("👤 教師IDを入力してください")

if teacher_id:
    teacher_row = df[df["teacher_id"] == teacher_id]
    if not teacher_row.empty:
        teacher_name = teacher_row["teacher"].values[0]
        st.success(f"教師名: {teacher_name}")
        class_name = teacher_row["homeroom_class"].values[0]
        selected_date = st.date_input("📅 日付を選択してください", datetime.now())
        if st.button("出欠入力へ"):
            st.session_state.teacher_id = teacher_id
            st.session_state.teacher_name = teacher_name
            st.session_state.class_name = class_name
            st.session_state.selected_date = selected_date.strftime("%Y-%m-%d")
            st.switch_page("pages/1_Homeroom.py")
    else:
        st.error("該当する教師IDが見つかりません。")
