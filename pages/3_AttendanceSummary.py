import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from google_sheets_utils import connect_to_sheet, get_worksheet_df

st.set_page_config(page_title="出欠集計画面", layout="wide")
st.title("📊 出欠集計画面")
st.markdown("### 集計条件を指定してください")

# 入力項目
start_date = st.date_input("開始日", datetime.today().replace(day=1))
end_date = st.date_input("終了日", datetime.today())

# スプレッドシート接続とデータ取得
book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("クラスを選択", class_list)

attendance_df = get_worksheet_df(book, "attendance_log")
attendance_df["date"] = pd.to_datetime(attendance_df["date"], errors="coerce").dt.date

# MHRのみを対象
attendance_df = attendance_df[attendance_df["period"] == "MHR"]

# 日付・クラスフィルター
filtered = attendance_df[
    (attendance_df["date"] >= start_date)
    & (attendance_df["date"] <= end_date)
    & (attendance_df["class"] == selected_class)
]

# 🔍 条件選択（数値入力＋有効化）
st.markdown("### 🔍 ハイライト条件を設定してください")

use_absent = st.checkbox("欠席回数で絞り込む", value=True)
absent_threshold = st.number_input("欠席回数以上（／）", min_value=0, max_value=365, value=10, step=1) if use_absent else 366

use_late = st.checkbox("遅刻回数で絞り込む", value=False)
late_threshold = st.number_input("遅刻回数以上（遅）", min_value=0, max_value=365, value=10, step=1) if use_late else 366

use_leave = st.checkbox("早退回数で絞り込む", value=False)
leave_threshold = st.number_input("早退回数以上（早）", min_value=0, max_value=365, value=10, step=1) if use_leave else 366

search_logic = st.radio("検索条件の論理", ["AND", "OR"], index=1)

students_in_class = students_df[students_df["class"] == selected_class].copy()

summary_data = []
highlight_indices = []

for idx, student in students_in_class.iterrows():
    sid = student["student_id"]
    sname = student["student_name"]
    data = filtered[filtered["student_id"] == sid]

    counts = {
        "／": 0, "遅": 0, "早": 0,
        "公": 0, "病": 0, "事": 0, "忌": 0, "停": 0, "保": 0, "○": 0
    }

    for status in data["status"]:
        if status in counts:
            counts[status] += 1

    # ハイライト条件判定
    conditions = []
    if use_absent:
        conditions.append(counts["／"] >= absent_threshold)
    if use_late:
        conditions.append(counts["遅"] >= late_threshold)
    if use_leave:
        conditions.append(counts["早"] >= leave_threshold)

    if conditions:
        if (search_logic == "AND" and all(conditions)) or (search_logic == "OR" and any(conditions)):
            highlight_indices.append(idx)

    summary_data.append({
        "生徒": f"{sid}：{sname}",
        **counts
    })

df_summary = pd.DataFrame(summary_data)

# ハイライト関数
def highlight_rows(row):
    idx = row.name
    if idx in highlight_indices:
        return ["background-color: #fa1414"] * len(row)
    return [""] * len(row)

styled = df_summary.style.apply(highlight_rows, axis=1)

# 表示
st.markdown(f"📅 {start_date}〜{end_date}：{selected_class}クラス（MHR）出欠集計結果")
st.dataframe(styled, use_container_width=True)

# ダウンロード
csv = df_summary.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 CSVでダウンロード", data=csv, file_name=f"{selected_class}_出欠集計.csv", mime="text/csv")
