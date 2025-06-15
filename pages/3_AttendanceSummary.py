import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    get_existing_attendance,
)
import pytz
import io

st.set_page_config(page_title="出欠集計画面", layout="centered")
st.title("📊 出欠集計画面")

# 入力UI
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日", value=datetime.today().date().replace(day=1))
with col2:
    end_date = st.date_input("終了日", value=datetime.today().date())

st.markdown("---")

# クラス選択
book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
class_list = sorted(students_df["class"].dropna().unique())
class_select = st.selectbox("クラスを選択", class_list)

# データ取得
attendance_df = get_existing_attendance(book, "attendance_log")

# EHRのみ対象
attendance_df = attendance_df[attendance_df["period"] == "EHR"].copy()
attendance_df["date"] = pd.to_datetime(attendance_df["date"], errors="coerce").dt.date
attend = attendance_df[
    (attendance_df["class"] == class_select)
    & (attendance_df["date"] >= start_date)
    & (attendance_df["date"] <= end_date)
]

# 出欠ステータスごとの重みマップ
status_map = {
    "○": (1, 1),
    "／": (1, 0),
    "公": (0, 0),
    "病": (0, 0),
    "事": (0, 0),
    "忌": (0, 0),
    "停": (0, 0),
    "遅": (1, 0.5),
    "早": (1, 0.5),
    "保": (1, 1),
}

def calc_row(group):
    total_m = 0
    total_c = 0
    counts = {s: 0 for s in status_map.keys()}
    for s in group["status"]:
        m, c = status_map.get(s, (0, 0))
        total_m += m
        total_c += c
        counts[s] += 1
    rate = total_c / total_m if total_m > 0 else None
    row = {
        "出席率": f"{rate*100:.2f}%" if rate is not None else None,
        **counts
    }
    return pd.Series(row)

grouped = attend.groupby("student_id")
summary = grouped.apply(calc_row).reset_index()

# 生徒名とIDを結合
summary = summary.merge(students_df[["student_id", "student_name"]], on="student_id", how="left")
summary["生徒"] = summary["student_id"] + "：" + summary["student_name"]

# 表示対象のカラム順
cols = ["生徒", "出席率"] + list(status_map.keys())
summary = summary[cols]

# 表示タイトル
st.markdown(f"📅 {start_date.isoformat()} ～ {end_date.isoformat()} : **{class_select} クラス（EHR） 出欠集計結果**")

# 80%未満の行を赤背景でハイライト
def highlight_low(s):
    try:
        v = float(s["出席率"].rstrip("%"))
        if v < 80:
            return ["background-color: #fa1414"] * len(s)
    except:
        pass
    return [""] * len(s)

styled = summary.style.apply(highlight_low, axis=1)
st.dataframe(styled, use_container_width=True)

# CSVダウンロードボタン
csv_data = summary.to_csv(index=False, encoding="utf-8-sig")
b = io.BytesIO(csv_data.encode("utf-8"))
st.download_button("CSV ダウンロード", b, file_name="attendance_summary.csv", mime="text/csv")
