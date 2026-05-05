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
    new_msg = {"時間": get_now_time(), "暱稱": nickname, "內容": content, "標籤": "訪客"}
    df = pd.concat([df, pd.DataFrame([new_msg])], ignore_index=True)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

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

# --- 邏輯判斷與主功能 ---
if main_df.empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()
else:
    # 核心：標籤頁定義
    tab1, tab2, tab_live, tab3, tab4, tab5 = st.tabs(["💰 下單投注", "**📝 註冊帳號**", "⚽ 即時比分", "📋 歷史記錄", "📊 統計圖表",  "💬 討 論 區"])
       
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

  # ==========================================
# Tab 2: 帳號管理 (雙重密碼鎖 + 管理員權限版)
# ==========================================
with tab2:    
    st.markdown("<h2 style='color:#1E90FF; font-weight:bold;'>📂 登錄帳號管理中心</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #1E90FF; margin-top: -10px;'>", unsafe_allow_html=True)
    
    # --- 1. 初始化檔案與欄位 ---
    req_file = "pending_requests.csv"
    req_cols = ["申請編號", "申請日期", "申請名稱", "備註事項", "審核結果", "權限"]

    if os.path.exists(req_file):
        try:
            req_df = pd.read_csv(req_file, dtype={'申請編號': str})
        except Exception:
            req_df = pd.DataFrame(columns=req_cols)
    else:
        req_df = pd.DataFrame(columns=req_cols)

    # --- 關鍵：管理員身分識別 + 密碼驗證 ---
    is_admin = False
    is_authenticated = False # 密碼驗證狀態
    
    if "current_db" in st.session_state:
        current_active_name = st.session_state.current_db.replace('.csv', '')
        # 先檢查 CSV 權限
        admin_row = req_df[(req_df['申請名稱'] == current_active_name) & (req_df['權限'].str.upper() == 'ADMIN')]
        
        if not admin_row.empty:
            is_admin = True
            # 如果是管理員，顯示密碼輸入框
            st.sidebar.markdown("---")
            admin_pwd = st.sidebar.text_input("🔑 管理員驗證碼", type="password", help="請輸入您的專屬密鑰以啟用管理功能")
            
            # --- 💡 這裡設定您的初始密碼 (例如: alai2026) ---
            if admin_pwd == "alai2026": 
                is_authenticated = True
                st.sidebar.success("🔓 權限已解鎖")
            elif admin_pwd != "":
                st.sidebar.error("❌ 密鑰錯誤")

    # --- 2. 區塊 A：提交新帳號申請 ---
    st.subheader("提交新帳號申請", anchor=False)
    new_name = st.text_input("請輸入您要創建的帳號名稱", placeholder="例如：Visitors")
    st.markdown("<small style='color:red; font-weight:bold;'>⚠️ 系統提醒：名稱僅限「英文與數字」，請勿使用中文或特殊符號。</small>", unsafe_allow_html=True)
    
    with st.expander("**📜 點擊展開：用戶服務協議與免責聲明**"):
        st.write("1. 本系統僅供個人賽事數據記錄使用，不具備任何投注功能。
        2. 用戶需自行承擔數據分析之風險，本平臺不保證任何獲利。
        3. 申請即表示您同意系統收集您的帳號名稱以進行權限管理。
        4. 嚴禁任何違反當地法律之行為。")
        is_agree = st.checkbox("我已閱讀並同意上述全部條款")

    if st.button("確認送出申請"):
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in new_name)
        if not new_name:
            st.warning("請先輸入名稱。")
        elif has_chinese:
            st.error("❌ 建立失敗：不可包含中文字。")[cite: 2]
        elif not is_agree:
            st.error("❌ 請先勾選「同意服務協議」。")
        else:
            new_id = f"{len(req_df) + 1:04d}"
            today_str = datetime.now().strftime("%Y年%m月%d日")
            target_csv = f"{new_name}.csv" if not new_name.endswith(".csv") else new_name
            with open(target_csv, "w", encoding="utf-8-sig") as f:
                f.write(f"免責聲明內容...\n保存會員資料：{new_id}/{new_name}\n")
            pd.DataFrame(columns=COLUMNS).to_csv(target_csv, index=False, encoding='utf-8-sig', mode='a')
            
            new_data = {"申請編號": new_id, "申請日期": today_str, "申請名稱": new_name, "備註事項": "已簽署免責", "審核結果": "⏳ 審核進行中", "權限": "User"}
            updated_df = pd.concat([req_df, pd.DataFrame([new_data])], ignore_index=True)
            updated_df.to_csv(req_file, index=False, encoding='utf-8-sig')
            st.success(f"✅ 申請已成功！")
            time.sleep(1)
            st.rerun()

    st.divider()

    # --- 3. 區塊 B：審核進度詳情 (管理員一鍵審核) ---
    st.subheader("帳號審核進度詳情", anchor=False)
    if not req_df.empty:
        # 同時符合 Admin 身分且密碼正確，才顯示按鈕[cite: 2]
        if is_admin and is_authenticated:
            for idx, row in req_df.iloc[::-1].iterrows():
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1.5])
                c1.write(row["申請編號"])
                c2.write(row["申請名稱"])
                if "進行中" in row["審核結果"]:
                    if c4.button("✅ 通過", key=f"approve_{idx}"):
                        req_df.at[idx, "審核結果"] = "通過"
                        req_df.to_csv(req_file, index=False, encoding='utf-8-sig')
                        st.rerun()
                else:
                    c3.success(row["審核結果"])
        else:
            st.dataframe(req_df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("目前尚無申請記錄。")

    st.divider()

    # --- 4. 區塊 C：已授權帳號清單 ---
    st.subheader("已授權帳號清單", anchor=False)
    physical_files = [f for f in os.listdir('.') if f.endswith('.csv') and f not in [req_file, CHAT_DB]]
    passed_names = req_df[req_df['審核結果'].str.contains("過關|通過|OK", na=False)]['申請名稱'].tolist()
    display_targets = [f for f in physical_files if f == DEFAULT_DB or f.replace('.csv','') in passed_names]

    if display_targets:
        for fname in display_targets:
            if fname == req_file: continue
            col1, col2, col3 = st.columns([2.5, 1, 1])
            col1.markdown(f"📁 **{fname}**")
            col2.link_button("🚀 啟動", "https://chouchenglai.streamlit.app/")
            
            # 刪除按鈕也需要「密碼校驗成功」才會出現[cite: 2]
            if is_admin and is_authenticated and fname != DEFAULT_DB:
                if col3.button("🗑️ 刪除", key=f"del_{fname}"):
                    os.remove(fname)
                    req_df = req_df[req_df['申請名稱'] != fname.replace('.csv','')]
                    req_df.to_csv(req_file, index=False, encoding='utf-8-sig')
                    st.rerun()
    else:
        st.info("暫無已授權之清單。")

    st.divider()

    # --- 4. 區塊 C：已授權帳號清單 ---    
    st.subheader("已授權帳號清單", anchor=False)
    st.caption("💡 溫馨提示：點擊啟動後將跳轉至主頁，請於左側選單切換至您的專屬帳號。")
    
    physical_files = [f for f in os.listdir('.') if f.endswith('.csv') and f not in [req_file, CHAT_DB]]
    passed_names = req_df[req_df['審核結果'].str.contains("過關|通過|OK", na=False)]['申請名稱'].tolist()
    display_targets = [f for f in physical_files if f == DEFAULT_DB or f.replace('.csv','') in passed_names or f in passed_names]

    if display_targets:
        for fname in display_targets:
            if fname == req_file: continue
            
            col1, col2, col3 = st.columns([2.5, 1, 1])
            with col1:
                st.markdown(f"📁 **{fname}**" + (" <span style='color:gray;'>(系統預設)</span>" if fname == DEFAULT_DB else ""), unsafe_allow_html=True)
            with col2:
                st.link_button("🚀 啟動", "https://chouchenglai.streamlit.app/", use_container_width=True)
            with col3:
                # 刪除功能：僅限 Admin 且受保護[cite: 1]
                if is_admin and fname != DEFAULT_DB:
                    if st.button("🗑️ 刪除", key=f"del_{fname}"):
                        os.remove(fname)
                        req_df = req_df[req_df['申請名稱'] != fname.replace('.csv','')]
                        req_df.to_csv(req_file, index=False, encoding='utf-8-sig')
                        st.toast(f"檔案 {fname} 已移除")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("暫無已授權之清單。")

    with tab_live:
        # 第一行：大標題
            st.markdown("### 📡 即時比分同步觀看 (Live)")
        
        # 第二行：藍色背景提示框
            st.info("💡 提示：擇優場次後，請複製賽事，再點擊上方欄目，切換【下單投注】")
           
        # 第三行：嵌入外部比分網[cite: 1]
            st.components.v1.iframe("https://live.titan007.com/indexall_big.aspx", height=800, scrolling=True)

    with tab3: # 📋 歷史記錄
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

    with tab4: # 統計圖表[cite: 2]        
        st.subheader("📈 統計表曲線圖")
        st.write("")
        st.line_chart(main_df["結算總分"], height=320)      

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
