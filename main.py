import streamlit as st
from google_sheets_utils import connect_to_sheet
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="教師と日付の選択", page_icon="📅")

# スプレッドシート接続
sheet_url = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
book = connect_to_sheet(sheet_url)
teacher_df = pd.DataFrame(book.worksheet("teachers_master").get_all_records())

st.title("📅 教師と日付の選択")
with st.form("main_form"):
    teacher_ids = teacher_df["teacher_id"].dropna().astype(str).tolist()
    selected_id = st.text_input("👩‍🏫 教師IDを入力してください", placeholder="例: T001")
    teacher_name = teacher_df.loc[teacher_df["teacher_id"] == selected_id, "teacher"].values[0] if selected_id in teacher_ids else ""
    if teacher_name:
        st.success(f"教師名: {teacher_name}")
        st.session_state["selected_teacher"] = teacher_name
    else:
        st.warning("有効な教師IDを入力してください")
    today = datetime.now() + timedelta(hours=9)
    selected_date = st.date_input("📅 日付を選択してください", today)
    st.session_state["selected_date"] = selected_date.strftime("%Y-%m-%d")
    submitted = st.form_submit_button("➡️ 出欠入力へ")
    if submitted and teacher_name:
        st.switch_page("pages/1_Homeroom.py")