"""
Smart Investment Sentinel (智投) - 主应用
实时金融分析仪表板 (最终完美版：爱心词云 + 跨平台 + 清除记录)
"""
import streamlit as st
import pandas as pd
import sys
import os
import jieba
import jieba.analyse

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from modules.data_loader import get_realtime_data, get_news
from modules.nlp_analyzer import analyze_news_sentiment, analyze_sentiment
from modules.predictor import PricePredictor
from modules.visualizer import (
    create_candlestick_chart, 
    create_wordcloud, 
    create_sentiment_pie_chart,
    create_correlation_heatmap,
    create_prediction_chart
)
from utils.db_manager import DatabaseManager

st.set_page_config(page_title="Smart Investment Sentinel", page_icon="📈", layout="wide")

# CSS 优化
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .news-item { padding: 8px 0; border-bottom: 1px solid #eee; }
    .stAlert { margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

def main():
    try:
        db_manager = DatabaseManager()
    except Exception:
        db_manager = None
    
    # --- 侧边栏 ---
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        # 1. 股票分析区 (改回了你喜欢的 help 提示)
        ticker = st.text_input(
            "股票代码", 
            value="600519.SH", 
            help="请输入标准代码，例如：\n- 茅台: 600519.SH\n- 平安: 000001.SZ\n- 工商银行: 601398.SH"
        )
        analyze_button = st.button("🚀 开始股票分析", type="primary", use_container_width=True)
        
        st.divider()
        
        # 2. 自定义文本分析区
        st.header("🛠️ 自定义分析")
        with st.form("custom_analysis_form"):
            st.caption("独立分析一段新闻或研报的情感：")
            custom_text = st.text_area("输入文本", height=100, placeholder="在此粘贴文本内容...")
            uploaded_file = st.file_uploader("或上传TXT", type=['txt'])
            submitted = st.form_submit_button("🔍 分析这段文本", use_container_width=True)
        
        if submitted:
            target_text = ""
            if uploaded_file is not None:
                try: target_text = uploaded_file.read().decode("utf-8")
                except: st.error("文件读取失败")
            elif custom_text: target_text = custom_text
            
            if target_text:
                score = analyze_sentiment(target_text)
                label = "积极" if score > 0.2 else "消极" if score < -0.2 else "中性"
                keywords = jieba.analyse.extract_tags(target_text, topK=5)
                st.success("✅ 分析完成")
                with st.expander("查看详细结果", expanded=True):
                    st.metric("情感得分", f"{score:.3f}", label)
                    st.markdown("**关键热词:**")
                    st.code("  ".join(keywords) if keywords else "无关键词", language=None)
            else:
                st.warning("⚠️ 请先在上方输入框粘贴文字！")

    # --- 主界面 ---
    st.title("📈 Smart Investment Sentinel (智投)")
    st.divider()

    if analyze_button and ticker:
        try:
            with st.spinner(f"正在全网抓取 {ticker} 数据并进行AI分析..."):
                current_price, historical_data = get_realtime_data(ticker)
                news_headlines = get_news(ticker)
                sentiment_result = analyze_news_sentiment(news_headlines)
                sentiment_score = sentiment_result['sentiment_score']
                predictor = PricePredictor(ticker)
                prediction = predictor.predict_next(current_price, sentiment_score)
                if db_manager: db_manager.save_record(ticker, current_price, prediction, sentiment_score)

            # 1. 核心指标
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            change_pct = ((prediction - current_price) / current_price) * 100
            col_m1.metric("当前价格", f"¥{current_price:,.2f}")
            col_m2.metric("AI预测价格", f"¥{prediction:,.2f}", f"{change_pct:+.2f}%")
            col_m3.metric("市场情绪", sentiment_result['sentiment_label'], f"{sentiment_score:+.2f}")
            col_m4.metric("分析新闻数", f"{len(news_headlines)} 条")
            
            st.divider()

            # 2. 图表区域
            st.subheader("📊 股价走势与预测")
            st.plotly_chart(create_candlestick_chart(historical_data, current_price, prediction, ticker), use_container_width=True)

            col_c1, col_c2 = st.columns(2)
            with col_c1: st.plotly_chart(create_prediction_chart(historical_data, current_price, prediction), use_container_width=True)
            with col_c2: st.plotly_chart(create_sentiment_pie_chart(sentiment_result), use_container_width=True)

            col_c3, col_c4 = st.columns(2)
            with col_c3: st.plotly_chart(create_correlation_heatmap(historical_data), use_container_width=True)
            with col_c4: 
                # 词云图：传入爱心图片路径 (前提是文件存在)
                st.pyplot(create_wordcloud(news_headlines, "love.png"))

            # 3. 新闻列表
            st.divider()
            st.subheader("📰 实时财经资讯")
            with st.container():
                if news_headlines:
                    for i, news in enumerate(news_headlines, 1):
                        st.markdown(f"**{i}.** {news}")
                else:
                    st.info("暂无相关新闻")

        except Exception as e:
            st.error(f"分析错误: {str(e)}")
            st.info("提示: 确保输入如 600519.SH 的格式，且网络连接正常")

    else:
        st.info("👈 请在左侧侧边栏输入股票代码并点击'开始股票分析'")

    # --- 5. 历史分析记录 (带清空功能) ---
    st.divider()
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1:
        st.subheader("📜 历史分析记录")
    with col_h2:
        # 清空按钮
        if db_manager and st.button("🗑️ 清空所有记录", type="secondary"):
            if db_manager.clear_all_history():
                st.toast("历史记录已清空！", icon="✅")
                # 重新加载页面以刷新表格
                time.sleep(1)
                st.rerun()

    if db_manager:
        try:
            with st.expander("点击查看历史数据表", expanded=True):
                history_df = db_manager.fetch_history(limit=20)
                if not history_df.empty:
                    st.dataframe(
                        history_df,
                        column_config={
                            "timestamp": "分析时间",
                            "ticker": "股票代码",
                            "current_price": st.column_config.NumberColumn("当前价", format="¥%.2f"),
                            "predicted_price": st.column_config.NumberColumn("预测价", format="¥%.2f"),
                            "sentiment_score": st.column_config.NumberColumn("情感得分", format="%.3f"),
                            "change_percent": st.column_config.NumberColumn("预测涨幅", format="%.2f%%"),
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.caption("暂无历史记录，快去分析一个股票吧！")
        except Exception as e:
            st.warning(f"无法加载历史记录: {e}")

if __name__ == "__main__":
    import time # 局部导入用于刷新
    main()