import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
import pytz
from google_sheets_utils import connect_to_sheet, get_worksheet_df, get_existing_attendance

st.set_page_config(page_title="出欠集計画面", layout="centered")
st.title("📊 出欠集計画面")

# — 入力UI —
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日", value=datetime.today().date().replace(day=1))
with col2:
    end_date = st.date_input("終了日", value=datetime.today().date())

students_df = get_worksheet_df(connect_to_sheet("attendance-shared"), "students_master")
class_list = sorted(students_df["class"].unique())
selected_class = st.selectbox("クラスを選択", class_list)

# — データ取得・絞り込み —
attendance_df = get_existing_attendance(connect_to_sheet("attendance-shared"), "attendance_log")
attendance_df["date"] = pd.to_datetime(attendance_df["date"], errors="coerce").dt.date

df = attendance_df[
    (attendance_df["class"] == selected_class) &
    (attendance_df["date"] >= start_date) &
    (attendance_df["date"] <= end_date) &
    (attendance_df["period"] == "EHR")  # ← EHR のデータのみ
][["student_id", "student_name", "status"]]

if df.empty:
    st.info("指定条件に合うEHRの出欠データがありません。")
    st.stop()

# — 出欠集計ロジック —
weight_map = {
    "○": (1,1),
    "／": (1,0),
    "公": (0,0), "病": (0,0), "事": (0,0), "忌": (0,0), "停": (0,0),
    "遅": (1,0.5), "早": (1,0.5),
    "保": (1,1)
}

status_list = ["○","／","公","病","事","忌","停","遅","早","保"]

# グルーピング
grouped = df.groupby(["student_id", "student_name"])["status"].apply(list).reset_index()

# 母数・子数・出席率 および個別カウント追加
grouped["母数"] = grouped["status"].apply(lambda sl: sum(weight_map[s][0] for s in sl))
grouped["子数"] = grouped["status"].apply(lambda sl: sum(weight_map[s][1] for s in sl))
grouped["出席率"] = (grouped["子数"] / grouped["母数"]) * 100
for s in status_list:
    grouped[s] = grouped["status"].apply(lambda sl, s=s: sl.count(s))

# 表示用整形
agg_display = grouped[["student_name", "母数", "子数", "出席率"] + status_list]
agg_display = agg_display.rename(columns={"student_name": "生徒名"})
agg_display["出席率"] = agg_display["出席率"].round(1)

# 条件付き書式：80%未満行を赤背景
def highlight_low(row):
    return ["background-color: #fa1414" if row["出席率"] < 80 else "" for _ in row]

# 表示タイトル
st.markdown(f"📅 {start_date} ～ {end_date} : {selected_class} クラス（EHR）出欠集計結果")

styled = agg_display.style.apply(highlight_low, axis=1)
st.dataframe(styled, use_container_width=True)

# — CSV出力 —
csv = agg_display.to_csv(index=False)
st.download_button("CSVダウンロード", csv, file_name="attendance_summary_ehr.csv", mime="text/csv")
