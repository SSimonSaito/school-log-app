# pages/3_AttendanceSummary.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from google_sheets_utils import connect_to_sheet, get_worksheet_df, get_existing_attendance

st.set_page_config(page_title="出欠集計", layout="wide")
st.title("📊 出欠集計画面")

# — 入力UI —
st.subheader("集計条件を指定してください")

today = pd.Timestamp.today().date()
start_date = st.date_input("開始日", value=today.replace(day=1))
end_date = st.date_input("終了日", value=today)

# クラス選択（students_master参照）
book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
class_list = sorted(students_df["class"].dropna().unique())
selected_class = st.selectbox("クラスを選択", class_list)

# 絞り込む出欠データ取得（attendance_log）
attendance_df = get_existing_attendance(book, "attendance_log")
attendance_df["date"] = pd.to_datetime(attendance_df["date"]).dt.date
attendance_df = attendance_df[
    (attendance_df["class"] == selected_class) &
    (attendance_df["date"] >= start_date) &
    (attendance_df["date"] <= end_date) &
    (attendance_df["period"] == "EHR")  # EHRベースで集計
].copy()

if attendance_df.empty:
    st.warning("該当データがありません。期間やクラスを確認してください。")
    st.stop()

# — 集計ロジック —
# 状況区分ごとの加算条件
count_def = {
    "○": (1,1),
    "／": (1,0),
    "公": (0,0), "病": (0,0), "事": (0,0), "忌": (0,0), "停": (0,0),
    "遅": (1,0.5), "早": (1,0.5), "保": (1,1)
}

# 生徒ごとの集計
agg_rows = []
for sid, group in attendance_df.groupby("student_id"):
    name = group["student_name"].iloc[0]
    n = d = 0
    for stt in group["status"]:
        m, c = count_def.get(stt, (0,0))
        n += m; d += c
    rate = (d/n*100) if n>0 else None
    agg_rows.append({
        "student_id": sid,
        "student_name": name,
        "対象回数": n,
        "出席数": d,
        "出席率 (%)": round(rate,1) if rate is not None else None
    })

summary_df = pd.DataFrame(agg_rows)

# — テーブル表示 & 条件付き書式 —
def highlight_low(s):
    return ['background-color:salmon' if v < 80 and pd.notna(v) else '' for v in s]

st.markdown(f"### {selected_class}／{start_date} 〜 {end_date} 集計結果")
styled = summary_df.style.apply(highlight_low, subset=["出席率 (%)"])
st.dataframe(styled, use_container_width=True)

# — CSV ダウンロード —
csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
st.download_button("📥 CSVダウンロード", data=csv, file_name=f"{selected_class}_{start_date}_attendance.csv")
