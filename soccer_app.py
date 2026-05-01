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
            if "月份" in df.columns: df = df.drop(columns=["月份"])
            return df
        except: return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    if "月份" in df.columns: df = df.drop(columns=["月份"])
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

# --- 執行初始化與統計 ---
ensure_files()
update_counters()

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
        invest_types = ['初始', '手動補倉', '補倉']
        total_inv = main_df[main_df['類型'].isin(invest_types)]['金額'].sum()
        real_p = current_bal - total_inv
        if real_p >= 0: st.success(f"📈 純獲利: `${real_p:,}`")
        else: st.error(f"📉 尚虧: `${abs(real_p):,}`")

# --- 旗艦標題設計 ---
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
        <div style="color: #999; font-family: monospace; font-size: 1.1em; margin-top: 10px;">www.ccl-soccer<span style="color: #00c853;">.tw</span></div>
    </div>
""", unsafe_allow_html=True)

# --- 主功能標籤頁 ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 投注下單", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

with tab1: # 投注
    balance = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
    st.components.v1.html("""
        <style>#clock-container { display: flex; align-items: center; background-color: #f8f9fb; padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-family: sans-serif; }</style>
        <div id="clock-container"><span style="font-size:14px;color:#666;margin-right:12px;">台北標準時間 (GMT+8):</span><span id="clock" style="font-size:15px;font-weight:600;"></span></div>
        <script>function up(){ const n=new Date(); document.getElementById('clock').innerHTML=n.toLocaleString(); } setInterval(up,1000); up();</script>
    """, height=52)
    
    @st.dialog("⚠️全額下注確認⚠️")
    def confirm_all_in():
        st.warning(f"確定要將全部餘額 {balance:,} 元一次下注嗎？")
        if st.button("💎 確定全額下注", type="primary", use_container_width=True):
            st.session_state.bet_val = balance; st.rerun()

    m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士")
    colb = st.columns(5)
    if 'bet_val' not in st.session_state: st.session_state.bet_val = 5000
    for i, amt in enumerate([5000, 10000, 15000, 20000]):
        if colb[i].button(f"🔵 {amt:,}"): st.session_state.bet_val = amt; st.rerun()
    if colb[4].button("💎 全額"): confirm_all_in()
    
    c1, c2 = st.columns(2)
    with c1: bet = st.number_input("下注金額", 0, 1000000, int(st.session_state.bet_val))
    with c2: gain = st.number_input("盈利金額", 0, 1000000, value=None)
    
    cw, cl = st.columns(2)
    if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=gain is None):
        new = {"日期": get_now_time(), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain), "盈虧金額": int(gain), "結算總分": balance + int(gain)}
        save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True)); st.rerun()
    if cl.button("❌ 未過關 (輸)", use_container_width=True):
        new = {"日期": get_now_time(), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet), "盈虧金額": -int(bet), "結算總分": balance - int(bet)}
        save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True)); st.rerun()

with tab2: st.dataframe(main_df.iloc[::-1], use_container_width=True)

with tab3: # 統計圖 (修正氣球亂跑問題[cite: 10])
    st.markdown("### 📊 統計圖曲線分析表")
    ready = st.checkbox("🟢 解鎖音效權限 (啟動演示)")
    if ready and not main_df.empty:
        st.line_chart(main_df["結算總分"])
        st.balloons() # 只有勾選演示時才噴氣球
    elif not main_df.empty:
        st.line_chart(main_df["結算總分"])

with tab4: # 報表管理中心[cite: 10]
    with st.expander("補倉"):
        val = st.number_input("金額", 0, 999999, 30000)
        if st.button("執行補倉"):
            bal = int(main_df["結算總分"].iloc[-1])
            new = {"日期": get_now_time(), "賽事項目": "補倉", "類型": "手動補倉", "金額": val, "盈虧金額": 0, "結算總分": bal + val}
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True)); st.rerun()

with tab5: # 討論區 (含回覆與超級管理員[cite: 9])
    if 'reply_to' not in st.session_state: st.session_state.reply_to = ""
    if 'user_nickname' not in st.session_state:
        with st.form("login"):
            name = st.text_input("輸入暱稱：")
            pwd = st.text_input("管理員密碼：", type="password") if name in ["管理員", "阿來"] else ""
            if st.form_submit_button("進入討論區") and name:
                st.session_state.user_nickname = name
                st.session_state.is_admin = (name in ["管理員", "阿來"] and pwd == ADMIN_PASSWORD)
                st.rerun()
    else:
        st.info(f"歡迎回來！您的尊稱：**{st.session_state.user_nickname}**")
        with st.form("chat", clear_on_submit=True):
            msg = st.text_area("留言內容", value=st.session_state.reply_to)
            if st.form_submit_button("送出留言") and msg:
                tag = "管理員" if st.session_state.is_admin else "訪客"
                save_chat(st.session_state.user_nickname, msg, tag)
                st.session_state.reply_to = ""; st.rerun()
        
        c_df = load_chat().sort_values(by="最後活動", ascending=False)
        for idx, r in c_df.iterrows():
            l_color = "#00c853" if r['標籤'] == "管理員" else "#888"
            st.markdown(f"""<div style="border-left: 5px solid {l_color}; padding-left: 15px; margin-bottom: 10px;">
                <strong>{r['暱稱']}</strong> <small style='color: #aaa;'>{r['時間']}</small><br>{r['內容']}</div>""", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 9])
            if c1.button("💬", key=f"r_{idx}"):
                st.session_state.reply_to = f"@{r['暱稱']} "; st.rerun()
            if st.session_state.is_admin and c2.button("🗑️", key=f"d_{idx}"):
                delete_chat(idx); st.rerun()

# --- 底部統計 (黑色純文本[cite: 9]) ---
st.divider()
total_v, online_v = get_counts()
col_left, col_right = st.columns([3, 1])
with col_left:
    st.markdown("<div style='color:#888;font-size:0.9em;'>謹慎理財 信用至上<br>Copyright © 2026 周振來管理系統版權所有</div>", unsafe_allow_html=True)
with col_right:
    st.markdown(f"<div style='color:#888;font-size:0.85em;text-align:right;'>本頁瀏覽訪問次數：{total_v}<br>本站現在在線人數：{online_v}</div>", unsafe_allow_html=True)