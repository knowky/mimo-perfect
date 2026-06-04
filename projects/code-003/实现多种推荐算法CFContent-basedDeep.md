# 实现多种推荐算法（CF/Content-based/Deep Learning）

**任务**: 机器学习推荐系统
**时间**: 2026-06-05T00:57:56.845872

# 机器学习推荐系统实现

## 项目概述

我将为您实现一个完整的推荐系统框架，包含协同过滤、基于内容的推荐和深度学习三种主要算法。这个实现将基于MovieLens数据集，具有良好的可扩展性和实用性。

## 项目结构

```
recommendation_system/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── movies.csv
│   │   └── ratings.csv
│   └── processed/
├── models/
│   ├── __init__.py
│   ├── collaborative_filtering.py
│   ├── content_based.py
│   └── deep_learning.py
├── utils/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── metrics.py
│   └── preprocessing.py
├── train.py
├── evaluate.py
└── demo.py
```

## 1. 项目初始化文件

**requirements.txt**
```txt
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
surprise>=1.1.1
tensorflow>=2.6.0
keras>=2.6.0
matplotlib>=3.4.0
seaborn>=0.11.0
jupyter>=1.0.0
tqdm>=4.62.0
scipy>=1.7.0
```

## 2. 数据加载与处理模块

**utils/__init__.py**
```python
"""
工具模块初始化文件
"""
from .data_loader import DataLoader
from .preprocessing import DataPreprocessor
from .metrics import RecommendationMetrics
```

**utils/data_loader.py**
```python
"""
数据加载模块
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
import os

class DataLoader:
    """数据加载器，负责加载和初步处理数据"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.movies_df = None
        self.ratings_df = None
        
    def load_movielens_data(self, dataset_size: str = "100k") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        加载MovieLens数据集
        
        Args:
            dataset_size: 数据集大小，可选 "100k", "1m", "10m"
            
        Returns:
            movies_df: 电影数据
            ratings_df: 评分数据
        """
        if dataset_size == "100k":
            movies_path = os.path.join(self.data_dir, "raw/movies.csv")
            ratings_path = os.path.join(self.data_dir, "raw/ratings.csv")
        else:
            raise ValueError(f"不支持的数据集大小: {dataset_size}")
        
        # 加载数据
        try:
            self.movies_df = pd.read_csv(movies_path)
            self.ratings_df = pd.read_csv(ratings_path)
            
            # 数据预览
            print(f"电影数量: {len(self.movies_df)}")
            print(f"评分数: {len(self.ratings_df)}")
            print(f"用户数量: {self.ratings_df['userId'].nunique()}")
            print(f"评分范围: {self.ratings_df['rating'].min()} - {self.ratings_df['rating'].max()}")
            
            return self.movies_df, self.ratings_df
            
        except FileNotFoundError as e:
            print(f"数据文件未找到: {e}")
            # 如果文件不存在，生成示例数据
            return self._generate_sample_data()
    
    def _generate_sample_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        生成示例数据用于演示
        """
        print("生成示例数据用于演示...")
        
        # 生成电影数据
        movies_data = {
            'movieId': range(1, 101),
            'title': [f'Movie {i}' for i in range(1, 101)],
            'genres': ['Action|Adventure' if i % 3 == 0 else 
                      'Comedy|Drama' if i % 3 == 1 else 
                      'Thriller|Crime' for i in range(100)]
        }
        
        # 生成评分数据
        np.random.seed(42)
        ratings_data = {
            'userId': np.random.randint(1, 51, 1000),
            'movieId': np.random.randint(1, 101, 1000),
            'rating': np.random.uniform(0.5, 5.0, 1000).round(1),
            'timestamp': np.random.randint(900000000, 1000000000, 1000)
        }
        
        self.movies_df = pd.DataFrame(movies_data)
        self.ratings_df = pd.DataFrame(ratings_data)
        
        return self.movies_df, self.ratings_df
    
    def get_user_item_matrix(self) -> pd.DataFrame:
        """
        获取用户-物品矩阵
        
        Returns:
            用户-物品矩阵
        """
        if self.ratings_df is None:
            raise ValueError("请先加载数据")
        
        # 创建用户-物品矩阵
        user_item_matrix = self.ratings_df.pivot(
            index='userId',
            columns='movieId',
            values='rating'
        ).fillna(0)
        
        return user_item_matrix
    
    def get_movie_info(self, movie_id: int) -> Dict:
        """
        获取电影详细信息
        
        Args:
            movie_id: 电影ID
            
        Returns:
            电影信息字典
        """
        if self.movies_df is None:
            raise ValueError("请先加载数据")
        
        movie = self.movies_df[self.movies_df['movieId'] == movie_id]
        
        if len(movie) == 0:
            return {}
        
        return movie.iloc[0].to_dict()
```

**utils/preprocessing.py**
```python
"""
数据预处理模块
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple, List, Dict
import re

class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self):
        self.user_encoder = LabelEncoder()
        self.item_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        
    def preprocess_ratings(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """
        预处理评分数据
        
        Args:
            ratings_df: 原始评分数据
            
        Returns:
            预处理后的评分数据
        """
        df = ratings_df.copy()
        
        # 编码用户ID和物品ID
        df['user_encoded'] = self.user_encoder.fit_transform(df['userId'])
        df['item_encoded'] = self.item_encoder.fit_transform(df['movieId'])
        
        # 标准化评分
        if len(df) > 1:
            df['rating_scaled'] = self.scaler.fit_transform(df[['rating']])
        else:
            df['rating_scaled'] = df['rating']
        
        return df
    
    def preprocess_movies(self, movies_df: pd.DataFrame) -> pd.DataFrame:
        """
        预处理电影数据
        
        Args:
            movies_df: 原始电影数据
            
        Returns:
            预处理后的电影数据
        """
        df = movies_df.copy()
        
        # 解析电影类型
        if 'genres' in df.columns:
            df['genres_list'] = df['genres'].apply(lambda x: x.split('|'))
            df['num_genres'] = df['genres_list'].apply(len)
            
            # 创建类型特征
            all_genres = set()
            for genres in df['genres_list']:
                all_genres.update(genres)
            
            for genre in all_genres:
                df[f'genre_{genre}'] = df['genres_list'].apply(
                    lambda x: 1 if genre in x else 0
                )
        
        # 提取年份（从标题中）
        if 'title' in df.columns:
            df['year'] = df['title'].apply(self._extract_year)
        
        return df
    
    def _extract_year(self, title: str) -> int:
        """
        从电影标题中提取年份
        
        Args:
            title: 电影标题
            
        Returns:
            年份，如果提取失败返回NaN
        """
        match = re.search(r'\((\d{4})\)', title)
        if match:
            return int(match.group(1))
        return np.nan
    
    def split_data(self, ratings_df: pd.DataFrame, 
                   test_size: float = 0.2, 
                   random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        划分训练集和测试集
        
        Args:
            ratings_df: 评分数据
            test_size: 测试集比例
            random_state: 随机种子
            
        Returns:
            train_df, test_df
        """
        train_df, test_df = train_test_split(
            ratings_df,
            test_size=test_size,
            random_state=random_state,
            stratify=ratings_df['userId'] if 'userId' in ratings_df.columns else None
        )
        
        return train_df, test_df
    
    def create_feature_matrix(self, movies_df: pd.DataFrame) -> np.ndarray:
        """
        创建电影特征矩阵（用于内容推荐）
        
        Args:
            movies_df: 预处理后的电影数据
            
        Returns:
            特征矩阵
        """
        # 选择数值特征列
        feature_cols = [col for col in movies_df.columns 
                       if col.startswith('genre_') or col == 'year' or col == 'num_genres']
        
        if not feature_cols:
            # 如果没有特征列，返回空数组
            return np.array([])
        
        # 提取特征并处理缺失值
        features = movies_df[feature_cols].fillna(0).values
        
        # 标准化特征
        if len(features) > 1:
            features = self.scaler.fit_transform(features)
        
        return features
    
    def get_user_history(self, ratings_df: pd.DataFrame, 
                         user_id: int, 
                         min_rating: float = 3.5) -> List[int]:
        """
        获取用户历史喜欢的电影列表
        
        Args:
            ratings_df: 评分数据
            user_id: 用户ID
            min_rating: 最低评分阈值
            
        Returns:
            用户喜欢的电影ID列表
        """
        user_ratings = ratings_df[
            (ratings_df['userId'] == user_id) & 
            (ratings_df['rating'] >= min_rating)
        ]
        
        return user_ratings['movieId'].tolist()
```

**utils/metrics.py**
```python
"""
推荐系统评估指标模块
"""
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict

class RecommendationMetrics:
    """推荐系统评估指标类"""
    
    @staticmethod
    def rmse(predictions: np.ndarray, actuals: np.ndarray) -> float:
        """
        计算均方根误差
        
        Args:
            predictions: 预测评分
            actuals: 实际评分
            
        Returns:
            RMSE值
        """
        return np.sqrt(np.mean((predictions - actuals) ** 2))
    
    @staticmethod
    def mae(predictions: np.ndarray, actuals: np.ndarray) -> float:
        """
        计算平均绝对误差
        
        Args:
            predictions: 预测评分
            actuals: 实际评分
            
        Returns:
            MAE值
        """
        return np.mean(np.abs(predictions - actuals))
    
    @staticmethod
    def precision_at_k(recommended: List[int], 
                       relevant: List[int], 
                       k: int = 10) -> float:
        """
        计算精确率@K
        
        Args:
            recommended: 推荐列表
            relevant: 相关物品列表
            k: 推荐列表长度
            
        Returns:
            精确率@K
        """
        if not recommended or not relevant:
            return 0.0
        
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        recommended_set = set(recommended_k)
        
        relevant_recommended = len(relevant_set.intersection(recommended_set))
        
        return relevant_recommended / k
    
    @staticmethod
    def recall_at_k(recommended: List[int], 
                    relevant: List[int], 
                    k: int = 10) -> float:
        """
        计算召回率@K
        
        Args:
            recommended: 推荐列表
            relevant: 相关物品列表
            k: 推荐列表长度
            
        Returns:
            召回率@K
        """
        if not recommended or not relevant:
            return 0.0
        
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        recommended_set = set(recommended_k)
        
        relevant_recommended = len(relevant_set.intersection(recommended_set))
        
        return relevant_recommended / len(relevant_set)
    
    @staticmethod
    def ndcg_at_k(recommended: List[int], 
                  relevant: List[int], 
                  k: int = 10) -> float:
        """
        计算归一化折损累积增益@K
        
        Args:
            recommended: 推荐列表
            relevant: 相关物品列表
            k: 推荐列表长度
            
        Returns:
            NDCG@K值
        """
        if not recommended or not relevant:
            return 0.0
        
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        
        # 计算DCG
        dcg = 0.0
        for i, item in enumerate(recommended_k):
            if item in relevant_set:
                dcg += 1.0 / np.log2(i + 2)  # i+2 因为索引从0开始
        
        # 计算IDCG（理想情况下的DCG）
        idcg = 0.0
        for i in range(min(k, len(relevant))):
            idcg += 1.0 / np.log2(i + 2)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def hit_rate_at_k(recommended_lists: List[List[int]], 
                      relevant_lists: List[List[int]], 
                      k: int = 10) -> float:
        """
        计算命中率@K
        
        Args:
            recommended_lists: 所有用户的推荐列表
            relevant_lists: 所有用户的相关物品列表
            k: 推荐列表长度
            
        Returns:
            命中率@K
        """
        hits = 0
        total_users = len(recommended_lists)
        
        for rec_list, rel_list in zip(recommended_lists, relevant_lists):
            rec_k = set(rec_list[:k])
            rel_set = set(rel_list)
            
            if len(rec_k.intersection(rel_set)) > 0:
                hits += 1
        
        return hits / total_users if total_users > 0 else 0.0
    
    @staticmethod
    def coverage(recommended_lists: List[List[int]], 
                 total_items: int, 
                 k: int = 10) -> float:
        """
        计算覆盖率
        
        Args:
            recommended_lists: 所有用户的推荐列表
            total_items: 总物品数
            k: 推荐列表长度
            
        Returns:
            覆盖率
        """
        recommended_items = set()
        
        for rec_list in recommended_lists:
            recommended_items.update(rec_list[:k])
        
        return len(recommended_items) / total_items if total_items > 0 else 0.0
    
    @staticmethod
    def diversity(recommended_list: List[int], 
                  similarity_matrix: np.ndarray, 
                  item_id_map: Dict[int, int]) -> float:
        """
        计算推荐多样性（基于物品相似度）
        
        Args:
            recommended_list: 推荐列表
            similarity_matrix: 物品相似度矩阵
            item_id_map: 物品ID到矩阵索引的映射
            
        Returns:
            多样性值（越高越多样）
        """
        if len(recommended_list) < 2:
            return 0.0
        
        # 获取推荐物品的索引
        indices = []
        for item_id in recommended_list:
            if item_id in item_id_map:
                indices.append(item_id_map[item_id])
        
        if len(indices) < 2:
            return 0.0
        
        # 计算平均相似度
        total_similarity = 0.0
        count = 0
        
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx_i = indices[i]
                idx_j = indices[j]
                
                if idx_i < similarity_matrix.shape[0] and idx_j < similarity_matrix.shape[1]:
                    total_similarity += similarity_matrix[idx_i, idx_j]
                    count += 1
        
        if count == 0:
            return 0.0
        
        avg_similarity = total_similarity / count
        diversity_score = 1.0 - avg_similarity
        
        return diversity_score
    
    @staticmethod
    def evaluate_all_metrics(predictions: np.ndarray, 
                             actuals: np.ndarray, 
                             recommended_lists: List[List[int]] = None,
                             relevant_lists: List[List[int]] = None,
                             k: int = 10) -> Dict[str, float]:
        """
        计算所有评估指标
        
        Args:
            predictions: 预测评分
            actuals: 实际评分
            recommended_lists: 推荐列表（可选）
            relevant_lists: 相关物品列表（可选）
            k: 推荐列表长度
            
        Returns:
            评估指标字典
        """
        metrics = {
            'rmse': RecommendationMetrics.rmse(predictions, actuals),
            'mae': RecommendationMetrics.mae(predictions, actuals)
        }
        
        if recommended_lists and relevant_lists:
            precisions = []
            recalls = []
            ndcgs = []
            
            for rec_list, rel_list in zip(recommended_lists, relevant_lists):
                precisions.append(RecommendationMetrics.precision_at_k(rec_list, rel_list, k))
                recalls.append(RecommendationMetrics.recall_at_k(rec_list, rel_list, k))
                ndcgs.append(RecommendationMetrics.ndcg_at_k(rec_list, rel_list, k))
            
            metrics.update({
                f'precision@{k}': np.mean(precisions),
                f'recall@{k}': np.mean(recalls),
                f'ndcg@{k}': np.mean(ndcgs),
                f'hit_rate@{k}': RecommendationMetrics.hit_rate_at_k(recommended_lists, relevant_lists, k)
            })
        
        return metrics
```

## 3. 推荐算法模型

**models/__init__.py**
```python
"""
推荐算法模型模块
"""
from .collaborative_filtering import CollaborativeFiltering
from .content_based import ContentBasedRecommender
from .deep_learning import DeepLearningRecommender
```

**models/collaborative_filtering.py**
```python
"""
协同过滤算法实现
"""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import TruncatedSVD
from surprise import Dataset, Reader, SVD, KNNBasic, NMF
from surprise.model_selection import cross_validate
from typing import List, Dict, Tuple, Optional
import pickle

class CollaborativeFiltering:
    """协同过滤推荐算法"""
    
    def __init__(self, method: str = 'svd', n_factors: int = 50, n_neighbors: int = 20):
        """
        初始化协同过滤算法
        
        Args:
            method: 算法方法，可选 'svd', 'knn', 'nmf'
            n_factors: 隐因子数量（用于SVD和NMF）
            n_neighbors: 最近邻数量（用于KNN）
        """
        self.method = method
        self.n_factors = n_factors
        self.n_neighbors = n_neighbors
        self.model = None
        self.trainset = None
        self.user_item_matrix = None
        self.user_similarity = None
        self.item_similarity = None
        
    def fit(self, ratings_df: pd.DataFrame, user_col: str = 'userId', 
            item_col: str = 'movieId', rating_col: str = 'rating'):
        """
        训练协同过滤模型
        
        Args:
            ratings_df: 评分数据
            user_col: 用户ID列名
            item_col: 物品ID列名
            rating_col: 评分列名
        """
        # 创建数据集
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(ratings_df[[user_col, item_col, rating_col]], reader)
        
        # 根据选择的方法训练模型
        if self.method == 'svd':
            self.model = SVD(n_factors=self.n_factors, random_state=42)
        elif self.method == 'knn':
            self.model = KNNBasic(k=self.n_neighbors, sim_options={'name': 'cosine', 'user_based': True})
        elif self.method == 'nmf':
            self.model = NMF(n_factors=self.n_factors, random_state=42)
        else:
            raise ValueError(f"不支持的方法: {self.method}")
        
        # 训练模型
        trainset = data.build_full_trainset()
        self.model.fit(trainset)
        self.trainset = trainset
        
        # 构建用户-物品矩阵（用于相似度计算）
        self._build_similarity_matrices(ratings_df, user_col, item_col, rating_col)
        
        print(f"{self.method.upper()} 模型训练完成")
        
    def _build_similarity_matrices(self, ratings_df: pd.DataFrame, 
                                   user_col: str, item_col: str, rating_col: str):
        """
        构建相似度矩阵
        """
        # 创建用户-物品矩阵
        self.user_item_matrix = ratings_df.pivot(
            index=user_col,
            columns=item_col,
            values=rating_col
        ).fillna(0)
        
        # 转换为稀疏矩阵
        sparse_matrix = csr_matrix(self.user_item_matrix.values)
        
        # 计算用户相似度（基于余弦相似度）
        user_similarity = NearestNeighbors(
            n_neighbors=min(self.n_neighbors, len(self.user_item_matrix) - 1),
            metric='cosine',
            algorithm='brute'
        )
        user_similarity.fit(sparse_matrix)
        self.user_similarity = user_similarity
        
        # 计算物品相似度
        item_similarity = NearestNeighbors(
            n_neighbors=min(self.n_neighbors, len(self.user_item_matrix.columns) - 1),
            metric='cosine',
            algorithm='brute'
        )
        item_similarity.fit(sparse_matrix.T)
        self.item_similarity = item_similarity
        
    def predict(self, user_id: int, item_id: int) -> float:
        """
        预测单个用户对单个物品的评分
        
        Args:
            user_id: 用户ID
            item_id: 物品ID
            
        Returns:
            预测评分
        """
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        try:
            prediction = self.model.predict(user_id, item_id)
            return prediction.est
        except:
            return 3.0  # 返回默认评分
    
    def recommend(self, user_id: int, n_recommendations: int = 10, 
                  exclude_rated: bool = True) -> List[Tuple[int, float]]:
        """
        为用户生成推荐列表
        
        Args:
            user_id: 用户ID
            n_recommendations: 推荐数量
            exclude_rated: 是否排除已评分物品
            
        Returns:
            推荐列表，每个元素为(物品ID, 预测评分)
        """
        if self.model is None or self.trainset is None:
            raise ValueError("模型尚未训练")
        
        # 获取所有物品ID
        all_items = [self.trainset.to_raw_iid(i) for i in self.trainset.all_items()]
        
        # 获取用户已评分的物品
        rated_items = set()
        if exclude_rated:
            try:
                user_inner_id = self.trainset.to_inner_uid(user_id)
                rated_items = set(self.trainset.ur[user_inner_id])
                rated_items = set([self.trainset.to_raw_iid(i) for i, _ in rated_items])
            except:
                pass
        
        # 预测评分
        predictions = []
        for item_id in all_items:
            if item_id not in rated_items:
                pred = self.predict(user_id, item_id)
                predictions.append((item_id, pred))
        
        # 按评分排序并返回Top-N
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:n_recommendations]
    
    def get_similar_users(self, user_id: int, n_users: int = 10) -> List[int]:
        """
        获取相似用户
        
        Args:
            user_id: 用户ID
            n_users: 相似用户数量
            
        Returns:
            相似用户ID列表
        """
        if self.user_similarity is None:
            raise ValueError("相似度矩阵尚未构建")
        
        try:
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            distances, indices = self.user_similarity.kneighbors(
                self.user_item_matrix.iloc[user_idx, :].values.reshape(1, -1),
                n_neighbors=n_users + 1
            )
            
            # 排除自己
            similar_users = []
            for idx in indices[0][1:]:
                similar_users.append(self.user_item_matrix.index[idx])
            
            return similar_users
        except:
            return []
    
    def get_similar_items(self, item_id: int, n_items: int = 10) -> List[int]:
        """
        获取相似物品
        
        Args:
            item_id: 物品ID
            n_items: 相似物品数量
            
        Returns:
            相似物品ID列表
        """
        if self.item_similarity is None:
            raise ValueError("相似度矩阵尚未构建")
        
        try:
            item_idx = self.user_item_matrix.columns.get_loc(item_id)
            distances, indices = self.item_similarity.kneighbors(
                self.user_item_matrix.iloc[:, item_idx].values.reshape(1, -1),
                n_neighbors=n_items + 1
            )
            
            # 排除自己
            similar_items = []
            for idx in indices[0][1:]:
                similar_items.append(self.user_item_matrix.columns[idx])
            
            return similar_items
        except:
            return []
    
    def save_model(self, filepath: str):
        """保存模型"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
    
    @classmethod
    def load_model(cls, filepath: str):
        """加载模型"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)
```

**models/content_based.py**
```python
"""
基于内容的推荐算法实现
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from sklearn.decomposition import TruncatedSVD
from typing import List, Dict, Tuple, Optional
import pickle

class ContentBasedRecommender:
    """基于内容的推荐算法"""
    
    def __init__(self, feature_type: str = 'tfidf', n_components: int = 100):
        """
        初始化基于内容的推荐算法
        
        Args:
            feature_type: 特征类型，可选 'tfidf', 'count', 'binary'
            n_components: 降维维度（用于LSA）
        """
        self.feature_type = feature_type
        self.n_components = n_components
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.item_features = None
        self.item_ids = None
        self.movies_df = None
        
    def fit(self, movies_df: pd.DataFrame, 
            content_col: str = 'genres',
            item_col: str = 'movieId'):
        """
        训练基于内容的推荐模型
        
        Args:
            movies_df: 电影数据
            content_col: 内容特征列名
            item_col: 物品ID列名
        """
        self.movies_df = movies_df.copy()
        self.item_ids = movies_df[item_col].values
        
        # 准备内容特征
        if content_col in movies_df.columns:
            # 将内容特征转换为字符串
            content_series = movies_df[content_col].fillna('')
            
            if self.feature_type == 'tfidf':
                self.tfidf_vectorizer = TfidfVectorizer(
                    stop_words='english',
                    max_features=5000
                )
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(content_series)
                
                # 使用LSA降维
                if self.n_components < self.tfidf_matrix.shape[1]:
                    svd = TruncatedSVD(n_components=self.n_components, random_state=42)
                    self.item_features = svd.fit_transform(self.tfidf_matrix)
                else:
                    self.item_features = self.tfidf_matrix.toarray()
            else:
                # 简单的二元特征
                self.item_features = np.zeros((len(movies_df), 0))
        
        print(f"基于内容的推荐模型训练完成，特征维度: {self.item_features.shape}")
    
    def get_item_similarity(self, item_id: int, n_items: int = 10) -> List[Tuple[int, float]]:
        """
        获取与指定物品最相似的物品
        
        Args:
            item_id: 物品ID
            n_items: 相似物品数量
            
        Returns:
            相似物品列表，每个元素为(物品ID, 相似度)
        """
        if self.item_features is None:
            raise ValueError("模型尚未训练")
        
        try:
            item_idx = np.where(self.item_ids == item_id)[0][0]
        except IndexError:
            return []
        
        # 计算相似度
        item_vector = self.item_features[item_idx].reshape(1, -1)
        similarities = cosine_similarity(item_vector, self.item_features)[0]
        
        # 排序并返回Top-N
        similar_indices = np.argsort(similarities)[::-1][1:n_items+1]
        
        similar_items = []
        for idx in similar_indices:
            if similarities[idx] > 0:  # 只返回正相似度
                similar_items.append((self.item_ids[idx], similarities[idx]))
        
        return similar_items
    
    def recommend_for_user(self, user_history: List[int], 
                           n_recommendations: int = 10,
                           diversity_weight: float = 0.3) -> List[Tuple[int, float]]:
        """
        基于用户历史为用户生成推荐
        
        Args:
            user_history: 用户历史喜欢的物品ID列表
            n_recommendations: 推荐数量
            diversity_weight: 多样性权重（0-1）
            
        Returns:
            推荐列表
        """
        if self.item_features is None:
            raise ValueError("模型尚未训练")
        
        if not user_history:
            # 如果没有历史，返回流行物品
            return self.get_popular_items(n_recommendations)
        
        # 获取用户历史物品的索引
        history_indices = []
        for item_id in user_history:
            try:
                idx = np.where(self.item_ids == item_id)[0][0]
                history_indices.append(idx)
            except IndexError:
                continue
        
        if not history_indices:
            return self.get_popular_items(n_recommendations)
        
        # 计算用户特征向量（历史物品特征的平均）
        user_vector = np.mean(self.item_features[history_indices], axis=0).reshape(1, -1)
        
        # 计算候选物品与用户特征的相似度
        similarities = cosine_similarity(user_vector, self.item_features)[0]
        
        # 创建候选物品列表（排除已交互物品）
        candidates = []
        for i, item_id in enumerate(self.item