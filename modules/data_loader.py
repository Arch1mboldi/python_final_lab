"""
数据加载模块
获取股票实时数据和新闻数据
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def get_realtime_data(ticker):
    """
    获取股票实时数据和历史数据
    
    Args:
        ticker (str): 股票代码
    
    Returns:
        tuple: (当前价格, 历史数据DataFrame)
    """
    try:
        # 创建股票对象
        stock = yf.Ticker(ticker)
        
        # 获取最近1个月的历史数据
        hist = stock.history(period="1mo")
        
        if hist.empty:
            raise ValueError(f"无法获取股票 {ticker} 的数据")
        
        # 获取当前价格（最新收盘价）
        current_price = hist['Close'].iloc[-1]
        
        return float(current_price), hist
        
    except Exception as e:
        print(f"获取数据失败: {e}")
        # 如果真实数据获取失败，返回模拟数据
        return get_mock_data(ticker)

def get_mock_data(ticker):
    """
    获取模拟数据（用于演示）
    """
    # 生成最近30天的模拟股价数据
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # 生成随机价格趋势
    np.random.seed(hash(ticker) % 2**32)  # 基于ticker的种子，确保同一股票有相同趋势
    base_price = random.uniform(50, 300)
    price_changes = np.random.normal(0, 0.02, len(dates))  # 2%的日波动
    prices = [base_price]
    
    for change in price_changes[:-1]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    hist = pd.DataFrame({
        'Open': [p * random.uniform(0.98, 1.02) for p in prices],
        'High': [p * random.uniform(1.01, 1.05) for p in prices],
        'Low': [p * random.uniform(0.95, 0.99) for p in prices],
        'Close': prices,
        'Volume': [random.randint(1000000, 10000000) for _ in prices]
    }, index=dates)
    
    current_price = hist['Close'].iloc[-1]
    return float(current_price), hist

def get_news(ticker):
    """
    获取股票相关新闻（模拟数据）
    
    Args:
        ticker (str): 股票代码
    
    Returns:
        list: 新闻标题列表
    """
    # 根据股票代码生成相关的模拟新闻
    news_templates = {
        'AAPL': [
            "Apple发布新一代iPhone，股价预期强劲增长",
            "Apple季度财报超预期，营收创历史新高",
            "Apple在AI领域取得重大突破，市场反应积极",
            "Apple面临供应链挑战，投资者表示担忧",
            "Apple宣布新的股票回购计划，股东信心提升"
        ],
        'GOOGL': [
            "Google母公司Alphabet发布强劲广告收入报告",
            "Google Cloud业务持续增长，AI投资见成效",
            "Alphabet面临反垄断调查，股价波动加剧",
            "Google推出新AI产品，技术领先地位巩固",
            "Alphabet宣布大规模招聘计划，扩张意图明显"
        ],
        'MSFT': [
            "Microsoft Azure云服务增长强劲，企业客户增长",
            "Microsoft与OpenAI合作深化，AI产品线扩展",
            "Microsoft发布Windows新版本，用户体验提升",
            "Microsoft面临监管压力，但基本面依然强劲",
            "Microsoft云计算业务增长放缓，投资者关注"
        ]
    }
    
    # 获取特定股票的新闻或使用通用新闻
    if ticker.upper() in news_templates:
        return news_templates[ticker.upper()]
    else:
        # 通用新闻模板
        general_news = [
            f"{ticker}公司发布最新财报，业绩表现亮眼",
            f"分析师上调{ticker}目标价，建议买入",
            f"{ticker}面临市场竞争压力，股价承压",
            f"机构投资者增配{ticker}股票，看好长期发展",
            f"{ticker}宣布重大合作伙伴关系，市场反应积极",
            f"经济环境变化影响{ticker}业务，投资者保持谨慎"
        ]
        return random.sample(general_news, min(5, len(general_news)))
