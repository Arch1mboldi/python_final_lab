"""
数据库管理模块
MySQL 数据库操作 (使用 SQLAlchemy + PyMySQL)
"""
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import pymysql

pymysql.install_as_MySQLdb()

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        # ================= 配置区域 =================
        self.DB_USER = "root"      # MySQL 用户名
        self.DB_PASSWORD = "12345678"      # MySQL 密码 (如果为空请保留空字符串)
        self.DB_HOST = "localhost" 
        self.DB_PORT = 3306        
        self.DB_NAME = "investment_analysis" 
        # ===========================================

        self.base_conn_str = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}"
        self.db_conn_str = f"{self.base_conn_str}/{self.DB_NAME}?charset=utf8mb4"
        self.engine = None
        self.init_db()
    
    def get_engine(self):
        if self.engine is None:
            self.engine = create_engine(self.db_conn_str, pool_recycle=3600)
        return self.engine

    def init_db(self):
        try:
            temp_engine = create_engine(self.base_conn_str)
            with temp_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.DB_NAME}"))
            
            engine = self.get_engine()
            with engine.connect() as conn:
                sql_create_table = """
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ticker VARCHAR(20) NOT NULL,
                        current_price DECIMAL(10, 2) NOT NULL,
                        predicted_price DECIMAL(10, 2) NOT NULL,
                        sentiment_score DECIMAL(5, 4) NOT NULL,
                        confidence_score DECIMAL(5, 4) DEFAULT 0.5,
                        analysis_date DATE DEFAULT (CURRENT_DATE)
                    )
                """
                conn.execute(text(sql_create_table))
                try:
                    conn.execute(text("CREATE INDEX idx_analysis_ticker ON analysis_history(ticker)"))
                    conn.execute(text("CREATE INDEX idx_analysis_date ON analysis_history(analysis_date)"))
                except Exception:
                    pass
                print("MySQL 数据库初始化完成")
        except Exception as e:
            print(f"数据库初始化失败: {e}")

    def save_record(self, ticker, price, prediction, sentiment, confidence=0.5):
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO analysis_history 
                    (ticker, current_price, predicted_price, sentiment_score, confidence_score)
                    VALUES (:ticker, :price, :prediction, :sentiment, :confidence)
                """)
                result = conn.execute(query, {
                    "ticker": ticker.upper(),
                    "price": price,
                    "prediction": prediction,
                    "sentiment": sentiment,
                    "confidence": confidence
                })
                conn.commit()
                return result.lastrowid
        except Exception as e:
            print(f"保存记录失败: {e}")
            return None
    
    def fetch_history(self, ticker=None, limit=50):
        try:
            engine = self.get_engine()
            if ticker:
                query = "SELECT id, timestamp, ticker, current_price, predicted_price, sentiment_score, ROUND((predicted_price - current_price) / current_price * 100, 2) as change_percent FROM analysis_history WHERE ticker = %(ticker)s ORDER BY timestamp DESC LIMIT %(limit)s"
                params = {"ticker": ticker.upper(), "limit": limit}
            else:
                query = "SELECT id, timestamp, ticker, current_price, predicted_price, sentiment_score, ROUND((predicted_price - current_price) / current_price * 100, 2) as change_percent FROM analysis_history ORDER BY timestamp DESC LIMIT %(limit)s"
                params = {"limit": limit}
            return pd.read_sql(query, engine, params=params)
        except Exception as e:
            print(f"获取历史失败: {e}")
            return pd.DataFrame()

    def clear_all_history(self):
        """清空所有历史记录"""
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("TRUNCATE TABLE analysis_history"))
                conn.commit()
            print("历史记录已清空")
            return True
        except Exception as e:
            print(f"清空记录失败: {e}")
            return False