import os
import pandas as pd
import pytz
import streamlit as st
import time
from datetime import datetime, timedelta, timezone
import base64

# ==========================================
# 1. 全域初始化與設定
# ==========================================
st.set_page_config(page_title="CCL-Soccer 足球賽事管理系統", page_icon="⚽", layout="wide")

DEFAULT_DB = "soccer_data.csv"
CHAT_DB = "ccl_chat_log.csv"
REQ_FILE = "pending_requests.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]
CHAT_COLUMNS = ["時間", "暱稱", "內容", "標籤"]
REQ_COLS = ["申請編號", "申請日期", "申請名稱", "備註事項", "審核結果"]

TW_TZ = pytz.timezone('Asia/Taipei')

# --- 工具函數 ---
def get_now_time():
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

def get_all_reports():
    # 只抓取存在的 csv 檔案，排除聊天紀錄和申請清單
    return [f for f in os.listdir('.') if f.endswith('.csv') and f not in [CHAT_DB, REQ_FILE]]

def ensure_files():
    """確保所有基礎 CSV 檔案存在，防止讀取崩潰"""
    for db, cols in [(DEFAULT_DB, COLUMNS), (CHAT_DB, CHAT_COLUMNS), (REQ_FILE, REQ_COLS)]:
        if not os.path.exists(db):
            pd.DataFrame(columns=cols).to_csv(db, index=False, encoding='utf-8-sig')

def save_data(df):
    """將數據儲存到當前啟用的帳本"""
    db_path = st.session_state.get('current_db', DEFAULT_DB)
    df.to_csv(db_path, index=False, encoding='utf-8-sig')

def load_data():
    """安全讀取當前報表數據[cite: 2]"""
    db_path = st.session_state.get('current_db', DEFAULT_DB)
    if os.path.exists(db_path):
        try:
            df = pd.read_csv(db_path)
            return df if not df.empty else pd.DataFrame(columns=COLUMNS)
        except:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

# --- 啟動初始化 ---
ensure_files()
if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

main_df = load_data()

# ==========================================
# 2. 視覺 Banner (Base64)
# ==========================================
img_path = "ccl_logo_header.jpg"
if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/jpeg;base64,{img_b64}" style="width: 90%; border-radius: 8px;">
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄 (統計中心)[cite: 2]
# ==========================================
with st.sidebar:
    st.header("💰 資金與統計中心")
    all_reports = get_all_reports()
    
    # 確保當前報表在清單內，防止選單報錯[cite: 2]
    if st.session_state.current_db not in all_reports:
        all_reports.append(st.session_state.current_db)
    
    selected_db = st.selectbox("切換報表", all_reports, index=all_reports.index(st.session_state.current_db))
    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()

    st.divider()
    if not main_df.empty:
        current_bal = int(main_df["結算總分"].iloc[-1])
        st.metric("目前可用本金", f"${current_bal:,}")
        invest_types = ['初始', '手動補倉', '補倉']
        total_inv = main_df[main_df['類型'].isin(invest_types)]['金額'].sum()
        st.write(f"💼 累積投入: `${total_inv:,}`")
        profit = current_bal - total_inv
        if profit >= 0: st.success(f"📈 純獲利: `${profit:,}`")
        else: st.error(f"📉 尚虧: `${abs(profit):,}`")
    else:
        st.info("💡 目前報表尚無數據")

    st.divider()
    csv_data = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整紀錄 (CSV)", data=csv_data, file_name=st.session_state.current_db)

# ==========================================
# 4. 主介面邏輯 (分階段排除故障)[cite: 2]
# ==========================================

# 階段 1：處理空報表初始化
if main_df.empty:
    st.subheader("🚀 初始化新報表")
    st.info(f"帳本「{st.session_state.current_db}」目前是空的，請先建立初始本金。")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("確認建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row]))
        st.rerun()

# 階段 2：當有數據時顯示完整功能 Tabs[cite: 2]
else:
    tab1, tab_live, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 下單投注", "⚽ 即時比分", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討論區"
    ])

    with tab1:
        try: balance = int(main_df["結算總分"].iloc[-1])
        except: balance = 0
        
        st.write(f"當前可用餘額：**{balance:,}**")
        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")
        
        c1, c2 = st.columns(2)
        bet_amt = c1.number_input("下注金額", 0, balance, 5000)
        gain_amt = c2.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")
        
        cw, cl = st.columns(2)
        can_submit = balance > 0 and bet_amt > 0
        
        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not can_submit or gain_amt is None):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

        if cl.button("❌ 未過關 (輸)", use_container_width=True, disabled=not can_submit):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

    with tab_live:
        st.components.v1.iframe("https://live.titan007.com/indexall_big.aspx", height=800, scrolling=True)

    with tab2:
        st.subheader("📜 歷史紀錄")
        st.dataframe(main_df.iloc[::-1], use_container_width=True, hide_index=True)

    with tab3:
        st.line_chart(main_df["結算總分"])

    # 階段 3：修復報表管理 (tab4) 崩潰問題[cite: 2]
    with tab4:
        st.header("📊 報表帳本管理中心")
        try:
            req_df = pd.read_csv(REQ_FILE, dtype={'申請編號': str})
        except:
            req_df = pd.DataFrame(columns=REQ_COLS)

        with st.form("new_request"):
            new_n = st.text_input("請輸入預計建立的報表名稱")
            if st.form_submit_button("確認提交"):
                if new_n:
                    new_id = f"{len(req_df) + 1:04d}"
                    new_row = {"申請編號": new_id, "申請日期": get_now_time(), "申請名稱": new_n, "備註事項": "", "審核結果": "⏳ 審核進行中"}
                    updated_req = pd.concat([req_df, pd.DataFrame([new_row])], ignore_index=True)
                    updated_req.to_csv(REQ_FILE, index=False, encoding='utf-8-sig')
                    
                    # 同步生成實體地基檔[cite: 2]
                    target_csv = f"{new_n}.csv" if not new_n.endswith(".csv") else new_n
                    if not os.path.exists(target_csv):
                        pd.DataFrame(columns=COLUMNS).to_csv(target_csv, index=False, encoding='utf-8-sig')
                    
                    st.success(f"系統訊息：已成功登錄申請 (編號: {new_id})")
                    time.sleep(1); st.rerun()

        st.divider()
        st.subheader("報表審核進度詳情")
        st.dataframe(req_df.iloc[::-1], use_container_width=True, hide_index=True)

    with tab5:
        st.markdown("### 💬 足球現場實況滾球推薦")
        st.write("討論區功能運行中...")

# 頁尾
st.divider()
st.markdown('<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來足球管理系統版權所有</div>', unsafe_allow_html=True)