
import streamlit as st
from modules.google_sheets_utils import get_teachers_df

st.set_page_config(page_title="メイン画面", layout="centered")
st.title("👨‍🏫 教師選択と日付入力")

df = get_teachers_df()
teacher_id_map = {str(row["teacher_id"]): row["teacher"] for _, row in df.iterrows() if row["teacher_id"]}
teacher_ids = list(teacher_id_map.keys())

selected_teacher_id = st.selectbox("教師IDを選択してください", teacher_ids)
selected_date = st.date_input("日付を選択してください")

if st.button("出欠入力へ進む"):
    st.session_state["teacher_id"] = selected_teacher_id
    st.session_state["teacher_name"] = teacher_id_map[selected_teacher_id]
    st.session_state["selected_date"] = selected_date
    st.switch_page("pages/1_Homeroom.py")
