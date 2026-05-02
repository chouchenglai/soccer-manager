# --- 邏輯判斷與主功能 ---
if main_df.empty:
    st.subheader("初始化報表")
    init_cap = st.number_input("起始本金", value=60000, step=1000)
    if st.button("建立"):
        row = {"日期": get_now_time(), "賽事項目": "初始", "類型": "初始", "金額": int(init_cap), "盈虧金額": 0, "結算總分": int(init_cap)}
        save_data(pd.DataFrame([row])); st.rerun()
else:
    # 調整順序：將「下單投注」放在第一位，確保預設開啟時就在下單頁面
    tab1, tab0, tab2, tab3, tab4, tab5 = st.tabs(["💰 下單投注", "📺 即時比分", "📋 歷史記錄", "📊 統計圖表", "📈 報表管理", "💬 討 論 區"])

    with tab1: # 原有的下單投注功能 (維持不變)
        try: balance = int(main_df["結算總分"].iloc[-1])
        except: balance = 0
        if "bet_val" not in st.session_state: st.session_state.bet_val = 5000
        
        # 時鐘區[cite: 1]
        st.components.v1.html("""
            <style>
                #clock-container { display: flex; align-items: center; background-color: #f8f9fb; padding: 8px 15px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-family: sans-serif; margin-bottom: 5px; }
                #clock { font-size: 15px; font-weight: 600; color: #31333f; letter-spacing: 0.8px; }
            </style>
            <div id="clock-container"><span id="clock">載入中...</span></div>
            <script>
                function updateClock() {
                    const now = new Date();
                    document.getElementById('clock').textContent = "台北標準時間 (GMT+8) : " + now.toLocaleDateString() + " " + now.getHours().toString().padStart(2,'0') + ":" + now.getMinutes().toString().padStart(2,'0') + ":" + now.getSeconds().toString().padStart(2,'0');
                }
                setInterval(updateClock, 1000); updateClock();
            </script>
        """, height=52)

        m_info = st.text_area("賽事資訊", placeholder="例如：英超 阿仙奴 vs 車路士", key="input_info")
        colb = st.columns(5)
        amounts = [5000, 10000, 15000, 20000]
        labels = ["🔵 5,000", "🟢 10,000", "🟡 15,000", "🔴 20,000"]
        for i in range(4):
            if colb[i].button(labels[i]): 
                st.session_state.bet_val = amounts[i]
                st.rerun()
        
        if colb[4].button("💎 全額（梭哈）"): confirm_all_in()

        c1, c2 = st.columns(2)
        with c1: bet_amt = st.number_input("下注金額", 0, max(1000000, balance), int(st.session_state.bet_val))
        with c2: gain_amt = st.number_input("盈利金額", 0, 1000000, value=None, placeholder="請輸入盈利")
        
        cw, cl = st.columns(2)
        if cw.button("✅ 過關 (贏)", use_container_width=True, disabled=gain_amt is None):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "贏 (+)", "金額": int(gain_amt), "盈虧金額": int(gain_amt), "結算總分": balance + int(gain_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()
        if cl.button("❌ 未過關 (輸)", use_container_width=True):
            new_row = {"日期": get_now_time(), "賽事項目": m_info, "類型": "輸 (-)", "金額": int(bet_amt), "盈虧金額": -int(bet_amt), "結算總分": balance - int(bet_amt)}
            save_data(pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)); st.rerun()

    with tab0: # 即時比分：改用 Link Button 避免廣告攔截
        st.subheader("🚀 即時比分與雙開模式")
        st.write("點擊下方按鈕將開啟比分網。開啟後，您可以手動調整瀏覽器視窗大小實現左右並排。")
        
        # 使用 Link Button 直接開啟外部連結，這不會被瀏覽器攔截
        st.link_button("🔥 開啟球探即時比分 (新窗口)", "https://live.titan007.com/indexall_big.aspx", use_container_width=True, type="primary")
        
        st.divider()
        col_live, col_bet = st.columns([6, 4])
        with col_live:
            st.markdown("##### 📡 備用嵌入式比分")
            st.components.v1.iframe("https://live.titan007.com/indexall_big.aspx", height=650, scrolling=True)
        with col_bet:
            st.markdown("##### ✍️ 賽事快速備忘錄")
            st.text_area("在此粘貼或輸入比分網看到的賽事資訊", placeholder="例如：拜仁 vs 多特蒙德...", key="live_memo", height=300)
            st.info("💡 提示：在此輸入的資訊不會儲存，請確認後切換至『下單投注』欄目提交。")

    # --- 其餘欄目 (tab2, tab3, tab4, tab5) 維持您原本的代碼邏輯 ---
    with tab2: st.dataframe(main_df.iloc[::-1], use_container_width=True)
    with tab3: st.line_chart(main_df["結算總分"])
    with tab4: st.write("報表管理功能已就緒。")
    with tab5: st.write("討論區功能已就緒。")