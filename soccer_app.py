# --- 1. 定義標籤頁 (這行一定要靠最左邊，不能有空格) ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 快速錄入", "📜 歷史注單", "📈 數據統計", "⚙️ 系統設定"])

# --- 2. 全域組件區 (重要：這一段絕對不能縮排！必須靠最左邊) ---
# 放在這裡，不論切換到哪一頁，時間都會固定在最上面
import time
from datetime import datetime, timedelta, timezone

st.components.v1.html("""
    <style>
        #clock-container {
            display: flex; align-items: center; background-color: #f8f9fb;
            padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b;
            font-family: 'Segoe UI', 'Roboto', 'Monaco', monospace; margin-bottom: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        #clock { font-size: 15px; font-weight: 600; color: #31333f; letter-spacing: 0.8px; }
        .prefix { font-size: 14px; color: #666; margin-right: 12px; }
    </style>
    <div id="clock-container">
        <span class="prefix">台北標準時間 (GMT+8) :</span>
        <span id="clock">載入中...</span>
    </div>
    <audio id="winAudio" src="https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3" preload="auto"></audio>
    <audio id="loseAudio" src="https://assets.mixkit.co/active_storage/sfx/2511/2511-preview.mp3" preload="auto"></audio>
    <audio id="clickAudio" src="https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3" preload="auto"></audio>
    <audio id="alertAudio" src="https://assets.mixkit.co/active_storage/sfx/951/951-preview.mp3" preload="auto"></audio>
    <script>
        function updateClock() {
            const now = new Date();
            const y = now.getFullYear();
            const m = String(now.getMonth() + 1).padStart(2, '0');
            const d = String(now.getDate()).padStart(2, '0');
            const hh = String(now.getHours()).padStart(2, '0');
            const mm = String(now.getMinutes()).padStart(2, '0');
            const ss = String(now.getSeconds()).padStart(2, '0');
            const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
            document.getElementById('clock').textContent = `${y}/${m}/${d} (${weekDays[now.getDay()]}) ${hh}:${mm}:${ss}`;
        }
        setInterval(updateClock, 1000); updateClock();

        window.parent.playAppSound = function(type) {
            const audio = document.getElementById(type + 'Audio');
            if (audio) {
                audio.pause(); audio.currentTime = 0;
                audio.play().catch(e => console.log('音效播放受限'));
            }
        };
    </script>
""", height=65)

# --- 3. 進入 TAB1 內容 (從這裡開始才需要縮排) ---
with tab1:
    # A. 數據與時區預算
    try:
        balance = int(main_df["結算總分"].iloc[-1]) if not main_df.empty else 0
    except:
        balance = 0
    tz_taipei = timezone(timedelta(hours=8))
    
    if "bet_val" not in st.session_state:
        st.session_state.bet_val = 5000

    # B. 定義全額確認彈窗
    @st.dialog("⚠️ 全額下注確認")
    def confirm_all_in():
        st.warning(f"確定要將全部餘額 {balance:,} 元一次下注嗎？")
        c_conf1, c_conf2 = st.columns(2)
        if c_conf1.button("🔥 確定梭哈", type="primary", use_container_width=True):
            st.components.v1.html("<script>window.parent.playAppSound('click');</script>", height=0)
            st.session_state.bet_val = balance
            st.rerun()
        if c_conf2.button("取消", use_container_width=True):
            st.rerun()

    # C. 介面與功能按鈕
    st.subheader("📊 資金與統計中心")
    m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")

    colb = st.columns(5)
    btn_vals = [5000, 10000, 15000, 20000]
    btn_labels = ["🔵 5,000", "🟢 10,000", "🟡 15,000", "🔴 20,000"]
    for i in range(4):
        if colb[i].button(btn_labels[i], use_container_width=True):
            st.components.v1.html("<script>window.parent.playAppSound('click');</script>", height=0)
            st.session_state.bet_val = btn_vals[i]
            time.sleep(0.15)
            st.rerun()
    if colb[4].button("💎 全額", use_container_width=True):
        st.components.v1.html("<script>window.parent.playAppSound('alert');</script>", height=0)
        confirm_all_in()

    c1, c2 = st.columns(2)
    with c1:
        bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
    with c2:
        gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利金額")

    # D. 結算按鈕 (含音效)
    can_submit = balance > 0 and bet_amt > 0 and bet_amt <= balance
    cw, cl = st.columns(2)

    if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=not can_submit or gain_amt is None):
        st.components.v1.html("<script>window.parent.playAppSound('win');</script>", height=0)
        time.sleep(0.3)
        now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
        new_row = {"日期": now_taipei, "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)}
        save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
        st.rerun()

    if cl.button("❌ 未過關 (輸)", use_container_width=True, disabled=not can_submit):
        st.components.v1.html("<script>window.parent.playAppSound('lose');</script>", height=0)
        time.sleep(0.3)
        now_taipei = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M:%S")
        new_row = {"日期": now_taipei, "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)}
        save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
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
            val = st.number_input("金額", 0, 999999999, 30000)
            if st.button("補"):
                bal = int(main_df["結算總分"].iloc[-1])
                new = {
                    "日期":get_now_time(),
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
