import streamlit as st
import pandas as pd
from google_sheets_utils import connect_to_sheet

st.title("🏫 Homeroom 出欠入力")

if "teacher" not in st.session_state or "date" not in st.session_state:
    st.warning("メインページで教師と日付を選択してください")
    st.stop()

teacher = st.session_state.teacher
date = st.session_state.date

st.write(f"👨‍🏫 教師: {teacher}")
st.write(f"📅 日付: {date}")
