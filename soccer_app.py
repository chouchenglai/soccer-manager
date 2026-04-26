import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. 多報表管理邏輯 ---
DEFAULT_DB = "soccer_master_data.csv"

def get_all_reports():
    """搜尋資料夾內所有的 csv 戰績表"""
    return [f for f in os.listdir('.') if f.endswith('.csv') and f != 'requirements.txt']

# 初始化 Session State
if 'current_db' not in st.session_state:
    st.session_state.current_db = DEFAULT_DB

def load_data():
    if os.path.exists(st.session_state.current_db):
        try:
            return pd.read_csv(st.session_state.current_db)
        except:
            return pd.DataFrame(columns=["日期", "月份", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"])
    return pd.DataFrame(columns=["日期", "月份", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"])

def save_data(df):
    df.to_csv(st.session_state.current_db, index=False, encoding='utf-8-sig')

# --- 2. 頁面初始化 ---
st.set_page_config(page_title="足球賽事一體化管理系統", layout="wide")

# 讀取當前數據
main_df = load_data()

# --- 3. Sidebar (已全部改回中文) ---
with st.sidebar:
    st.header("📊 帳戶統計中心")
    all_reports = get_all_reports()
    
    # 報表切換
    selected_db = st.selectbox("切換當前報表", all_reports, index=all_reports.index(st.session_state.current_db) if st.session_state.current_db in all_reports else 0)
    
    if selected_db != st.session_state.current_db:
        st.session_state.current_db = selected_db
        st.rerun()
    
    st.divider()
    if not main_df.empty:
        current_total = int(main_df["結算總分"].iloc[-1])
        st.metric("目前帳戶總積分", f"{current_total:,}")
    
    st.write(f"當前檔案: `{st.session_state.current_db}`")

# --- 4. 主介面 (標題與警示語) ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>⚽ 足球賽事走地一體化管理</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: #B91C1C; font-weight: bold;'>⚠️ 謹慎理財！信用至上！ ⚠️</h5>", unsafe_allow_html=True)

if main_df.empty:
    st.subheader("🚀 初始化新報表")
    init_cap = st.number_input("請設定起始本金", value=60000, step=1000)
    if st.button("確認開啟新報表"):
        now = datetime.now()
        init_row = {"日期": now.strftime("%Y-%m-%d %H:%M"), "月份": now.strftime("%Y-%m"), "賽事項目": "系統：初始本金匯入", "類型": "初始", "金額": 0, "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([init_row]))
        st.rerun()
else:
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 快速錄入", "📋 歷史明細", "📊 統計圖表", "📂 報表管理"])

    with tab1:
        m_info = st.text_area("賽事資訊", height=80, placeholder="例如：英超 阿仙奴 vs 車路士")
        
        st.write("🪙 籌碼快選")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("5K", use_container_width=True): st.session_state.bet_input = 5000; st.session_state.gain_input = 5000
        if c2.button("10K", use_container_width=True): st.session_state.bet_input = 10000; st.session_state.gain_input = 10000
        if c3.button("15K", use_container_width=True): st.session_state.bet_input = 15000; st.session_state.gain_input = 15000
        if c4.button("20K", use_container_width=True): st.session_state.bet_input = 20000; st.session_state.gain_input = 20000
        
        col1, col2 = st.columns(2)
        with col1: bet_val = st.number_input("未過關扣除", value=st.session_state.get('bet_input', 5000), step=100)
        with col2: gain_val = st.number_input("過關增加", value=st.session_state.get('gain_input', 5000), step=100)
        
        c_win, c_loss = st.columns(2)
        balance = int(main_df["結算總分"].iloc[-1])
        if c_win.button("✅ 過關 (贏)", use_container_width=True, type="primary"):
            new_row = {"日期": datetime.now().strftime("%Y-%m-%d %H:%M"), "月份": datetime.now().strftime("%Y-%m"), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_val), "盈虧金額": int(gain_val), "結算總分": balance + int(gain_val)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()
        if c_loss.button("❌ 未過關 (輸)", use_container_width=True):
            new_row = {"日期": datetime.now().strftime("%Y-%m-%d %H:%M"), "月份": datetime.now().strftime("%Y-%m"), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_val), "盈虧金額": -int(bet_val), "結算總分": balance - int(bet_val)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

    with tab2:
        st.dataframe(main_df.iloc[::-1].style.format({"金額": "{:,}", "盈虧金額": "{:+,.0f}", "結算總分": "{:,}"}), use_container_width=True)

    with tab3:
        st.line_chart(main_df["結算總分"])
        pie_data = main_df[main_df['類型'].isin(['贏 (+)', '輸 (-)'])]
        if not pie_data.empty:
            win_n = len(pie_data[pie_data['類型']=='贏 (+)'])
            st.metric("當前報表命中率", f"{win_n/len(pie_data)*100:.1f}%")

    with tab4:
        st.subheader("📂 報表維護中心")
        with st.expander("➕ 建立新報表"):
            new_name = st.text_input("輸入新報表名稱")
            if st.button("確認建立"):
                if new_name:
                    new_file = f"{new_name}.csv"
                    pd.DataFrame(columns=["日期", "月份", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"]).to_csv(new_file, index=False)
                    st.success(f"報表 '{new_name}' 已成功建立！")
                    st.rerun()
        
        st.divider()
        with st.expander("🗑️ 刪除報表"):
            st.warning("警告：此操作無法還原！")
            target_del = st.selectbox("選擇要刪除的報表", [f for f in all_reports if f != DEFAULT_DB])
            if st.button("🔥 永久刪除該報表"):
                if target_del:
                    os.remove(target_del)
                    st.session_state.current_db = DEFAULT_DB
                    st.success(f"已成功刪除 {target_del}")
                    st.rerun()