import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="CCL-Live 會員升級中心",
    layout="wide"
)

# =========================================================
# 台北時區
# =========================================================

taipei_tz = ZoneInfo("Asia/Taipei")
now = datetime.now(taipei_tz)

# =========================================================
# 優惠截止時間
# =========================================================

discount_end = datetime(
    2026, 7, 31, 23, 59, 59,
    tzinfo=taipei_tz
)

# =========================================================
# 倒數功能（最後10天才顯示）
# =========================================================

remaining = discount_end - now

countdown_html = ""

if remaining.days <= 10 and remaining.total_seconds() > 0:

    total_seconds = int(remaining.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    countdown_html = f"""
    <div style="
        margin-top:30px;
        background:linear-gradient(90deg,#ff9800,#ff5722);
        padding:20px;
        border-radius:20px;
        text-align:center;
        color:white;
        font-weight:900;
        box-shadow:0 8px 25px rgba(0,0,0,0.25);
    ">

    <div style="
        font-size:1.5rem;
        margin-bottom:10px;
    ">
    ⏰ 限時優惠倒數
    </div>

    <div style="
        font-size:2rem;
        letter-spacing:2px;
    ">
    {days} 天 {hours} 小時 {minutes} 分 {seconds} 秒
    </div>

    </div>
    """

# =========================================================
# CSS 樣式
# =========================================================

st.markdown("""

<style>

html, body, [class*="css"]  {
    font-family: "Microsoft JhengHei", sans-serif;
}

.block-container{
    padding-top:2rem;
    padding-bottom:3rem;
}

.price-card{
    background:white;
    border-radius:25px;
    padding:35px;
    box-shadow:0 10px 35px rgba(0,0,0,0.12);
    transition:0.3s;
    border:2px solid transparent;
    height:100%;
}

.price-card:hover{
    transform:translateY(-8px);
    border:2px solid #1f6bff;
}

.old-price{
    color:#888;
    text-decoration:line-through;
    font-size:1rem;
}

.new-price{
    color:#e53935;
    font-size:2.6rem;
    font-weight:800;
    margin-top:10px;
    letter-spacing:1px;
    line-height:1.2;
}

.save-tag{
    background:#ffeb3b;
    color:#000;
    padding:5px 12px;
    border-radius:999px;
    font-size:0.9rem;
    font-weight:900;
}

.buy-btn{
    width:100%;
    padding:14px;
    border-radius:15px;
    background:linear-gradient(90deg,#1565c0,#1e88e5);
    color:white !important;
    font-size:1.05rem;
    font-weight:900;
    margin-top:18px;
    cursor:pointer;
    display:block;
    text-align:center;
}

.buy-btn:hover{
    opacity:0.92;
}

</style>

""", unsafe_allow_html=True)

# ================================
# 頁面設定
# ================================

st.set_page_config(
    page_title="CCL-Live VIP",
    layout="wide"
)

# ================================
# CSS
# ================================

st.markdown("""
<style>

body{
    background:#f5f7fb;
}

.vip-header{
    background:linear-gradient(135deg,#0d2c75,#2450c4);
    border-radius:35px;
    padding:70px 50px;
    text-align:center;
    color:white;
    position:relative;
    overflow:hidden;
    box-shadow:0 15px 40px rgba(0,0,0,0.25);
}

.vip-header::after{
    content:'';
    position:absolute;
    width:320px;
    height:320px;
    background:rgba(255,255,255,0.06);
    border-radius:50%;
    top:-120px;
    right:-80px;
}

.vip-title{
    font-size:3.3rem;
    font-weight:900;
    margin-bottom:30px;
}

.vip-subtitle{
    font-size:1.3rem;
    margin-top:20px;
    margin-bottom:25px;
}

.vip-feature-box{
    background:rgba(255,255,255,0.08);
    border-radius:30px;
    padding:45px;
    margin-top:55px;
}

.vip-feature-title{
    color:#ffe95c;
    font-size:2rem;
    font-weight:900;
    margin-bottom:30px;
}

.feature-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:20px;
    margin-top:30px;
}

.feature-item{
    font-size:1.35rem;
    font-weight:700;
    text-align:left;
}

.plan-card{
    background:white;
    border-radius:28px;
    padding:34px;
    box-shadow:0 10px 28px rgba(0,0,0,0.10);
    min-height:640px;
    transition:0.25s;
}

.plan-card:hover{
    transform:translateY(-8px);
    box-shadow:0 18px 40px rgba(0,0,0,0.18);
}

.plan-title{
    font-size:2.2rem;
    font-weight:800;
    color:#1a2a4d;
    line-height:1.35;
    letter-spacing:1px;
}

.old-price{
    color:#888;
    font-size:1.4rem;
    text-decoration:line-through;
    margin-top:20px;
}

.new-price{
    color:#e53935;
    font-size:2.3rem;
    font-weight:900;
}

.save-badge{
    background:#ffe32b;
    display:inline-block;
    padding:12px 24px;
    border-radius:999px;
    font-weight:900;
    margin-top:18px;
    color:black;
}

.plan-features{
    margin-top:35px;
    font-size:1.3rem;
    line-height:2.1;
}

.upgrade-btn{
    background:#1976d2;
    color:white;
    padding:18px 36px;
    border-radius:18px;
    font-size:1.35rem;
    font-weight:900;
    text-align:center;
    margin-top:35px;
}

hr{
    margin-top:30px;
    margin-bottom:30px;
}

</style>
""", unsafe_allow_html=True)

# ================================
# 頂部
# ================================

st.markdown(f"""
<div class="vip-header">

<div class="vip-title">
⚽ CCL-Live 帳號升級中心
</div>

<div class="vip-subtitle">
🎊 為慶祝本網站成立，特別推出限時優惠方案
</div>

{countdown_html}

<div style="
margin-top:28px;
font-size:1.2rem;
font-weight:700;
color:white;
">
優惠期間｜115年6月1日 ～ 115年7月31日
</div>

<div class="vip-feature-box">

<div class="vip-feature-title">
升級會員後，即可享有
</div>

<div class="feature-grid">

<div class="feature-item">
✔ 雲端保存報表數據
</div>

<div class="feature-item">
✔ 長期歷史分析功能
</div>

<div class="feature-item">
✔ 多帳本管理系統
</div>

<div class="feature-item">
✔ 會員專屬統計工具
</div>

<div class="feature-item">
✔ VIP 專區功能優先使用權
</div>

<div class="feature-item">
✔ 未來功能永久更新支援
</div>

</div>
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# =========================================================
# 會員方案
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

# =========================================================
# 月費
# =========================================================

with col1:

    st.markdown("""

    <div class="price-card">

    <h2>月費制</h2>

    <div class="old-price">
    原價 NT$ 399 / 1個月
    </div>

    <div class="new-price">
    NT$ 299
    </div>

    <div class="save-tag">
    現省 NT$100
    </div>

    <hr>

    ✔ 雲端保存報表  
    ✔ 模擬倉永久保存  
    ✔ 會員統計功能  
    
    <a href="https://www.paypal.com/ncp/payment/FJG3KFN3T7JRG"
   target="_blank"
   style="text-decoration:none;">

    <button class="buy-btn">
    立即升級
    </button>

</a>

    </div>

    """, unsafe_allow_html=True)

# =========================================================
# 季費
# =========================================================

with col2:

    st.markdown("""

    <div class="price-card">

    <h2>季費制</h2>

    <div class="old-price">
    原價 NT$ 897 / 3個月
    </div>

    <div class="new-price">
    NT$ 597
    </div>

    <div class="save-tag">
    現省 NT$300
    </div>

    <hr>

    ✔ 最熱門方案  
    ✔ 長期分析功能  
    ✔ 專屬會員工具  

    <button class="buy-btn">
    立即升級
    </button>

    </div>

    """, unsafe_allow_html=True)

# =========================================================
# 年費
# =========================================================

with col3:

    st.markdown("""

    <div class="price-card">

    <h2>年費制</h2>

    <div class="old-price">
    原價 NT$ 3588/年
    </div>

    <div class="new-price">
    NT$ 1188
    </div>

    <div class="save-tag">
    超值優惠
    </div>

    <hr>

    ✔ 高 CP 值方案  
    ✔ 完整 VIP 功能  
    ✔ 優先體驗更新  

    <button class="buy-btn">
    立即升級
    </button>

    </div>

    """, unsafe_allow_html=True)

# =========================================================
# 終身會員
# =========================================================

with col4:

    st.markdown("""

    <div class="price-card">

    <h2>終身制</h2>

    <div class="old-price">
    原價 NT$ 6999
    </div>

    <div class="new-price">
    NT$ 2500
    </div>

    <div class="save-tag">
    永久使用
    </div>

    <hr>

    ✔ 永久免續費  
    ✔ 所有 VIP 功能  
    ✔ 更新永久支援  

    <button class="buy-btn">
    永久升級
    </button>

    </div>

    """, unsafe_allow_html=True)

# =========================================================
# 底部資訊
# =========================================================

st.markdown("<br><br>", unsafe_allow_html=True)

st.info("💡 PayPal Pte. Ltd. 提供付款功能，現在架構中，即將推出新服務，敬請關注期待！。")

st.markdown("""

<div style="
text-align:center;
color:#777;
padding:30px;
font-size:0.95rem;
">

Copyright © 2026 CCL-Live 體育賽事管理系統

</div>

""", unsafe_allow_html=True)