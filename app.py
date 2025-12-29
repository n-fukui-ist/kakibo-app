import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import json # 追加

# ==========================================
# 設定
# ==========================================
SPREADSHEET_KEY = "13Hz5QeTEdNrpqfWuJe7BIul2o-EasvEuLWVTOMFTYBI"

# ==========================================
# 関数：Googleスプレッドシートに接続
# ==========================================
def connect_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. パソコンにある "secrets.json" を探す
    if os.path.exists("secrets.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", scope)
    
    # 2. なければ、クラウド上の "Secrets" から読み込む
    else:
        # 文字列として保存されたJSONを読み込んで辞書にする
        key_dict = json.loads(st.secrets["GCP_KEY_JSON"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_KEY).sheet1

# ==========================================
# アプリのメイン画面
# ==========================================
st.title("☁️ クラウド家計簿アプリ")

# --- 入力エリア ---
st.sidebar.header("📝 入力フォーム")
date = st.sidebar.date_input("日付", datetime.date.today())
type_option = st.sidebar.radio("収支", ["支出", "収入"], horizontal=True)
category = st.sidebar.selectbox("カテゴリ", ["食費", "交通費", "日用品", "趣味", "固定費", "給料", "その他"])
item = st.sidebar.text_input("内容 (例: コンビニ)")
amount = st.sidebar.number_input("金額", min_value=0, step=100)

if st.sidebar.button("登録する"):
    with st.spinner("送信中..."):
        try:
            sheet = connect_google_sheet()
            # 支出ならマイナスにする
            signed_amount = amount if type_option == "収入" else -amount
            
            # 日付を文字列に変換
            date_str = date.strftime('%Y-%m-%d')
            
            # 行を追加（リストの順番はシートの列順に合わせる）
            # A列:日付, B列:項目, C列:カテゴリ, D列:金額, E列:タイプ
            row = [date_str, item, category, signed_amount, type_option]
            sheet.append_row(row)
            
            st.sidebar.success("スプレッドシートに保存しました！")
        except Exception as e:
            st.sidebar.error(f"エラーが発生しました: {e}")

# --- データ表示エリア ---
st.subheader("📊 現在のデータ (Google Sheets)")

try:
    sheet = connect_google_sheet()
    # 全データを取得してPandasの表にする
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        # 見やすく表示
        st.dataframe(df, use_container_width=True)
        
        # 合計計算
        total = df["金額"].sum()
        st.metric("現在の残高", f"¥{total:,}")
    else:
        st.info("データがまだありません。")

except Exception as e:
    st.error("スプレッドシートを読み込めませんでした。")
    st.write(e) # textをwriteに変更すると、詳細が見やすくなります
    import traceback
    st.text(traceback.format_exc()) # エラーの発生場所（何行目か）を表示