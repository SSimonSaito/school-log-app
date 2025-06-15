import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
import pytz
from google_sheets_utils import connect_to_sheet, get_worksheet_df, get_existing_attendance

st.set_page_config(page_title="出欠集計画面", layout="centered")
st.title("📊 出欠集計画面")

# 入力UI
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日", value=datetime.today().date().replace(day=1))
with col2:
    end_date = st.date_input("終了日", value=datetime.today().date())

students_df = get_worksheet_df(connect_to_sheet("attendance-shared"), "students_master")
class_list = sorted(students_df["class"].unique())
selected_class = st.selectbox("クラスを選択", class_list)

# データ取得・集計
attendance_df = get_existing_attendance(connect_to_sheet("attendance-shared"), "attendance_log")
# date列は既に日付文字列として入ってる前提
attendance_df["date"] = pd.to_datetime(attendance_df["date"], errors="coerce").dt.date
mask = (
    (attendance_df["class"] == selected_class) &
    (attendance_df["date"] >= start_date) &
    (attendance_df["date"] <= end_date)
)
df = attendance_df.loc[mask, ["student_id", "student_name", "status"]]

# 空データハンドリング
if df.empty:
    st.info("指定期間／クラスに出欠記録がありません。")
    st.stop()

# ステータスごとの加算ロジック
weight_map = {
    "○": (1,1),
    "／": (1,0),
    "公": (0,0), "病": (0,0), "事": (0,0), "忌": (0,0), "停": (0,0),
    "遅": (1,0.5), "早": (1,0.5),
    "保": (1,1)
}

agg = df.groupby(["student_id", "student_name"]).status.apply(list).reset_index()
agg["母数"] = agg["status"].apply(lambda sl: sum(weight_map[s][0] for s in sl))
agg["子数"] = agg["status"].apply(lambda sl: sum(weight_map[s][1] for s in sl))
agg["出席率"] = agg["子数"] / agg["母数"] * 100

# フォーマット調整
agg["出席率"] = agg["出席率"].round(1)
agg_display = agg[["student_name", "母数", "子数", "出席率"]].rename(columns={
    "student_name": "生徒名"
})

# 条件付き書式関数
def highlight_low(row):
    return ["background-color: #ffcccc" if row["出席率"] < 80 else "" for _ in row]

# タイトル
st.markdown(f"📅 {start_date} 〜 {end_date} : {selected_class} クラス 出欠集計結果")

# 表示
styled = agg_display.style.apply(highlight_low, axis=1)
st.dataframe(styled, use_container_width=True)

# CSVダウンロード
csv = agg_display.to_csv(index=False)
st.download_button("CSVダウンロード", csv, file_name="attendance_summary.csv", mime="text/csv")
