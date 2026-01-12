import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置 ---
st.set_page_config(page_title="美股全能操盘手 v4.1", page_icon="🛡️", layout="wide")
st.title('🛡️ 美股全能操盘手 v4.1 (防封版)')

# --- 2. 侧边栏 ---
st.sidebar.header("🔍 股票选择")
default_tickers = ["NVDA", "TSLA", "AMD", "AAPL", "MSFT", "META", "AMZN", "GOOGL", "COIN", "MSTR", "SMCI", "PLTR"]
ticker = st.sidebar.selectbox("选择股票", default_tickers)
period = st.sidebar.selectbox("时间范围", ["3mo", "6mo", "1y", "ytd"], index=1)

# --- 3. 核心升级：增加缓存功能 ---
# @st.cache_data 意味着：如果下载过这个股票的数据，就直接用内存里的，别去骚扰雅虎
@st.cache_data(ttl=3600) 
def get_data_cached(ticker, period):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    if len(df) == 0:
        return pd.DataFrame(), None # 防止空数据报错

    # 计算指标
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # 布林带
    df['std'] = df['Close'].rolling(window=20).std()
    df['Upper_BB'] = df['MA20'] + (2 * df['std'])
    df['Lower_BB'] = df['MA20'] - (2 * df['std'])
    
    # MACD
    short_ema = df['Close'].ewm(span=12, adjust=False).mean()
    long_ema = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df, stock.info

# --- 4. 展示逻辑 ---
try:
    df, info = get_data_cached(ticker, period)
    
    if df.empty:
        st.warning("⚠️ 暂时无法获取数据，请稍后刷新重试（可能是雅虎接口繁忙）。")
    else:
        current_price = df['Close'].iloc[-1]
        last_close = df['Close'].iloc[-2]
        change = current_price - last_close
        pct_change = (change / last_close) * 100

        # 数据看板
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("当前价格", f"${current_price:.2f}", f"{pct_change:.2f}%")
        col2.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}", "强弱指标")
        
        # 评分系统
        score = 0
        if current_price > df['MA20'].iloc[-1]: score += 2
        if df['MA20'].iloc[-1] > df['MA50'].iloc[-1]: score += 2
        if df['RSI'].iloc[-1] > 50: score += 2
        if df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1]: score += 2
        if current_price > df['Upper_BB'].iloc[-1]: score += 2
        
        status_text = "🐻 空头" if score < 4 else "🐮 多头" if score > 6 else "⚖️ 震荡"
        col3.metric("技术评分", f"{score}/10", status_text)
        col4.metric("成交量", f"{df['Volume'].iloc[-1]/1000000:.1f} M")

        # 画图
        st.subheader(f"📈 {ticker} 走势图")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        
        # K线
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='K线'), row=1, col=1)
        # 均线
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
        # 布林带
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper_BB'], line=dict(color='gray', width=1, dash='dot'), name='上轨'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower_BB'], line=dict(color='gray', width=1, dash='dot'), name='下轨'), row=1, col=1)
        # MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], line=dict(color='orange', width=1), name='Signal'), row=2, col=1)
        colors = ['green' if val >= 0 else 'red' for val in (df['MACD'] - df['Signal_Line'])]
        fig.add_trace(go.Bar(x=df.index, y=(df['MACD'] - df['Signal_Line']), marker_color=colors, name='动能'), row=2, col=1)
        
        fig.update_layout(height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"出了点小问题：{e}")
    st.info("💡 提示：如果显示 Rate limited，请等待 15 分钟再刷新。")
