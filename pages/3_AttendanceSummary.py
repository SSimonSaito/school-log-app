# 3_AttendanceSummary.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from modules.google_sheets_utils import connect_to_sheet, get_worksheet_df, get_existing_attendance
from io import StringIO

st.set_page_config(page_title="出欠集計画面", layout="centered")
st.title("📊 出欠集計画面")

# 入力UI
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日", value=pd.to_datetime("2025-06-01").date())
with col2:
    end_date = st.date_input("終了日", value=pd.to_datetime("2025-06-15").date())

book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
classes = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("クラスを選択", classes)

# attendance_log 取得・整形
attendance_df = get_existing_attendance(book, "attendance_log")
# date列を日付型に変換し、エラー行を除去
attendance_df["date"] = pd.to_datetime(attendance_df["date"], errors="coerce").dt.date
attendance_df = attendance_df.dropna(subset=["date"])

# フィルタ処理
mask = (
    (attendance_df["class"] == selected_class) &
    (attendance_df["date"] >= start_date) &
    (attendance_df["date"] <= end_date)
)
attendance_df = attendance_df.loc[mask]

if attendance_df.empty:
    st.info("対象期間・クラスの出欠データが見つかりません。期間やクラスを確認してください。")
    st.stop()

# EHR 出席実績のみ集計
ehr_df = attendance_df.copy()
# 状況ごとの母数・子数換算
weight_map = {
    "○": (1,1), "／":(1,0), "公":(0,0), "病":(0,0),
    "事":(0,0), "忌":(0,0), "停":(0,0), "遅":(1,0.5),
    "早":(1,0.5), "保":(1,1)
}

ehr_df["m"] = ehr_df["status"].map(lambda s: weight_map.get(s, (0,0))[0])
ehr_df["c"] = ehr_df["status"].map(lambda s: weight_map.get(s, (0,0))[1])

# 生徒ごと集計
agg = ehr_df.groupby(["student_id","student_name"]).agg(
    total_m=("m","sum"),
    total_c=("c","sum"),
    count_dates=("date","nunique")
).reset_index()
agg["attendance_rate"] = (agg["total_c"] / agg["total_m"]).fillna(0) * 100

# 可視化テーブル準備
display_df = agg.copy()
display_df["出席率"] = display_df["attendance_rate"].round(1).astype(str) + "%"
display_df = display_df[["student_id","student_name","count_dates","出席率"]]

# ハイライトのスタイリング
def highlight_low(s):
    return ["background-color: #ffcccc" if float(x.rstrip("%")) < 80 else "" for x in s["出席率"]]

styled = display_df.style.apply(highlight_low, axis=1)

st.markdown(f"### 📅 {start_date}〜{end_date}：{selected_class}クラス 出欠集計結果")
st.dataframe(styled, use_container_width=True)

# CSV 書き出しボタン
csv_buf = StringIO()
display_df.to_csv(csv_buf, index=False)
csv_str = csv_buf.getvalue()
st.download_button(
    label="CSVとしてダウンロード",
    data=csv_str,
    file_name=f"attendance_summary_{selected_class}_{start_date}_{end_date}.csv",
    mime="text/csv"
)
