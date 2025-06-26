import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# 📊 ヘッダー
st.title("📈 テスト結果分析")

# ✅ Google Sheets からデータ取得
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# 🎌 フォント設定
font_path = "./ipaexg.ttf"
jp_font = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = jp_font.get_name()

# 🔽 選択UI
subject_name = st.selectbox("科目を選択してください", subjects_df["subject"].tolist())
selected_subject_code = subjects_df[subjects_df["subject"] == subject_name]["subject_code"].values[0]

term = st.selectbox("学期を選択してください", [
    "1学期中間", "1学期期末",
    "2学期中間", "2学期期末",
    "3学期期末"
])

selected_classes = st.multiselect(
    "クラスを選択してください",
    [f"{g}{s}" for g in range(1, 4) for s in ["A", "B", "C", "D"]],
    default=[]
)

# 🧪 フィルタリング
filtered_df = test_log_df[
    (test_log_df["subject_code"] == selected_subject_code) &
    (test_log_df["term"] == term) &
    (test_log_df["class"].isin(selected_classes))
]

if filtered_df.empty:
    st.warning("データが見つかりませんでした。")
else:
    scores = pd.to_numeric(filtered_df["score"], errors="coerce").dropna()
    
    # 📊 ヒストグラム（分布図）
    fig, ax = plt.subplots()
    bins = np.histogram_bin_edges(scores, bins='auto')
    counts, bins, _ = ax.hist(scores, bins=bins, edgecolor='black', color='skyblue')

    # 数値を棒の上に表示
    for count, x in zip(counts, bins[:-1]):
        ax.text(x + (bins[1] - bins[0])/2, count, str(int(count)), ha='center', va='bottom', fontproperties=jp_font)

    ax.set_title(f"{term}：{subject_name} のスコア分布", fontproperties=jp_font)
    ax.set_xlabel("スコア", fontproperties=jp_font)
    ax.set_ylabel("人数", fontproperties=jp_font)
    st.pyplot(fig)

    # 📌 統計量
    st.markdown("### 📐 テスト統計")
    st.write(f"最高点: {scores.max():.1f} 点")
    st.write(f"最低点: {scores.min():.1f} 点")
    st.write(f"平均点: {scores.mean():.1f} 点")
    st.write(f"中央値: {scores.median():.1f} 点")
    st.write(f"標準偏差: {scores.std():.1f} 点")
