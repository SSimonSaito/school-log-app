
import streamlit as st
import pandas as pd
from google_sheets_utils import load_master_dataframe

st.set_page_config(page_title="School Log App", layout="wide")

st.title("📅 教師と日付の選択")

sheet_name = "teachers_master"
try:
    teacher_df = load_master_dataframe(sheet_name)
    teacher_df.columns = teacher_df.columns.str.strip()
    teacher_df = teacher_df.dropna(subset=["teacher"])
    teacher_df = teacher_df.sort_values("homeroom_class")
    teacher_list = teacher_df["teacher"].tolist()
except Exception as e:
    st.error(f"教師マスタの読み込みに失敗しました: {e}")
    teacher_list = []

with st.form("select_teacher_date"):
    teacher_selected = st.selectbox("👩‍🏫 教師を選択してください", teacher_list)
    date_selected = st.date_input("📅 日付を選択してください")
    submitted = st.form_submit_button("➡️ 出欠入力へ")

if submitted:
    st.session_state.teacher = teacher_selected
    st.session_state.date = str(date_selected)
    st.success(f"{teacher_selected} の {date_selected} の記録を開始します")
