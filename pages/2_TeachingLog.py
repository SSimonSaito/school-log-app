import streamlit as st
import datetime
from google_sheets_utils import connect_to_sheet

st.title("📘 Teaching Log（授業記録）")

sheet = connect_to_sheet("teaching_log")
teacher = st.text_input("教師名")
subject = st.text_input("教科")
date = st.date_input("日付", datetime.date.today())
period = st.selectbox("時限", list(range(1, 7)))
summary = st.text_area("授業内容")

if st.button("登録"):
    sheet.append_row([
        str(date),
        teacher,
        subject,
        period,
        summary,
        datetime.datetime.now().isoformat()
    ])
    st.success("授業記録を登録しました。")
