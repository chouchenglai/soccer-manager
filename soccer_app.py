import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz   # 新增：處理時區

# --- 基本設定 ---
DEFAULT_DB = "soccer_master_data.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]

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

# --- 時區工具 ---
def now_taipei():
    tz = pytz.timezone("Asia/Taipei")
    return datetime.now(tz)

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

    if not main_df.empty:
        balance = int(main_df["結算總分"].iloc[-1])
        st.metric("目前可用本金", f"{balance:,}")

        total_investment = main_df[main_df['類型'].isin(['初始', '手動補倉'])]['金額'].sum()
        real_profit = balance - total_investment

        st.write(f"💼 累計投入: `{total_investment:,}`")

        if real_profit >= 0:
            st.success(f"📈 純獲利: `{real_profit:,}`")
        else:
            st.error(f"📉 尚虧: `{abs(real_profit):,}`")

    st.write(f"檔案: `{st.session_state.current_db}`")

# --- 標題 ---
st.markdown("<h1 style='text-align: center;'>⚽ 足球賽事管理系統</h1>", unsafe_allow_html=True)

st.markdown(
    "<h4 style='text-align: center; color: white; background-color: red; padding: 10px; border-radius: 10px;'>⚠️ 謹慎理財！信用至上！ ⚠️</h4>",
    unsafe_allow_html=True
)

# --- 初始化 ---
if main_df.empty:
    st.subheader("初始化報表")

    init_cap_str = st.text_input("起始本金", "60,000")
    try:
        init_cap = int(init_cap_str.replace(",", ""))
    except:
        init_cap = 0

    if st.button("建立"):
        now = now_taipei()
        row = {
            "日期": now.strftime("%Y-%m-%d %H:%M"),
            "賽事項目": "初始",
            "類型": "初始",
            "金額": init_cap,
            "盈虧金額": 0,
            "結算總分": init_cap
        }
        save_data(pd.DataFrame([row]))
        st.rerun()

# --- 主功能 ---
else:
    tab1, tab2, tab3, tab4 = st.tabs(["💰投注下單", "📋歷史記錄", "📊統計圖表", "📈報表管理"])

    # --- TAB1 ---
    with tab1:
        balance = int(main_df["結算總分"].iloc[-1])

        if "bet_val" not in st.session_state:
            st.session_state.bet_val = 5000

        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士")

        colb = st.columns(4)
        if colb[0].button("🔵 5,000"): st.session_state.bet_val = 5000
        if colb[1].button("🟢 10,000"): st.session_state.bet_val = 10000
        if colb[2].button("🟡 15,000"): st.session_state.bet_val = 15000
        if colb[3].button("🔴 20,000"): st.session_state.bet_val = 20000

        c1, c2 = st.columns(2)

        with c1:
            bet_amt_str = st.text_input("下注金額", f"{st.session_state.bet_val:,}")
            try:
                bet_amt = int(bet_amt_str.replace(",", ""))
            except:
                bet_amt = 0

        with c2:
            gain_amt_str = st.text_input("盈利金額", "")
            try:
                gain_amt = int(gain_amt_str.replace(",", "")) if gain_amt_str else 0
            except:
                gain_amt = 0

        st.session_state.bet_val = bet_amt
        st.session_state.gain_val = gain_amt

        can = balance > 0 and bet_amt > 0 and bet_amt <= balance

        cw, cl = st.columns(2)

        if cw.button("✅過關 (贏)", disabled=not can and not gain_amt):
            now = now_taipei()
            new = {
                "日期": now.strftime("%Y-%m-%d %H:%M"),
                "賽事項目": m_info,
                "類型": "贏 (+)",
                "金額": gain_amt,
                "盈虧金額": gain_amt,
                "結算總分": balance + gain_amt
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()

        if cl.button("❌ 未過關 (輸)", disabled=not can):
            now = now_taipei()
            new = {
                "日期": now.strftime("%Y-%m-%d %H:%M"),
                "賽事項目": m_info,
                "類型": "輸 (-)",
                "金額": bet_amt,
                "盈虧金額": -bet_amt,
                "結算總分": balance - bet_amt
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()
