import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from pathlib import Path
import sys

# 📌 modules フォルダへのパス追加
sys.path.append(str(Path(__file__).resolve().parents[1] / "modules"))
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# === フォント設定 ===
root = Path(__file__).resolve().parents[1]
font_path = root / "ipaexg.ttf"

if font_path.exists():
    jp_font = fm.FontProperties(fname=str(font_path))
    plt.rcParams["font.family"] = jp_font.get_name()
else:
    st.error(f"❌ 日本語フォント「ipaexg.ttf」が見つかりません：\n{font_path}")
    st.stop()

# === Streamlit UI設定 ===
st.set_page_config(page_title="🧮 テスト分析", layout="wide")
st.title("🧮 テスト結果分析")

# === Google Sheetsからデータ取得 ===
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# === フィルタ選択肢 ===
subject_dict = dict(zip(subjects_df["subject"], subjects_df["subject_code"]))
terms = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
classes = [f"{grade}{cls}" for grade in range(1, 4) for cls in ["A", "B", "C", "D"]]

selected_subject = st.selectbox("📘 科目を選択", list(subject_dict.keys()))
selected_term = st.selectbox("🗓️ テスト期間を選択", terms)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", classes, default=classes[:1])

# === データ抽出 ===
filtered = test_log_df[
    (test_log_df["subject_code"] == subject_dict[selected_subject]) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()
filtered["score"] = pd.to_numeric(filtered["score"], errors="coerce")

if filtered.empty:
    st.warning("⚠️ 該当するスコアデータが見つかりませんでした。")
    st.stop()

# === 統計表示 ===
stats = {
    "📈 平均": round(filtered["score"].mean(), 2),
    "👿 最低点": int(filtered["score"].min()),
    "🏆 最高点": int(filtered["score"].max()),
    "⚖️ 中央値": round(filtered["score"].median(), 2),
    "📏 標準偏差": round(filtered["score"].std(), 2)
}
cols = st.columns(len(stats))
for col, (label, val) in zip(cols, stats.items()):
    col.metric(label, val)

# === KDE 分布描画（x軸を 0〜100 に固定）===
st.subheader("📈 スコア分布（KDE）")
fig, ax = plt.subplots(figsize=(10, 6))
sns.kdeplot(filtered["score"], fill=True, color="royalblue", ax=ax)
ax.set_title(f"{selected_term} {selected_subject} の分布", fontproperties=jp_font)
ax.set_xlabel("スコア", fontproperties=jp_font)
ax.set_ylabel("密度", fontproperties=jp_font)
ax.set_xlim(0, 100)
ax.grid(True)
st.pyplot(fig)
