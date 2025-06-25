import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import sys
import os
from tenacity import retry, stop_after_attempt, wait_fixed

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from google_sheets_utils import connect_to_sheet, get_worksheet_df, write_attendance_data

st.set_page_config(page_title="Test Results Log", layout="wide")
st.title("📝 テスト結果の入力・確認")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def load_data():
    book = connect_to_sheet("attendance-shared")
    students_df = get_worksheet_df(book, "students_master")
    subjects_df = get_worksheet_df(book, "subjects_master")
    try:
        test_log_df = get_worksheet_df(book, "test_log")
    except Exception:
        test_log_df = pd.DataFrame(columns=[
            "date", "teacher_id", "class", "student_id", "student_name", "subject_code", "term", "score"
        ])
    return book, students_df, subjects_df, test_log_df

# --- 初期読み込みエラー対応 ---
load_error = False
try:
    book, students_df, subjects_df, test_log_df = load_data()
except Exception as e:
    st.error(f"❌ データの読み込みに失敗しました: {e}")
    load_error = True

if load_error:
    if st.button("🔁 再試行"):
        st.rerun()
    st.stop()

# --- ユーザー入力 ---
teacher_id = st.text_input("👨‍🏫 教師IDを入力してください")
selected_class = st.selectbox("🏫 クラスを選択", sorted(students_df["class"].dropna().unique()))
selected_subject_name = st.selectbox("📘 科目を選択", subjects_df["subject"].dropna().unique())
selected_subject_code = subjects_df[subjects_df["subject"] == selected_subject_name]["subject_code"].values[0]
terms = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]

students = students_df[students_df["class"] == selected_class].copy()

# --- 表の作成 ---
st.markdown("### ✏️ テストスコア入力")
data = {}

# フィルタ済みの既存ログ
existing_data = test_log_df[
    (test_log_df["class"] == selected_class) &
    (test_log_df["subject_code"] == selected_subject_code)
]

for term in terms:
    data[term] = []

    st.markdown(f"#### {term}")
    for _, row in students.iterrows():
        sid = row["student_id"]
        sname = row["student_name"]

        existing_score_row = existing_data[
            (existing_data["student_id"] == sid) & (existing_data["term"] == term)
        ]
        default_val = existing_score_row["score"].values[0] if not existing_score_row.empty else ""

        score = st.number_input(
            f"{sname}（{sid}）", key=f"{term}_{sid}", min_value=0, max_value=100, value=int(default_val) if default_val != "" else 0, step=1
        ) if default_val != "" else st.number_input(
            f"{sname}（{sid}）", key=f"{term}_{sid}", min_value=0, max_value=100, step=1
        )

        data[term].append({
            "student_id": sid,
            "student_name": sname,
            "score": score
        })

# --- 保存ボタン ---
if st.button("💾 保存"):
    try:
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
        today_str = datetime.now(jst).strftime("%Y-%m-%d")

        new_rows = []
        for term in terms:
            for row in data[term]:
                score_val = row["score"]
                if score_val == "" or pd.isna(score_val):
                    continue
                new_rows.append([
                    today_str, teacher_id, selected_class,
                    row["student_id"], row["student_name"],
                    selected_subject_code, term, score_val
                ])

        df_existing = test_log_df[
            ~(
                (test_log_df["class"] == selected_class) &
                (test_log_df["subject_code"] == selected_subject_code)
            )
        ]
        updated_df = pd.concat([
            df_existing,
            pd.DataFrame(new_rows, columns=test_log_df.columns)
        ], ignore_index=True)

        sheet = book.worksheet("test_log")
        sheet.clear()
        sheet.append_row(updated_df.columns.tolist())
        sheet.append_rows(updated_df.values.tolist())

        st.success("✅ テスト結果を保存しました。")
    except Exception as e:
        st.error(f"❌ 保存中にエラーが発生しました: {e}")
