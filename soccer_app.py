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
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

# --- 工具 ---
def get_all_reports():
    return [f for f in os.listdir('.') if f.endswith('.csv') and f != CHAT_DB]

def ensure_files():
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

# --- 修正後的核心工具 ---
def ensure_files():
    # 報表檔案 (DEFAULT_DB) 這裡不預先建立，讓主邏輯判斷是否存在
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

def load_data():
    # 這裡只負責讀取，若檔案不存在就回傳空表，不要主動去寫入空檔
    target = st.session_state.current_db
    if os.path.exists(target):
        try:
            df = pd.read_csv(target)
            if "月份" in df.columns: df = df.drop(columns=["月份"])
            return df
        except: 
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

# --- 初始化 ---
ensure_files()
if 'current_db' not in st.session_state: st.session_state.current_db = DEFAULT_DB
all_reports = get_all_reports()
if not all_reports: all_reports = [DEFAULT_DB]
if st.session_state.current_db not in all_reports: st.session_state.current_db = all_reports[0]

main_df = load_data()

# --- 標誌顯示區 (Base64) ---
import base64
def get_base64_img(file_path):
    with open(file_path, "rb") as f: data = f.read()
    return base64.b64encode(data).decode()

img_path = "ccl_logo_header.jpg"
if os.path.exists(img_path):
    img_b64 = get_base64_img(img_path)
    st.markdown(f"""
        <style>
            .banner-box {{ width: 90%; text-align: center; background-color: #ffffff; padding: 0px 0; margin-bottom: 20px; overflow: hidden; }}
            .banner-img {{ width: 90%; transform: scale(1.1); transform-origin: center; height: auto; display: block; margin: 0 auto; }}
        </style>
        <div class="banner-box"><img src="data:image/jpeg;base64,{img_b64}" class="banner-img"></div>
    """, unsafe_allow_html=True)

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
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

def is_initialized(df):
    try:
        return not df.empty and "初始" in df["類型"].values
    except:
        return False

# --- 邏輯判斷與主功能 (請替換原代碼中對應位置) ---

# 1. 再次確認檔案狀態
file_exists = os.path.exists(st.session_state.current_db)
if file_exists:
    # 讀取當前數據，確保 main_df 不是空的
    main_df = load_data()

# 2. 核心判斷：如果檔案不存在，或是裡面連一行數據都沒有 (除了標題)
if not file_exists or len(main_df) == 0:
    st.subheader("🚀 初始化報表")
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
        # 強制寫入檔案並立即更新
        new_df = pd.DataFrame([row])
        new_df.to_csv(st.session_state.current_db, index=False, encoding='utf-8-sig')
        st.success("報表已建立！")
        time.sleep(0.5)
        st.rerun()
else:
    # --- 只要檔案有資料，就直接進入主功能頁面 ---
    tab1, tab_live, tab2, tab3, tab4, tab5 = st.tabs(["💰 下單投注", "⚽ 即時比分", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])
    
    # 接下來接您原本各個 tab 的內容...
    
    with tab1: # 下單投注
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
            <audio id="winAudio" src="https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3" preload="auto"></audio>
            <audio id="loseAudio" src="https://assets.mixkit.co/active_storage/sfx/2511/2511-preview.mp3" preload="auto"></audio>
            <audio id="clickAudio" src="https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3" preload="auto"></audio>
            <audio id="alertAudio" src="https://assets.mixkit.co/active_storage/sfx/951/951-preview.mp3" preload="auto"></audio>
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
        with c1: bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        with c2: gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")
        st.write("")
        
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

# --- 再投入補倉 ---
        st.write("")   
        col_link, col_empty = st.columns([2, 8]) # 放在左側
        with col_link:
            # 超鏈接按鈕
            if st.button("🔗 再投入補倉", help="點擊直接進行補倉操作", use_container_width=False):                
                st.session_state.show_add_funds = True
                st.rerun()

        # --- 如果標記為 True，則彈出補倉輸入框 ---
        if st.session_state.get('show_add_funds', False):
            st.divider()
            st.subheader("📥 快速補倉面板")
            with st.form("quick_add_funds"):
                add_amt = st.number_input("請輸入補倉金額", min_value=1000, step=1000, value=30000)
                c_submit, c_cancel = st.columns([2, 8])
                if c_submit.form_submit_button("確認補倉"):
                    # 執行補倉邏輯
                    current_bal = int(main_df["結算總分"].iloc[-1])
                    new_row = {
                        "日期": get_now_time(),
                        "賽事項目": "手動補倉 (快捷)",
                        "類型": "補倉",
                        "金額": int(add_amt),
                        "盈虧金額": 0,
                        "結算總分": current_bal + int(add_amt)
                    }
                    save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.session_state.show_add_funds = False # 關閉面板
                    st.success(f"成功補倉 ${add_amt:,}！")
                    time.sleep(0.5)
                    st.rerun()
                if c_cancel.form_submit_button("取消"):
                    st.session_state.show_add_funds = False
                    st.rerun()

    with tab_live:
        # 第一行：大標題
            st.markdown("### 📡 即時比分同步觀看 (Live)")
        
        # 第二行：藍色背景提示框
            st.info("💡 提示：擇優場次後，請複製賽事，再點擊上方欄目，切換【下單投注】")
           
        # 第三行：嵌入外部比分網[cite: 1]
            st.components.v1.iframe("https://live.titan007.com/indexall_big.aspx", height=800, scrolling=True)

    with tab2: # 📋 歷史記錄
        st.subheader("📜 完整賽事歷史紀錄")
        
        # 1. 定義染色邏輯 (確保縮排正確)
        def color_row(row):
            style = ['color: black'] * len(row)
            # 判斷盈虧顏色
            if row['盈虧金額'] > 0: 
                target_color = 'color: green'
            elif row['盈虧金額'] < 0: 
                target_color = 'color: red'
            else: 
                target_color = 'color: black'
            
            # 將顏色套用到「類型」與「盈虧金額」這兩欄
            style[row.index.get_loc('類型')] = target_color
            style[row.index.get_loc('盈虧金額')] = target_color
            return style

        # 2. 顯示表格 (包含倒序處理與千分位格式化)
        if not main_df.empty:
            # iloc[::-1] 讓最新的資料排在最上面
            styled_df = main_df.iloc[::-1].style.apply(color_row, axis=1).format({
                "金額": "{:,}", 
                "盈虧金額": "{:+,.0f}", 
                "結算總分": "{:,}"
            })
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("目前尚無歷史紀錄。")

    with tab3: # 統計圖表[cite: 2]
        st.line_chart(main_df["結算總分"], height=320)

    with tab4: # 報表管理
        st.subheader("📁 系統報表管理中心")
        
        # --- 區塊 1：新增報表 ---
        with st.expander("➕ 新增報表檔案"):
            n = st.text_input("報表名稱", placeholder="請輸入名稱（不需輸入 .csv）")
            if st.button("確認建立報表"):
                if n:
                    file_name = f"{n}.csv"
                    # 建立一個只有標題欄位的空 CSV
                    pd.DataFrame(columns=COLUMNS).to_csv(file_name, index=False)
                    st.success(f"✅ 報表「{file_name}」已成功建立！")
                    time.sleep(1)
                    st.rerun() # 重新執行以更新左側選單列表
                else:
                    st.error("⚠️ 請輸入報表名稱！")

        # --- 區塊 2：刪除報表 ---
        with st.expander("🗑️ 刪除現有報表"):
            # 重新獲取一次列表，排除預設資料庫
            d_list = [f for f in get_all_reports() if f != DEFAULT_DB]
            
            if d_list:
                t = st.selectbox("選擇欲刪除的報表檔案", d_list)
                if st.button("確認刪除報表", type="secondary"):
                    try:
                        os.remove(t)
                        st.session_state.current_db = DEFAULT_DB # 刪除後自動跳回預設檔
                        st.warning(f"檔案 {t} 已刪除。")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"刪除失敗：{e}")
            else:
                st.info("目前沒有可刪除的自訂報表。")  

# ---------------------------------------------------------
    # 5. 討論區模組 (修正版：區分身分顏色 + 引用回覆功能)
    # ---------------------------------------------------------
    with tab5:
        st.markdown("### 💬 足球現場實況滾球推薦")
        
        def get_chat_safely():
            if os.path.exists(CHAT_DB):
                try:
                    if os.path.getsize(CHAT_DB) > 0:
                        return pd.read_csv(CHAT_DB)
                except: pass
            return pd.DataFrame(columns=CHAT_COLUMNS)

        chat_data = get_chat_safely()
        
        if 'user_nickname' not in st.session_state:
            with st.form("name_registration"):
                st.info("👋 歡迎！參與討論前請先設定您的暱稱。")
                name_input = st.text_input("首次留言，請輸入您的暱稱：")
                if st.form_submit_button("確認進入") and name_input.strip():
                    st.session_state.user_nickname = name_input.strip()
                    st.rerun()
        else:
            # 初始化引用變數
            if "reply_target" not in st.session_state:
                st.session_state.reply_target = ""
            
            curr_user = st.session_state.user_nickname
            is_admin = curr_user.lower() in ['管理員', 'admin']
            
            st.caption(f"✅ 當前身分：{'🟢 管理員' if is_admin else '👤 ' + curr_user}")
            
            # 留言輸入表單
            with st.form("chat_form", clear_on_submit=True):
                msg_content = st.text_area("輸入您的內容...", value=st.session_state.reply_target, height=100)
                col_s1, col_s2 = st.columns([2, 8])
                if col_s1.form_submit_button("🚀 送出留言") and msg_content.strip():
                    save_chat(curr_user, msg_content.strip())
                    st.session_state.reply_target = "" # 送出後清空引用
                    st.rerun()
                if st.session_state.reply_target and col_s2.form_submit_button("取消引用"):
                    st.session_state.reply_target = ""
                    st.rerun()
            
            st.divider()
            
            if not chat_data.empty:
                for idx, row in chat_data.iloc[::-1].iterrows():
                    # 判斷該筆留言者是否為管理員
                    is_msg_admin = str(row['暱稱']).lower() in ['管理員', 'admin']
                    
                    # 顏色與樣式邏輯
                    border_style = "5px solid #00c853" if is_msg_admin else "1px solid #ddd"
                    name_color = "#00c853" if is_msg_admin else "#666"
                    name_text = "管理員" if is_msg_admin else row['暱稱']
                    bg_color = "#f9f9f9" if is_msg_admin else "#ffffff"

                    with st.container():
                        c_left, c_right = st.columns([7.5, 2.5])
                        with c_left:
                            st.markdown(f"""
                                <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin-bottom: 5px; border-left: {border_style}; border-top: {border_style if not is_msg_admin else 'none'}; border-right: {border_style if not is_msg_admin else 'none'}; border-bottom: {border_style if not is_msg_admin else 'none'};">
                                    <strong style="color: {name_color}; font-size: 1.1em;">{name_text}</strong> 
                                    <span style="color: #aaa; font-size: 0.8em; margin-left: 10px;">{row['時間']}</span>
                                    <p style="margin-top: 10px; color: #333;">{row['內容']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with c_right:
                            u_key = f"m_{idx}"
                            # 1. 回覆按鈕
                            if st.button("💬 回覆", key=f"rp_{u_key}", use_container_width=True):
                                st.session_state.reply_target = f"@{name_text}："
                                st.rerun()
                            
                            # 2. 編輯功能
                            if st.checkbox("📝 編輯", key=f"ed_{u_key}"):
                                new_txt = st.text_area("修改內容：", value=row['內容'], key=f"at_{u_key}")
                                if st.button("確認修改", key=f"sv_{u_key}"):
                                    chat_data.at[idx, '內容'] = new_txt
                                    chat_data.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')
                                    st.rerun()
                            
                            # 3. 刪除按鈕
                            if st.button("🗑️ 刪除", key=f"dl_{u_key}", use_container_width=True):
                                chat_data.drop(idx).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')
                                st.rerun()
                    st.write("") 
            else:
                st.write("目前尚無討論。")
               
# --- 底部 ---
st.divider()
st.markdown("""<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來足球管理系統版權所有</div>""", unsafe_allow_html=True)