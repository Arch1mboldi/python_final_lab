"""
数据库管理模块
SQLite数据库操作
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os

class DatabaseManager:
    """
    数据库管理器
    负责SQLite数据库的初始化、读写操作
    """
    
    def __init__(self, db_path="investment_analysis.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """
        初始化数据库表结构
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建分析历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ticker TEXT NOT NULL,
                        current_price REAL NOT NULL,
                        predicted_price REAL NOT NULL,
                        sentiment_score REAL NOT NULL,
                        confidence_score REAL DEFAULT 0.5,
                        analysis_date DATE DEFAULT (date('now'))
                    )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_ticker 
                    ON analysis_history(ticker)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_date 
                    ON analysis_history(analysis_date)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
                    ON analysis_history(timestamp)
                ''')
                
                conn.commit()
                print("数据库初始化完成")
                
        except Exception as e:
            print(f"数据库初始化失败: {e}")
    
    def save_record(self, ticker, price, prediction, sentiment, confidence=0.5):
        """
        保存分析记录
        
        Args:
            ticker (str): 股票代码
            price (float): 当前价格
            prediction (float): 预测价格
            sentiment (float): 情感得分
            confidence (float): 置信度得分
        
        Returns:
            int: 记录ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO analysis_history 
                    (ticker, current_price, predicted_price, sentiment_score, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ticker.upper(), price, prediction, sentiment, confidence))
                
                record_id = cursor.lastrowid
                conn.commit()
                
                print(f"记录已保存 - ID: {record_id}, {ticker}")
                return record_id
                
        except Exception as e:
            print(f"保存记录失败: {e}")
            return None
    
    def fetch_history(self, ticker=None, limit=50):
        """
        获取分析历史记录
        
        Args:
            ticker (str): 股票代码过滤，如果为None则获取所有
            limit (int): 返回记录数量限制
        
        Returns:
            pd.DataFrame: 历史记录DataFrame
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if ticker:
                    query = '''
                        SELECT 
                            id,
                            timestamp,
                            ticker,
                            current_price,
                            predicted_price,
                            sentiment_score,
                            confidence_score,
                            ROUND((predicted_price - current_price) / current_price * 100, 2) as change_percent
                        FROM analysis_history
                        WHERE ticker = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(ticker.upper(), limit))
                else:
                    query = '''
                        SELECT 
                            id,
                            timestamp,
                            ticker,
                            current_price,
                            predicted_price,
                            sentiment_score,
                            confidence_score,
                            ROUND((predicted_price - current_price) / current_price * 100, 2) as change_percent
                        FROM analysis_history
                        ORDER BY timestamp DESC
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(limit,))
                
                return df
                
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return pd.DataFrame()
    
    def get_statistics(self, ticker=None):
        """
        获取分析统计信息
        
        Args:
            ticker (str): 股票代码过滤
        
        Returns:
            dict: 统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if ticker:
                    query = '''
                        SELECT 
                            COUNT(*) as total_analyses,
                            AVG(sentiment_score) as avg_sentiment,
                            AVG(confidence_score) as avg_confidence,
                            AVG(ABS(predicted_price - current_price) / current_price) as avg_prediction_error,
                            MIN(timestamp) as first_analysis,
                            MAX(timestamp) as last_analysis
                        FROM analysis_history
                        WHERE ticker = ?
                    '''
                    result = pd.read_sql_query(query, conn, params=(ticker.upper(),))
                else:
                    query = '''
                        SELECT 
                            COUNT(*) as total_analyses,
                            AVG(sentiment_score) as avg_sentiment,
                            AVG(confidence_score) as avg_confidence,
                            AVG(ABS(predicted_price - current_price) / current_price) as avg_prediction_error,
                            MIN(timestamp) as first_analysis,
                            MAX(timestamp) as last_analysis
                        FROM analysis_history
                    '''
                    result = pd.read_sql_query(query, conn)
                
                stats = result.iloc[0].to_dict() if not result.empty else {}
                
                # 转换数据类型
                if stats:
                    stats['total_analyses'] = int(stats.get('total_analyses', 0))
                    stats['avg_sentiment'] = round(stats.get('avg_sentiment', 0), 3)
                    stats['avg_confidence'] = round(stats.get('avg_confidence', 0), 3)
                    stats['avg_prediction_error'] = round(stats.get('avg_prediction_error', 0) * 100, 2)
                
                return stats
                
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}
    
    def get_ticker_performance(self):
        """
        获取各股票表现统计
        
        Returns:
            pd.DataFrame: 股票表现统计
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        ticker,
                        COUNT(*) as analysis_count,
                        AVG(sentiment_score) as avg_sentiment,
                        AVG(confidence_score) as avg_confidence,
                        AVG(predicted_price) as avg_predicted_price,
                        AVG(current_price) as avg_actual_price
                    FROM analysis_history
                    GROUP BY ticker
                    ORDER BY analysis_count DESC
                '''
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    # 计算平均预测准确率
                    df['avg_change_percent'] = ((df['avg_predicted_price'] - df['avg_actual_price']) / df['avg_actual_price'] * 100).round(2)
                    df['avg_sentiment'] = df['avg_sentiment'].round(3)
                    df['avg_confidence'] = df['avg_confidence'].round(3)
                
                return df
                
        except Exception as e:
            print(f"获取股票表现失败: {e}")
            return pd.DataFrame()
    
    def clean_old_records(self, days=30):
        """
        清理旧记录
        
        Args:
            days (int): 保留最近N天的记录
        
        Returns:
            int: 删除的记录数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM analysis_history
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"已清理 {deleted_count} 条旧记录")
                return deleted_count
                
        except Exception as e:
            print(f"清理旧记录失败: {e}")
            return 0
    
    def export_to_csv(self, filename="analysis_history.csv"):
        """
        导出数据到CSV文件
        
        Args:
            filename (str): 输出文件名
        
        Returns:
            bool: 导出是否成功
        """
        try:
            df = self.fetch_history(limit=1000)  # 导出最近1000条记录
            
            if df.empty:
                print("没有数据可导出")
                return False
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"数据已导出到 {filename}")
            return True
            
        except Exception as e:
            print(f"导出数据失败: {e}")
            return False
    
    def get_recent_analyses(self, hours=24):
        """
        获取最近N小时的分析记录
        
        Args:
            hours (int): 小时数
        
        Returns:
            pd.DataFrame: 最近的分析记录
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT *
                    FROM analysis_history
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                '''.format(hours)
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            print(f"获取最近分析失败: {e}")
            return pd.DataFrame()
    
    def backup_database(self, backup_path=None):
        """
        备份数据库
        
        Args:
            backup_path (str): 备份文件路径，如果为None则自动生成
        
        Returns:
            str: 备份文件路径
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            print(f"数据库已备份到 {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"数据库备份失败: {e}")
            return None
