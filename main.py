import streamlit as st
from google_sheets_utils import connect_to_sheet, get_teacher_name_by_id
from datetime import datetime
import pytz

st.set_page_config(page_title="教師と日付の選択", page_icon="📅")

st.title("📅 教師と日付の選択")

# Google Sheets 接続
book = connect_to_sheet("attendance-shared")
teacher_df = book.worksheet("teachers_master").get_all_records()
teacher_dict = {row["teacher_id"]: row["teacher"] for row in teacher_df if row["teacher_id"]}

# 教師ID入力
teacher_id = st.text_input("🧑‍🏫 教師IDを入力してください")

# 教師名表示
teacher_name = teacher_dict.get(teacher_id.strip())
if teacher_id:
    if teacher_name:
        st.success(f"教師名: {teacher_name}")
    else:
        st.warning("⚠️ 有効な教師IDを入力してください")

# 日付選択
jst = pytz.timezone("Asia/Tokyo")
today = datetime.now(jst).date()
selected_date = st.date_input("📅 日付を選択してください", value=today)

# 出欠入力へ
if teacher_name and st.button("➡️ 出欠入力へ"):
    st.session_state["teacher_id"] = teacher_id
    st.session_state["teacher_name"] = teacher_name
    st.session_state["selected_date"] = str(selected_date)
    st.switch_page("pages/1_Homeroom.py")