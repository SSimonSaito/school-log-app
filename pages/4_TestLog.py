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
    get_existing_attendance,
    write_attendance_data,
)

st.set_page_config(page_title="テスト結果入力・確認", layout="wide")
st.title("📝 テスト結果入力・確認")

# Google Sheets に接続
book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
subjects_df = get_worksheet_df(book, "subjects_master")
testlog_df = get_worksheet_df(book, "test_log") if "test_log" in [ws.title for ws in book.worksheets()] else pd.DataFrame()

# 教師IDの入力
teacher_id = st.text_input("👨‍🏫 教師IDを入力してください")

# クラス選択
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("🏫 クラスを選択", class_list)

# 科目選択（プルダウン）
subject_options = subjects_df["subject"].dropna().tolist()
selected_subject = st.selectbox("📚 科目を選択", subject_options)

# 学期・試験区分
term_options = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
selected_term = st.selectbox("🗓️ 試験区分を選択", term_options)

# 対象生徒データの抽出
students_in_class = students_df[students_df["class"] == selected_class].copy()
students_in_class = students_in_class.sort_values("student_id")

# 既存スコアの読み込み（subject, term, class 単位）
if not testlog_df.empty:
    existing_scores = testlog_df[
        (testlog_df["class"] == selected_class) &
        (testlog_df["subject"] == selected_subject) &
        (testlog_df["term"] == selected_term)
    ]
else:
    existing_scores = pd.DataFrame()

# 入力欄
st.markdown("### ✏️ 生徒別スコア入力")
score_inputs = []
for _, row in students_in_class.iterrows():
    sid = row["student_id"]
    sname = row["student_name"]
    existing_score = ""
    if not existing_scores.empty:
        existing_row = existing_scores[existing_scores["student_id"] == sid]
        if not existing_row.empty:
            existing_score = existing_row["score"].values[0]

    score = st.number_input(f"{sname}（{sid}）のスコア", min_value=0, max_value=100, step=1, value=int(existing_score) if existing_score != "" else 0)
    score_inputs.append([
        datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        selected_class,
        sid,
        sname,
        selected_subject,
        selected_term,
        score,
        teacher_id
    ])

# 保存ボタン
if st.button("💾 スコアを保存"):
    try:
        # 既存ログから対象範囲を削除（上書き）
        if not testlog_df.empty:
            testlog_df = testlog_df[
                ~(
                    (testlog_df["class"] == selected_class) &
                    (testlog_df["subject"] == selected_subject) &
                    (testlog_df["term"] == selected_term)
                )
            ]
        else:
            testlog_df = pd.DataFrame(columns=[
                "timestamp", "class", "student_id", "student_name",
                "subject", "term", "score", "teacher_id"
            ])

        updated_df = pd.concat([
            testlog_df,
            pd.DataFrame(score_inputs, columns=testlog_df.columns)
        ], ignore_index=True)

        sheet = book.worksheet("test_log") if "test_log" in [ws.title for ws in book.worksheets()] else book.add_worksheet(title="test_log", rows="1000", cols="20")
        sheet.clear()
        sheet.append_row(updated_df.columns.tolist())
        sheet.append_rows(updated_df.values.tolist())

        st.success("✅ スコアを保存しました")
    except Exception as e:
        st.error(f"❌ 保存中にエラーが発生しました: {e}")
