"""
自然语言处理模块
进行情感分析
"""
from textblob import TextBlob
import re
import random

def clean_text(text):
    """
    清理文本数据
    """
    if not isinstance(text, str):
        return ""
    
    # 移除特殊字符，保留中文、英文、数字和基本标点
    text = re.sub(r'[^\w\s\-\.\!\?\,\:;\"\']', '', text)
    # 去除多余空格
    text = ' '.join(text.split())
    
    return text

def analyze_sentiment(text_list):
    """
    分析文本情感得分
    
    Args:
        text_list (list): 文本列表或单个文本
    
    Returns:
        float: 情感得分 (-1 到 1)
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
            # 使用 TextBlob 进行情感分析
            blob = TextBlob(clean_text_data)
            sentiment_score = blob.sentiment.polarity
            
            # 权重调整：中文和英文情感词典差异
            # 如果文本包含中文关键词，调整权重
            chinese_positive_words = ['增长', '上涨', '利好', '超预期', '强劲', '突破', '积极', '信心', '提升']
            chinese_negative_words = ['下降', '下跌', '担忧', '承压', '挑战', '压力', '谨慎', '波动', '放缓']
            
            text_lower = text.lower()
            
            # 中文正面词权重
            chinese_pos_count = sum(1 for word in chinese_positive_words if word in text)
            # 中文负面词权重
            chinese_neg_count = sum(1 for word in chinese_negative_words if word in text)
            
            # 调整得分
            sentiment_score += (chinese_pos_count * 0.1) - (chinese_neg_count * 0.1)
            
            # 确保得分在有效范围内
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            sentiment_scores.append(sentiment_score)
            
        except Exception as e:
            print(f"分析文本失败: {text}, 错误: {e}")
            continue
    
    if not sentiment_scores:
        return 0.0
    
    # 计算平均得分
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # 金融文本特殊处理：避免极端情感影响
    # 如果所有得分都是极端值（接近-1或1），适度调整
    if avg_sentiment > 0.8:
        avg_sentiment = 0.6
    elif avg_sentiment < -0.8:
        avg_sentiment = -0.6
    
    return round(avg_sentiment, 3)

def get_sentiment_label(sentiment_score):
    """
    根据情感得分返回标签
    
    Args:
        sentiment_score (float): 情感得分
    
    Returns:
        str: 情感标签
    """
    if sentiment_score >= 0.5:
        return "积极"
    elif sentiment_score >= 0.1:
        return "略微积极"
    elif sentiment_score >= -0.1:
        return "中性"
    elif sentiment_score >= -0.5:
        return "略微消极"
    else:
        return "消极"

def analyze_news_sentiment(news_headlines):
    """
    分析新闻标题情感（专门用于新闻分析）
    
    Args:
        news_headlines (list): 新闻标题列表
    
    Returns:
        dict: 包含情感得分、标签和详细分析的字典
    """
    if not news_headlines:
        return {
            'sentiment_score': 0.0,
            'sentiment_label': '中性',
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'detailed_scores': []
        }
    
    detailed_scores = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for headline in news_headlines:
        if not isinstance(headline, str):
            continue
            
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
    提取关键词
    
    Args:
        text_list (list): 文本列表
        top_n (int): 返回前N个关键词
    
    Returns:
        list: 关键词列表
    """
    from collections import Counter
    import re
    
    # 合并所有文本
    all_text = ' '.join([str(text) for text in text_list if text])
    
    # 提取单词（英文单词和中文词组）
    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    
    # 简单中文分词（基于标点分割）
    chinese_words = []
    for char in all_text:
        if char in ['，', '。', '！', '？', '、', '；', '：']:
            continue
        if not char.isascii() and len(char) == 1:
            chinese_words.append(char)
    
    # 统计词频
    word_counts = Counter(english_words)
    
    # 过滤停用词
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an', 'and', 'as', 'if', 'it', 'its', 'he', 'she', 'they', 'them', 'their', 'we', 'you', 'i'}
    
    filtered_words = [(word, count) for word, count in word_counts.items() if word not in stop_words]
    
    # 按频率排序
    top_words = sorted(filtered_words, key=lambda x: x[1], reverse=True)[:top_n]
    
    return [word for word, count in top_words]
