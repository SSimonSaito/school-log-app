import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import sys
import os

# モジュールパス追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df
)

st.set_page_config(page_title="🧪 テスト結果入力", layout="wide")
st.title("🧪 テスト結果入力画面")

# スプレッドシート接続
book = connect_to_sheet("attendance-shared")

# マスター取得
students_df = get_worksheet_df(book, "students_master")
subjects_df = get_worksheet_df(book, "subjects_master")

# 教師ID入力
teacher_id = st.text_input("教師IDを入力してください").strip()

# 科目選択
subject_map = {row["subject"]: row["subject_code"] for _, row in subjects_df.iterrows()}
selected_subject = st.selectbox("科目を選択してください", list(subject_map.keys()))
selected_subject_code = subject_map[selected_subject]

# クラス選択
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("クラスを選択してください", class_list)

# 対象の生徒取得
students_in_class = students_df[students_df["class"] == selected_class].copy()

# 既存データ取得
try:
    test_log_df = get_worksheet_df(book, "test_log")
except Exception:
    test_log_df = pd.DataFrame(columns=[
        "date", "teacher_id", "class", "student_id", "student_name",
        "subject_code", "term", "score"
    ])

# 対象期間（term）
terms = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]

# 入力UI表示
st.markdown("### 📋 スコア入力表")

# 表形式入力のための空のデータフレームを準備
table_data = []
for _, row in students_in_class.iterrows():
    sid = row["student_id"]
    sname = row["student_name"]
    row_data = {"student_id": sid, "student_name": sname}
    for term in terms:
        existing_row = test_log_df[
            (test_log_df["class"] == selected_class) &
            (test_log_df["student_id"] == sid) &
            (test_log_df["subject_code"] == selected_subject_code) &
            (test_log_df["term"] == term)
        ]
        existing_score = (
            int(existing_row["score"].values[0])
            if not existing_row.empty and pd.notna(existing_row["score"].values[0])
            else None
        )
        row_data[term] = existing_score
    table_data.append(row_data)

# スコア入力
updated_data = []
for i, row in enumerate(table_data):
    st.markdown(f"**{row['student_name']} ({row['student_id']})**")
    cols = st.columns(len(terms))
    score_row = {"student_id": row["student_id"], "student_name": row["student_name"]}
    for j, term in enumerate(terms):
        score = cols[j].number_input(
            f"{term}", value=row[term] if row[term] is not None else 10,
            key=f"{row['student_id']}_{term}", step=1, format="%d"
        )
        score_row[term] = score
    updated_data.append(score_row)

# 保存処理
if st.button("💾 保存"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now(jst).strftime("%Y-%m-%d")

    new_records = []
    for row in updated_data:
        sid = row["student_id"]
        sname = row["student_name"]
        for term in terms:
            score = row[term]
            if score is None or score == "":
                continue
            new_records.append([
                today, teacher_id, selected_class,
                sid, sname, selected_subject_code, term, score
            ])

    # 対象範囲を削除
    test_log_df = test_log_df[
        ~(
            (test_log_df["class"] == selected_class) &
            (test_log_df["subject_code"] == selected_subject_code) &
            (test_log_df["student_id"].isin([r["student_id"] for r in updated_data])) &
            (test_log_df["term"].isin(terms))
        )
    ]

    updated_df = pd.concat([
        test_log_df,
        pd.DataFrame(new_records, columns=test_log_df.columns)
    ], ignore_index=True)

    # 書き込み
    sheet = book.worksheet("test_log")
    sheet.clear()
    sheet.append_row(updated_df.columns.tolist())
    sheet.append_rows(updated_df.values.tolist())

    st.success("✅ テスト結果を保存しました")
