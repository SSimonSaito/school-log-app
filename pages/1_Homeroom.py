import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import connect_to_sheet

st.title("🏫 Homeroom 出欠入力")

sheet_name = "attendance_log"
sheet = connect_to_sheet(sheet_name)

today = datetime.now() + timedelta(hours=9)

# 一覧読み込み
df_existing = pd.DataFrame(sheet.get_all_records())
if df_existing.empty or "date" not in df_existing.columns:
    st.warning("既存の出欠データがありません。")
else:
    df_existing.columns = df_existing.columns.map(str).str.strip()
    st.dataframe(df_existing)

st.success("出欠データ入力フォームはここに実装予定です。")
