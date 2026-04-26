import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# --- 1. 核心數據管理 ---
DB_FILE = "soccer_master_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["日期", "月份", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# --- 2. 頁面初始化 ---
st.set_page_config(page_title="足球全能一體化管理系統", layout="wide")

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. 籌碼與數據更新邏輯 ---
def update_chip(val):
    st.session_state.bet_input = val
    st.session_state.gain_input = val

def delete_record(index):
    # 刪除特定索引的數據
    st.session_state.main_df = st.session_state.main_df.drop(index).reset_index(drop=True)
    # 重新計算所有「結算總分」，確保刪除中間紀錄時後面的餘額會自動修正
    if not st.session_state.main_df.empty:
        new_scores = []
        current_score = 0
        for i, row in st.session_state.main_df.iterrows():
            if row['類型'] == '初始':
                current_score = row['結算總分']
            else:
                current_score += row['盈虧金額']
            new_scores.append(current_score)
        st.session_state.main_df['結算總分'] = new_scores
    save_data(st.session_state.main_df)
    st.toast("✅ 紀錄已刪除，金額已自動重新計算")

# --- 4. 側邊欄 ---
with st.sidebar:
    st.header("💰 資金與統計中心")
    if st.session_state.main_df.empty:
        st.subheader("第一步：設定起點")
        init_cap = st.number_input("請輸入起始本金", value=60000, step=1000, format="%d")
        if st.button("確認設定並開始"):
            now = datetime.now()
            init_row = {"日期": now.strftime("%Y-%m-%d %H:%M"), "月份": now.strftime("%Y-%m"), "賽事項目": "系統：初始本金匯入", "類型": "初始", "金額": 0, "盈虧金額": 0, "結算總分": int(init_cap)}
            st.session_state.main_df = pd.DataFrame([init_row])
            save_data(st.session_state.main_df)
            st.rerun()
    
    if not st.session_state.main_df.empty:
        df = st.session_state.main_df
        current_total = int(df["結算總分"].iloc[-1])
        st.metric("目前帳戶總積分", f"{current_total:,}")
        curr_month = datetime.now().strftime("%Y-%m")
        m_df = df[(df['月份'] == curr_month) & (df['類型'] != "初始")]
        if not m_df.empty:
            m_profit = int(m_df['盈虧金額'].sum())
            st.metric(f"{curr_month} 總盈虧", f"{m_profit:,}", delta=m_profit)

    st.divider()
    if not st.session_state.main_df.empty:
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.main_df.to_excel(writer, sheet_name='詳細戰績紀錄', index=False)
            st.download_button(label="📥 下載完整 Excel 戰績表", data=output.getvalue(), file_name=f"足球管理報告_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
        except: pass

    if st.button("🚨 清空所有數據"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.main_df = pd.DataFrame(columns=["日期", "月份", "賽事項目", "類型", "金額", "盈虧金額", "結算總分"])
        st.rerun()

# --- 5. 主介面 ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 0px;'>⚽ 足球賽事走地一體化管理</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #B91C1C; font-weight: bold; margin-top: 5px;'>⚠️ 謹慎理財！信用至上！ ⚠️</h4>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.main_df.empty:
    st.info("⬅️ 請先在左側邊欄輸入您的「起始本金」以啟用系統。")
else:
    tab1, tab2, tab3 = st.tabs(["🚀 快速錄入", "📋 歷史明細", "📊 統計圖表"])

    with tab1:
        st.subheader("新增賽事紀錄")
        m_info = st.text_area("粘帖賽事資訊", height=80)
        c1, c2, c3, c4 = st.columns(4)
        c1.button("🔵 5,000", on_click=update_chip, args=(5000,), use_container_width=True)
        c2.button("🟢 10,000", on_click=update_chip, args=(10000,), use_container_width=True)
        c3.button("🟡 15,000", on_click=update_chip, args=(15000,), use_container_width=True)
        c4.button("🔴 20,000", on_click=update_chip, args=(20000,), use_container_width=True)

        if "bet_input" not in st.session_state: st.session_state.bet_input = 5000
        if "gain_input" not in st.session_state: st.session_state.gain_input = 5000

        col1, col2 = st.columns(2)
        with col1: bet_val = st.number_input("輸時金額", format="%d", key="bet_input")
        with col2: gain_val = st.number_input("獲利金額", format="%d", key="gain_input")
        
        c_win, c_loss = st.columns(2)
        balance = int(st.session_state.main_df["結算總分"].iloc[-1])
        if c_win.button("✅ 過關 (贏)", use_container_width=True, type="primary"):
            new_row = {"日期": datetime.now().strftime("%Y-%m-%d %H:%M"), "月份": datetime.now().strftime("%Y-%m"), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_val), "盈虧金額": int(gain_val), "結算總分": balance + int(gain_val)}
            st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.main_df); st.rerun()

        if c_loss.button("❌ 未過關 (輸)", use_container_width=True):
            new_row = {"日期": datetime.now().strftime("%Y-%m-%d %H:%M"), "月份": datetime.now().strftime("%Y-%m"), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_val), "盈虧金額": -int(bet_val), "結算總分": balance - int(bet_val)}
            st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.main_df); st.rerun()

    with tab2:
        st.subheader("全量數據明細")
        # 計算即時命中率
        df_calc = st.session_state.main_df.copy()
        hit_rates, win_count, total_games = [], 0, 0
        for i, row in df_calc.iterrows():
            if row['類型'] == '贏 (+)': win_count += 1; total_games += 1
            elif row['類型'] == '輸 (-)': total_games += 1
            hit_rates.append((win_count / total_games * 100) if total_games > 0 else 0)
        df_calc['即時命中率'] = hit_rates

        # 顯示表格 (排除月份)
        df_display = df_calc.drop(columns=["月份"]).iloc[::-1]
        
        def color_profit(val):
            try:
                v = int(val)
                return 'color: #28a745; font-weight: bold;' if v > 0 else 'color: #dc3545; font-weight: bold;' if v < 0 else ''
            except: return ''

        st.dataframe(df_display.style.map(color_profit, subset=['盈虧金額']).format({"金額": "{:,.0f}", "盈虧金額": "{:+,.0f}", "結算總分": "{:,.0f}", "即時命中率": "{:.1f}%"}), use_container_width=True)
        
        # --- 新增：刪除與修正操作區 ---
        st.divider()
        st.write("🗑️ **異動注單管理 (選擇上方序號刪除錯誤記錄)**")
        del_idx = st.selectbox("選擇要刪除的紀錄序號 (ID)", options=df_calc.index, format_func=lambda x: f"ID: {x} - {df_calc.loc[x, '賽事項目'][:20]}...")
        if st.button("🗑️ 確認刪除選定注單", type="secondary"):
            if df_calc.loc[del_idx, '類型'] == '初始':
                st.warning("初始本金紀錄建議不要刪除，如需更改請使用「清空所有數據」。")
            else:
                delete_record(del_idx)
                st.rerun()

    with tab3:
        st.subheader("視覺化戰績分析")
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("📈 資金增長走勢")
            st.line_chart(st.session_state.main_df["結算總分"])
        with col_b:
            st.write("⭕ 命中標準統計")
            pie_data = st.session_state.main_df[st.session_state.main_df['類型'].isin(['贏 (+)', '輸 (-)'])]
            if not pie_data.empty:
                win_n = len(pie_data[pie_data['類型']=='贏 (+)'])
                total_n = len(pie_data)
                st.metric("總投注場次", f"{total_n} 場")
                st.progress(win_n/total_n, text=f"命中率: {win_n/total_n*100:.1f}%")