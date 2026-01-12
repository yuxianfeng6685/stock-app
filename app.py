import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置 ---
st.set_page_config(page_title="美股全能操盘手 v4.0", page_icon="💻", layout="wide")
st.title('💻 美股全能操盘手 v4.0 (Pro Dashboard)')

# --- 2. 侧边栏：股票选择 ---
st.sidebar.header("🔍 股票选择")

# 预设股票池
default_tickers = ["NVDA", "TSLA", "AMD", "AAPL", "MSFT", "META", "AMZN", "GOOGL", "COIN", "MSTR", "MARA", "SMCI", "PLTR"]
ticker = st.sidebar.selectbox("选择你要分析的股票", default_tickers)

# 时间范围
period = st.sidebar.selectbox("时间范围", ["3mo", "6mo", "1y", "ytd"], index=1)

# --- 3. 获取数据与计算指标 ---
def get_data(ticker, period):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    # 简单的移动平均线
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # 布林带 (Bollinger Bands)
    df['std'] = df['Close'].rolling(window=20).std()
    df['Upper_BB'] = df['MA20'] + (2 * df['std'])
    df['Lower_BB'] = df['MA20'] - (2 * df['std'])
    
    # MACD 指标
    short_ema = df['Close'].ewm(span=12, adjust=False).mean()
    long_ema = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # RSI 指标
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df, stock.info

try:
    df, info = get_data(ticker, period)
    current_price = df['Close'].iloc[-1]
    last_close = df['Close'].iloc[-2]
    change = current_price - last_close
    pct_change = (change / last_close) * 100

    # --- 4. 顶部核心数据栏 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("当前价格", f"${current_price:.2f}", f"{pct_change:.2f}%")
    col2.metric("RSI (强弱指标)", f"{df['RSI'].iloc[-1]:.1f}", "超买>70 | 超卖<30")
    
    # 计算技术评分 (0-10分)
    score = 0
    if current_price > df['MA20'].iloc[-1]: score += 2
    if df['MA20'].iloc[-1] > df['MA50'].iloc[-1]: score += 2
    if df['RSI'].iloc[-1] > 50: score += 2
    if df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1]: score += 2
    if current_price > df['Upper_BB'].iloc[-1]: score += 2 # 突破布林上轨
    
    status_color = "red" if score < 4 else "green" if score > 6 else "orange"
    status_text = "🐻 空头主导" if score < 4 else "🐮 多头强势" if score > 6 else "⚖️ 震荡整理"
    
    col3.metric("技术评分 (0-10)", f"{score} 分", status_text)
    col4.metric("成交量", f"{df['Volume'].iloc[-1]/1000000:.1f} M")

    # --- 5. 绘制专业 K 线图 (Plotly) ---
    st.subheader(f"📈 {ticker} 专业走势图")
    
    # 创建子图：上面是K线，下面是MACD
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # 1. K线图
    fig.add_trace(go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name='K线'), row=1, col=1)

    # 2. 均线 MA20
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
    
    # 3. 布林带
    fig.add_trace(go.Scatter(x=df.index, y=df['Upper_BB'], line=dict(color='gray', width=1, dash='dot'), name='布林上轨'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Lower_BB'], line=dict(color='gray', width=1, dash='dot'), name='布林下轨'), row=1, col=1)

    # 4. MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], line=dict(color='orange', width=1), name='Signal'), row=2, col=1)
    
    # 颜色条 (Histogram)
    colors = ['green' if val >= 0 else 'red' for val in (df['MACD'] - df['Signal_Line'])]
    fig.add_trace(go.Bar(x=df.index, y=(df['MACD'] - df['Signal_Line']), marker_color=colors, name='动能柱'), row=2, col=1)

    # 布局美化
    fig.update_layout(height=600, xaxis_rangeslider_visible=False, title_text=f"{ticker} 详细技术分析")
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. AI 极简分析结论 ---
    st.info(f"""
    🤖 **AI 自动复盘：**
    * **趋势判断：** 当前价格在 20日均线 {'之上 🔼' if current_price > df['MA20'].iloc[-1] else '之下 🔽'}。
    * **动能指标：** RSI 为 {df['RSI'].iloc[-1]:.1f}，MACD {'金叉 (看涨)' if df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1] else '死叉 (看跌)'}。
    * **操作建议：** {"🔥 **多头排列，适合持股待涨**" if score >= 8 else "⚠️ **趋势走弱，注意风险**" if score <= 3 else "👀 **震荡行情，建议观望**"}
    """)

except Exception as e:
    st.error(f"无法获取数据，请检查代码是否正确或稍后再试。错误信息: {e}")
