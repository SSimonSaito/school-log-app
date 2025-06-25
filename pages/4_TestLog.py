import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    write_attendance_data,
    write_status_log,
    get_existing_attendance,
)

# UI表示設定
st.set_page_config(page_title="📝 Test Log", layout="wide")
st.title("📝 テスト結果ログ")

# スプレッドシート接続
try:
    book = connect_to_sheet("attendance-shared")
    students_df = get_worksheet_df(book, "students_master")
    subjects_df = get_worksheet_df(book, "subjects_master")
    test_log_df = get_worksheet_df(book, "test_log")
except Exception as e:
    st.error(f"❌ スプレッドシート接続に失敗しました: {e}")
    st.stop()

# UI要素の選択
subject_names = subjects_df["subject"].tolist()
selected_subject_name = st.selectbox("📘 科目を選択", subject_names)
selected_subject_code = subjects_df[subjects_df["subject"] == selected_subject_name]["subject_code"].values[0]

class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("🏫 クラスを選択", class_list)

teacher_id = st.text_input("🧑‍🏫 教師IDを入力してください", "")

# 表示対象の生徒と学期
students_in_class = students_df[students_df["class"] == selected_class].copy()
terms = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]

# デフォルト値取得
filtered_log = test_log_df[
    (test_log_df["class"] == selected_class) &
    (test_log_df["subject_code"] == selected_subject_code)
]

# UI入力用のDataFrame作成
input_scores = pd.DataFrame(index=students_in_class["student_name"], columns=terms)

for _, row in filtered_log.iterrows():
    student_name = row["student_name"]
    term = row["term"]
    score = row["score"]
    if student_name in input_scores.index and term in input_scores.columns:
        input_scores.loc[student_name, term] = score

# 入力フォーム
st.markdown("### ✏️ スコアを入力")
score_inputs = {}
for student in input_scores.index:
    cols = st.columns(len(terms) + 1)
    cols[0].markdown(f"**{student}**")
    for i, term in enumerate(terms):
        key = f"{student}_{term}"
        default_value = input_scores.loc[student, term]
        score_inputs[key] = cols[i + 1].number_input(
            label=term,
            key=key,
            min_value=0,
            max_value=100,
            value=int(default_value) if pd.notnull(default_value) else 0
        )

# 保存処理
if st.button("💾 保存"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    today_str = datetime.now(jst).strftime("%Y-%m-%d")
    rows_to_save = []

    for _, student_row in students_in_class.iterrows():
        student_id = student_row["student_id"]
        student_name = student_row["student_name"]
        for term in terms:
            score_key = f"{student_name}_{term}"
            score = score_inputs.get(score_key)
            if score is not None:
                rows_to_save.append([
                    today_str,
                    teacher_id,
                    selected_class,
                    student_id,
                    student_name,
                    selected_subject_code,
                    term,
                    score,
                    now
                ])

    try:
        # 既存データ削除
        test_log_df = test_log_df[
            ~(
                (test_log_df["class"] == selected_class) &
                (test_log_df["subject_code"] == selected_subject_code)
            )
        ]

        updated_df = pd.concat([
            test_log_df,
            pd.DataFrame(rows_to_save, columns=[
                "date", "teacher_id", "class", "student_id", "student_name",
                "subject_code", "term", "score", "timestamp"
            ])
        ], ignore_index=True)

        sheet = book.worksheet("test_log")
        sheet.clear()
        sheet.append_row(updated_df.columns.tolist())
        sheet.append_rows(updated_df.values.tolist())

        st.success("✅ テストスコアを保存しました。")
    except Exception as e:
        st.error(f"❌ 保存中にエラーが発生しました: {e}")
