import streamlit as st
from modules.google_sheets_utils import get_teachers_df

st.set_page_config(page_title="メイン画面", layout="centered")
st.title("👨‍🏫 教師選択と日付入力")

# 教師マスタからデータを取得
df = get_teachers_df()
teacher_id_map = {
    str(row["teacher_id"]): row["teacher"]
    for _, row in df.iterrows() if row["teacher_id"]
}
teacher_ids = list(teacher_id_map.keys())

# 教師IDと日付を選択
selected_teacher_id = st.selectbox("教師IDを選択してください", teacher_ids)
selected_date = st.date_input("日付を選択してください")

# セッションに保存
st.session_state["teacher_id"] = selected_teacher_id
st.session_state["teacher_name"] = teacher_id_map[selected_teacher_id]
st.session_state["selected_date"] = selected_date

# ページ遷移ボタン
col1, col2 = st.columns(2)
with col1:
    if st.button("🏫 出欠入力へ進む"):
        st.switch_page("pages/1_Homeroom.py")

with col2:
    if st.button("📘 教務入力へ進む"):
        st.switch_page("pages/2_TeachingLog.py")
