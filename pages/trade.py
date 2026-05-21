import pytz
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

# 1. 頁面設定 (最頂端)
st.set_page_config(page_title="CCL-Live 體育賽事管理系統", page_icon="⚽", layout="wide")

# --- 基本設定 ---
DEFAULT_DB = "ccl-soccer.csv"
CHAT_DB = "ccl_chat_log.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]
CHAT_COLUMNS = ["時間", "暱稱", "內容", "標籤"]

TW_TZ = pytz.timezone('Asia/Taipei') # 設定台北時區

def get_now_time():
    # 這裡會回傳正確的台北時間字串
    return datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")

# --- 工具 ---
def get_all_reports():
    # 這裡加上條件：排除「註冊帳本 (pending_requests.csv)」和「聊天紀錄」
    forbidden_files = [CHAT_DB, "pending_requests.csv"]
    return [f for f in os.listdir('.') if f.endswith('.csv') and f not in forbidden_files]

def ensure_files():
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=CHAT_COLUMNS).to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

def load_data():
    if os.path.exists(st.session_state.current_db):
        try:
            # 自動跳過前面非 CSV 的說明文字
            df = pd.read_csv(
                        st.session_state.current_db,
                        encoding='utf-8-sig',
                        on_bad_lines='skip'
                        )

            # 如果欄位不完整，自動修復
            missing_cols = [col for col in COLUMNS if col not in df.columns]
            for col in missing_cols:
                df[col] = None

            df = df[COLUMNS]

            # 清除舊月份欄位
            if "月份" in df.columns:
                df = df.drop(columns=["月份"])

            return df

        except Exception as e:
            st.error(f"CSV 讀取失敗：{e}")
            return pd.DataFrame(columns=COLUMNS)

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
current_tw_date = datetime.now(TW_TZ).date()

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

# ==========================================
# 🚀 全局討論區提醒系統 
# ==========================================

# 1. 數據準備
current_chat_data = load_chat()
new_msg_count = len(current_chat_data)

if 'last_chat_count' not in st.session_state:
    st.session_state.last_chat_count = new_msg_count

# 2. 直接在這裡抓取身分權限 (解決報錯關鍵)
check_is_admin = False
req_file = "pending_requests.csv"
if "current_db" in st.session_state and os.path.exists(req_file):
    try:
        r_df = pd.read_csv(req_file)
        curr_name = st.session_state.current_db.replace('.csv', '')
        admin_match = r_df[(r_df['申請名稱'] == curr_name) & (r_df['權限'].str.upper() == 'ADMIN')]
        if not admin_match.empty:
            check_is_admin = True
    except:
        pass

# 3. 側邊欄開關 (使用我們剛才算好的 check_is_admin)
with st.sidebar:
    st.divider()
    # 提供開關給用戶，不論是誰都能控制自己的接收狀態
    show_notif = st.toggle("接收討論區新訊息廣播", value=True)
    if check_is_admin:
        st.caption("🛡️ 管理員身分已驗證")

# 4. 提醒邏輯：管理員發言穿透 OR 用戶開啟開關
if new_msg_count > st.session_state.last_chat_count:
    latest_msg = current_chat_data.iloc[-1]
    
    sender_name = str(latest_msg['暱稱']).lower()
    is_sender_admin = sender_name in ['管理員', 'admin']
    
    if is_sender_admin or show_notif:
        # 判斷樣式
        if is_sender_admin:
            box_style = "background: linear-gradient(90deg, #1E90FF, #00008B); border-left: 10px solid #FFD700;"
            title_tag = "🔥 【管理員指令】"
        else:
            box_style = "background: linear-gradient(90deg, #1E90FF, #00BFFF); border-left: 6px solid #FFD700;"
            title_tag = "📢 新留言提醒"

        st.markdown(f"""
            <div style="{box_style} color: white; padding: 15px 20px; border-radius: 8px; 
                        margin-bottom: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
                        animation: slideIn 0.5s ease-out;">
                <b>{title_tag}</b><br>
                <span style="color: #FFD700; font-weight: bold;">{latest_msg['暱稱']}</span> 
                說：「{latest_msg['內容'][:30]}...」
            </div>
            <style>@keyframes slideIn {{ from {{ transform: translateY(-20px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}</style>
        """, unsafe_allow_html=True)
        
        c_notif1, c_notif2 = st.columns([2.8, 7.2])
        if c_notif1.button("🔍 立即查看", key="notif_go_v6"):
            st.session_state.last_chat_count = new_msg_count
            st.rerun()
        if c_notif2.button("🆗 我知道了", key="notif_close_v6"):
            st.session_state.last_chat_count = new_msg_count
            st.rerun()

# --- Sidebar (側邊欄) ---
with st.sidebar:

    st.header("💰 資金與統計中心")

    idx = all_reports.index(st.session_state.current_db) \
        if st.session_state.current_db in all_reports else 0

    selected_db = st.selectbox(
        "切換帳號",
        all_reports,
        index=idx
    )

    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()

    st.divider()

    if not main_df.empty:

        try:
            current_bal = int(
                pd.to_numeric(
                    main_df["結算總分"],
                    errors='coerce'
                ).dropna().iloc[-1]
            )

        except:
            current_bal = 0

        st.metric(
            "目前可用本金",
            f"${current_bal:,}"
        )

        invest_types = ['初始', '手動補倉', '補倉']

        total_investment = main_df[
            main_df['類型'].isin(invest_types)
        ]['金額'].sum()

        st.write(
            f"💼 累積投入: `${total_investment:,}`"
        )

        real_profit = current_bal - total_investment

        if real_profit >= 0:
            st.success(
                f"📈 純獲利: `${real_profit:,}`"
            )
        else:
            st.error(
                f"📉 尚虧: `${abs(real_profit):,}`"
            )

        csv = main_df.to_csv(
            index=False
        ).encode('utf-8-sig')

        st.download_button(
            "📥 下載完整紀錄 (CSV)",
            data=csv,
            file_name="soccer_backup.csv"
        )

# --- 邏輯判斷與主功能 ---
if main_df.empty or main_df["結算總分"].dropna().empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()
else:
    # 核心：標籤頁定義
    st.markdown("""
    <style>
        /* 針對 Streamlit 預設標籤列的第二個按鈕 (nth-child(2)) 裡面的文字 (p) 進行樣式修改 */
        div[data-baseweb="tab-list"] button[data-baseweb="tab"]:nth-child(2) p {
            color: #1E90FF !important;      /* 替換為閃耀的藍寶石色 */
            font-weight: bold !important;   /* 強制字體加粗 */
        }
    </style>
    """, unsafe_allow_html=True)  

col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 返回首頁"):
        st.switch_page("/soccer_app.py")

with col2:
    if st.button("🎯 返回主平台"):
        st.switch_page("pages/ccl-live.py")

# 下單投注

    st.write("")
    st.markdown(
    '<div id="top_page"></div>',
    unsafe_allow_html=True
)

    try:
        balance = int(main_df["結算總分"].iloc[-1])

    except:
        balance = 0

    # =========================
    # 台北時間
    # =========================

    st.components.v1.html("""
        <style>
            #clock-container {
                display: flex;
                align-items: center;
                background-color: #f8f9fb;
                padding: 8px 15px;
                border-radius: 6px;
                border-left: 5px solid #ff4b4b;
                font-family: sans-serif;
                margin-bottom: 5px;
            }

            #clock {
                font-size: 15px;
                font-weight: 600;
                color: #31333f;
                letter-spacing: 0.8px;
            }

            .prefix {
                font-size: 14px;
                color: #666;
                margin-right: 12px;
            }
        </style>

        <div id="clock-container">
            <span class="prefix">
                台北標準時間 (GMT+8) :
            </span>

            <span id="clock">
                載入中...
            </span>
        </div>

        <script>
            function updateClock() {

                const now = new Date();

                const hh = String(
                    now.getHours()
                ).padStart(2, '0');

                const mm = String(
                    now.getMinutes()
                ).padStart(2, '0');

                const ss = String(
                    now.getSeconds()
                ).padStart(2, '0');

                document.getElementById('clock')
                    .textContent =
                    now.toLocaleDateString()
                    + " "
                    + hh + ":" + mm + ":" + ss;
            }

            setInterval(updateClock, 1000);

            updateClock();
        </script>

    """, height=52)

    st.write("")

# =========================
# 賽事資訊
# =========================

st.markdown("## 🏆 賽事資訊")

# =========================
# 快速索引
# =========================

st.markdown("""
<div style="
    display:flex;
    flex-wrap:wrap;
    gap:12px;
    margin-bottom:25px;
">
""", unsafe_allow_html=True)

# =========================
# 初始化賽事數量
# =========================

if "extra_match_count" not in st.session_state:

    st.session_state.extra_match_count = 5

# =========================
# 快速索引
# =========================

show_count = min(
    st.session_state.extra_match_count,
    10
)

col_nav = st.columns(5)

for x in range(1, show_count + 1):

    current_col = col_nav[(x - 1) % 5]

    with current_col:

        st.markdown(
            f"""
            <a href="#match_{x}"
                style="
                    text-decoration:none;
                    background:#f1f3f6;
                    padding:12px;
                    border-radius:10px;
                    color:#333;
                    font-weight:bold;
                    display:block;
                    text-align:center;
                    margin-bottom:10px;
                ">
                第{x}場
            </a>
            """,
            unsafe_allow_html=True
        )

st.divider()

# =========================
# 建立賽事區塊
# =========================

for i in range(1, st.session_state.extra_match_count + 1):

    # -------------------------
    # 錨點定位
    # -------------------------

    st.markdown(
        f"""
        <div id="match_{i}"></div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------
    # 賽事標題
    # -------------------------

    st.markdown(f"## 📌 第{i}場賽事")

    # -------------------------
    # 賽事輸入
    # -------------------------

    match_info = st.text_area(
        f"請輸入第{i}場賽事",
        placeholder="例如：英超 阿仙奴 vs 車路士",
        key=f"match_input_{i}"
    )

    # -------------------------
    # 摺疊下注設定
    # -------------------------

    with st.expander(f"⚙️ 第{i}場下注設定"):

        bet_amt = st.number_input(
            f"第{i}場下注金額",
            min_value=0,
            max_value=1000000,
            value=5000,
            step=1000,
            key=f"bet_{i}"
        )

        gain_amt = st.number_input(
            f"第{i}場盈利金額",
            min_value=0,
            max_value=1000000,
            value=0,
            step=1000,
            key=f"gain_{i}"
        )

        col_win, col_lose = st.columns(2)

        # =====================
        # 過關
        # =====================

        if col_win.button(
            f"✅ 第{i}場過關",
            key=f"win_{i}"
        ):

            if match_info.strip() == "":

                st.warning(
                    f"請先輸入第{i}場賽事資訊"
                )

            else:

                latest_df = load_data()

                latest_balance = int(
                    latest_df["結算總分"].iloc[-1]
                )

                new_balance = (
                    latest_balance + int(gain_amt)
                )

                new_row = {
                    "日期": get_now_time(),
                    "賽事項目": match_info,
                    "類型": "贏 (+)",
                    "金額": int(gain_amt),
                    "盈虧金額": int(gain_amt),
                    "結算總分": new_balance
                }

                updated_df = pd.concat(
                    [
                        latest_df,
                        pd.DataFrame([new_row])
                    ],
                    ignore_index=True
                )

                save_data(updated_df)

                st.success(
                    f"第{i}場已記錄為過關"
                )

                st.rerun()

        # =====================
        # 未過關
        # =====================

        if col_lose.button(
            f"❌ 第{i}場未過關",
            key=f"lose_{i}"
        ):

            if match_info.strip() == "":

                st.warning(
                    f"請先輸入第{i}場賽事資訊"
                )

            else:

                latest_df = load_data()

                latest_balance = int(
                    latest_df["結算總分"].iloc[-1]
                )

                new_balance = (
                    latest_balance - int(bet_amt)
                )

                new_row = {
                    "日期": get_now_time(),
                    "賽事項目": match_info,
                    "類型": "輸 (-)",
                    "金額": int(bet_amt),
                    "盈虧金額": -int(bet_amt),
                    "結算總分": new_balance
                }

                updated_df = pd.concat(
                    [
                        latest_df,
                        pd.DataFrame([new_row])
                    ],
                    ignore_index=True
                )

                save_data(updated_df)

                st.error(
                    f"第{i}場已記錄為未過關"
                )

                st.rerun()

    st.divider()

# =========================
# 更多賽事
# =========================

if st.button("➕ 更多賽事（再新增5場）"):

    if st.session_state.extra_match_count < 10:

        st.session_state.extra_match_count += 5

        st.rerun()

# =========================
# 快速補倉
# =========================

st.write("")

st.markdown("""
<a href="#top_page"
style="
    text-decoration:none;
    background:#1E90FF;
    color:white;
    padding:10px 18px;
    border-radius:8px;
    font-weight:bold;
">
⬆ 返回頂部
</a>
""", unsafe_allow_html=True)

if st.button("🔗 再投入補倉"):

    st.write("")

    st.session_state.show_add_funds = True

if st.session_state.get(
    'show_add_funds',
    False
):

    st.divider()

    st.subheader("📥 快速補倉面板")

    with st.form("quick_add_funds"):

        add_amt = st.number_input(
            "請輸入補倉金額",
            min_value=1000,
            step=1000,
            value=30000
        )

        c_submit, c_cancel = st.columns([2, 8])

        if c_submit.form_submit_button(
            "確認補倉"
        ):

            current_bal = int(
                main_df["結算總分"].iloc[-1]
            )

            new_row = {
                "日期": get_now_time(),
                "賽事項目": "手動補倉 (快捷)",
                "類型": "補倉",
                "金額": int(add_amt),
                "盈虧金額": 0,
                "結算總分":
                    current_bal + int(add_amt)
            }

            updated_df = pd.concat(
                [
                    main_df,
                    pd.DataFrame([new_row])
                ],
                ignore_index=True
            )

            save_data(updated_df)

            st.session_state.show_add_funds = False

            st.success(
                f"成功補倉 ${add_amt:,}！"
            )

            time.sleep(0.5)

            st.rerun()

        if c_cancel.form_submit_button(
            "取消"
        ):

            st.session_state.show_add_funds = False

            st.rerun()    

col1= st.columns(1)

# --- 底部 ---
st.markdown("""
<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">
謹慎理財 信用至上<br>
Copyright © 2026 CCL-Live 體育賽事管理系統版權所有
</div>
""", unsafe_allow_html=True)