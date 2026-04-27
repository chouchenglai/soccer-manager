import pytz
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 時區工具 ---
def now_taipei():
    tz = pytz.timezone("Asia/Taipei")
    return datetime.now(tz)

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
        now = now_taipei()
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

        with tab1:
        # 1. 取得當前餘額 (避免破產時出錯)
        current_bal = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
        
        m_info = st.text_area("賽事資訊", placeholder="請輸入賽事詳情...")
        
        col1, col2 = st.columns(2)
        with col1:
            # 【關鍵修復】將 max_value 設為 1,000,000。這樣即便餘額是 0，輸入框也不會崩潰。
            bet = st.number_input("下注金額", min_value=0, max_value=1000000, value=5000)
            
        with col2:
            gain = st.number_input("預計獲利", min_value=0, max_value=1000000, value=5000)
        
        # 2. 判斷是否允許投注 (邏輯檢查，不影響 UI 渲染)
        can_submit = True
        if bet > current_bal:
            st.error(f"⚠️ 餘額不足！目前可用：{current_bal:,}")
            can_submit = False
        elif not m_info.strip():
            can_submit = False

        # 3. 按鈕區 (增加 disabled 屬性，餘額不足時按鈕會變灰，無法點擊)
        c_w, c_l = st.columns(2)
        if c_w.button("✅ 贏", use_container_width=True, type="primary", disabled=not can_submit):
            new = {
                "日期": get_now_time(),
                "賽事項目": m_info,
                "類型": "贏 (+)",
                "金額": int(gain),
                "盈虧金額": int(gain),
                "結算總分": current_bal + int(gain)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()

        if c_l.button("❌ 輸", use_container_width=True, disabled=not can_submit):
            new = {
                "日期": get_now_time(),
                "賽事項目": m_info,
                "類型": "輸 (-)",
                "金額": int(bet),
                "盈虧金額": -int(bet),
                "結算總分": current_bal - int(bet)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new])], ignore_index=True))
            st.rerun()

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
        st.line_chart(main_df["結算總分"])

        data = main_df[main_df['類型'].isin(['贏 (+)', '輸 (-)'])]
        if not data.empty:
            win = len(data[data['類型'] == '贏 (+)'])
            st.metric("勝率", f"{win/len(data)*100:.1f}%")

       # --- TAB4 ---
    with tab4:
        with st.expander("補倉"):
            val_str = st.text_input("金額", "30,000")
            try:
                # 移除逗號並轉為整數
                val = int(val_str.replace(",", ""))
            except:
                val = 0

            if st.button("補") and val > 0:
                # 破產保護邏輯：即便 main_df 是空的或結算總分抓不到，也預設為 0
                try:
                    if not main_df.empty:
                        bal = int(main_df["結算總分"].iloc[-1])
                    else:
                        bal = 0
                except:
                    bal = 0
                
                new = {
                    "日期": get_now_time(),
                    "賽事項目": "手動補倉",
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
                    new_file = f"{name}.csv"
                    pd.DataFrame(columns=COLUMNS).to_csv(new_file, index=False)
                    st.rerun()

        with st.expander("刪除報表"):
            deletable = [f for f in all_reports if f != DEFAULT_DB]
            if deletable:
                target = st.selectbox("選擇刪除對象", deletable)
                if st.button("刪除"):
                    os.remove(target)
                    st.session_state.current_db = DEFAULT_DB
                    st.rerun()