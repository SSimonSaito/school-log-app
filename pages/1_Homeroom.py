import streamlit as st
from google_sheets_utils import connect_to_sheet, write_attendance, get_existing_attendance
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Homeroom 出欠入力", page_icon="🏫")
st.title("🏫 Homeroom 出欠入力")

# 教師名と日付取得
teacher = st.session_state.get("selected_teacher", "")
today = st.session_state.get("selected_date", datetime.now().strftime("%Y-%m-%d"))

if not teacher:
    st.warning("教師を選択してください（main画面へ戻る）")
    st.stop()

st.markdown(f"👩‍🏫 教師: {teacher}")
st.markdown(f"📅 日付: {today}")

sheet_url = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
book = connect_to_sheet(sheet_url)
students_df = pd.DataFrame(book.worksheet("students_master").get_all_records())
teachers_df = pd.DataFrame(book.worksheet("teachers_master").get_all_records())

homeroom_class = teachers_df.loc[teachers_df["teacher"] == teacher, "homeroom_class"].values[0]
students = students_df[students_df["class"] == homeroom_class].copy()

# 既存データ取得
df_existing = get_existing_attendance(book)
existing = df_existing[(df_existing["date"] == today) & (df_existing["class"] == homeroom_class) & (df_existing["entered_by"] == "homeroom-morning")]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
default_status = {row["student_id"]: row["status"] for _, row in existing.iterrows()} if not existing.empty else {}

with st.form("homeroom_form"):
    selected_status = {}
    for _, row in students.iterrows():
        sid = row["student_id"]
        label = f'{sid} - {row["student_name"]}'
        default = default_status.get(sid, "○")
        selected_status[sid] = st.radio(label, status_options, index=status_options.index(default), horizontal=True)
    if existing.shape[0] > 0:
        if not st.checkbox("⚠️ 既存データがあります。上書きしますか？", value=False):
            st.stop()
    submitted = st.form_submit_button("📬 出欠を一括登録")
    if submitted:
        for _, row in students.iterrows():
            write_attendance(book.worksheet("attendance_log"), homeroom_class, row["student_id"], row["student_name"], selected_status[row["student_id"]], "homeroom-morning", today)
        st.success("✅ 出欠を登録しました")