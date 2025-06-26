import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# =========================
# 📌 フォント設定
# =========================
font_path = "/mnt/data/ipaexg.ttf"  # アップロードされたフォントパス
jp_font = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = jp_font.get_name()

# =========================
# ⚙️ Streamlit UI設定
# =========================
st.set_page_config(page_title="🧮 テスト分析", layout="wide")
st.title("🧮 テスト結果分析")

# =========================
# 📗 スプレッドシート接続
# =========================
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# =========================
# 🔽 プルダウン選択肢の準備
# =========================
subject_dict = dict(zip(subjects_df["subject"], subjects_df["subject_code"]))
subject_list = list(subject_dict.keys())

term_list = [
    "1学期中間", "1学期期末",
    "2学期中間", "2学期期末",
    "3学期期末"
]

class_list = [
    "1A", "1B", "1C", "1D",
    "2A", "2B", "2C", "2D",
    "3A", "3B", "3C", "3D"
]

# =========================
# 🎛️ UIでフィルター指定
# =========================
selected_subject = st.selectbox("📘 科目を選択", subject_list)
selected_subject_code = subject_dict[selected_subject]
selected_term = st.selectbox("🗓️ テスト期間を選択", term_list)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", class_list, default=class_list[:1])

# =========================
# 🧹 データ抽出・前処理
# =========================
filtered_df = test_log_df[
    (test_log_df["subject_code"] == selected_subject_code) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")

# =========================
# 📊 統計と分布表示
# =========================
if filtered_df.empty:
    st.warning("該当するデータが見つかりませんでした。")
else:
    # 🔢 統計情報表示
    stats = {
        "📈 平均": round(filtered_df["score"].mean(), 2),
        "👿 最低点": int(filtered_df["score"].min()),
        "🏆 最高点": int(filtered_df["score"].max()),
        "⚖️ 中央値": round(filtered_df["score"].median(), 2),
        "📏 標準偏差": round(filtered_df["score"].std(), 2)
    }

    st.subheader("📊 統計情報")
    stat_cols = st.columns(len(stats))
    for col, (label, value) in zip(stat_cols, stats.items()):
        col.metric(label, value)

    # 📈 分布図（KDE）
    st.subheader("📈 スコア分布（カーネル密度推定）")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.kdeplot(filtered_df["score"], shade=True, ax=ax, color="royalblue")
    ax.set_title(f"{selected_term} の {selected_subject} 分布", fontproperties=jp_font, fontsize=16)
    ax.set_xlabel("スコア", fontproperties=jp_font)
    ax.set_ylabel("密度", fontproperties=jp_font)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.grid(True)

    st.pyplot(fig)
