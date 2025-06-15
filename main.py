
import streamlit as st
from google_sheets_utils import connect_to_sheet
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="教師と日付の選択", page_icon="📅")

sheet_url = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA/edit#gid=0"
sheet_name = "teachers_master"
sheet = connect_to_sheet(sheet_url, sheet_name)

df = pd.DataFrame(sheet.get_all_records())
df.columns = df.columns.str.strip()

teacher_ids = df["id"].dropna().astype(str).tolist()
teacher_id = st.text_input("🧑‍🏫 教師IDを入力してください", value="")

teacher_name = ""
if teacher_id in teacher_ids:
    teacher_name = df[df["id"] == teacher_id]["teacher"].values[0]
    st.success(f"教師名: {teacher_name}")
else:
    st.warning("該当する教師が見つかりません")

date = st.date_input("📅 日付を選択してください", value=datetime.now())

if st.button("➡️ 出欠入力へ") and teacher_name:
    st.switch_page("pages/1_Homeroom.py")
    st.session_state["teacher_name"] = teacher_name
    st.session_state["selected_date"] = date
