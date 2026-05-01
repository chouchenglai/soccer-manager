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
            if "月份" in df.columns: df = df.drop(columns=["月份"])
            return df
        except: return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    if "月份" in df.columns: df = df.drop(columns=["月份"])
    df.to_csv(st.session_state.current_db, index=False, encoding='utf-8-sig')

def load_chat():
    if os.path.exists(CHAT_DB): return pd.read_csv(CHAT_DB)
    return pd.DataFrame(columns=CHAT_COLUMNS)

def save_chat(nickname, content):
    df = load_chat()
    new_msg = {
        "時間": get_now_time(), "暱稱": nickname, "內容": content,
        "標籤": "訪客" if nickname != "阿來" else "管理員"
    }
    df = pd.concat([df, pd.DataFrame([new_msg])], ignore_index=True)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

# --- 初始化 ---
ensure_files()
if 'current_db' not in st.session_state: st.session_state.current_db = DEFAULT_DB
all_reports = get_all_reports()
if not all_reports: all_reports = [DEFAULT_DB]
if st.session_state.current_db not in all_reports: st.session_state.current_db = all_reports[0]
main_df = load_data()

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
        if real_profit >= 0: st.success(f"📈 純獲利: `${real_profit:,}`")
        else: st.error(f"📉 尚虧: `${abs(real_profit):,}`")
    st.write(f"檔案: `{st.session_state.current_db}`")
    st.divider()
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

# ---------------------------------------------------------
# 3. 主頁面頂端：旗艦標題設計
# ---------------------------------------------------------
st.markdown("""
    <style>
        .ccl-brand-box { text-align: center; padding: 40px 0 30px 0; background: linear-gradient(to bottom, #ffffff, #f8f8f8); border-bottom: 3px solid #00c853; margin-bottom: 35px; border-radius: 20px; }
        .ccl-chinese-main { font-size: 3.5em; color: #1a1a1a; letter-spacing: 8px; font-weight: 900; display: block; margin-bottom: 10px; line-height: 1.2; font-family: "Microsoft JhengHei", "Heiti TC", "PingFang TC", sans-serif; }
        .ccl-sub-brand { font-family: 'Verdana', sans-serif; font-weight: 900; font-size: 1.6em; letter-spacing: 1px; margin: 0; }
        .ccl-url { font-family: 'Courier New', monospace; color: #999; font-size: 1.0em; margin-top: 12px; }
        .official-badge { background-color: #00c853; color: white; padding: 3px 15px; border-radius: 25px; font-size: 0.7em; font-weight: bold; margin-left: 12px; vertical-align: middle; }
    </style>
    <div class="ccl-brand-box">
        <div class="ccl-chinese-main">足球走地賽事管理系統</div>
        <div class="ccl-sub-brand"><span style="color:#555">CCL-</span><span style="color:#00c853">Soccer</span><span class="official-badge">Verified</span></div>
        <div class="ccl-url">www.ccl-soccer<span style="color: #00c853;">.tw</span></div>
    </div>
""", unsafe_allow_html=True)

if main_df.empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 投注下單", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

    with tab1: # 投注下單
        try: balance = int(main_df["結算總分"].iloc[-1])
        except: balance = 0
        if "bet_val" not in st.session_state: st.session_state.bet_val = 5000
        st.components.v1.html("""
            <style>
                #clock-container { display: flex; align-items: center; background-color: #f8f9fb; padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-family: sans-serif; margin-bottom: 5px; }
                #clock { font-size: 15px; font-weight: 600; color: #31333f; letter-spacing: 0.8px; }
                .prefix { font-size: 14px; color: #666; margin-right: 12px; }
            </style>
            <div id="clock-container"><span class="prefix">台北標準時間 (GMT+8) :</span><span id="clock">載入中...</span></div>
            <script>
                function updateClock() {
                    const now = new Date();
                    const hh = String(now.getHours()).padStart(2, '0');
                    const mm = String(now.getMinutes()).padStart(2, '0');
                    const ss = String(now.getSeconds()).padStart(2, '0');
                    document.getElementById('clock').textContent = now.toLocaleDateString() + " " + hh + ":" + mm + ":" + ss;
                }
                setInterval(updateClock, 1000); updateClock();
                window.parent.playAppSound = function(type) {
                    var audio = window.parent.document.getElementById(type + 'Audio');
                    if (audio) { audio.pause(); audio.currentTime = 0; audio.play().catch(e => console.log(e)); }
                };
            </script>
        """, height=52)

        # 3. 定義全額確認對話框
        @st.dialog("⚠️全額下注確認⚠️")
        def confirm_all_in():
            st.warning(f"確定要將全部餘額 {balance:,} 元一次下注嗎？")
            c_conf1, c_conf2 = st.columns(2)
            if c_conf1.button("💎 確定全額下注", type="primary", use_container_width=True):
                st.components.v1.html("<script>window.parent.playAppSound('click');</script>", height=0)
                st.session_state.bet_val = balance
                st.rerun()
            if c_conf2.button("取消", use_container_width=True):
                st.rerun()

        # 4. 介面內容區       
        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")

        # 5. 籌碼快選按鈕
        colb = st.columns(5)
        amounts = [5000, 10000, 15000, 20000]
        labels = ["🔵 5,000", "🟢 10,000", "🟡 15,000", "🔴 20,000"]
        for i in range(4):
            if colb[i].button(labels[i]):
                st.components.v1.html("<script>window.parent.playAppSound('click');</script>", height=0)
                st.session_state.bet_val = amounts[i]; time.sleep(0.1); st.rerun()
        if colb[4].button("💎 全額（梭哈）"):
            st.components.v1.html("<script>window.parent.playAppSound('alert');</script>", height=0)
            confirm_all_in()

        c1, c2 = st.columns(2)
        with c1: bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        with c2: gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")
        
        tz_taipei = timezone(timedelta(hours=8))
        can_submit = balance > 0 and bet_amt > 0 and bet_amt <= balance
        cw, cl = st.columns(2)

        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not can_submit or gain_amt is None):
            st.components.v1.html("<script>window.parent.playAppSound('win');</script>", height=0); time.sleep(0.2)
            now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
            new_row = {"日期": now_taipei, "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

        if cl.button("❌ 未過關 (輸)", use_container_width=True, disabled=not can_submit):
            st.components.v1.html("<script>window.parent.playAppSound('lose');</script>", height=0); time.sleep(0.2)
            now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
            new_row = {"日期": now_taipei, "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

    with tab2: # 歷史記錄
        def color_row(row):
            style = ['color: black'] * len(row)
            if row['盈虧金額'] > 0: target_color = 'color: green'
            elif row['盈虧金額'] < 0: target_color = 'color: red'
            else: target_color = 'color: black'
            style[row.index.get_loc('類型')] = target_color
            style[row.index.get_loc('盈虧金額')] = target_color
            return style
        st.dataframe(main_df.iloc[::-1].style.apply(color_row, axis=1).format({"金額": "{:,}", "盈虧金額": "{:+,.0f}", "結算總分": "{:,}"}), use_container_width=True)

    with tab3: # 統計圖表 (氣球邏輯修正)
        st.markdown("### 📊 統計圖曲線分析表")
        ready = st.checkbox("🟢 啟動動態演示", value=False)
        v_box = st.empty(); c_box = st.empty()
        if ready and not main_df.empty:
            data = pd.to_numeric(main_df["結算總分"]).tolist()
            delay = 0.1 if len(data) < 30 else max(0.01, 120 / len(data))
            for i in range(len(data)):
                curr = data[i]
                color = "#00c853" if i == 0 or curr >= data[i-1] else "#ff4b4b"
                v_box.markdown(f'<div style="text-align: right; padding: 12px; border-right: 6px solid {color}; background-color: white; border-radius: 8px;"><span style="font-size: 3.5em; font-weight: bold; color: {color} !important;">${int(curr):,}</span></div>', unsafe_allow_html=True)
                c_box.line_chart(data[:i+1], height=320)
                time.sleep(delay)
            st.balloons() # 僅在 tab3 演示結束時觸發
        elif not main_df.empty: c_box.line_chart(main_df["結算總分"], height=320)

    with tab4: # 報表管理
        with st.expander("補倉"):
            val = st.number_input("金額", 0, 999999999, 30000)
            if st.button("補"):
                bal = int(main_df["結算總分"].iloc[-1])
                new = {"日期":get_now_time(), "賽事項目": "補倉", "類型": "手動補倉", "金額": val, "盈虧金額": 0, "結算總分": bal + val}
                save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True)); st.rerun()
        with st.expander("新增報表"):
            n = st.text_input("名稱")
            if st.button("建立報表") and n: pd.DataFrame(columns=COLUMNS).to_csv(f"{n}.csv", index=False); st.rerun()

    with tab5: # 討 論 區[cite: 6]
        st.markdown("### 💬 足球現場實況滾球推薦")
        if 'user_nickname' not in st.session_state:
            with st.form("name_form"):
                name = st.text_input("首次留言，請輸入您的暱稱：", placeholder="例如：玩家稱呼")
                if st.form_submit_button("確認進入") and name:
                    st.session_state.user_nickname = name; st.rerun()
        else:
            st.info(f"歡迎回來！您的名稱：**{st.session_state.user_nickname}**")
            with st.form("chat_form", clear_on_submit=True):
                msg = st.text_area("輸入內容...", height=100)
                if st.form_submit_button("送出留言") and msg:
                    save_chat(st.session_state.user_nickname, msg); st.success("送出成功！"); time.sleep(1); st.rerun()
            st.divider()
            c_df = load_chat()
            if not c_df.empty:
                for _, r in c_df.iloc[::-1].iterrows():
                    l_color = "#00c853" if r['標籤'] == "管理員" else "#888"
                    st.markdown(f"""<div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {l_color};"><span style="color: {l_color}; font-weight: bold;">{r['暱稱']}</span> <span style="color: #aaa; font-size: 0.8em; margin-left: 10px;">{r['時間']}</span><p style="margin-top: 10px; color: #333; line-height: 1.5;">{r['內容']}</p></div>""", unsafe_allow_html=True)

# --- 底部宣告 ---
st.divider()
st.markdown("""<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來管理系統版權所有</div>""", unsafe_allow_html=True)