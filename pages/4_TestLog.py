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
    write_attendance_data
)

st.set_page_config(page_title="📝 テスト結果ログ", layout="wide")
st.title("📝 テスト結果入力・確認")

# セッション確認
if "teacher_id" not in st.session_state:
    st.error("❌ mainページから教師IDを選択してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]

# スプレッドシート接続
book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
subjects_df = get_worksheet_df(book, "subjects_master")

# test_log 読み込み（必要カラムがなければ補完）
try:
    test_log_df = get_worksheet_df(book, "test_log")
except Exception:
    test_log_df = pd.DataFrame()

required_columns = ["date", "teacher_id", "class", "student_id", "student_name", "subject_code", "term", "score"]
for col in required_columns:
    if col not in test_log_df.columns:
        test_log_df[col] = None

# クラス・科目選択
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("🏫 クラスを選択", class_list)

subject_map = dict(zip(subjects_df["subject"], subjects_df["subject_code"]))
selected_subject = st.selectbox("📚 科目を選択", list(subject_map.keys()))
selected_subject_code = subject_map[selected_subject]

# 対象生徒取得
students_in_class = students_df[students_df["class"] == selected_class].copy()

# ターム一覧
terms = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]

# 表構築（縦：生徒、横：term）
st.markdown("### ✏️ テスト結果入力")
test_inputs = []

input_data = {}
for _, student in students_in_class.iterrows():
    sid = student["student_id"]
    sname = student["student_name"]
    input_data[sid] = {"name": sname, "scores": {}}
    st.markdown(f"#### {sname}（{sid}）")
    cols = st.columns(len(terms))
    for i, term in enumerate(terms):
        existing_score = test_log_df[
            (test_log_df["student_id"] == sid) &
            (test_log_df["class"] == selected_class) &
            (test_log_df["subject_code"] == selected_subject_code) &
            (test_log_df["term"] == term)
        ]["score"]
        default_score = int(existing_score.values[0]) if not existing_score.empty and pd.notna(existing_score.values[0]) else ""
        score = cols[i].number_input(f"{term}", min_value=0, max_value=100, value=default_score if default_score != "" else 0, key=f"{sid}_{term}")
        input_data[sid]["scores"][term] = score

if st.button("💾 保存"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now(jst).strftime("%Y-%m-%d")
    rows_to_write = []

    for sid, data in input_data.items():
        for term, score in data["scores"].items():
            if score is not None:
                rows_to_write.append([
                    today,
                    teacher_id,
                    selected_class,
                    sid,
                    data["name"],
                    selected_subject_code,
                    term,
                    score
                ])

    if rows_to_write:
        # 既存行削除
        test_log_df = test_log_df[
            ~(
                (test_log_df["class"] == selected_class) &
                (test_log_df["subject_code"] == selected_subject_code) &
                (test_log_df["student_id"].isin(students_in_class["student_id"]))
            )
        ]
        updated_df = pd.concat([
            test_log_df,
            pd.DataFrame(rows_to_write, columns=required_columns)
        ], ignore_index=True)

        sheet = book.worksheet("test_log")
        sheet.clear()
        sheet.append_row(updated_df.columns.tolist())
        sheet.append_rows(updated_df.values.tolist())

        st.success("✅ テスト結果を保存しました")
    else:
        st.warning("⚠️ 入力されたスコアがありません")
