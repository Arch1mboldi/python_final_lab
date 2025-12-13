"""
机器学习预测模块
基于历史数据进行价格预测
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class PricePredictor:
    """
    股价预测器
    使用机器学习模型预测股票价格
    """
    
    def __init__(self, ticker):
        """
        初始化预测器
        
        Args:
            ticker (str): 股票代码
        """
        self.ticker = ticker.upper()
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ['moving_avg', 'previous_close', 'volume_ma', 'volatility']
        
        # 训练模型
        self._train_model()
    
    def _prepare_features(self, data):
        """
        准备机器学习特征
        
        Args:
            data (pd.DataFrame): 股票历史数据
        
        Returns:
            np.array: 特征矩阵
        """
        features = []
        
        # 确保数据按日期排序
        data = data.sort_index()
        
        for i in range(len(data)):
            row = data.iloc[i]
            
            # 移动平均线 (5日)
            if i >= 4:
                ma_5 = data['Close'].iloc[i-4:i+1].mean()
            else:
                ma_5 = row['Close']
            
            # 前一日收盘价
            prev_close = data['Close'].iloc[i-1] if i > 0 else row['Close']
            
            # 成交量移动平均 (5日)
            if i >= 4:
                volume_ma = data['Volume'].iloc[i-4:i+1].mean()
            else:
                volume_ma = row['Volume']
            
            # 波动率 (5日)
            if i >= 4:
                returns = data['Close'].iloc[i-4:i+1].pct_change().dropna()
                volatility = returns.std() if len(returns) > 0 else 0
            else:
                volatility = 0
            
            features.append([ma_5, prev_close, volume_ma, volatility])
        
        return np.array(features)
    
    def _train_model(self):
        """
        训练机器学习模型
        """
        try:
            # 获取训练数据
            from modules.data_loader import get_realtime_data
            current_price, historical_data = get_realtime_data(self.ticker)
            
            if len(historical_data) < 10:
                print(f"数据不足，使用简单预测方法")
                self.is_trained = False
                return
            
            # 准备特征和目标变量
            X = self._prepare_features(historical_data)
            y = historical_data['Close'].values
            
            # 移除第一行（因为第一行没有前一天数据）
            X = X[1:]
            y = y[1:]
            
            if len(X) < 5:
                print(f"特征数据不足，使用简单预测方法")
                self.is_trained = False
                return
            
            # 分割训练和测试数据
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 特征标准化
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 尝试多个模型，选择最好的
            models = {
                'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
                'LinearRegression': LinearRegression()
            }
            
            best_score = -np.inf
            best_model = None
            
            for name, model in models.items():
                model.fit(X_train_scaled, y_train)
                score = model.score(X_test_scaled, y_test)
                
                if score > best_score:
                    best_score = score
                    best_model = model
            
            self.model = best_model
            self.is_trained = True
            
            # 计算模型性能
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"模型训练完成 - MAE: {mae:.2f}, R²: {r2:.3f}")
            
        except Exception as e:
            print(f"模型训练失败: {e}")
            self.is_trained = False
    
    def predict_next(self, current_price, sentiment_score=0):
        """
        预测下一个时间点的价格
        
        Args:
            current_price (float): 当前价格
            sentiment_score (float): 情感得分 (-1 到 1)
        
        Returns:
            float: 预测价格
        """
        try:
            if not self.is_trained or self.model is None:
                # 如果模型未训练，使用简单预测
                return self._simple_predict(current_price, sentiment_score)
            
            # 获取最新数据进行预测
            from modules.data_loader import get_realtime_data
            _, historical_data = get_realtime_data(self.ticker)
            
            if len(historical_data) < 5:
                return self._simple_predict(current_price, sentiment_score)
            
            # 准备最新特征
            latest_features = self._prepare_features(historical_data[-5:])
            latest_features = latest_features[-1:]  # 取最后一行
            
            # 标准化特征
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # 预测
            base_prediction = self.model.predict(latest_features_scaled)[0]
            
            # 结合情感分析调整预测
            adjusted_prediction = self._apply_sentiment_adjustment(
                base_prediction, current_price, sentiment_score
            )
            
            return round(adjusted_prediction, 2)
            
        except Exception as e:
            print(f"预测失败: {e}")
            return self._simple_predict(current_price, sentiment_score)
    
    def _simple_predict(self, current_price, sentiment_score):
        """
        简单预测方法（当机器学习模型不可用时）
        
        Args:
            current_price (float): 当前价格
            sentiment_score (float): 情感得分
        
        Returns:
            float: 预测价格
        """
        # 基于情感得分的简单调整
        sentiment_factor = 1 + (sentiment_score * 0.02)  # 最多2%的调整
        
        # 添加随机波动
        import random
        random_factor = random.uniform(0.98, 1.02)
        
        prediction = current_price * sentiment_factor * random_factor
        
        return round(prediction, 2)
    
    def _apply_sentiment_adjustment(self, base_prediction, current_price, sentiment_score):
        """
        基于情感得分调整预测结果
        
        Args:
            base_prediction (float): 基础预测价格
            current_price (float): 当前价格
            sentiment_score (float): 情感得分
        
        Returns:
            float: 调整后的预测价格
        """
        # 情感得分影响因子
        if sentiment_score >= 0.5:
            sentiment_factor = 1.005  # 积极情感 +0.5%
        elif sentiment_score >= 0.2:
            sentiment_factor = 1.002  # 略微积极 +0.2%
        elif sentiment_score <= -0.5:
            sentiment_factor = 0.995  # 消极情感 -0.5%
        elif sentiment_score <= -0.2:
            sentiment_factor = 0.998  # 略微消极 -0.2%
        else:
            sentiment_factor = 1.0   # 中性
        
        # 平滑调整，避免过度波动
        adjustment_weight = 0.3  # 情感因素占30%权重
        
        adjusted_prediction = (
            base_prediction * (1 - adjustment_weight) + 
            base_prediction * sentiment_factor * adjustment_weight
        )
        
        # 确保预测价格在合理范围内
        max_change = current_price * 0.05  # 最多5%的变化
        lower_bound = current_price - max_change
        upper_bound = current_price + max_change
        
        adjusted_prediction = max(lower_bound, min(upper_bound, adjusted_prediction))
        
        return adjusted_prediction
    
    def get_prediction_confidence(self, current_price, prediction):
        """
        获取预测置信度
        
        Args:
            current_price (float): 当前价格
            prediction (float): 预测价格
        
        Returns:
            float: 置信度得分 (0-1)
        """
        try:
            # 基于预测变化幅度计算置信度
            change_percent = abs(prediction - current_price) / current_price
            
            # 变化越小，置信度越高
            if change_percent <= 0.01:  # 1%以内
                confidence = 0.9
            elif change_percent <= 0.03:  # 3%以内
                confidence = 0.7
            elif change_percent <= 0.05:  # 5%以内
                confidence = 0.5
            else:
                confidence = 0.3
            
            # 如果模型训练成功，提高置信度
            if self.is_trained:
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            print(f"计算置信度失败: {e}")
            return 0.5
    
    def get_model_info(self):
        """
        获取模型信息
        
        Returns:
            dict: 模型信息字典
        """
        return {
            'ticker': self.ticker,
            'is_trained': self.is_trained,
            'model_type': type(self.model).__name__ if self.model else 'Simple',
            'features': self.feature_names
        }
