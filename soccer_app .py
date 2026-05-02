import pytz
import streamlit as st
import pandas as pd
import os
import time
import base64
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
    """獲取導航的台北目前時間"""
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
    """安全讀取：跳過數位簽章標記行"""
    if os.path.exists(st.session_state.current_db):
        try:
            # 💡 關鍵修正：加上 comment='#' 確保跳過第一行的協議文字
            df = pd.read_csv(st.session_state.current_db, comment='#')
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

def load_chat():
    if os.path.exists(CHAT_DB):
        return pd.read_csv(CHAT_DB)
    return pd.DataFrame(columns=CHAT_COLUMNS)

def save_chat(nickname, content):
    df = load_chat()
    new_msg = {
        "時間": get_now_time(),
        "暱稱": nickname,
        "內容": content,
        "標籤": "訪客" if nickname != "admin" else "管理員"
    }
    df = pd.concat([df, pd.DataFrame([new_msg])], ignore_index=True)
    df.to_csv(CHAT_DB, index=False, encoding='utf-8-sig')

# --- 初始化 ---
ensure_files()

if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

all_reports = get_all_reports()
if not all_reports:
    all_reports = [DEFAULT_DB]
if st.session_state.current_db not in all_reports:
    st.session_state.current_db = all_reports[0]

# 加載數據
main_df = load_data()

# --- 側邊欄計算與顯示 ---
with st.sidebar:
    st.header("💰 資金與統計中心")
    
    # 重新獲取列表確保同步
    all_reports = get_all_reports()
    idx = all_reports.index(st.session_state.current_db) if st.session_state.current_db in all_reports else 0
    selected_db = st.selectbox("切換報表", all_reports, index=idx)

    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()

    st.divider()

    # 🛡️ 安全獲取當前餘額：防止 KeyError
    if not main_df.empty and "結算總分" in main_df.columns:
        current_bal = int(main_df["結算總分"].iloc[-1])
    else:
        current_bal = 0
        
    st.metric("目前可用本金", f"${current_bal:,}")

    if not main_df.empty:
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

# --- 頂部 Banner ---
img_path = "ccl_logo_header.jpg"
if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<div style="text-align: center; margin-bottom: 50px;"><img src="data:image/jpeg;base64,{img_b64}" style="max-width: 100%; border-radius: 10px;"></div>', unsafe_allow_html=True)
else:    
    st.markdown("<h2 style='text-align: center; color: #004b93;'>足球走地賽事管理系統</h2>", unsafe_allow_html=True)

# 🚀 寶藍色標籤 CSS
st.markdown("""<style>button[data-baseweb="tab"]:nth-child(2) p {color: #007bff !important; font-weight: 900 !important;} button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {border-bottom-color: #007bff !important;}</style>""", unsafe_allow_html=True)

# --- 協議對話框 ---
@st.dialog("📋 CCL-Soccer 會員服務許可協議")
def show_agreement():
    st.warning("⚠️ 為了保障您的權益，請仔細閱讀以下條款。")
    agreement_content = """### 五、 賽事客觀認知 (站長重要提醒)\n**用戶在參考報明牌資訊時，原則已同意免責條款聲明。賽事無絕對的認同，畢竟數據只是提供參考，輸贏與否，取決於球員球技，如果數據再漂亮，球員球技不行，最後也是會無用，量力而為，以平常心看待結果，要有恆心及毅力，必定能有所成就，希望大家都能愉快參與。**"""
    with st.container(height=380): st.markdown(agreement_content)
    st.divider()
    if st.checkbox("我已閱讀並完全同意上述「所有」協定內容"):
        if st.button("確認並進入註冊", type="primary"):
            st.session_state.agreed_terms = True
            st.rerun()

# --- 主功能邏輯 ---
if main_df.empty and st.session_state.current_db == DEFAULT_DB:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()
else:
    tab1, tab2, tab_live, tab3, tab4, tab5 = st.tabs(["💰 下單投注",  "📝 註冊帳號",  "⚽ 即時比分",  "📋 歷史記錄", "📊 統計圖表",  "💬 討 論 區"])

    with tab1: # 下單投注
        balance = current_bal
        if "bet_val" not in st.session_state: st.session_state.bet_val = 5000
        # ... (此處省略部分已有的 HTML 時鐘與音效代碼) ...
        
        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")
        colb = st.columns(5)
        for i, amt in enumerate([5000, 10000, 15000, 20000]):
            if colb[i].button(f"金額 {amt:,}"): 
                st.session_state.bet_val = amt; st.rerun()
        
        c1, c2 = st.columns(2)
        bet_amt = c1.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        gain_amt = c2.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")
        
        can_submit = balance > 0 and bet_amt > 0 and bet_amt <= balance
        cw, cl = st.columns(2)
        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not (can_submit and gain_amt is not None)):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()
        if cl.button("❌ 未過關 (輸)", use_container_width=True, disabled=not can_submit):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

        # 快速補倉
        if st.button("🔗 再投入補倉"): st.session_state.show_add_funds = True; st.rerun()
        if st.session_state.get('show_add_funds', False):
            with st.form("quick_add_funds"):
                add_amt = st.number_input("請輸入補倉金額", min_value=1000, step=1000, value=30000)
                if st.form_submit_button("確認補倉"):
                    new_row = {"日期": get_now_time(), "賽事項目": "手動補倉", "類型": "補倉", "金額": int(add_amt), "盈虧金額": 0, "結算總分": balance + int(add_amt)}
                    save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.session_state.show_add_funds = False; st.rerun()

    with tab2: # 📝 註冊帳號
        if not st.session_state.get("agreed_terms", False):
            st.info("💡 歡迎加入！請點擊按鈕閱讀協議並開始註冊。")
            if st.button("🚀 閱讀協議並開始註冊", use_container_width=True): show_agreement()
        else:
            with st.expander("▼ 加入會員 (協議認證通過)", expanded=True):
                n = st.text_input("名稱", placeholder="請輸入欲創建的報表名稱...")
                if st.button("確認送出"):
                    if n:
                        file_name = f"{n}.csv"
                        now_str = datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        agreement_stamp = f"# 協議狀態: [已認證_同意服務協議] | 認證時間: {now_str}\n"
                        # ✨ 核心修正：註冊時直接寫入初始化數據，防止跳轉後報錯
                        init_df = pd.DataFrame([{"日期": now_str, "賽事項目": "系統初始化", "類型": "初始", "金額": 0, "盈虧金額": 0, "結算總分": 0}])
                        with open(file_name, "w", encoding="utf-8-sig") as f:
                            f.write(agreement_stamp)
                            init_df.to_csv(f, index=False)
                        st.session_state.current_db = file_name
                        st.session_state.agreed_terms = False
                        st.success(f"🎊 會員「{n}」註冊成功！自動切換中..."); time.sleep(1); st.rerun()

    with tab_live: # 即時比分
        st.components.v1.iframe("https://live.titan007.com/indexall_big.aspx", height=800, scrolling=True)

    with tab3: # 歷史記錄
        st.dataframe(main_df.iloc[::-1], use_container_width=True)

    with tab4: # 統計圖表
        if not main_df.empty: st.line_chart(main_df["結算總分"])

    with tab5: # 討論區
        st.write("討論區模組正常運作中...")
        # ... (保留您原本的討論區代碼即可) ...

# --- 底部宣告 ---
st.divider()
st.markdown("""<div style="color: #888; font-size: 0.9em; text-align: left; padding-bottom: 20px;">謹慎理財 信用至上<br>Copyright © 2026 周振來足球管理系統版權所有</div>""", unsafe_allow_html=True)