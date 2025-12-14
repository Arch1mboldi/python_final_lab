"""
自然语言处理模块 (升级版)
功能：
1. 使用 SnowNLP 进行中文情感分析 (更适合中文语境)
2. 使用 Jieba 进行关键词提取 (TF-IDF算法)
"""
from snownlp import SnowNLP
import jieba
import jieba.analyse
import re

def clean_text(text):
    """
    清理文本数据
    """
    if not isinstance(text, str):
        return ""
    
    # 移除特殊字符，只保留中文、英文、数字和基本标点
    # 增加对中文标点的支持
    text = re.sub(r'[^\w\s\-\.\!\?\,\:;\"\'\u4e00-\u9fa5，。！？、；：“”‘’]', '', text)
    # 去除多余空格
    text = ' '.join(text.split())
    
    return text

def analyze_sentiment(text_list):
    """
    分析文本情感得分 (使用 SnowNLP)
    
    Args:
        text_list (list): 文本列表或单个文本
    
    Returns:
        float: 情感得分 (-1 到 1, 以适配预测模型)
    """
    if isinstance(text_list, str):
        text_list = [text_list]
    
    if not text_list:
        return 0.0
    
    sentiment_scores = []
    
    for text in text_list:
        if not text or not isinstance(text, str):
            continue
            
        # 清理文本
        clean_text_data = clean_text(text)
        if not clean_text_data:
            continue
            
        try:
            # === 核心修改：使用 SnowNLP ===
            s = SnowNLP(clean_text_data)
            score = s.sentiments  # SnowNLP 返回 0.0 (消极) ~ 1.0 (积极)
            
            # === 分数映射 ===
            # 将 0~1 映射到 -1~1，保持与原项目逻辑兼容
            # 0 -> -1
            # 0.5 -> 0
            # 1 -> 1
            mapped_score = (score - 0.5) * 2
            
            sentiment_scores.append(mapped_score)
            
        except Exception as e:
            print(f"SnowNLP 分析失败: {text[:10]}..., 错误: {e}")
            continue
    
    if not sentiment_scores:
        return 0.0
    
    # 计算平均得分
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # 保留3位小数
    return round(avg_sentiment, 3)

def get_sentiment_label(sentiment_score):
    """
    根据情感得分返回标签 (-1 到 1)
    """
    if sentiment_score >= 0.4:  # 稍微调整阈值，SnowNLP比较敏感
        return "积极"
    elif sentiment_score >= 0.1:
        return "略微积极"
    elif sentiment_score >= -0.1:
        return "中性"
    elif sentiment_score >= -0.4:
        return "略微消极"
    else:
        return "消极"

def analyze_news_sentiment(news_headlines):
    """
    分析新闻标题情感
    """
    if not news_headlines:
        return {
            'sentiment_score': 0.0,
            'sentiment_label': '中性',
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'detailed_scores': [],
            'total_news': 0
        }
    
    detailed_scores = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for headline in news_headlines:
        score = analyze_sentiment(headline)
        detailed_scores.append(score)
        
        if score >= 0.1:
            positive_count += 1
        elif score <= -0.1:
            negative_count += 1
        else:
            neutral_count += 1
    
    if not detailed_scores:
        avg_score = 0.0
    else:
        avg_score = sum(detailed_scores) / len(detailed_scores)
    
    return {
        'sentiment_score': round(avg_score, 3),
        'sentiment_label': get_sentiment_label(avg_score),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'detailed_scores': detailed_scores,
        'total_news': len(detailed_scores)
    }

def extract_keywords(text_list, top_n=10):
    """
    提取关键词 (升级为使用 Jieba TF-IDF)
    """
    if isinstance(text_list, list):
        text = ' '.join([str(t) for t in text_list])
    else:
        text = str(text_list)
        
    try:
        # 使用 jieba.analyse.extract_tags 提取关键词
        # topK: 返回几个关键词
        # withWeight: 是否返回权重 (这里不需要)
        # allowPOS: 仅提取名词(n)等，过滤掉虚词
        keywords = jieba.analyse.extract_tags(
            text, 
            topK=top_n, 
            allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn') 
        )
        return keywords
    except Exception as e:
        print(f"关键词提取失败: {e}")
        return []