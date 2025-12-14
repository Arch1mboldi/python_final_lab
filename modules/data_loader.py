"""
数据加载模块
功能：
1. 使用 Tushare API 获取中国股市实时/历史数据
2. 使用 Requests + BeautifulSoup 爬取实时财经新闻 (优先)
3. 如果爬取失败，使用模拟数据兜底 (保证演示稳定性)
"""
import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import random  # 必须要导入 random

# 初始化 Tushare (使用你提供的 Token)
ts.set_token('28bc1c29f82fb0f6aa7060d4524e96f87fa0d61ed18a6f45eab30389')
pro = ts.pro_api()

def get_realtime_data(ticker):
    """
    获取股票数据 (使用 Tushare)
    """
    try:
        # 1. 自动处理日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        # 2. 调用 Tushare 接口
        df = pro.daily(ts_code=ticker, start_date=start_date, end_date=end_date)
        
        if df.empty:
            raise ValueError(f"Tushare 未找到股票 {ticker} 的数据")

        # 3. 数据清洗与格式转换
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        df.sort_index(ascending=True, inplace=True)
        
        # 重命名列
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'vol': 'Volume'
        }, inplace=True)
        
        current_price = df['Close'].iloc[-1]
        
        return float(current_price), df

    except Exception as e:
        print(f"Tushare 获取数据失败: {e}")
        raise e

def get_news(ticker):
    """
    增强版新闻爬虫 + 模拟兜底
    策略：
    1. 尝试 爬虫方案 A (中新网)
    2. 尝试 爬虫方案 B (新浪财经)
    3. 兜底: 如果都失败，返回模拟数据
    """
    news_headlines = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    print(f"--- 开始爬取新闻: {ticker} ---")

    # === 爬虫方案 A: 中国新闻网 ===
    try:
        url = "https://www.chinanews.com.cn/finance/index.shtml"
        response = requests.get(url, headers=headers, timeout=3)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select('div.content_list ul li a')
            if not links: links = soup.select('ul li a')

            count = 0
            for link in links:
                title = link.get_text().strip()
                if len(title) > 8 and "http" in link.get('href', ''):
                    news_headlines.append(title)
                    count += 1
                if count >= 8: break
    except Exception:
        pass # 失败了静默跳过，尝试下一个

    # === 爬虫方案 B: 新浪财经 ===
    if not news_headlines:
        try:
            url = "https://finance.sina.com.cn/roll/index.d.html?cid=100872"
            response = requests.get(url, headers=headers, timeout=3)
            response.encoding = response.apparent_encoding 
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.select('ul.list_009 li a')
                for link in links[:8]:
                    title = link.get_text().strip()
                    if len(title) > 5:
                        news_headlines.append(title)
        except Exception:
            pass

    # === 最终兜底: 模拟数据 (原始代码逻辑) ===
    if not news_headlines:
        print("注意: 网络爬虫未获取到数据，已切换至模拟新闻模式。")
        
        # 原始的模拟新闻模板
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
        
        # 尝试匹配股票代码 (虽然你现在用的是数字代码，大概率匹配不到，会进下面的 else)
        if ticker.upper() in news_templates:
            return news_templates[ticker.upper()]
        else:
            # 通用新闻模板 (会动态替换 ticker 名字)
            general_news = [
                f"{ticker}公司发布最新财报，业绩表现亮眼",
                f"分析师上调{ticker}目标价，建议买入",
                f"{ticker}面临市场竞争压力，股价承压",
                f"机构投资者增配{ticker}股票，看好长期发展",
                f"{ticker}宣布重大合作伙伴关系，市场反应积极",
                f"经济环境变化影响{ticker}业务，投资者保持谨慎"
            ]
            # 随机返回 5 条
            return random.sample(general_news, min(5, len(general_news)))
        
    return news_headlines