import pytz
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 頁面設定 (最頂端)
st.set_page_config(page_title="CCL-Soccer", page_icon="⚽", layout="wide")

# --- 基本設定 ---
DEFAULT_DB = "soccer_master_data.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]

TW_TZ = pytz.timezone('Asia/Taipei') # 設定台北時區

def get_now_time():
    """獲取精確的台北目前時間"""
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

# --- 工具 ---
def get_all_reports():
    return [f for f in os.listdir('.') if f.endswith('.csv')]

def ensure_default_db():
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)

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

# --- 初始化 ---
ensure_default_db()

if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

all_reports = get_all_reports()

if not all_reports:
    ensure_default_db()
    all_reports = [DEFAULT_DB]

if st.session_state.current_db not in all_reports:
    st.session_state.current_db = all_reports[0]

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
        if real_profit >= 0:
            st.success(f"📈 純獲利: `${real_profit:,}`")
        else:
            st.error(f"📉 尚虧: `${abs(real_profit):,}`")

    st.write(f"檔案: `{st.session_state.current_db}`")
    st.divider()
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

# ---------------------------------------------------------
# 3. 主頁面頂端：全新「足球走地」中文優先旗艦版標題
# ---------------------------------------------------------
st.markdown("""
    <style>
        .ccl-brand-box {
            text-align: center; 
            padding: 30px 0 25px 0;
            background: linear-gradient(to bottom, #ffffff, #fafafa);
            border-bottom: 2px solid #00c853;
            margin-bottom: 25px;
            border-radius: 15px;
        }
        .ccl-chinese-main {
            font-size: 3.5em; 
            color: #1E1E1E;
            letter-spacing: 6px;
            font-weight: 800;
            display: block;
            margin-bottom: 5px;
            font-family: "Microsoft JhengHei", "Heiti TC", sans-serif;
        }
        .ccl-sub-brand {
            font-family: 'Verdana', sans-serif;
            font-weight: 900;
            font-size: 1.8em;
            letter-spacing: 0px;
            margin: 0;
        }
        .ccl-prefix { color: #444; }
        .ccl-suffix { color: #00c853; }
        .ccl-url {
            font-family: 'Courier New', monospace;
            color: #888;
            font-size: 1.0em;
            margin-top: 10px;
        }
        .official-badge {
            background-color: #00c853;
            color: white;
            padding: 2px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: bold;
            margin-left: 10px;
            vertical-align: middle;
        }
    </style>
    
    <div class="ccl-brand-box">
        <div class="ccl-chinese-main">
            足球走地賽事管理系統
        </div>
        <div class="ccl-sub-brand">
            <span class="ccl-prefix">CCL-</span><span class="ccl-suffix">Soccer</span>
            <span class="official-badge">Verified</span>
        </div>
        <div class="ccl-url">
            ccl-soccer<span style="color: #00c853;">.tw</span>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- 邏輯判斷與主功能 ---
if main_df.empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {
            "日期": get_now_time(),
            "賽事項目": "初始",
            "類型": "初始",
            "金額": int(init_cap),
            "盈虧金額": 0,
            "結算總分": int(init_cap)
        }
        save_data(pd.DataFrame([row]))
        st.rerun()

else:
    tab1, tab2, tab3, tab4 = st.tabs(["💰 投注下單", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理"])

    # --- TAB1: 快速錄入 ---
    with tab1:
        import time
        from datetime import datetime, timedelta, timezone
        
        try:
            balance = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
        except:
            balance = 0
        
        if "bet_val" not in st.session_state:
            st.session_state.bet_val = 5000

        st.components.v1.html("""
            <style>
                #clock-container {
                    display: flex; align-items: center; background-color: #f8f9fb;
                    padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b;
                    font-family: 'Segoe UI', 'Roboto', 'Monaco', monospace; margin-bottom: 5px;
                }
                #clock { font-size: 15px; font-weight: 600; color: #31333f; letter-spacing: 0.8px; }
                .prefix { font-size: 14px; color: #666; margin-right: 12px; }
            </style>
            <div id="clock-container">
                <span class="prefix">台北標準時間 (GMT+8) :</span>
                <span id="clock">載入中...</span>
            </div>
            <audio id="winAudio" src="https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3" preload="auto"></audio>
            <audio id="loseAudio" src="https://assets.mixkit.co/active_storage/sfx/2511/2511-preview.mp3" preload="auto"></audio>
            <audio id="clickAudio" src="https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3" preload="auto"></audio>
            <audio id="alertAudio" src="https://assets.mixkit.co/active_storage/sfx/951/951-preview.mp3" preload="auto"></audio>
            <script>
                function updateClock() {
                    const now = new Date();
                    const y = now.getFullYear();
                    const m = String(now.getMonth() + 1).padStart(2, '0');
                    const d = String(now.getDate()).padStart(2, '0');
                    const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
                    const hh = String(now.getHours()).padStart(2, '0');
                    const mm = String(now.getMinutes()).padStart(2, '0');
                    const ss = String(now.getSeconds()).padStart(2, '0');
                    document.getElementById('clock').textContent = `${y}/${m}/${d} (${weekDays[now.getDay()]}) ${hh}:${mm}:${ss}`;
                }
                setInterval(updateClock, 1000); updateClock();
                window.parent.playAppSound = function(type) {
                    var audio = document.getElementById(type + 'Audio');
                    if (audio) { audio.pause(); audio.currentTime = 0; audio.play().catch(e => console.log(e)); }
                };
            </script>
        """, height=52)

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

        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")

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
        with c1:
            bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        with c2:
            gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")

        tz_taipei = timezone(timedelta(hours=8))
        can_submit = balance > 0 and bet_amt > 0 and bet_amt <= balance
        cw, cl = st.columns(2)

        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not can_submit or gain_amt is None):
            st.components.v1.html("<script>window.parent.playAppSound('win');</script>", height=0)
            time.sleep(0.2)
            now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
            new_row = {
                "日期": now_taipei, "賽事項目": m_info, "類型": "贏 (+)",
                "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

        if cl.button("❌ 未過關 (輸)", use_container_width=True, disabled=not can_submit):
            st.components.v1.html("<script>window.parent.playAppSound('lose');</script>", height=0)
            time.sleep(0.2)
            now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
            new_row = {
                "日期": now_taipei, "賽事項目": m_info, "類型": "輸 (-)",
                "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

    # --- 其餘分頁保持 ---
    with tab2:
        def color_row(row):
            style = ['color: black'] * len(row)
            if row['盈虧金額'] > 0:
                target_color = 'color: green'
            elif row['盈虧金額'] < 0:
                target_color = 'color: red'
            else:
                target_color = 'color: black'
            type_idx = row.index.get_loc('類型')
            profit_idx = row.index.get_loc('盈虧金額')
            style[type_idx] = target_color
            style[profit_idx] = target_color
            return style

        st.dataframe(
            main_df.iloc[::-1].style.apply(color_row, axis=1)
            .format({"金額": "{:,}", "盈虧金額": "{:+,.0f}", "結算總分": "{:,}"}), 
            use_container_width=True
        )

    with tab3:
        st.markdown("### 📊 統計圖曲線分析表")
        st.components.v1.html("""
            <audio id="tick_audio" src="https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3" preload="auto"></audio>
            <audio id="win_audio" src="https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3" preload="auto"></audio>
            <audio id="low_audio" src="https://assets.mixkit.co/active_storage/sfx/251/251-preview.mp3" preload="auto"></audio>
            <script>
                window.parent.playTick = function() { var s = document.getElementById('tick_audio'); s.currentTime = 0; s.play(); }
                window.parent.playWin = function() { var s = document.getElementById('win_audio'); s.currentTime = 0; s.play(); }
                window.parent.playLow = function() { var s = document.getElementById('low_audio'); s.currentTime = 0; s.play(); }
            </script>
        """, height=0)

        ctrl_col, val_col = st.columns([1, 1.2])
        with ctrl_col:
            ready = st.checkbox("🟢 解鎖音效權限 (啟動演示)", value=False)
        value_placeholder = val_col.empty()
        chart_placeholder = st.empty()
        msg_box = st.empty()

        if ready:
            if not main_df.empty:
                full_data = pd.to_numeric(main_df["結算總分"]).tolist()
                num_records = len(full_data)
                delay = 0.1 if num_records < 30 else max(0.01, 120 / num_records)
                msg_box.info(f"🚀 分析中...")
                
                for i in range(num_records):
                    curr = full_data[i]
                    is_up = True if i == 0 else curr >= full_data[i-1]
                    color_code = "#00c853" if is_up else "#ff4b4b"
                    value_placeholder.markdown(f"""
                        <div style="text-align: right; padding: 12px; border-right: 6px solid {color_code}; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                            <span style="font-size: 1.0em; color: #555 !important;">目前結算總額:</span><br>
                            <span style="font-size: 3.5em; font-weight: bold; color: {color_code} !important; font-family: 'Courier New', monospace;">
                                ${int(curr):,}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                    chart_placeholder.line_chart(full_data[:i+1], height=320)
                    st.components.v1.html("<script>window.parent.playTick();</script>", height=0)
                    if i > 5 and curr == min(full_data[:i+1]):
                        st.components.v1.html("<script>window.parent.playLow();</script>", height=0)
                    time.sleep(delay)
                st.components.v1.html("<script>window.parent.playWin();</script>", height=0)
                st.balloons()
            else:
                msg_box.error("❌ 無資料！")
        else:
            if not main_df.empty:
                chart_placeholder.line_chart(main_df["結算總分"], height=320)

    with tab4:
        with st.expander("補倉"):
            val = st.number_input("金額", 0, 999999999, 30000)
            if st.button("補"):
                bal = int(main_df["結算總分"].iloc[-1])
                new = {
                    "日期":get_now_time(), "賽事項目": "補倉", "類型": "手動補倉",
                    "金額": val, "盈虧金額": 0, "結算總分": bal + val
                }
                save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
                st.rerun()

        with st.expander("新增報表"):
            name = st.text_input("名稱")
            if st.button("建立報表"):
                if name:
                    pd.DataFrame(columns=COLUMNS).to_csv(f"{name}.csv", index=False)
                    st.rerun()

        with st.expander("刪除報表"):
            deletable = [f for f in all_reports if f != DEFAULT_DB]
            if deletable:
                target = st.selectbox("選擇", deletable)
                if st.button("刪除"):
                    os.remove(target)
                    st.session_state.current_db = DEFAULT_DB
                    st.rerun()