import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    write_testscore_data,
)

st.set_page_config(page_title="📝 テスト結果入力", layout="wide")
st.title("📝 テスト結果入力画面")

# 教師ID入力
teacher_id = st.text_input("👨‍🏫 教師IDを入力してください", key="teacher_id_input")

# スプレッドシート接続
book = connect_to_sheet("attendance-shared")
subjects_df = get_worksheet_df(book, "subjects_master")
students_df = get_worksheet_df(book, "students_master")
existing_scores_df = get_worksheet_df(book, "test_log")

# 科目選択（subjects_masterより）
subject_list = subjects_df["subject"].dropna().unique().tolist()
selected_subject = st.selectbox("📘 科目を選択してください", subject_list)

# クラス選択
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("🏫 クラスを選択してください", class_list)

# 当該クラスの生徒取得
students_in_class = students_df[students_df["class"] == selected_class].copy()

# term 定義
term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]

# フォームで入力
st.markdown("### ✏️ テストスコア入力")

# 表形式で入力
score_inputs = {}
for i, student in students_in_class.iterrows():
    student_id = student["student_id"]
    student_name = student["student_name"]
    st.markdown(f"#### {student_name}（{student_id}）")
    cols = st.columns(len(term_list))
    for j, term in enumerate(term_list):
        # 既存スコア確認
        existing_row = existing_scores_df[
            (existing_scores_df["class"] == selected_class) &
            (existing_scores_df["student_id"] == student_id) &
            (existing_scores_df["subject"] == selected_subject) &
            (existing_scores_df["term"] == term)
        ]
        default_score = existing_row["score"].values[0] if not existing_row.empty else ""
        score_inputs[(student_id, student_name, term)] = cols[j].number_input(
            f"{term}", min_value=0, max_value=100, value=int(default_score) if str(default_score).isdigit() else 0, key=f"{student_id}_{term}"
        )

# 保存ボタン
if st.button("💾 保存"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d")
    save_data = []
    for (student_id, student_name, term), score in score_inputs.items():
        if score is not None and score != 0:
            save_data.append([
                now,
                selected_class,
                student_id,
                student_name,
                selected_subject,
                term,
                score,
                teacher_id
            ])
    if save_data:
        try:
            write_testscore_data(book, "test_log", save_data)
            st.success("✅ テストスコアを保存しました")
        except Exception as e:
            st.error(f"❌ 保存に失敗しました: {e}")
    else:
        st.warning("⚠️ 有効なスコアが入力されていません")
