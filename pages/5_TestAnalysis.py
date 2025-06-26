import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
import matplotlib.font_manager as fm
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# フォント設定
font_path = "ipaexg.ttf"
try:
    jp_font = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = jp_font.get_name()
except Exception as e:
    st.error("\u274c 日本語フォントファイル（ipaexg.ttf）が見つかりません。 アプリと同じフォルダにあるかご確認ください。")
    st.stop()

# Streamlit UI設定
st.set_page_config(page_title="\U0001f9ee テスト分析", layout="wide")
st.title("\U0001f9ee テスト結果分析")

# スプレッドシート接続
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# subject_code -> subject名に変換
test_log_df = test_log_df.merge(subjects_df, on="subject_code", how="left")

# フィルタUI
subject_list = sorted(subjects_df["subject"].dropna().unique())
term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
class_list = [
    "1A", "1B", "1C", "1D",
    "2A", "2B", "2C", "2D",
    "3A", "3B", "3C", "3D"
]

selected_subject = st.selectbox("\U0001f4d8 科目を選択", subject_list)
selected_term = st.selectbox("\U0001f4c5 テスト期間を選択", term_list)
selected_classes = st.multiselect("\U0001f3eb クラスを選択（複数可）", class_list, default=class_list[:1])

# データ抽出
filtered_df = test_log_df[
    (test_log_df["subject"] == selected_subject) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")

if filtered_df.empty:
    st.warning("該当するデータが見つかりませんでした。")
else:
    # 統計情報表示
    stats = {
        "📈 平均": round(filtered_df["score"].mean(), 2),
        "👿 最低点": int(filtered_df["score"].min()),
        "🏆 最高点": int(filtered_df["score"].max()),
        "⚖️ 中央値": round(filtered_df["score"].median(), 2),
        "📏 標準偏差": round(filtered_df["score"].std(), 2)
    }

    st.subheader("\U0001f4ca 統計情報")
    stat_cols = st.columns(len(stats))
    for col, (label, value) in zip(stat_cols, stats.items()):
        col.metric(label, value)

    # 分布グラフ（KDE + ヒストグラム）
    st.subheader("\U0001f4c8 スコア分布（棒+KDE）")

    scores = filtered_df["score"].dropna()
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    # 棒グラフ（ヒストグラム）
    counts, bin_edges, _ = ax1.hist(
        scores,
        bins=10,
        range=(0, 100),
        color="skyblue",
        edgecolor="black",
        align="mid"
    )

    # 棒グラフ上に人数表示
    for i in range(len(counts)):
        if counts[i] > 0:
            ax1.text(
                (bin_edges[i] + bin_edges[i + 1]) / 2,
                counts[i] + 0.5,
                str(int(counts[i])),
                ha="center",
                fontsize=10
            )

    # KDEスケーリング
    if len(scores) > 1:
        kde = gaussian_kde(scores)
        x_vals = np.linspace(0, 100, 200)
        kde_vals = kde(x_vals)

        # KDE値を棒グラフの最大値にスケーリング
        max_count = counts.max()
        kde_vals_scaled = kde_vals * (max_count / kde_vals.max())

        ax2.plot(x_vals, kde_vals_scaled, color="blue", lw=2)
        ax2.set_ylim(0, max(20, kde_vals_scaled.max() * 1.1))
        ax2.set_ylabel("密度", fontproperties=jp_font)

    # 軸設定
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 30)
    ax1.set_xlabel("スコア", fontproperties=jp_font)
    ax1.set_ylabel("人数", fontproperties=jp_font)
    ax1.set_title(f"{selected_term} の {selected_subject} 分布", fontproperties=jp_font, fontsize=16)

    st.pyplot(fig)
