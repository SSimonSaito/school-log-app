
import streamlit as st

st.set_page_config(page_title="Homeroom", layout="wide")
st.title("🏫 Homeroom 出欠入力")

if "teacher" not in st.session_state or "date" not in st.session_state:
    st.warning("メイン画面で教師と日付を選択してください。")
    st.stop()

teacher = st.session_state.teacher
date = st.session_state.date

st.write(f"👩‍🏫 教師: {teacher}")
st.write(f"📅 日付: {date}")

# ここに出欠入力機能を後ほど追加予定
