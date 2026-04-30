import pytz
import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
st.set_page_config(page_title="足球賽事一體化管理系統", layout="wide")

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

# --- Sidebar ---
with st.sidebar:
    st.header("💰 資金與統計中心")

    idx = all_reports.index(st.session_state.current_db) if st.session_state.current_db in all_reports else 0
    selected_db = st.selectbox("切換報表", all_reports, index=idx)

    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()

    st.divider()

    # --- 這裡開始替換：確保縮排與 with st.sidebar 對齊 ---
    if not main_df.empty:
        # 1. 顯示目前總餘額
        current_bal = int(main_df["結算總分"].iloc[-1])
        st.metric("目前可用本金", f"${current_bal:,}")

        # 2. 計算累積投入 (包含初始、手動補倉)
        # 這裡會掃描 CSV 類型欄位，抓取您手動改好的「初始」金額 60000
        invest_types = ['初始', '手動補倉', '補倉']
        total_investment = main_df[main_df['類型'].isin(invest_types)]['金額'].sum()
        
        st.write(f"💼 累積投入: `${total_investment:,}`")
        
        # 3. 計算純獲利
        real_profit = current_bal - total_investment
        
        if real_profit >= 0:
            st.success(f"📈 純獲利: `${real_profit:,}`")
        else:
            st.error(f"📉 尚虧: `${abs(real_profit):,}`")

    # 4. 保留原本的檔案名稱顯示與下載按鈕
    st.write(f"檔案: `{st.session_state.current_db}`")
    
    st.divider()
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 下載完整紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

# --- 標題 ---
st.markdown("<h1 style='text-align: center;'>⚽ 足球賽事管理系統</h1>", unsafe_allow_html=True)

st.markdown(
    "<h4 style='text-align: center; color: white; background-color: red; padding: 10px; border-radius: 10px;'>⚠️ 謹慎理財！信用至上！ ⚠️</h4>",
    unsafe_allow_html=True
)

# --- 初始化 ---
if main_df.empty:
    st.subheader("初始化報表")

    init_cap = st.number_input("起始本金", value=60000, step=1000)

    if st.button("建立"):
        now = datetime.now()
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

# --- 主功能 ---
else:
    tab1, tab2, tab3, tab4 = st.tabs(["💰投注下單", "📋歷史記錄", "📊統計圖表", "📈報表管理"])

    # --- TAB1: 快速錄入 ---
    with tab1:
        import time
        from datetime import datetime, timedelta, timezone
        
        # 1. 取得當前總分
        try:
            balance = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
        except:
            balance = 0
        
        # 初始化下注金額狀態
        if "bet_val" not in st.session_state:
            st.session_state.bet_val = 5000

        # 2. 極簡橫向時鐘與音效組件
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

        # 6. 下注與盈利輸入區
        c1, c2 = st.columns(2)
        with c1:
            bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        with c2:
            gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")

        st.write("")

        # 7. 提交執行區 (核心修正：統一台北時區)
        tz_taipei = timezone(timedelta(hours=8)) # 強制定義 GMT+8
        
        can_submit = balance > 0 and bet_amt > 0 and bet_amt <= balance
        cw, cl = st.columns(2)

        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not can_submit or gain_amt is None):
            st.components.v1.html("<script>window.parent.playAppSound('win');</script>", height=0)
            time.sleep(0.2)
            # 取得精確台北時間
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
            # 取得精確台北時間
            now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
            new_row = {
                "日期": now_taipei, "賽事項目": m_info, "類型": "輸 (-)",
                "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

    # --- TAB2 ---
    with tab2:
        # 1. 定義顏色規則函數
        def color_row(row):
            # 建立一個清單，預設所有格子都是黑色
            style = ['color: black'] * len(row)
            
            # 判斷邏輯：根據「盈虧金額」來決定顏色
            if row['盈虧金額'] > 0:
                target_color = 'color: green'
            elif row['盈虧金額'] < 0:
                target_color = 'color: red'
            else:
                target_color = 'color: black'
            
            # 2. 找到「類型」與「盈虧金額」所在的欄位索引
            type_idx = row.index.get_loc('類型')
            profit_idx = row.index.get_loc('盈虧金額')
            
            # 3. 把這兩個位置塗上顏色
            style[type_idx] = target_color
            style[profit_idx] = target_color
            
            return style

        # 4. 顯示表格：應用樣式並設定數字格式
        st.dataframe(
            main_df.iloc[::-1].style.apply(color_row, axis=1)
            .format({"金額": "{:,}", "盈虧金額": "{:+,.0f}", "結算總分": "{:,}"}), 
            use_container_width=True
        )

    # --- TAB3 ---
    with tab3:     
        if not main_df.empty:
            # 取得即時數據欄位：結算總分
            full_data = main_df["結算總分"].tolist()
            num_records = len(full_data)
            
            # 自動限時 120 秒播放完畢
            TOTAL_LIMIT = 120 
            delay = max(0.01, TOTAL_LIMIT / num_records)
            
            st.info(f"📈 正在生成每日數據發展演示... (共 {num_records} 筆)")
            
            for i in range(1, num_records):
                curr = full_data[i]
                prev = full_data[i-1]
                
                # 漲綠跌紅邏輯
                color = "#00FF41" if curr >= prev else "#FF3131"
                status_txt = "🟢 強勢反彈" if curr >= prev else "🔴 遭遇回撤"                
                                
                # 曲線圖繪製 (固定高度 320 避免 F11)
                chart_placeholder.line_chart(full_data[:i+1], height=320)
                
                # 觸發音效
                st.components.v1.html("<script>window.parent.playTick();</script>", height=0)
                
                # 歷史低點警告
                if curr == min(full_data[:i+1]) and i > 5:
                    st.components.v1.html("<script>window.parent.playLow();</script>", height=0)

                import time
                time.sleep(delay)