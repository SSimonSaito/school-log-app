import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# フォント読み込み
font_path = "./ipaexg.ttf"
try:
    jp_font = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = jp_font.get_name()
except:
    st.error("❌ 日本語フォントファイル（ipaexg.ttf）が見つかりません。 アプリと同じフォルダにあるかご確認ください。")

# Streamlit 設定
st.set_page_config(page_title="🧮 テスト分析", layout="wide")
st.title("🧮 テスト結果分析")

# スプレッドシートからデータ取得
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")

# 選択UI
subject_list = sorted(test_log_df["subject_code"].dropna().unique())
term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
class_list = [
    "1A", "1B", "1C", "1D",
    "2A", "2B", "2C", "2D",
    "3A", "3B", "3C", "3D"
]

selected_subject = st.selectbox("📘 科目を選択", subject_list)
selected_term = st.selectbox("🗓️ テスト期間を選択", term_list)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", class_list, default=class_list[:1])

# データ抽出と前処理
filtered_df = test_log_df[
    (test_log_df["subject_code"] == selected_subject) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")

if filtered_df.empty:
    st.warning("該当するデータが見つかりませんでした。")
else:
    st.subheader("📊 統計情報")
    stats = {
        "📈 平均": round(filtered_df["score"].mean(), 2),
        "📉 最低点": int(filtered_df["score"].min()),
        "🏆 最高点": int(filtered_df["score"].max()),
        "⚖️ 中央値": round(filtered_df["score"].median(), 2),
        "📏 標準偏差": round(filtered_df["score"].std(), 2)
    }
    stat_cols = st.columns(len(stats))
    for col, (label, value) in zip(stat_cols, stats.items()):
        col.metric(label, value)

    st.subheader("📊 分布図 + KDE（最大15に調整） + 人数表示")

    fig, ax = plt.subplots(figsize=(10, 6))

    # ヒストグラム（人数）描画
    hist = sns.histplot(
        filtered_df["score"],
        bins=20,
        stat="count",
        color="skyblue",
        edgecolor="black",
        alpha=0.6,
        ax=ax,
        label="人数"
    )

    # 各棒の上に人数表示
    for patch in hist.patches:
        height = patch.get_height()
        if height > 0:
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                height + 0.5,
                int(height),
                ha="center",
                va="bottom",
                fontsize=9,
                fontproperties=jp_font
            )

    # KDE 曲線描画
    kde_line = sns.kdeplot(
        filtered_df["score"],
        bw_adjust=1,
        ax=ax,
        color="royalblue",
        label="KDE"
    )

    # KDE をスケーリング
    x = kde_line.lines[0].get_xdata()
    y = kde_line.lines[0].get_ydata()
    if len(y) > 0:
        scale_factor = 15 / max(y)
        kde_line.lines[0].set_ydata(y * scale_factor)

    # 軸設定
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.set_xlabel("スコア", fontproperties=jp_font)
    ax.set_ylabel("人数", fontproperties=jp_font)
    ax.set_title(f"{selected_term} の {selected_subject} 分布", fontproperties=jp_font, fontsize=16)
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
