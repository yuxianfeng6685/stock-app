import streamlit as st
import yfinance as yf
import pandas as pd

# --- 页面设置 ---
st.set_page_config(page_title="美股猎手 v2.0", page_icon="⚡", layout="wide")
st.title('⚡ 美股猎手 v2.0 (Trend Hunter)')
st.markdown("不用一个个输代码，直接点击下方按钮扫描核心资产！")

# --- 侧边栏：控制台 ---
st.sidebar.header("🎯 扫描目标设置")

# 预设的纳指100成分股 (这里列出了主要的科技成长股)
nasdaq_100 = "NVDA MSFT AAPL AMZN META GOOGL TSLA AVGO COST PEP CSCO TMUS AMD INTC QCOM TXN AMGN HON AMAT SBUX GILD INTU MDLZ ADP ISRG BKNG VRTX REGN ADI KLAC PANW SNPS LRCX CDNS CHTR MELI MAR NXPI ORLY CTAS FTNT PCAR DXCM KDP PAYX MCHP AEP LULU ADSK IDXX AZN ROST MRVL ODFL MNST CSX FAST EXC BIIB CCEP CTES DLTR DXCM EA EBAY ENPH EXC EXPD FAST FISV FTNT GFS GILD GILD GOOG HON IDXX ILMN INTU ISRG JD KDP KHC KLAC LCID LRCX LULU MAR MCHP MDLZ MELI META MNST MRVL MSFT MU NFLX NVDA NXPI ODFL ORLY PANW PAYX PCAR PDD PEP PYPL QCOM REGN RIVN ROST SBUX SGEN SIRI SNPS SPLK TEAM TMUS TSLA TXN VRSK VRTX WBA WBD WDAY XCEL ZM"

# 按钮：快速填充
if st.sidebar.button("⚡ 加载“纳指100”成分股"):
    st.session_state.tickers = nasdaq_100

# 获取用户输入 (如果没有点击按钮，就用默认的)
if 'tickers' not in st.session_state:
    st.session_state.tickers = "NVDA TSLA AMD PLTR MSTR COIN MARA SMCI"

tickers_input = st.sidebar.text_area("股票池 (可手动修改)", st.session_state.tickers, height=150)
tickers_list = list(set(tickers_input.upper().split())) # 去重+转大写

# --- 核心分析逻辑 ---
def analyze_stock(ticker):
    try:
        # 获取数据（只取最近3个月以加快速度）
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        if len(hist) < 50: return None

        # 计算指标
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        ma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        vol = hist['Volume'].iloc[-1]
        avg_vol = hist['Volume'].rolling(window=20).mean().iloc[-1]
        
        # 涨跌幅
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # 判断状态
        trend = "🥶 弱势"
        score = 0
        
        if current_price > ma20: 
            score += 1
        if ma20 > ma50: 
            score += 1
        if vol > avg_vol * 1.5: # 放量
            score += 1
            
        if score == 3: trend = "🚀 强势爆发"
        elif score == 2: trend = "🔥 上升趋势"
        elif score == 1: trend = "👀 观察"
            
        return {
            "代码": ticker,
            "现价": current_price,
            "涨跌幅%": round(change_pct, 2),
            "状态": trend,
            "成交量放大": "✅ 是" if vol > avg_vol * 1.2 else "平稳"
        }
    except:
        return None

# --- 执行扫描 ---
if st.button('🚀 开始全量扫描', type="primary"):
    st.write(f"正在分析 {len(tickers_list)} 只股票，可能会花 1-2 分钟，请耐心等待...")
    my_bar = st.progress(0)
    results = []
    
    # 循环抓取
    for i, ticker in enumerate(tickers_list):
        data = analyze_stock(ticker)
        if data:
            results.append(data)
        # 更新进度条
        my_bar.progress((i + 1) / len(tickers_list))
        
    # 展示结果
    if results:
        df = pd.DataFrame(results)
        
        # 样式美化：高亮强势股
        def color_trend(val):
            color = 'black'
            if '🚀' in val: color = 'green'
            elif '🔥' in val: color = 'orange'
            elif '🥶' in val: color = 'gray'
            return f'color: {color}; font-weight: bold'

        st.success("扫描完成！")
        st.dataframe(
            df.sort_values(by="涨跌幅%", ascending=False).style.applymap(color_trend, subset=['状态']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("没有获取到数据，请检查网络或股票代码。")
