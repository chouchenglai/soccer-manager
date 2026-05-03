import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 基本設定 ---
DEFAULT_DB = "soccer_data.csv"
COLUMNS = ["日期", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]

# --- 核心工具 ---
def ensure_default_db():
    # 如果檔案不存在，建立一個全新的空白檔案
    if not os.path.exists(DEFAULT_DB):
        pd.DataFrame(columns=COLUMNS).to_csv(DEFAULT_DB, index=False)

def load_data():
    ensure_default_db()
    try:
        df = pd.read_csv(DEFAULT_DB)
        return df
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DEFAULT_DB, index=False)
    st.success("✅ 紀錄儲存成功！")

# --- 程式初始化 ---
st.set_page_config(page_title="足球管理中心 - 專業本地版", layout="wide")
main_df = load_data()

# --- 側邊欄：統計與備份 ---
st.sidebar.title("⚽ 本地管理中心")

if not main_df.empty:
    # 1. 目前總餘額
    current_bal = main_df["結算總分"].iloc[-1]
    st.sidebar.metric("目前總餘額", f"${current_bal:,}")

    # 2. 累計投入 (自動偵測 '初始' 與 '補倉' 類型)
    invest_types = ['初始', '手動補倉', '補倉']
    total_investment = main_df[main_df['類型'].isin(invest_types)]['金額'].sum()
    st.sidebar.write(f"💼 累積投入: `${total_investment:,}`")
    
    # 3. 純獲利計算與變色顯示
    real_profit = current_bal - total_investment
    if real_profit >= 0:
        st.sidebar.success(f"📈 純獲利: `${real_profit:,}`")
    else:
        st.sidebar.error(f"📉 尚虧: `${abs(real_profit):,}`")

    st.sidebar.divider()
    # 4. 下載備份功能
    csv = main_df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 下載完整紀錄 (CSV)", data=csv, file_name="soccer_backup.csv")

# --- 主介面 ---
tab1, tab2, tab3 = st.tabs(["📊 數據錄入", "📜 歷史紀錄", "📈 趨勢分析"])

with tab1:
    # --- 關鍵邏輯：如果資料庫是空的，必須先設定本金 ---
    if main_df.empty:
        st.subheader("🏁 初始化報表")
        st.info("偵測到全新帳本，請先設定您的起始本金。")
        init_cap = st.number_input("請輸入起始本金 (例如您的 60,000)", value=60000, step=1000)
        
        # 使用系統當前時間作為起始時間
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if st.button("建立初始紀錄並開始使用"):
            row = {
                "日期": current_time,
                "賽事項目": "初始本金",
                "類型": "初始",
                "金額": int(init_cap),
                "盈虧金額": 0,
                "結算總分": int(init_cap)
            }
            save_data(pd.DataFrame([row]))
            st.rerun()
            
    else:
        # --- 正常錄入介面 ---
        st.subheader("📝 賽事結果登錄")
        
        col_d, col_t = st.columns(2)
        # 預設直接抓系統當下的日期與時間，方便快速錄入
        input_date = col_d.date_input("1. 選擇日期", datetime.now())
        input_time = col_t.time_input("2. 選擇時間", datetime.now())
        log_time = f"{input_date} {input_time.strftime('%H:%M')}"
        
        m_info = st.text_input("3. 賽事項目", placeholder="例如：英超 曼聯vs利物浦")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            bet_amt = st.number_input("4. 下注金額", min_value=0, value=5000, step=100)
        with col_a2:
            profit_amt = st.number_input("5. 贏球盈利 (贏球時加分的金額)", min_value=0, value=4000, step=100)
        
        # 目前結算總分 (地基)
        last_balance = int(main_df["結算總分"].iloc[-1])

        cw1, cw2 = st.columns(2)
        
        if cw1.button("✅ 過關 (贏)", use_container_width=True, type="primary"):
            new_row = {
                "日期": log_time,
                "賽事項目": m_info if m_info else "未命名賽事",
                "類型": "贏 (+)",
                "金額": int(bet_amt),
                "盈虧金額": int(profit_amt),
                "結算總分": last_balance + int(profit_amt)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

        if cw2.button("❌ 未過關 (輸)", use_container_width=True):
            new_row = {
                "日期": log_time,
                "賽事項目": m_info if m_info else "未命名賽事",
                "類型": "輸 (-)",
                "金額": int(bet_amt),
                "盈虧金額": -int(bet_amt),
                "結算總分": last_balance - int(bet_amt)
            }
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

        st.divider()
        st.write("### 🕒 最近 5 筆紀錄")
        st.dataframe(main_df.tail(5), use_container_width=True)

with tab2:
    st.subheader("📜 歷史全紀錄")
    if not main_df.empty:
        # 倒序顯示，最新的在最上面
        st.dataframe(
            main_df.iloc[::-1], 
            use_container_width=True,
            column_config={
                "金額": st.column_config.NumberColumn(format="$ %d"),
                "盈虧金額": st.column_config.NumberColumn(format="$ %d"),
                "結算總分": st.column_config.NumberColumn(format="$ %d"),
            }
        )

with tab3:
    st.subheader("📈 總盈虧趨勢")
    if not main_df.empty:
        st.line_chart(main_df["結算總分"])