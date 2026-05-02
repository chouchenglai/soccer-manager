import pytz
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

# 1. 頁面設定 (最頂端)
st.set_page_config(page_title="CCL-Soccer 足球賽事管理系統", page_icon="⚽", layout="wide")

# --- 基本設定 ---
DEFAULT_DB = "soccer_data.csv"
CHAT_DB = "ccl_chat_log.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]
CHAT_COLUMNS = ["時間", "暱稱", "內容", "標籤"]

TW_TZ = pytz.timezone('Asia/Taipei') # 設定台北時區

def get_now_time():
    """獲取精確的台北目前時間"""
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

# --- 工具 ---
def get_all_reports():
    return [f for f in os.listdir('.') if f.endswith('.csv') and f != CHAT_DB]

def ensure_files():
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

def load_data():
    if os.path.exists(st.session_state.current_db):
        try:
            df = pd.read_csv(st.session_state.current_db)
            if "月份" in df.columns:
                df = df.drop(columns=["月份"])
            return df
        except:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    if "月份" in df.columns:
        df = df.drop(columns=["月份"])
    df.to_csv(st.session_state.current_db, index=False, encoding='utf-8-sig')

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
        "標籤": "訪客" if nickname != "admin" else "管理員"
    }
    df = pd.concat([df, pd.DataFrame([new_msg])], ignore_index=True)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

# --- 新增功能：外部跳轉確認對話框 ---
@st.dialog("⚠️ 進入操盤模式確認")
def confirm_dual_mode():
    st.warning("即將開啟雙開模式，本頁面將直接覆蓋為：左側比分 + 右側下單。")
    st.write("這能確保您在同一個視窗內完成所有操作，不被瀏覽器攔截。")
    c_link1, c_link2 = st.columns(2)
    if c_link1.button("✅ 確定進入", type="primary", use_container_width=True):
        st.session_state.dual_mode = True
        st.rerun()
    if c_link2.button("取消", use_container_width=True):
        st.rerun()

# --- 初始化 ---
ensure_files()

if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

if 'dual_mode' not in st.session_state:
    st.session_state.dual_mode = False

all_reports = get_all_reports()

if not all_reports:
    all_reports = [DEFAULT_DB]

if st.session_state.current_db not in all_reports:
    st.session_state.current_db = all_reports[0]

main_df = load_data()

# --- 標誌顯示區 (Base64) ---
import base64
def get_base64_img(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "ccl_logo_header.jpg"

if os.path.exists(img_path):
    img_b64 = get_base64_img(img_path)
    st.markdown(f"""
        <style>
            .banner-box {{
                width: 100%;
                text-align: center;
                background-color: #ffffff;
                padding: 0px 0;
                margin-bottom: -15px;
                border-radius: 12px;
                overflow: hidden;
            }}
            .banner-img {{
                max-width: 100%;
                height: auto;
                transform: scale(1.15);
                transform-origin: center;
                display: block;
                margin: 0 auto;
            }}
        </style>
        <div class="banner-box">
            <img src="data:image/jpeg;base64,{img_b64}" class="banner-img">
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align: center; color: #004b93;'>足球走地賽事管理系統</h2>", unsafe_allow_html=True)

# --- Sidebar (側邊欄) ---
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
        invest_types = ['初始', '手動補倉', '補倉']
        total_investment = main_df[main_df['類型'].isin(invest_types)]['金額'].sum()
        st.write(f"💼 累積投入: `${total_investment:,}`")
        real_profit = current_bal - total_investment
        if real_profit >= 0:
            st.success(f"📈 純獲利: `${real_profit:,}`")
        else:
            st.error(f"📉 尚虧: `${abs(real_profit):,}`")

    st.write(f"檔案: `{st.session_state.current_db}`")
    st.divider()
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

# --- 邏輯判斷與主功能 ---
if main_df.empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()

# --- 核心：操盤模式狀態判斷 ---
elif st.session_state.dual_mode:
    if st.button("⬅️ 退出操盤模式 (返回系統主頁)", use_container_width=True):
        st.session_state.dual_mode = False
        st.rerun()
    
    st.divider()
    col_live, col_bet = st.columns([6, 4])
    
    with col_live:
        st.markdown("##### 📡 球探即時比分 (同步監控)")
        st.components.v1.iframe("https://live.titan007.com/indexall_big.aspx", height=800, scrolling=True)
    
    with col_bet:
        st.markdown("##### ✍️ 快速下單區")
        m_info_dual = st.text_area("複製左側賽事貼上到此處", placeholder="例如：德甲 拜仁 vs 多特", key="dual_info", height=150)
        try: balance = int(main_df["結算總分"].iloc[-1])
        except: balance = 0
        
        d_c1, d_c2 = st.columns(2)
        d_bet = d_c1.number_input("下注金額", 0, balance, 5000, key="d_bet")
        d_gain = d_c2.number_input("盈利金額", 0, 1000000, value=None, placeholder="贏則輸入", key="d_gain")
        
        if st.button("✅ 快速提交 (贏)", use_container_width=True, type="primary", disabled=d_gain is None):
            new_row = {"日期": get_now_time(), "賽事項目": m_info_dual, "類型": "贏 (+)", "金額": int(d_gain), "盈虧金額": int(d_gain), "結算總分": balance + int(d_gain)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()
        if st.button("❌ 快速提交 (輸)", use_container_width=True):
            new_row = {"日期": get_now_time(), "賽事項目": m_info_dual, "類型": "輸 (-)", "金額": int(d_bet), "盈虧金額": -int(d_bet), "結算總分": balance - int(d_bet)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

else:
    # 正常模式 Tab
    tab1, tab0, tab2, tab3, tab4, tab5 = st.tabs(["💰 下單投注", "📺 即時比分", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

    with tab1: # 下單投注
        try: balance = int(main_df["結算總分"].iloc[-1])
        except: balance = 0
        if "bet_val" not in st.session_state: st.session_state.bet_val = 5000
        st.components.v1.html("""
            <style>
                #clock-container { display: flex; align-items: center; background-color: #f8f9fb; padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-family: sans-serif; margin-bottom: 5px; }
                #clock { font-size: 15px; font-weight: 600; color: #31333f; letter-spacing: 0.8px; }
            </style>
            <div id="clock-container"><span id="clock">載入中...</span></div>
            <script>
                function updateClock() {
                    const now = new Date();
                    document.getElementById('clock').textContent = "台北標準時間 (GMT+8) : " + now.toLocaleDateString() + " " + now.getHours().toString().padStart(2,'0') + ":" + now.getMinutes().toString().padStart(2,'0') + ":" + now.getSeconds().toString().padStart(2,'0');
                }
                setInterval(updateClock, 1000); updateClock();
            </script>
        """, height=52)

        @st.dialog("⚠️全額下注確認⚠️")
        def confirm_all_in():
            st.warning(f"確定要將全部餘額 {balance:,} 元一次下注嗎？")
            c_conf1, c_conf2 = st.columns(2)
            if c_conf1.button("💎 確定全額下注", type="primary", use_container_width=True):
                st.session_state.bet_val = balance
                st.rerun()
            if c_conf2.button("取消", use_container_width=True):
                st.rerun()

        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")
        colb = st.columns(5)
        amounts = [5000, 10000, 15000, 20000]
        labels = ["🔵 5,000", "🟢 10,000", "🟡 15,000", "🔴 20,000"]
        for i in range(4):
            if colb[i].button(labels[i]):
                st.session_state.bet_val = amounts[i]; st.rerun()
        if colb[4].button("💎 全額（梭哈）"):
            confirm_all_in()

        c1, c2 = st.columns(2)
        with c1: bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        with c2: gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")
        
        tz_taipei = timezone(timedelta(hours=8))
        can_submit = balance > 0 and bet_amt > 0 and bet_amt <= balance
        cw, cl = st.columns(2)

        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not can_submit or gain_amt is None):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

        if cl.button("❌ 未過關 (輸)", use_container_width=True, disabled=not can_submit):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

    with tab0: # 即時比分切換按鈕
        st.subheader("📺 進入雙開操盤模式")
        st.info("點擊下方按鈕後，本頁面將切換為『左側看比分、右側直接下單』佈局。")
        if st.button("🚀 確認進入操盤模式", type="primary", use_container_width=True):
            confirm_dual_mode()

    with tab2: # 歷史記錄
        st.dataframe(main_df.iloc[::-1], use_container_width=True)
    with tab3: # 統計圖表
        st.line_chart(main_df["結算總分"], height=320)
    with tab4: # 報表管理
        with st.expander("補倉"):
            val = st.number_input("金額", 0, 999999999, 30000)
            if st.button("補"):
                bal = int(main_df["結算總分"].iloc[-1])
                new = {"日期":get_now_time(), "賽事項目": "補倉", "類型": "手動補倉", "金額": val, "盈虧金額": 0, "結算總分": bal + val}
                save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True)); st.rerun()
    with tab5: # 討論區
        st.markdown("### 💬 足球現場實況滾球推薦")
        # (保留原本討論區邏輯...)

# --- 底部宣告 ---
st.divider()
st.markdown("""<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來足球管理系統版權所有</div>""", unsafe_allow_html=True)