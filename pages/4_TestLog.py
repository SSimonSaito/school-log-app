import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from tenacity import retry, stop_after_attempt, wait_fixed
from modules.google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df
)

st.set_page_config(page_title="🔪 テスト入力画面", layout="centered")
st.title("🔪 テストスコア入力")

# セッションチェック
if "teacher_id" not in st.session_state:
    st.error("❌ main画面から教師IDを入力してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def load_data():
    book = connect_to_sheet("attendance-shared")
    students_df = get_worksheet_df(book, "students_master")
    subjects_df = get_worksheet_df(book, "subjects_master")
    test_log_df = get_worksheet_df(book, "test_log")
    return book, students_df, subjects_df, test_log_df

# 再試行機能付きデータ読込
try:
    book, students_df, subjects_df, test_log_df = load_data()
except Exception as e:
    st.error(f"❌ データ読み込みに失敗しました: {e}")
    if st.button("🔁 再試行"):
        st.experimental_rerun()
    st.stop()

# クラスと科目選択
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("🏫 クラスを選択", class_list)

subject_dict = dict(zip(subjects_df["subject_code"], subjects_df["subject"]))
selected_subject_name = st.selectbox("📘 科目を選択", subject_dict.values())
selected_subject_code = next((k for k, v in subject_dict.items() if v == selected_subject_name), None)

# 学期選択肢
term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]

# 表形式スコア入力
st.markdown("## ✏️ テストスコア入力")
students_in_class = students_df[students_df["class"] == selected_class]
score_inputs = {}

for _, student in students_in_class.iterrows():
    student_id = student["student_id"]
    student_name = student["student_name"]
    cols = st.columns(len(term_list) + 1)
    cols[0].markdown(f"**{student_name}**")
    score_inputs[student_id] = {}
    for i, term in enumerate(term_list):
        prior_row = test_log_df[
            (test_log_df["class"] == selected_class) &
            (test_log_df["student_id"] == student_id) &
            (test_log_df["subject"] == selected_subject_name) &
            (test_log_df["term"] == term)
        ]
        default_value = prior_row["score"].values[0] if not prior_row.empty else 10
        score_inputs[student_id][term] = cols[i+1].number_input(
            label=f"{student_name} - {term}",
            value=default_value if pd.notna(default_value) else 10,
            key=f"{student_id}_{term}",
            step=1
        )

# 保存処理
if st.button("📏 保存"):
    try:
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
        today_str = datetime.now(jst).strftime("%Y-%m-%d")

        filtered_df = test_log_df[~(
            (test_log_df["teacher_id"] == teacher_id) &
            (test_log_df["class"] == selected_class) &
            (test_log_df["subject"] == selected_subject_name)
        )]

        new_records = []
        for student_id, term_scores in score_inputs.items():
            student_name = students_df[students_df["student_id"] == student_id]["student_name"].values[0]
            for term, score in term_scores.items():
                if score is not None:
                    new_records.append([
                        today_str, selected_class, student_id, student_name,
                        selected_subject_name, term, score, teacher_id, now
                    ])

        df_to_append = pd.DataFrame(new_records, columns=[
            "date", "class", "student_id", "student_name", "subject",
            "term", "score", "teacher_id", "timestamp"
        ])

        sheet = book.worksheet("test_log")
        sheet.clear()
        sheet.append_row(df_to_append.columns.tolist())
        sheet.append_rows(df_to_append.values.tolist())

        st.success("✅ スコアを保存しました。")
    except Exception as e:
        st.error(f"❌ 保存中にエラーが発生しました: {e}")
