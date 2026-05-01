import pytz
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

# 1. 頁面設定 (最頂端)
st.set_page_config(page_title="CCL-Soccer", page_icon="⚽", layout="wide")

# --- 基本設定 ---
DEFAULT_DB = "soccer_master_data.csv"
CHAT_DB = "ccl_chat_log.csv"
COUNTER_FILE = "visitor_count.txt"
ACTIVE_USERS_FILE = "active_users.log"
ADMIN_PASSWORD = "ccl888" 
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]
CHAT_COLUMNS = ["時間", "暱稱", "內容", "標籤", "最後活動"]

TW_TZ = pytz.timezone('Asia/Taipei') 

def get_now_time():
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M:%S")

# --- 訪問統計工具 ---
def update_counters():
    if 'visited' not in st.session_state:
        st.session_state.visited = True
        if not os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "w") as f: f.write("1")
        else:
            with open(COUNTER_FILE, "r+") as f:
                content = f.read().strip()
                count = int(content) + 1 if content else 1
                f.seek(0)
                f.write(str(count))
                f.truncate()
    
    now = time.time()
    try:
        session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id
    except:
        session_id = "unknown"
    
    active_users = {}
    if os.path.exists(ACTIVE_USERS_FILE):
        with open(ACTIVE_USERS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    uid, ts = parts
                    if now - float(ts) < 300: 
                        active_users[uid] = ts
    
    active_users[session_id] = now
    with open(ACTIVE_USERS_FILE, "w") as f:
        for uid, ts in active_users.items():
            f.write(f"{uid},{ts}\n")
    
    return active_users

def get_counts():
    try:
        with open(COUNTER_FILE, "r") as f: total_v = f.read().strip()
    except: total_v = "1"
    
    try:
        with open(ACTIVE_USERS_FILE, "r") as f: online_v = len(f.readlines())
    except: online_v = 1
    return total_v, online_v

# --- 數據工具 ---
def ensure_files():
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

def load_data():
    if os.path.exists(st.session_state.current_db):
        try:
            df = pd.read_csv(st.session_state.current_db)
            return df
        except: return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(st.session_state.current_db, index=False, encoding='utf-8-sig')

def load_chat():
    if os.path.exists(CHAT_DB):
        df = pd.read_csv(CHAT_DB)
        if "最後活動" not in df.columns: df["最後活動"] = df["時間"]
        return df
    return pd.DataFrame(columns=CHAT_COLUMNS)

def save_chat(nickname, content, tag="訪客"):
    df = load_chat()
    now = get_now_time()
    new_msg = {"時間": now, "暱稱": nickname, "內容": content, "標籤": tag, "最後活動": now}
    df = pd.concat([df, pd.DataFrame([new_msg])], ignore_index=True)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

def delete_chat(index):
    df = load_chat()
    df = df.drop(index)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

# --- 初始化與統計 ---
ensure_files()
update_counters()[cite: 7]

if 'current_db' not in st.session_state: st.session_state.current_db = DEFAULT_DB
all_reports = [f for f in os.listdir('.') if f.endswith('.csv') and f != CHAT_DB]
if not all_reports: all_reports = [DEFAULT_DB]
main_df = load_data()

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

# --- 標題 ---
st.markdown("""
    <style>
        .ccl-brand-box { text-align: center; padding: 40px 0 30px 0; background: linear-gradient(to bottom, #ffffff, #f8f8f8); border-bottom: 3px solid #00c853; margin-bottom: 35px; border-radius: 20px; }
        .ccl-chinese-main { font-size: 3.5em; color: #1a1a1a; letter-spacing: 8px; font-weight: 900; display: block; margin-bottom: 10px; line-height: 1.2; font-family: "Microsoft JhengHei", sans-serif; }
        .ccl-sub-brand { font-family: 'Verdana', sans-serif; font-weight: 900; font-size: 1.6em; }
        .official-badge { background-color: #00c853; color: white; padding: 3px 15px; border-radius: 25px; font-size: 0.7em; margin-left: 12px; vertical-align: middle; }
    </style>
    <div class="ccl-brand-box">
        <div class="ccl-chinese-main">足球走地賽事管理系統</div>
        <div class="ccl-sub-brand"><span style="color:#555">CCL-</span><span style="color:#00c853">Soccer</span><span class="official-badge">Verified</span></div>
    </div>
""", unsafe_allow_html=True)

# --- 主標籤頁 ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 投注下單", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

with tab1:
    try: balance = int(main_df["結算總分"].iloc[-1])
    except: balance = 0
    st.components.v1.html("""
        <style>#clock-container { display: flex; align-items: center; background-color: #f8f9fb; padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-family: sans-serif; }</style>
        <div id="clock-container"><span style="font-size:14px;color:#666;margin-right:12px;">台北標準時間:</span><span id="clock" style="font-size:15px;font-weight:600;"></span></div>
        <script>function up(){ const n=new Date(); document.getElementById('clock').innerHTML=n.toLocaleString(); } setInterval(up,1000); up();</script>
    """, height=52)
    
    m_info = st.text_area("賽事資訊", placeholder="輸入對陣資訊...")
    colb = st.columns(5)
    if 'bet_val' not in st.session_state: st.session_state.bet_val = 5000
    for i, amt in enumerate([5000, 10000, 15000, 20000]):
        if colb[i].button(f"🔵 {amt:,}"): st.session_state.bet_val = amt; st.rerun()
    
    c1, c2 = st.columns(2)
    with c1: bet = st.number_input("下注金額", 0, 1000000, int(st.session_state.bet_val))
    with c2: gain = st.number_input("盈利金額", 0, 1000000, value=None)
    
    if st.button("✅ 過關 (贏)", use_container_width=True, disabled=gain is None):
        new = {"日期": get_now_time(), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain), "盈虧金額": int(gain), "結算總分": balance + int(gain)}
        save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True)); st.rerun()

with tab2: st.dataframe(main_df.iloc[::-1], use_container_width=True)
with tab3: st.line_chart(main_df["結算總分"])
with tab4: st.write("報表管理中心")

with tab5: # 討論區[cite: 7]
    if 'reply_to' not in st.session_state: st.session_state.reply_to = ""
    if 'user_nickname' not in st.session_state:
        with st.form("name_form"):
            name = st.text_input("輸入暱稱：")
            pwd = st.text_input("密碼 (管理員)：", type="password") if name in ["管理員", "阿來"] else ""
            if st.form_submit_button("進入討論區") and name:
                st.session_state.user_nickname = name
                st.session_state.is_admin = (name in ["管理員", "阿來"] and pwd == ADMIN_PASSWORD)
                st.rerun()
    else:
        with st.form("chat", clear_on_submit=True):
            msg = st.text_area("內容", value=st.session_state.reply_to)
            if st.form_submit_button("送出") and msg:
                save_chat(st.session_state.user_nickname, msg, "管理員" if st.session_state.is_admin else "訪客")
                st.session_state.reply_to = ""; st.rerun()
        
        c_df = load_chat().sort_values(by="最後活動", ascending=False)
        for idx, r in c_df.iterrows():
            st.markdown(f"**{r['暱稱']}** ({r['時間']})")
            st.write(r['內容'])
            if st.button("💬 回覆", key=f"r_{idx}"):
                st.session_state.reply_to = f"@{r['暱稱']} "; st.rerun()
            if st.session_state.is_admin and st.button("🗑️ 刪除", key=f"d_{idx}"):
                delete_chat(idx); st.rerun()

# ---------------------------------------------------------
# 4. 頁面最底部：純文本視覺統一版[cite: 7, 8]
# ---------------------------------------------------------
st.divider()
total_v, online_v = get_counts()

col_left, col_right = st.columns([3, 1])

with col_left:
    st.markdown("""
        <div style="color: #888; font-size: 0.9em; text-align: left;">
            謹慎理財 信用至上<br>
            Copyright © 2026 周振來管理系統版權所有
        </div>
    """, unsafe_allow_html=True)

with col_right:
    # 這裡將字體改為純黑色文本效果，與左側版權資訊呼應
    st.markdown(f"""
        <div style="color: #888; font-size: 0.85em; text-align: right; line-height: 1.6;">
            本頁瀏覽訪問次數：{total_v}<br>
            本站現在在線人數：{online_v}
        </div>
    """, unsafe_allow_html=True)