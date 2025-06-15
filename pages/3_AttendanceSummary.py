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

book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("クラスを選択", class_list)

# ログ取得
attendance_df = get_worksheet_df(book, "attendance_log")
attendance_df = attendance_df[attendance_df["period"] == "EHR"]

# 日付整形とフィルタ
attendance_df["date"] = pd.to_datetime(attendance_df["date"], errors="coerce").dt.date
filtered = attendance_df[
    (attendance_df["date"] >= start_date)
    & (attendance_df["date"] <= end_date)
    & (attendance_df["class"] == selected_class)
]

# 対象生徒
students_in_class = students_df[students_df["class"] == selected_class].copy()

# ステータス定義と重み
status_weights = {"○": 1, "／": 0, "遅": 0.5, "早": 0.5, "保": 1}
countable_statuses = ["○", "／", "遅", "早", "保"]

summary_data = []

for _, student in students_in_class.iterrows():
    sid = student["student_id"]
    sname = student["student_name"]
    data = filtered[filtered["student_id"] == sid]

    total_mother = 0
    total_child = 0
    counts = {k: 0 for k in status_weights}
    counts.update({k: 0 for k in ["公", "病", "事", "忌", "停"]})

    for status in data["status"]:
        if status in status_weights:
            total_mother += 1
            total_child += status_weights[status]
        if status in counts:
            counts[status] += 1

    rate = f"{(total_child / total_mother * 100):.2f}%" if total_mother > 0 else None

    summary_data.append({
        "生徒": f"{sid}：{sname}",
        "出席率": rate,
        **counts
    })

df_summary = pd.DataFrame(summary_data)
df_summary[list(status_weights)] = df_summary[list(status_weights)].astype(int)

# ハイライトルール
def highlight_low(s):
    val = s["出席率"]
    try:
        if val and float(val.rstrip("%")) < 80:
            return ["background-color: #fa1414"] * len(s)
    except:
        pass
    return [""] * len(s)

styled = df_summary.style.apply(highlight_low, axis=1)

# 表示
st.markdown(f"📅 {start_date}〜{end_date}：{selected_class}クラス（EHR）出欠集計結果")
st.dataframe(styled, use_container_width=True)

# CSVダウンロード
csv = df_summary.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 CSVでダウンロード", data=csv, file_name=f"{selected_class}_出欠集計.csv", mime="text/csv")
