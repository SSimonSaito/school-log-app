import streamlit as st
from datetime import datetime

st.title("📘 TeachingLog 授業記録入力")

st.markdown(f"🧑‍🏫 教師: {st.session_state.teacher}")
st.markdown(f"📅 日付: {st.session_state.date}")

st.info("※ 授業記録UIはここに追加可能です。")