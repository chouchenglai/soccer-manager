import streamlit as st
import base64

# ====================================
# 頁面設定
# ====================================

st.set_page_config(
    page_title="CCL-Live 體育賽事管理系統",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================================
# 隱藏左側導航
# ====================================

st.markdown("""
<style>

/* 隱藏左側導航 */

[data-testid="stSidebar"] {
    display: none;
}

[data-testid="collapsedControl"] {
    display: none;
}

section[data-testid="stSidebar"] {
    display: none;
}

[data-testid="stSidebarNav"] {
    display: none;
}

/* 主背景 */

.main {
    background: #f4f7fb;
}

/* Hero */

.hero-box{
    background: linear-gradient(135deg,#0f172a,#2563eb);
    border-radius: 35px;
    padding: 60px;
    margin-top: 20px;
    margin-bottom: 50px;
    text-align: center;
    box-shadow: 0 10px 35px rgba(0,0,0,0.18);
}

/* Logo */

.hero-logo{
    width: 100%;
    max-width: 1100px;
    display: block;
    margin: auto;
    margin-bottom: 35px;
}

/* 副標 */

.hero-sub{
    font-size: 36px;
    font-weight: 800;
    color: white;
    margin-bottom: 18px;
}

/* 說明 */

.hero-desc{
    font-size: 22px;
    color: #dbeafe;
    letter-spacing: 2px;
}

/* 標題 */

.section-title{
    font-size: 42px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 30px;
}

/* 卡片 */

.card{
    background: white;
    border-radius: 24px;
    padding: 35px;
    min-height: 230px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    transition: 0.3s;
    margin-bottom: 25px;
}

.card:hover{
    transform: translateY(-8px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

.card-title{
    font-size: 28px;
    font-weight: 800;
    margin-bottom: 20px;
    color: #111827;
}

.card-text{
    font-size: 18px;
    color: #4b5563;
    line-height: 1.9;
}

/* Footer */

.footer{
    text-align:center;
    color:#6b7280;
    margin-top:60px;
    margin-bottom:20px;
    font-size:16px;
}

</style>
""", unsafe_allow_html=True)

# ====================================
# 讀取 LOGO
# ====================================

def get_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_base64 = get_base64("ccl_logo_header.jpg")

# ====================================
# Hero
# ====================================

st.markdown(f"""
<div class="hero-box">

<img class="hero-logo"
src="data:image/jpg;base64,{logo_base64}">

<div class="hero-sub">
體育賽事模擬交易與分析平臺

<a href="/live" style="color: white; text-decoration: none;">⚽ 即時比分</a> ｜ 
<a href="/history" style="color: white; text-decoration: none;">📊 歷史數據</a> ｜ 
<a href="/trade" style="color: white; text-decoration: none;">📈 模擬倉管理</a> ｜ 
<a href="/chat" style="color: white; text-decoration: none;">💬 交流討論</a>

</div>

</div>
""", unsafe_allow_html=True)
  
# ====================================
# 平臺功能
# ====================================

st.markdown("""
<div class="section-title">
🔥 平臺核心功能
</div>
""", unsafe_allow_html=True)

# ====================================
# 第一列
# ====================================

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown("""
    <div class="card">
    <div class="card-title">💰 模擬交易</div>
    <div class="card-text">
    自動結算盈虧<br>
    即時同步總資金變化
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("查看即時比分", key="live"):
            st.switch_page("pages/live.py")

with col2:

    st.markdown("""
    <div class="card">
    <div class="card-title">📈 統計圖表</div>
    <div class="card-text">
    自動生成資金曲線圖<br>
    分析長期操作表現
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("查看統計圖表", key="chart"):
        st.switch_page("pages/ccl-live.py")

with col3:

    st.markdown("""
    <div class="card">
    <div class="card-title">💬 討論交流</div>
    <div class="card-text">
    即時討論熱門賽事<br>
    現場即分享報明牌
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("進入討論區", key="chat"):
        st.switch_page("pages/ccl-live.py")

# ====================================
# 第二列
# ====================================

col4, col5, col6 = st.columns(3)

with col4:

    st.markdown("""
    <div class="card">
    <div class="card-title">📋 歷史記錄</div>
    <div class="card-text">
    完整保存歷史數據<br>
    支援後續分析回測
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("查看歷史記錄", key="history"):
        st.switch_page("pages/ccl-live.py")

with col5:

    st.markdown("""
    <div class="card">
    <div class="card-title">⚽ 即時比分</div>
    <div class="card-text">
    同步全球體育賽事<br>
    即時查看最新動態
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("查看即時比分", key="live2"):
        st.switch_page("pages/ccl-live.py")

with col6:

    st.markdown("""
    <div class="card">
    <div class="card-title">🔥 最新公告</div>
    <div class="card-text">
    現場即時同步發佈<br>
    本站報明牌資訊欄
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("最新公告", key="ai"):
        st.switch_page("pages/ccl-live.py")

# ====================================
# 底部
# ====================================

st.markdown("""
<div class="footer">

CCL-Live 體育賽事管理系統 © 2026

<br><br>

www.ccl-live.tw

</div>
""", unsafe_allow_html=True)
