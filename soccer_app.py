import os
import pandas as pd
import pytz
import streamlit as st
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

# --- 修正後的初始化工具區 ---
def ensure_files():
    # 1. 確保預設報表存在
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False, encoding='utf-8-sig')
    
    # 2. 確保討論區存在
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

    # 3. 【新增這段】確保「申請進度表」存在，防止 read_csv 報錯
    req_file = "pending_requests.csv"
    if not os.path.exists(req_file):
        pd.DataFrame(columns=["時間", "用戶名稱", "報表名稱", "狀態"]).to_csv(req_file, index=False, encoding='utf-8-sig')

# 1. 先定義函數 (讓 Python 知道這件工具怎麼用)
def ensure_files():
    # 確保主報表、討論區、以及申請清單存在
    for db, cols in [(DEFAULT_DB, COLUMNS), (CHAT_DB, CHAT_COLUMNS)]:
        if not os.path.exists(db):
            pd.DataFrame(columns=cols).to_csv(db, index=False, encoding='utf-8-sig')
    
    if not os.path.exists("pending_requests.csv"):
        pd.DataFrame(columns=["時間", "用戶名稱", "報表名稱", "狀態"]).to_csv("pending_requests.csv", index=False, encoding='utf-8-sig')

def load_data():
    if 'current_db' not in st.session_state:
        st.session_state.current_db = DEFAULT_DB
    # (中間省略)
    return pd.DataFrame(columns=COLUMNS)

# --- 🎯 就是這裡！把存檔函數更新在這 ---
def save_data(df):
    """將 DataFrame 儲存到當前選擇的 CSV 檔案中"""
    df.to_csv(st.session_state.current_db, index=False, encoding='utf-8-sig')

# --- 接著才是呼叫它們 ---
ensure_files()
main_df = load_data()

# 2. 函數定義完後，才正式呼叫它們
ensure_files()

# 3. 初始化並讀取資料
if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

main_df = load_data()

# --- 2. 【核心修復】初始化 session_state 變數 ---
if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

# --- 3. 呼叫讀取資料 (現在 current_db 絕對存在，不會再報錯了) ---
main_df = load_data()
# --- 初始化 ---
ensure_files()
def ensure_files():
    # 確保主報表、討論區存在
    for db, cols in [(DEFAULT_DB, COLUMNS), (CHAT_DB, CHAT_COLUMNS)]:
        if not os.path.exists(db):
            pd.DataFrame(columns=cols).to_csv(db, index=False, encoding='utf-8-sig')
    
    # 確保申請進度表存在
    if not os.path.exists("pending_requests.csv"):
        pd.DataFrame(columns=["時間", "用戶名稱", "報表名稱", "狀態"]).to_csv("pending_requests.csv", index=False, encoding='utf-8-sig')

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

# --- Sidebar (側邊欄) 恢復原始經典風格 ---
with st.sidebar:
    st.header("💰 資金與統計中心")
    
    # 1. 獲取報表清單
    all_reports = get_all_reports()
    
    # 2. 安全計算索引
    idx = all_reports.index(st.session_state.current_db) if st.session_state.current_db in all_reports else 0
    
    # 3. 切換報表下拉選單
    selected_db = st.selectbox("切換報表", all_reports, index=idx)
    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()
        
    st.divider()

    # 4. 數據統計顯示區
    if not main_df.empty:
        # 獲取目前可用本金 (取最後一筆結算總分)
        current_bal = int(main_df["結算總分"].iloc[-1])
        st.metric("目前可用本金", f"${current_bal:,}")
        
        # 定義投入類型並計算總投入
        invest_types = ['初始', '手動補倉', '補倉']
        total_investment = main_df[main_df['類型'].isin(invest_types)]['金額'].sum()
        st.write(f"💼 累積投入: `${total_investment:,}`")
        
        # 計算實際盈虧
        real_profit = current_bal - total_investment
        
        # 根據盈虧狀況顯示 success (綠) 或 error (紅)
        if real_profit >= 0:
            st.success(f"📈 純獲利: `${real_profit:,}`")
        else:
            st.error(f"📉 尚虧: `${abs(real_profit):,}`")
    else:
        st.info("💡 目前報表尚無數據")

    st.divider()

    # 5. 下載按鈕
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載完整紀錄 (CSV)", 
        data=csv, 
        file_name=st.session_state.current_db
    )

# --- 邏輯判斷與主功能 ---
if main_df.empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()
else:
    # 核心：標籤頁定義
    tab1, tab_live, tab2, tab3, tab4, tab5 = st.tabs(["💰 下單投注", "⚽ 即時比分", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

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

    # ==========================================
# Tab 4: 報表管理 (商用標準穩定版 - 零特效)
# ==========================================
with tab4:
    st.header("📊 報表帳本管理中心")
    
    # --- 1. 初始化檔案與欄位 (標準商用格式) ---
    req_file = "pending_requests.csv"
    req_cols = ["申請編號", "申請日期", "申請名稱", "備註事項", "審核結果"]

    # --- 2. 安全讀取邏輯 (修正：強制編號為字串格式) ---
    if os.path.exists(req_file):
        try:
            # 關鍵點：加入 dtype 參數，強制編號欄位不被轉為數字
            req_df = pd.read_csv(req_file, dtype={'申請編號': str})
            
            if not all(col in req_df.columns for col in req_cols):
                req_df = pd.DataFrame(columns=req_cols)
        except Exception:
            req_df = pd.DataFrame(columns=req_cols)
    else:
        req_df = pd.DataFrame(columns=req_cols)

    # --- 3. 區塊 A：提交新報表申請 ---
    st.subheader("提交新報表申請", anchor=False)
    new_name = st.text_input("請輸入預計建立的報表名稱", placeholder="例如：Fran Chou")
    if st.button("確認送出申請"):
        if new_name:
            # 自動計算編號與日期
            new_id = f"{len(req_df) + 1:04d}"
            today_str = datetime.now().strftime("%Y年%m月%d日")
            
            new_data = {
                "申請編號": new_id,
                "申請日期": today_str,
                "申請名稱": new_name,
                "備註事項": "",
                "審核結果": "⏳ 審核進行中"
            }
            
            # 存檔至伺服器
            updated_df = pd.concat([req_df, pd.DataFrame([new_data])], ignore_index=True)
            updated_df.to_csv(req_file, index=False, encoding='utf-8-sig')
            
            # 建立物理 CSV 檔案基礎
            target_csv = f"{new_name}.csv" if not new_name.endswith(".csv") else new_name
            if not os.path.exists(target_csv):
                pd.DataFrame(columns=COLUMNS).to_csv(target_csv, index=False, encoding='utf-8-sig')
            
            # 標準成功提示
            st.success(f"系統訊息：已成功登錄申請 (編號: {new_id})")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("請先輸入名稱再送出。")

    st.divider()

    # --- 4. 區塊 B：審核進度清單 (標準表格，無樣式干擾) ---
    st.subheader("報表審核進度詳情", anchor=False)
    if not req_df.empty:
        # 最新申請排在最前，使用標準 dataframe 顯示
        st.dataframe(
            req_df.iloc[::-1], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("目前尚無申請紀錄。")

    st.divider()

    # --- 5. 區塊 C：可用報表帳本清單 (嚴格審核機制) ---
    st.subheader("已授權報表清單", anchor=False)
    
    # 掃描現有 CSV 檔案
    physical_files = [f for f in os.listdir('.') if f.endswith('.csv') and f not in [req_file, CHAT_DB]]
    
    # 過濾已通過名單
    passed_names = req_df[req_df['審核結果'].str.contains("通過", na=False)]['申請名稱'].tolist()
    
    # 顯示邏輯：主帳本必出，其餘需審核通過
    display_targets = [f for f in physical_files if f == DEFAULT_DB or f.replace('.csv','') in passed_names or f in passed_names]

    if display_targets:
        for fname in display_targets:
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.text(f"📁 {fname}" + (" (系統預設)" if fname == DEFAULT_DB else ""))
            with col_b:
                if st.button("啟動", key=f"switch_{fname}"):
                    st.session_state.current_db = fname
                    st.rerun()
    else:
        st.info("暫無已授權之報表。")  

# ---------------------------------------------------------
    # 5. 討論區模組 (防崩潰終極版)
    # ---------------------------------------------------------
    with tab5:
        st.markdown("### 💬 足球現場實況滾球推薦")
        
        # 🛡️ 內部安全讀取函數 (直接處理空檔案報錯)
        def get_chat_safely():
            if os.path.exists(CHAT_DB):
                try:
                    # 檢查檔案是否為空，防止 EmptyDataError
                    if os.path.getsize(CHAT_DB) > 0:
                        return pd.read_csv(CHAT_DB)
                    else:
                        return pd.DataFrame(columns=CHAT_COLUMNS)
                except:
                    return pd.DataFrame(columns=CHAT_COLUMNS)
            return pd.DataFrame(columns=CHAT_COLUMNS)

        # 讀取聊天紀錄
        chat_data = get_chat_safely()
        
        # 1. 訪客登記邏輯
        if 'user_nickname' not in st.session_state:
            with st.container():
                st.info("👋 歡迎！參與討論前請先設定您的暱稱。")
                with st.form("name_registration"):
                    name_input = st.text_input("首次留言，請輸入您的暱稱：", placeholder="例如：路過的球神")
                    submit_name = st.form_submit_button("確認進入")
                    if submit_name and name_input.strip():
                        st.session_state.user_nickname = name_input.strip()
                        st.rerun()
        else:
            # 顯示當前身份
            st.caption(f"✅ 您目前以 **{st.session_state.user_nickname}** 的身份在線")
            
            # 2. 留言輸入表單[cite: 2]
            with st.form("chat_form", clear_on_submit=True):
                msg_content = st.text_area("輸入您的內容...", height=100, placeholder="分享賽事觀點...")
                submit_msg = st.form_submit_button("🚀 送出留言")
                if submit_msg:
                    if msg_content.strip():
                        # 調用全局定義的 save_chat 函數
                        save_chat(st.session_state.user_nickname, msg_content.strip())
                        st.success("留言已送出")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("內容不能為空喔！")
            
            st.divider()
            
            # 3. 留言顯示區 (從最新顯示到最舊)[cite: 2]
            if not chat_data.empty:
                for idx, row in chat_data.iloc[::-1].iterrows():
                    with st.container():
                        c_left, c_right = st.columns([8, 2])
                        
                        with c_left:
                            # 渲染留言樣式
                            st.markdown(f"""
                                <div style="background-color: #f9f9f9; padding: 12px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #00c853;">
                                    <strong style="color: #00c853;">{row['暱稱']}</strong> 
                                    <span style="color: #888; font-size: 0.8em; margin-left: 10px;">{row['時間']}</span>
                                    <p style="margin-top: 8px; color: #333; line-height: 1.6;">{row['內容']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with c_right:
                            # 生成唯一 Key[cite: 2]
                            unique_key = f"msg_{idx}_{row['時間']}"
                            
                            if st.button("🗑️ 刪除", key=f"del_{unique_key}"):
                                updated_chat = chat_data.drop(idx)
                                updated_chat.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')
                                st.rerun()
                            
                            if st.checkbox("📝 編輯", key=f"edt_{unique_key}"):
                                new_text = st.text_area("修正留言：", value=row['內容'], key=f"area_{unique_key}")
                                if st.button("確認修改", key=f"save_{unique_key}"):
                                    chat_data.at[idx, '內容'] = new_text
                                    chat_data.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')
                                    st.success("已更新！")
                                    time.sleep(0.5)
                                    st.rerun()
                    st.write("") 
            else:
                st.write("目前還沒有討論內容，快來搶頭香吧！")
               
# --- 底部 ---
st.divider()
st.markdown("""<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來足球管理系統版權所有</div>""", unsafe_allow_html=True)