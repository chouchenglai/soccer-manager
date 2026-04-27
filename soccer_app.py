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

    # --- TAB1 ---
    with tab1:
        balance = int(main_df["結算總分"].iloc[-1])

        if "bet_val" not in st.session_state:
            st.session_state.bet_val = 5000

        # 加入提示文字
        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士")

        colb = st.columns(4)
        if colb[0].button("🔵5,000"): st.session_state.bet_val = 5000
        if colb[1].button("🟢 10,000"): st.session_state.bet_val = 10000
        if colb[2].button("🟡 15,000"): st.session_state.bet_val = 15000
        if colb[3].button("🔴 20,000"): st.session_state.bet_val = 20000

        c1, c2 = st.columns(2)

        with c1:
            bet_amt = st.number_input("下注金額", 0, balance, int(st.session_state.bet_val))
        with c2:
            gain_amt = st.number_input(
                "盈利金額",
                min_value=0,
                max_value=999999999,
                value=None,
                placeholder="請輸入盈利金額"
            )

        st.session_state.bet_val = bet_amt
        st.session_state.gain_val = gain_amt if gain_amt else 0

        can = balance > 0 and bet_amt > 0 and bet_amt <= balance

        cw, cl = st.columns(2)

        if cw.button("✅過關 (贏)", disabled=not can and not gain_amt):
            new = {
                "日期": get_now_time(),
                "賽事項目": m_info,
                "類型": "贏 (+)",
                "金額": gain_amt,
                "盈虧金額": gain_amt,
                "結算總分": balance + gain_amt
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()

        if cl.button("❌ 未過關 (輸)", disabled=not can):
            new = {
                "日期": get_now_time(),
                "賽事項目": m_info,
                "類型": "輸 (-)",
                "金額": bet_amt,
                "盈虧金額": -bet_amt,
                "結算總分": balance - bet_amt
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()

# --- TAB2: 歷史明細 (防彈穩定版) ---
    with tab2:
        # 1. 安全抓取初始本金
        init_cap = 60000
        if not main_df.empty and '類型' in main_df.columns and '金額' in main_df.columns:
            initial_rows = main_df[main_df['類型'] == '初始']
            if not initial_rows.empty:
                init_cap = initial_rows['金額'].iloc[0]

        # 2. 定義顏色判斷邏輯
        def color_row(row):
            # 建立預設樣式
            style = ['color: black'] * len(row)
            
            # 檢查必要欄位是否存在，避免 KeyError
            required_cols = ['盈虧金額', '結算總分', '類型']
            if not all(col in row.index for col in required_cols):
                return style

            try:
                # --- A. 單場勝負顏色 ---
                p_val = float(row['盈虧金額'])
                win_loss_style = 'color: green' if p_val > 0 else 'color: red' if p_val < 0 else 'color: black'

                # --- B. 帳戶存亡顏色 ---
                s_val = float(row['結算總分'])
                total_score_style = 'color: green' if s_val >= float(init_cap) else 'color: red'

                # 3. 獲取索引並塗色
                type_idx = row.index.get_loc('類型')
                profit_idx = row.index.get_loc('盈虧金額')
                total_idx = row.index.get_loc('結算總分')

                style[type_idx] = win_loss_style
                style[profit_idx] = win_loss_style
                style[total_idx] = total_score_style
            except:
                pass
            
            return style

        # 4. 渲染表格 (增加空資料保護)
        if main_df.empty:
            st.info("目前尚無資料紀錄。")
        else:
            st.dataframe(
                main_df.iloc[::-1].style.apply(color_row, axis=1)
                .format({
                    "金額": "{:,.0f}", 
                    "盈虧金額": "{:+,.0f}", 
                    "結算總分": "{:,.0f}"
                }, na_rep="0"), 
                use_container_width=True
            )

# --- TAB3 ---
    with tab3:
        st.line_chart(main_df["結算總分"])

        data = main_df[main_df['類型'].isin(['贏 (+)', '輸 (-)'])]
        if not data.empty:
            win = len(data[data['類型'] == '贏 (+)'])
            st.metric("勝率", f"{win/len(data)*100:.1f}%")

# --- TAB4 ---
with tab4:   # 這裡和 tab1, tab2, tab3 保持同一層
    with st.expander("補倉"):   # 再縮排一層
        val_str = st.text_input("金額", "30,000")  # 再縮排一層
        try:
            val = int(val_str.replace(",", ""))
        except:
            val = 0

        if st.button("補") and val > 0:
            bal = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
            new = {
                "日期": now_taipei().strftime("%Y-%m-%d %H:%M"),
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
