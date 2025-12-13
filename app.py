"""
Smart Investment Sentinel (智投) - 主应用
一个实时金融分析仪表板
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from modules.data_loader import get_realtime_data, get_news
from modules.nlp_analyzer import analyze_sentiment
from modules.predictor import PricePredictor
from modules.visualizer import create_candlestick_chart, create_wordcloud
from utils.db_manager import DatabaseManager

def main():
    st.set_page_config(
        page_title="Smart Investment Sentinel (智投)",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化数据库
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    # 页面标题
    st.title("Smart Investment Sentinel (智投)")
    st.markdown("### 实时金融分析仪表板")
    
    # 侧边栏
    with st.sidebar:
        st.header("📊 分析配置")
        
        # 股票代码输入
        ticker = st.text_input("股票代码", value="AAPL", help="输入股票代码，如AAPL, GOOGL, MSFT等")
        
        # 文件上传
        st.subheader("📁 上传分析报告")
        uploaded_file = st.file_uploader("上传文本文件用于情感分析", type=['txt'])
        
        # 开始分析按钮
        analyze_button = st.button("🚀 开始分析", type="primary")
    
    # 主面板
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if analyze_button and ticker:
            try:
                with st.spinner("正在获取数据..."):
                    # 1. 获取股票数据
                    current_price, historical_data = get_realtime_data(ticker)
                    
                    # 2. 获取新闻数据
                    news_headlines = get_news(ticker)
                    
                    # 3. 情感分析
                    sentiment_score = analyze_sentiment(news_headlines)
                    
                    # 4. 机器学习预测
                    predictor = PricePredictor(ticker)
                    prediction = predictor.predict_next(current_price, sentiment_score)
                    
                    # 5. 保存到数据库
                    db_manager.save_record(
                        ticker=ticker,
                        price=current_price,
                        prediction=prediction,
                        sentiment=sentiment_score
                    )
                
                # 显示当前价格和情感得分
                st.metric("当前价格", f"${current_price:.2f}")
                st.metric("情感得分", f"{sentiment_score:.3f}", delta=f"{sentiment_score:.1%}")
                st.metric("预测价格", f"${prediction:.2f}", delta=f"{(prediction-current_price)/current_price:.1%}")
                
                # 显示新闻
                st.subheader("📰 最新新闻")
                for i, headline in enumerate(news_headlines, 1):
                    st.write(f"{i}. {headline}")
                
            except Exception as e:
                st.error(f"分析过程中出现错误: {str(e)}")
        
        # 显示历史分析
        st.subheader("📈 分析历史")
        try:
            history_df = db_manager.fetch_history()
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("暂无历史分析记录")
        except Exception as e:
            st.error(f"获取历史记录失败: {str(e)}")
    
    with col2:
        # 如果有数据则显示图表
        if analyze_button and ticker:
            try:
                with st.spinner("生成图表..."):
                    # 创建K线图
                    fig = create_candlestick_chart(historical_data, current_price, prediction)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 创建词云图
                    wordcloud_fig = create_wordcloud(news_headlines)
                    st.pyplot(wordcloud_fig, clear_figure=True)
                    
            except Exception as e:
                st.error(f"生成图表失败: {str(e)}")
    
    # 页面底部信息
    st.markdown("---")
    st.markdown(
        "**Smart Investment Sentinel (智投)** | "
        "基于 Streamlit + yfinance + TextBlob + Scikit-learn 构建 | "
        f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

if __name__ == "__main__":
    main()
