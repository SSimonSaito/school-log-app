import streamlit as st

st.set_page_config(page_title="School Log App", layout="wide")
st.title("School Log App")

st.markdown("""
このアプリは出欠情報をGoogle Sheetsと連携し、以下の機能を提供します：

- Homeroom（朝・夕）出欠管理
- Teaching Log（授業ごとの出欠管理、定期テスト点数入力）

左のサイドバーから各ページを選択してください。
""")
st.session_state.setdefault("sheet_name", "attendance-shared")
st.session_state.setdefault("json_key_path", "credentials.json")
