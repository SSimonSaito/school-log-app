import streamlit as st
from modules.google_sheets_utils import get_teachers_df

st.set_page_config(page_title="メイン画面", layout="centered")
st.title("👨‍🏫 教師ID入力と日付選択")

# 教師マスタの取得
df = get_teachers_df()
teacher_dict = {
    str(row["teacher_id"]): row["teacher"]
    for _, row in df.iterrows() if row["teacher_id"]
}

# 教師IDの手動入力
input_teacher_id = st.text_input("教師IDを入力してください").strip()

# 教師名の表示
if input_teacher_id in teacher_dict:
    teacher_name = teacher_dict[input_teacher_id]
    st.success(f"👨‍🏫 教師名: {teacher_name}")
else:
    teacher_name = None
    if input_teacher_id:
        st.warning("❗該当する教師IDが見つかりません。")

# 日付入力
selected_date = st.date_input("📅 日付を選択してください")

# 有効な教師IDが入力されている場合のみ進行可能
if teacher_name:
    # セッションに保存
    st.session_state["teacher_id"] = input_teacher_id
    st.session_state["teacher_name"] = teacher_name
    st.session_state["selected_date"] = selected_date

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏫 出欠入力へ進む"):
            st.switch_page("pages/1_Homeroom.py")

    with col2:
        if st.button("📘 教務入力へ進む"):
            st.switch_page("pages/2_TeachingLog.py")
