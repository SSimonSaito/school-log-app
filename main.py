import streamlit as st
from google_sheets_utils import connect_to_sheet
import pandas as pd

st.title("🎓 出欠記録アプリ")

sheet_url = st.secrets["spreadsheet_id"]
sheet = connect_to_sheet(sheet_url, "teachers_master")

df = pd.DataFrame(sheet.get_all_records())

teacher_ids = df["teacher_id"].dropna().astype(str).tolist()
teacher_id_input = st.text_input("👤 教師IDを入力してください")

if teacher_id_input in teacher_ids:
    teacher_name = df.loc[df["teacher_id"] == teacher_id_input, "teacher"].values[0]
    st.success(f"こんにちは、{teacher_name}先生")
    if st.button("出欠入力へ"):
        st.switch_page("pages/1_Homeroom.py")
else:
    st.info("有効な教師IDを入力してください")