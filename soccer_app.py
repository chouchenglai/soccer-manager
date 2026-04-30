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

    # --- TAB3: 統計圖表 (智慧速率優化版) ---
    with tab3:
        st.markdown("### 📊 統計圖曲線分析表")

        # 1. 專業音效腳本
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

        # 2. 佈局控制
        ctrl_col, val_col = st.columns([1, 1.2])
        with ctrl_col:
            st.write("🔧 **演示控制**")
            ready = st.checkbox("🟢 解鎖音效權限 (啟動智慧播放)", value=False)

        value_placeholder = val_col.empty()
        chart_placeholder = st.empty()

        if ready:
            if not main_df.empty:
                full_data = main_df["結算總分"].tolist()
                num_records = len(full_data)
                
                # --- 核心優化：智慧判斷播放速率 ---
                # 如果資料太少（少於30筆），固定每筆間隔 0.1 秒，快速跑完
                if num_records < 30:
                    delay = 0.1 
                    st.info(f"⚡ 數據量較少，啟動「快速掃描模式」... (共 {num_records} 筆)")
                else:
                    # 資料多時，按照 2 分鐘比例縮放
                    delay = max(0.01, 120 / num_records)
                    st.info(f"📈 正在生成每日數據發展演示... (共 {num_records} 單)")
                
                for i in range(num_records):
                    curr = full_data[i]
                    is_up = True if i == 0 else curr >= full_data[i-1]
                    color = "#00c853" if is_up else "#ff4b4b"
                    
                    # 更新發光看板
                    value_placeholder.markdown(f"""
                        <div style="text-align: right; padding: 12px; border-right: 6px solid {color}; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                            <span style="font-size: 1.0em; color: #555; font-weight: 500;">目前結算總額:</span><br>
                            <span style="font-size: 3.5em; font-weight: bold; color: {color} !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.1); font-family: 'Courier New', monospace;">
                                ${int(curr):,}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 繪製動態曲線
                    chart_placeholder.line_chart(full_data[:i+1], height=320)
                    
                    # 播放音效
                    st.components.v1.html("<script>window.parent.playTick();</script>", height=0)
                    
                    # 低點警告音
                    if i > 5 and curr == min(full_data[:i+1]):
                        st.components.v1.html("<script>window.parent.playLow();</script>", height=0)

                    import time
                    time.sleep(delay)
                
                # 結束演示
                st.components.v1.html("<script>window.parent.playWin();</script>", height=0)
                st.balloons()
                st.success(f"🏁 數據重演完畢！最終餘額：${int(full_data[-1]):,}")
            else:
                st.error("❌ 尚未讀取到新筆注單")
        else:
            if not main_df.empty:
                chart_placeholder.line_chart(main_df["結算總分"], height=320)
                st.info("💡 提示：勾選上方「解鎖音效權限」即可啟動智慧動態演示")

    # --- TAB4 ---
    with tab4:
        with st.expander("補倉"):
            val = st.number_input("金額", 0, 999999999, 30000)
            if st.button("補"):
                bal = int(main_df["結算總分"].iloc[-1])
                new = {
                    "日期":get_now_time(),
                    "賽事項目": "補倉",
                    "類型": "手動補倉",
                    "金額": val,
                    "盈虧金額": 0,
                    "結算總分": bal + val
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
