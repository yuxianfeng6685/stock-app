import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="美股选股器", page_icon="📈")
st.title('🚀 我的美股动量选股器')

# 侧边栏
default_tickers = "NVDA TSLA AMD PLTR MSTR COIN AAPL MSFT GOOGL AMZN"
tickers_input = st.sidebar.text_area("输入股票代码 (空格隔开)", default_tickers)
tickers_list = list(set(tickers_input.upper().split()))

# 核心功能
if st.button('开始扫描', type="primary"):
    st.write("正在分析数据...")
    results = []
    for ticker in tickers_list:
        try:
            hist = yf.Ticker(ticker).history(period="6mo")
            if len(hist) > 50:
                price = hist['Close'].iloc[-1]
                ma20 = hist['Close'].rolling(20).mean().iloc[-1]
                ma50 = hist['Close'].rolling(50).mean().iloc[-1]
                
                status = "🥶 弱势"
                if price > ma20 and ma20 > ma50:
                    status = "🔥 强势爆发"
                elif price > ma20:
                    status = "🙂 企稳"
                
                results.append({"代码": ticker, "现价": round(price, 2), "状态": status})
        except: pass
    
    if results:
        st.dataframe(pd.DataFrame(results).style.applymap(lambda v: 'background-color: #d1e7dd' if '强势' in v else '', subset=['状态']))





