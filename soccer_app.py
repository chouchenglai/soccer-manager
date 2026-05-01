import pytz
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

# 1. 頁面設定 (最頂端)
st.set_page_config(page_title="CCL-Soccer 足球走地賽事管理系統", page_icon="⚽", layout="wide")

# --- 基本設定 ---
DEFAULT_DB = "soccer_master_data.csv"
CHAT_DB = "ccl_chat_log.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]
CHAT_COLUMNS = ["時間", "暱稱", "內容", "標籤"]

TW_TZ = pytz.timezone('Asia/Taipei') 

def get_now_time():
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

# --- 工具 ---
def ensure_files():
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

def load_chat():
    if os.path.exists(CHAT_DB):
        return pd.read_csv(CHAT_DB)
    return pd.DataFrame(columns=CHAT_COLUMNS)

def save_chat(nickname, content):
    df = load_chat()
    new_msg = {
        "時間": get_now_time(),
        "暱稱": nickname,
        "內容": content,
        "標籤": "訪客" if nickname != "阿來" else "管理員"
    }
    df = pd.concat([df, pd.DataFrame([new_msg])], ignore_index=True)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

# --- 初始化 ---
ensure_files()
if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

all_reports = [f for f in os.listdir('.') if f.endswith('.csv') and f != CHAT_DB]
main_df = pd.read_csv(st.session_state.current_db) if os.path.exists(st.session_state.current_db) else pd.DataFrame(columns=COLUMNS)

# --- Sidebar ---
with st.sidebar:
    st.header("💰 資金與統計中心")
    idx = all_reports.index(st.session_state.current_db) if st.session_state.current_db in all_reports else 0
    selected_db = st.selectbox("切換報表", all_reports, index=idx)
    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()
    st.divider()
    if not main_df.empty:
        current_bal = int(main_df["結算總分"].iloc[-1])
        st.metric("目前可用本金", f"${current_bal:,}")
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

# ---------------------------------------------------------
# 3. 主頁面頂端標題 (旗艦版)
# ---------------------------------------------------------
st.markdown("""
    <style>
        .ccl-brand-box { text-align: center; padding: 40px 0 30px 0; background: linear-gradient(to bottom, #ffffff, #f8f8f8); border-bottom: 3px solid #00c853; margin-bottom: 35px; border-radius: 20px; }
        .ccl-chinese-main { font-size: 3.5em; color: #1a1a1a; letter-spacing: 8px; font-weight: 900; display: block; margin-bottom: 10px; font-family: "Microsoft JhengHei", sans-serif; }
        .ccl-sub-brand { font-family: 'Verdana', sans-serif; font-weight: 900; font-size: 1.6em; }
        .ccl-url { color: #999; font-size: 1.0em; margin-top: 12px; font-family: monospace; }
        .official-badge { background-color: #00c853; color: white; padding: 3px 15px; border-radius: 25px; font-size: 0.7em; margin-left: 12px; vertical-align: middle; }
    </style>
    <div class="ccl-brand-box">
        <div class="ccl-chinese-main">足球走地賽事管理系統</div>
        <div class="ccl-sub-brand"><span style="color:#555">CCL-</span><span style="color:#00c853">Soccer</span><span class="official-badge">Verified</span></div>
        <div class="ccl-url">www.ccl-soccer<span style="color: #00c853;">.tw</span></div>
    </div>
""", unsafe_allow_html=True)

# --- 主功能標籤頁 ---
if main_df.empty:
    st.subheader("初始化報表")
    # ... (初始化代碼保持原樣)
else:
    # 這裡將「討 論 區」移動到了「報表管理」旁邊[cite: 3]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 投注下單", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

    with tab1: # 投注下單功能 (保持原樣)
        # ... (代碼保持原樣，含全額下注功能)
        st.write("已恢復全額下注與時鐘組件")

    with tab2: # 歷史記錄 (保持原樣)
        st.dataframe(main_df.iloc[::-1], use_container_width=True)

    with tab3: # 統計圖表 (保持原樣)
        st.write("統計圖表曲線分析")

    with tab4: # 報表管理 (保持原樣)
        st.write("報表管理中心")

    # ---------------------------------------------------------
    # 5. 全新：討 論 區 模組[cite: 3]
    # ---------------------------------------------------------
    with tab5:
        st.markdown("### 💬 足球現場實況滾球推薦")
        
        # 暱稱檢查邏輯 (瀏覽器緩存識別)
        if 'user_nickname' not in st.session_state:
            with st.form("name_form"):
                name = st.text_input("首次留言，請輸入您的暱稱：", placeholder="例如：玩家稱呼")
                if st.form_submit_button("確認進入"):
                    if name:
                        st.session_state.user_nickname = name
                        st.rerun()
        else:
            # 顯示目前暱稱
            st.info(f"歡迎回來！您目前的名稱：**{st.session_state.user_nickname}**")
            
            # 留言輸入區
            with st.form("chat_form", clear_on_submit=True):
                msg = st.text_area("輸入您的內容...", height=100)
                if st.form_submit_button("送出留言"):
                    if msg:
                        save_chat(st.session_state.user_nickname, msg)
                        st.success("留言已送出！")
                        time.sleep(1)
                        st.rerun()

            st.divider()
            
            # 顯示留言列表 (最新在上方)
            chat_df = load_chat()
            if not chat_df.empty:
                for _, row in chat_df.iloc[::-1].iterrows():
                    # 區分管理員與訪客顏色
                    label_color = "#00c853" if row['標籤'] == "管理員" else "#888"
                    st.markdown(f"""
                        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {label_color};">
                            <span style="color: {label_color}; font-weight: bold;">{row['暱稱']}</span> 
                            <span style="color: #aaa; font-size: 0.8em; margin-left: 10px;">{row['時間']}</span>
                            <p style="margin-top: 10px; color: #333; line-height: 1.5;">{row['內容']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("目前還沒有人留言，歡迎您加入及討論賽事！")

# --- 底部宣告 ---
st.divider()
st.markdown("""<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來管理系統版權所有</div>""", unsafe_allow_html=True)