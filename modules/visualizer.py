"""
数据可视化模块
生成图表和可视化内容
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def create_candlestick_chart(historical_data, current_price, prediction, ticker="股票"):
    """
    创建K线图（蜡烛图），包含预测价格
    
    Args:
        historical_data (pd.DataFrame): 历史股价数据
        current_price (float): 当前价格
        prediction (float): 预测价格
        ticker (str): 股票代码
    
    Returns:
        plotly.graph_objects.Figure: K线图对象
    """
    try:
        # 确保数据按日期排序
        hist = historical_data.sort_index()
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} 股价K线图', '成交量')
        )
        
        # 添加K线图
        fig.add_trace(
            go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='股价',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )
        
        # 添加移动平均线
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['MA5'],
                name='MA5',
                line=dict(color='#ff9800', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['MA20'],
                name='MA20',
                line=dict(color='#2196f3', width=2)
            ),
            row=1, col=1
        )
        
        # 添加预测价格线
        last_date = hist.index[-1]
        next_date = last_date + timedelta(days=1)
        
        fig.add_trace(
            go.Scatter(
                x=[last_date, next_date],
                y=[current_price, prediction],
                name='价格预测',
                line=dict(color='red', width=3, dash='dash'),
                mode='lines+markers',
                marker=dict(size=10, symbol='diamond')
            ),
            row=1, col=1
        )
        
        # 添加预测点标记
        fig.add_trace(
            go.Scatter(
                x=[next_date],
                y=[prediction],
                name='预测点',
                mode='markers',
                marker=dict(size=12, color='red', symbol='star'),
                text=f'预测价格: ${prediction:.2f}',
                textposition='top center'
            ),
            row=1, col=1
        )
        
        # 添加成交量
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist['Volume'],
                name='成交量',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title=f'{ticker} 股价分析与预测',
            xaxis_title='日期',
            yaxis_title='价格 ($)',
            yaxis2_title='成交量',
            hovermode='x unified',
            showlegend=True,
            height=600,
            template='plotly_white'
        )
        
        # 更新y轴
        fig.update_yaxes(title_text="价格 ($)", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        
        # 隐藏x轴上的范围滑块
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        return fig
        
    except Exception as e:
        print(f"创建K线图失败: {e}")
        # 返回简单的线图作为备用
        return create_simple_price_chart(historical_data, current_price, prediction, ticker)

def create_simple_price_chart(historical_data, current_price, prediction, ticker="股票"):
    """
    创建简单的价格图表（备用方案）
    """
    try:
        hist = historical_data.sort_index()
        
        fig = go.Figure()
        
        # 添加历史价格线
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='历史价格',
                line=dict(color='blue', width=2)
            )
        )
        
        # 添加预测线
        last_date = hist.index[-1]
        next_date = last_date + timedelta(days=1)
        
        fig.add_trace(
            go.Scatter(
                x=[last_date, next_date],
                y=[current_price, prediction],
                mode='lines+markers',
                name='价格预测',
                line=dict(color='red', width=3, dash='dash'),
                marker=dict(size=10)
            )
        )
        
        fig.update_layout(
            title=f'{ticker} 股价预测图',
            xaxis_title='日期',
            yaxis_title='价格 ($)',
            template='plotly_white',
            height=400
        )
        
        return fig
        
    except Exception as e:
        print(f"创建简单图表失败: {e}")
        return go.Figure()

def create_wordcloud(text_list):
    """
    创建词云图
    
    Args:
        text_list (list): 文本列表
    
    Returns:
        matplotlib.figure.Figure: 词云图对象
    """
    try:
        # 合并所有文本
        if isinstance(text_list, str):
            text_list = [text_list]
        
        combined_text = ' '.join([str(text) for text in text_list if text])
        
        if not combined_text.strip():
            # 如果没有文本，创建空图
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, '暂无文本数据', ha='center', va='center', fontsize=16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        # 创建词云
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            colormap='viridis',
            font_path=None,  # 使用默认字体
            relative_scaling=0.5,
            random_state=42
        ).generate(combined_text)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.set_title('新闻关键词云', fontsize=16, fontweight='bold')
        ax.axis('off')
        
        # 调整布局
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        print(f"创建词云图失败: {e}")
        # 返回错误提示图
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f'词云生成失败\n{str(e)}', ha='center', va='center', fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig

def create_sentiment_chart(sentiment_data):
    """
    创建情感分析图表
    
    Args:
        sentiment_data (dict): 情感分析数据
    
    Returns:
        plotly.graph_objects.Figure: 情感图表
    """
    try:
        if not sentiment_data or 'detailed_scores' not in sentiment_data:
            return go.Figure()
        
        scores = sentiment_data['detailed_scores']
        labels = sentiment_data.get('labels', ['新闻'] * len(scores))
        
        fig = go.Figure()
        
        # 创建情感得分柱状图
        colors = ['green' if score > 0 else 'red' if score < 0 else 'gray' for score in scores]
        
        fig.add_trace(
            go.Bar(
                x=list(range(len(scores))),
                y=scores,
                name='情感得分',
                marker_color=colors,
                text=[f'{score:.3f}' for score in scores],
                textposition='auto'
            )
        )
        
        fig.update_layout(
            title='新闻情感分析',
            xaxis_title='新闻序号',
            yaxis_title='情感得分',
            template='plotly_white',
            height=400
        )
        
        # 添加水平参考线
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
        fig.add_hline(y=0.5, line_dash="dot", line_color="green", opacity=0.3)
        fig.add_hline(y=-0.5, line_dash="dot", line_color="red", opacity=0.3)
        
        return fig
        
    except Exception as e:
        print(f"创建情感图表失败: {e}")
        return go.Figure()

def create_prediction_chart(predictions_data):
    """
    创建预测对比图表
    
    Args:
        predictions_data (list): 预测数据列表
    
    Returns:
        plotly.graph_objects.Figure: 预测对比图
    """
    try:
        if not predictions_data:
            return go.Figure()
        
        fig = go.Figure()
        
        # 添加实际价格线
        if 'actual' in predictions_data:
            actual_data = predictions_data['actual']
            fig.add_trace(
                go.Scatter(
                    x=actual_data['dates'],
                    y=actual_data['prices'],
                    mode='lines+markers',
                    name='实际价格',
                    line=dict(color='blue', width=2)
                )
            )
        
        # 添加预测价格线
        if 'predicted' in predictions_data:
            pred_data = predictions_data['predicted']
            fig.add_trace(
                go.Scatter(
                    x=pred_data['dates'],
                    y=pred_data['prices'],
                    mode='lines+markers',
                    name='预测价格',
                    line=dict(color='red', width=2, dash='dash')
                )
            )
        
        fig.update_layout(
            title='价格预测对比',
            xaxis_title='日期',
            yaxis_title='价格 ($)',
            template='plotly_white',
            height=400
        )
        
        return fig
        
    except Exception as e:
        print(f"创建预测图表失败: {e}")
        return go.Figure()

def create_portfolio_performance_chart(portfolio_data):
    """
    创建投资组合表现图表
    
    Args:
        portfolio_data (pd.DataFrame): 投资组合数据
    
    Returns:
        plotly.graph_objects.Figure: 投资组合表现图
    """
    try:
        if portfolio_data.empty:
            return go.Figure()
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('投资组合价值', '日收益率')
        )
        
        # 投资组合价值
        fig.add_trace(
            go.Scatter(
                x=portfolio_data.index,
                y=portfolio_data['portfolio_value'],
                mode='lines',
                name='投资组合价值',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
        
        # 日收益率
        returns = portfolio_data['portfolio_value'].pct_change().dropna()
        colors = ['green' if ret > 0 else 'red' for ret in returns]
        
        fig.add_trace(
            go.Bar(
                x=returns.index,
                y=returns,
                name='日收益率',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title='投资组合表现分析',
            template='plotly_white',
            height=600
        )
        
        return fig
        
    except Exception as e:
        print(f"创建投资组合图表失败: {e}")
        return go.Figure()
