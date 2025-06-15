import streamlit as st
from google_sheets_utils import connect_to_sheet
import pandas as pd

st.set_page_config(page_title="School Log App", layout="centered")

sheet_url = st.secrets["sheet_url"]
sheet = connect_to_sheet(sheet_url, "teachers_master")

df = pd.DataFrame(sheet.get_all_records())
df.columns = df.columns.str.strip()

st.title("🎓 出欠・授業記録システム")

teacher_id = st.text_input("👤 教師IDを入力してください（例: T001）")

if teacher_id:
    match = df[df["teacher_id"] == teacher_id.strip()]
    if not match.empty:
        teacher_name = match.iloc[0]["teacher"]
        st.success(f"教師名: {teacher_name}")
        if st.button("📋 出欠入力へ"):
            st.session_state.teacher_name = teacher_name
            st.session_state.teacher_id = teacher_id
            st.switch_page("pages/1_Homeroom.py")
    else:
        st.error("該当する教師IDが見つかりません。")
