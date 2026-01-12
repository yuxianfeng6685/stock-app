import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面设置 ---
st.set_page_config(page_title="美股雷达 v5.0", page_icon="📡", layout="wide")
st.title('📡 美股雷达 v5.0 (智能选股版)')

# --- 2. 侧边栏：超级选股器 ---
st.sidebar.header("1. 选择战场 (板块)")

# 定义热门板块的股票池
sectors = {
    "👑 科技七巨头 (Mag 7)": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "META"],
    "🤖 AI 与芯片": ["AMD", "AVGO", "TSM", "INTC", "QCOM", "MU", "SMCI", "ARM", "ASML"],
    "💰 加密货币概念": ["MSTR", "COIN", "MARA", "RIOT", "CLSK", "HOOD"],
    "🐼 热门中概股": ["BABA", "PDD", "JD", "BIDU", "NIO", "XPEV", "LI", "BILI"],
    "☁️ SaaS 与软件": ["PLTR", "CRM", "ADBE", "SNOW", "DDOG", "NET", "PANW", "CRWD"],
    "💊 减肥药与医疗": ["LLY", "NVO", "PFE", "MRK", "JNJ", "ABBV"]
}

# 下拉菜单选择板块
selected_sector = st.sidebar.selectbox("你想扫描哪个板块？", list(sectors.keys()))
tickers_to_scan = sectors[selected_sector]

st.sidebar.header("2. 猎杀条件 (过滤)")
show_only_oversold = st.sidebar.checkbox("只显示超卖 (RSI < 35)", value=False)
show_only_bullish = st.sidebar.checkbox("只显示强势 (价格 > 20日线)", value=False)

# --- 3. 核心计算 (带缓存) ---
@st.cache_data(ttl=1800) # 缓存30分钟，避免重复请求
def scan_market(ticker_list):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(ticker_list):
        status_text.text(f"正在雷达扫描: {ticker} ...")
        try:
            stock = yf.Ticker(ticker)
            # 只取最近3个月数据，速度最快
            hist = stock.history(period="3mo")
            
            if len(hist) > 20:
                # 基础数据
                curr_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                pct_change = ((curr_price - prev_price) / prev_price) * 100
                vol = hist['Volume'].iloc[-1] / 1000000 # 换算成百万
                
                # 技术指标
                ma20 = hist['Close'].rolling(20).mean().iloc[-1]
                
                # RSI 计算
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_val = rsi.iloc[-1]
                
                # 判断信号
                signal = "😐 震荡"
                score = 0
                if rsi_val < 30: 
                    signal = "💎 黄金坑 (超卖)"
                    score = 2 # 抄底分高
                elif rsi_val > 70: 
                    signal = "🔥 极度过热"
                    score = -1
                elif curr_price > ma20:
                    signal = "📈 趋势向上"
                    score = 1
                
                results.append({
                    "代码": ticker,
                    "现价": round(curr_price, 2),
                    "涨跌幅%": round(pct_change, 2),
                    "RSI": round(rsi_val, 1),
                    "状态": signal,
                    "MA20": ma20, # 用于后台过滤
                    "成交量(M)": round(vol, 1)
                })
        except:
            pass
        progress_bar.progress((i + 1) / len(ticker_list))
        
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(results)

# --- 4. 执行逻辑 ---
if st.button("📡 启动雷达扫描", type="primary"):
    df = scan_market(tickers_to_scan)
    
    if not df.empty:
        # --- 智能过滤逻辑 ---
        final_df = df.copy()
        
        if show_only_oversold:
            final_df = final_df[final_df['RSI'] < 35]
            st.warning("已开启过滤：只显示 RSI < 35 的超卖股票")
            
        if show_only_bullish:
            final_df = final_df[final_df['现价'] > final_df['MA20']]
            st.success("已开启过滤：只显示站上 20日均线 的强势股")

        # --- 展示结果 ---
        if final_df.empty:
            st.info("扫描完成，但没有股票符合你当前的过滤条件。试试取消勾选侧边栏的过滤框。")
        else:
            # 颜色美化
            def highlight_row(val):
                color = ''
                if '黄金坑' in str(val): color = 'background-color: #d4edda; color: green'
                elif '过热' in str(val): color = 'background-color: #f8d7da; color: red'
                return color

            st.write(f"### 🎯 扫描结果 ({len(final_df)} 只)")
            
            # 显示表格
            st.dataframe(
                final_df.drop(columns=['MA20']).sort_values(by="涨跌幅%", ascending=False).style.applymap(highlight_row, subset=['状态']),
                use_container_width=True,
                hide_index=True
            )
            
            # 简单的气泡图 (X轴=RSI, Y轴=涨跌幅)
            st.write("### 📊 市场情绪分布图")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=final_df['RSI'],
                y=final_df['涨跌幅%'],
                mode='markers+text',
                text=final_df['代码'],
                textposition="top center",
                marker=dict(size=12, color=final_df['RSI'], colorscale='RdYlGn_r', showscale=True)
            ))
            fig.add_vline(x=30, line_dash="dash", line_color="green", annotation_text="超卖区")
            fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="超买区")
            fig.update_layout(xaxis_title="RSI (强弱指标)", yaxis_title="今日涨跌幅 (%)", height=500)
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error("无法获取数据，请稍后重试。")

else:
    st.info("👈 请在左侧选择一个板块，然后点击上面的按钮开始扫描！")
