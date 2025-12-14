"""
数据可视化模块
生成图表和可视化内容 (修复版：完美爱心词云)
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm # 需要导入这个来设置标题字体
from wordcloud import WordCloud
from datetime import datetime, timedelta
import warnings
import platform
import os
import jieba
from PIL import Image

warnings.filterwarnings('ignore')

# --- 字体配置 helper (跨平台兼容版) ---
def get_chinese_font_path():
    """自动获取系统中文字体路径 (兼容 Mac 和 Windows)"""
    system_name = platform.system()
    
    if system_name == 'Darwin':  # macOS
        possible_fonts = [
            '/System/Library/Fonts/PingFang.ttc',         # 苹方
            '/System/Library/Fonts/STHeiti Light.ttc',    # 黑体
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            '/Library/Fonts/Arial Unicode.ttf'
        ]
    elif system_name == 'Windows': # Windows
        possible_fonts = [
            'C:\\Windows\\Fonts\\msyh.ttc',   # 微软雅黑
            'C:\\Windows\\Fonts\\simhei.ttf', # 黑体
            'C:\\Windows\\Fonts\\simsun.ttc'  # 宋体
        ]
    else:
        possible_fonts = [] # Linux 或其他

    for f in possible_fonts:
        if os.path.exists(f):
            return f
    return None

def create_candlestick_chart(historical_data, current_price, prediction, ticker="股票"):
    """1. K线图（蜡烛图）"""
    try:
        hist = historical_data.sort_index()
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} 股价走势', '成交量')
        )
        # K线
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
            name='K线', increasing_line_color='#ef5350', decreasing_line_color='#26a69a'
        ), row=1, col=1)
        # 均线
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA5'], name='MA5', line=dict(color='#ffa726', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA20'], name='MA20', line=dict(color='#29b6f6', width=1)), row=1, col=1)
        # 预测点
        next_date = hist.index[-1] + timedelta(days=1)
        fig.add_trace(go.Scatter(
            x=[next_date], y=[prediction], name='明日预测', mode='markers+text',
            marker=dict(size=12, color='#7e57c2', symbol='star'),
            text=[f'{prediction:.2f}'], textposition='top center'
        ), row=1, col=1)
        # 成交量
        colors = ['#ef5350' if row['Open'] < row['Close'] else '#26a69a' for index, row in hist.iterrows()]
        fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='成交量', marker_color=colors), row=2, col=1)
        
        fig.update_layout(
            height=500, margin=dict(l=20, r=20, t=40, b=20),
            xaxis_rangeslider_visible=False, template='plotly_white', hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig
    except Exception as e:
        print(f"K线图错误: {e}")
        return go.Figure()

def create_prediction_chart(historical_data, current_price, prediction):
    """2. 趋势预测图"""
    try:
        hist = historical_data.iloc[-30:]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['Close'], mode='lines', name='历史收盘价',
            line=dict(color='#42a5f5', width=3), fill='tozeroy', fillcolor='rgba(66, 165, 245, 0.1)'
        ))
        next_date = hist.index[-1] + timedelta(days=1)
        fig.add_trace(go.Scatter(
            x=[hist.index[-1], next_date], y=[current_price, prediction],
            mode='lines+markers', name='趋势预测',
            line=dict(color='#ef5350', width=2, dash='dash'), marker=dict(size=8)
        ))
        fig.update_layout(title="短期价格趋势预测", height=350, template='plotly_white', margin=dict(l=20, r=20, t=40, b=20))
        return fig
    except Exception: return go.Figure()

def create_sentiment_pie_chart(sentiment_data):
    """3. 情感分布图"""
    try:
        labels = ['积极', '消极', '中性']
        values = [sentiment_data.get('positive_count', 0), sentiment_data.get('negative_count', 0), sentiment_data.get('neutral_count', 0)]
        colors = ['#66bb6a', '#ef5350', '#bdbdbd']
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=colors), textinfo='label+percent')])
        fig.update_layout(title="新闻舆情分布", height=350, margin=dict(l=20, r=20, t=40, b=20), showlegend=True)
        return fig
    except Exception: return go.Figure()

def create_correlation_heatmap(historical_data):
    """4. 相关性热力图"""
    try:
        df = historical_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        corr_matrix = df.corr()
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.index,
            colorscale='Viridis', text=np.round(corr_matrix.values, 2), texttemplate="%{text}", showscale=True
        ))
        fig.update_layout(title="量价因子相关性", height=350, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    except Exception: return go.Figure()

def create_wordcloud(text_list, mask_image_path="love.png"):
    """
    5. 词云图 (修复版)
    """
    try:
        if not text_list: return plt.figure()
        
        full_text = ' '.join([str(t) for t in text_list])
        cut_text = " ".join(jieba.cut(full_text))
        font_path = get_chinese_font_path()
        
        mask = None
        if os.path.exists(mask_image_path):
            try:
                mask = np.array(Image.open(mask_image_path))
            except Exception as e:
                print(f"图片蒙版加载失败: {e}")
        
        # 词云生成配置
        wc = WordCloud(
            background_color='white',
            width=800, height=600,
            max_words=100,
            colormap='Reds',
            font_path=font_path, 
            mask=mask,
            contour_width=2, # 减小轮廓宽度
            contour_color='pink',
            random_state=42
        ).generate(cut_text)
        
        # --- 绘图修正区域 ---
        
        # 1. 调整画布大小：使其更紧凑，解决“太大”的问题
        fig, ax = plt.subplots(figsize=(6, 4))  
        
        ax.imshow(wc, interpolation='bilinear')
        
        ax.axis('off') 

        # 3. 设置中文标题：使用 FontProperties 解决标题乱码
        if font_path:
            font_prop = fm.FontProperties(fname=font_path, size=14)
            ax.set_title('舆情关键词云', fontproperties=font_prop, color='#333333', pad=12)
        else:
            ax.set_title('Word Cloud', fontsize=14, color='#333333', pad=12)

        # 4. 紧凑布局：
        plt.tight_layout(pad=0.5)
        
        return fig
    except Exception as e:
        print(f"词云生成失败: {e}")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f'词云错误: {str(e)}', ha='center')
        ax.axis('off')
        return fig