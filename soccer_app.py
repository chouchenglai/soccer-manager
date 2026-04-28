import pytz
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets_connection import GSheetsConnection

# --- 核心連接 ---
# 建立 Google Sheets 連接
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 基本設定 ---
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]
TW_TZ = pytz.timezone('Asia/Taipei')

def get_now_time():
    """獲取精確的台北目前時間"""
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

# --- 數據處理工具 ---
def load_data():
    # 使用您改好的英文標籤名稱 Sheet1，並設定不快取以即時更新
    return conn.read(worksheet="Sheet1", ttl=0)

def save_data(df):
    # 移除自動生成的月份欄位，確保資料格式與 Google Sheets 一致
    if "月份" in df.columns:
        df = df.drop(columns=["月份"])
    try:        
        # 將資料完整更新回雲端 Google Sheets
        conn.update(worksheet="Sheet1", data=df)
        # 清除快取，讓 App 下一次讀取時能看到剛存進去的資料
        st.cache_data.clear()
        st.success("✅ 數據已成功同步至 Google Sheets！")
    except Exception as e:
        st.error(f"❌ 同步失敗，請檢查 Secrets 設定：{e}")

# --- 初始化讀取數據 ---
main_df = load_data()

# --- 側邊欄 ---
st.set_page_config(page_title="足球管理系統", layout="wide")
st.sidebar.title("⚽ 足球投資管理系統")
st.sidebar.info(f"📅 台北時間：{get_now_time()}")

# --- 主介面分頁 ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 數據錄入", "📜 歷史紀錄", "📈 趨勢分析", "⚙️ 系統設定"])

# --- TAB1: 數據錄入 ---
with tab1:
    st.subheader("新增比賽紀錄")
    m_info = st.text_input("賽事項目 (如: 英超 曼聯vs利物浦)")
    gain_amt = st.number_input("下注金額 / 盈虧", value=1000)
    
    # 取得當前餘額（最後一筆的結算總分）
    balance = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
    st.metric("當前錢包餘額", f"${balance:,}")

    cw1, cw2 = st.columns(2)
    
    if cw1.button("✅ 過關 (贏)", use_container_width=True):
        new_row = {
            "日期": get_now_time(),
            "賽事項目": m_info if m_info else "未命名賽事",
            "類型": "贏 (+)",
            "金額": int(gain_amt),
            "盈虧金額": int(gain_amt),
            "結算總分": balance + int(gain_amt)
        }
        save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
        st.rerun()

    if cw2.button("❌ 未過關 (輸)", use_container_width=True):
        new_row = {
            "日期": get_now_time(),
            "賽事項目": m_info if m_info else "未命名賽事",
            "類型": "輸 (-)",
            "金額": int(gain_amt),
            "盈虧金額": -int(gain_amt),
            "結算總分": balance - int(gain_amt)
        }
        save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
        st.rerun()

    st.divider()
    st.write("### 最近 5 筆紀錄")
    st.dataframe(main_df.tail(5), use_container_width=True)

# --- TAB2: 歷史紀錄 ---
with tab2:
    st.subheader("所有歷史交易詳情")
    st.dataframe(main_df.sort_index(ascending=False), use_container_width=True)

# --- TAB3: 趨勢分析 ---
with tab3:
    st.subheader("資產盈虧趨勢")
    if not main_df.empty:
        st.line_chart(main_df["結算總分"])
        
        data = main_df[main_df['類型'].isin(['贏 (+)', '輸 (-)'])]
        if not data.empty:
            win_count = len(data[data['類型'] == '贏 (+)'])
            st.metric("累積勝率", f"{(win_count/len(data))*100:.1f}%")

# --- TAB4: 系統設定 ---
with tab4:
    st.subheader("帳戶操作")
    with st.expander("💰 手動補倉 (入金)"):
        val = st.number_input("補倉金額", min_value=0, value=10000)
        if st.button("確認補倉"):
            bal = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
            new = {
                "日期": get_now_time(),
                "賽事項目": "手動補倉",
                "類型": "補倉",
                "金額": val,
                "盈虧金額": 0,
                "結算總分": bal + val
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()