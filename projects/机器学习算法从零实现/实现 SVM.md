# 实现 SVM

**任务**: 机器学习算法从零实现
**时间**: 2026-06-04T23:19:37.833893

# 机器学习算法从零实现：支持向量机(SVM)完整实现

## 1. SVM算法概述

支持向量机(Support Vector Machine, SVM)是一种强大的监督学习算法，主要用于分类和回归分析。SVM的核心思想是寻找一个最优超平面，使得不同类别的样本能够被正确分开，并且使得分类间隔(margin)最大化。

### 1.1 SVM基本原理

对于线性可分数据，SVM寻找一个超平面 \(w^Tx + b = 0\)，使得：
- 正样本满足 \(w^Tx + b \geq 1\)
- 负样本满足 \(w^Tx + b \leq -1\)

最大化间隔等价于最小化 \(\frac{1}{2}\|w\|^2\)，这是一个凸优化问题。

### 1.2 对偶问题与核技巧

通过拉格朗日乘子法，原问题转化为对偶问题：
\[
\max_{\alpha} \sum_{i=1}^n \alpha_i - \frac{1}{2} \sum_{i=1}^n \sum_{j=1}^n \alpha_i \alpha_j y_i y_j x_i^T x_j
\]
约束条件为：
\[
0 \leq \alpha_i \leq C, \quad \sum_{i=1}^n \alpha_i y_i = 0
\]

对于非线性可分数据，引入核函数 \(K(x_i, x_j) = \phi(x_i)^T \phi(x_j)\) 将数据映射到高维空间。

## 2. 完整实现代码

我们将实现以下组件：
1. SVM分类器（线性核和RBF核）
2. SMO算法求解器
3. 训练和预测功能
4. 辅助工具函数

```python
"""
支持向量机(SVM)从零实现
使用SMO算法进行优化
支持线性核和RBF核
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List, Optional
import time

class SVM:
    """支持向量机分类器"""
    
    def __init__(self, kernel='linear', C=1.0, tol=1e-3, max_iter=1000, gamma=1.0):
        """
        初始化SVM分类器
        
        参数:
        kernel: 核函数类型 ('linear', 'rbf')
        C: 正则化参数
        tol: 收敛容差
        max_iter: 最大迭代次数
        gamma: RBF核的参数
        """
        self.kernel = kernel
        self.C = C
        self.tol = tol
        self.max_iter = max_iter
        self.gamma = gamma
        self.alphas = None
        self.b = 0
        self.X_train = None
        self.y_train = None
        self.support_vectors = None
        self.support_vector_labels = None
        self.support_vector_alphas = None
        
    def _kernel_function(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算核函数
        
        参数:
        x1, x2: 输入向量
        
        返回:
        核函数值
        """
        if self.kernel == 'linear':
            return np.dot(x1, x2)
        elif self.kernel == 'rbf':
            return np.exp(-self.gamma * np.linalg.norm(x1 - x2)**2)
        else:
            raise ValueError(f"不支持的核函数类型: {self.kernel}")
    
    def _compute_kernel_matrix(self, X: np.ndarray) -> np.ndarray:
        """
        计算核矩阵
        
        参数:
        X: 数据矩阵
        
        返回:
        核矩阵
        """
        n_samples = X.shape[0]
        K = np.zeros((n_samples, n_samples))
        for i in range(n_samples):
            for j in range(n_samples):
                K[i, j] = self._kernel_function(X[i], X[j])
        return K
    
    def _select_j(self, i: int, n_samples: int) -> int:
        """
        随机选择第二个变量j（不同于i）
        
        参数:
        i: 第一个变量的索引
        n_samples: 样本总数
        
        返回:
        第二个变量的索引
        """
        j = i
        while j == i:
            j = np.random.randint(0, n_samples)
        return j
    
    def _clip_alpha(self, alpha_j: float, L: float, H: float) -> float:
        """
        裁剪alpha_j到[L, H]范围内
        
        参数:
        alpha_j: 原始alpha值
        L, H: 下界和上界
        
        返回:
        裁剪后的alpha值
        """
        if alpha_j > H:
            return H
        elif alpha_j < L:
            return L
        else:
            return alpha_j
    
    def _take_step(self, i: int, j: int) -> bool:
        """
        SMO算法的主要步骤：更新alpha_i和alpha_j
        
        参数:
        i, j: 两个变量的索引
        
        返回:
        是否更新成功
        """
        if i == j:
            return False
        
        alpha_i_old = self.alphas[i].copy()
        alpha_j_old = self.alphas[j].copy()
        
        y_i = self.y_train[i]
        y_j = self.y_train[j]
        
        # 计算误差
        E_i = self._svm_predict(i) - y_i
        E_j = self._svm_predict(j) - y_j
        
        # 计算边界L和H
        if y_i != y_j:
            L = max(0, alpha_j_old - alpha_i_old)
            H = min(self.C, self.C + alpha_j_old - alpha_i_old)
        else:
            L = max(0, alpha_j_old + alpha_i_old - self.C)
            H = min(self.C, alpha_j_old + alpha_i_old)
        
        if L == H:
            return False
        
        # 计算eta
        K_ii = self.K[i, i]
        K_jj = self.K[j, j]
        K_ij = self.K[i, j]
        
        eta = 2 * K_ij - K_ii - K_jj
        
        if eta >= 0:
            return False
        
        # 更新alpha_j
        alpha_j_new = alpha_j_old - y_j * (E_i - E_j) / eta
        alpha_j_new = self._clip_alpha(alpha_j_new, L, H)
        
        # 检查是否有显著变化
        if abs(alpha_j_new - alpha_j_old) < self.tol * (alpha_j_new + alpha_j_old + self.tol):
            return False
        
        # 更新alpha_i
        alpha_i_new = alpha_i_old + y_i * y_j * (alpha_j_old - alpha_j_new)
        
        # 更新阈值b
        b1 = self.b - E_i - y_i * (alpha_i_new - alpha_i_old) * K_ii - y_j * (alpha_j_new - alpha_j_old) * K_ij
        b2 = self.b - E_j - y_i * (alpha_i_new - alpha_i_old) * K_ij - y_j * (alpha_j_new - alpha_j_old) * K_jj
        
        if 0 < alpha_i_new < self.C:
            self.b = b1
        elif 0 < alpha_j_new < self.C:
            self.b = b2
        else:
            self.b = (b1 + b2) / 2
        
        # 更新alpha值
        self.alphas[i] = alpha_i_new
        self.alphas[j] = alpha_j_new
        
        return True
    
    def _svm_predict(self, idx: int) -> float:
        """
        对单个样本进行预测（使用核技巧）
        
        参数:
        idx: 样本索引
        
        返回:
        预测值（未符号化）
        """
        prediction = 0.0
        for j in range(len(self.alphas)):
            if self.alphas[j] > 0:
                prediction += self.alphas[j] * self.y_train[j] * self.K[idx, j]
        prediction += self.b
        return prediction
    
    def _examine_example(self, i: int) -> bool:
        """
        检查并更新样本i
        
        参数:
        i: 样本索引
        
        返回:
        是否更新成功
        """
        y_i = self.y_train[i]
        alpha_i = self.alphas[i]
        E_i = self._svm_predict(i) - y_i
        
        if ((y_i * E_i < -self.tol and alpha_i < self.C) or 
            (y_i * E_i > self.tol and alpha_i > 0)):
            
            # 选择启发式方法选择第二个变量
            # 首先尝试选择使|E_i - E_j|最大的j
            max_diff = -1
            max_j = -1
            
            for j in range(len(self.alphas)):
                if self.alphas[j] > 0 and self.alphas[j] < self.C:
                    E_j = self._svm_predict(j) - self.y_train[j]
                    diff = abs(E_i - E_j)
                    if diff > max_diff:
                        max_diff = diff
                        max_j = j
            
            if max_j != -1 and self._take_step(i, max_j):
                return True
            
            # 如果启发式方法失败，随机选择
            j = self._select_j(i, len(self.alphas))
            if self._take_step(i, j):
                return True
            
            # 如果随机选择也失败，尝试所有非边界样本
            for j in np.random.permutation(len(self.alphas)):
                if 0 < self.alphas[j] < self.C:
                    if self._take_step(i, j):
                        return True
        
        return False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'SVM':
        """
        训练SVM模型
        
        参数:
        X: 训练数据特征矩阵
        y: 训练数据标签（-1或1）
        
        返回:
        self: 训练后的SVM实例
        """
        start_time = time.time()
        
        self.X_train = X.copy()
        self.y_train = y.copy()
        n_samples = X.shape[0]
        
        # 初始化alpha值为0
        self.alphas = np.zeros(n_samples)
        
        # 计算核矩阵
        print("计算核矩阵...")
        self.K = self._compute_kernel_matrix(X)
        
        # 主循环：SMO算法
        num_changed = 0
        examine_all = True
        iteration = 0
        
        while (num_changed > 0 or examine_all) and iteration < self.max_iter:
            num_changed = 0
            
            if examine_all:
                # 遍历所有样本
                for i in range(n_samples):
                    if self._examine_example(i):
                        num_changed += 1
                iteration += 1
            else:
                # 只遍历非边界样本（0 < alpha < C）
                non_bound_indices = np.where((self.alphas > 0) & (self.alphas < self.C))[0]
                for i in non_bound_indices:
                    if self._examine_example(i):
                        num_changed += 1
                iteration += 1
            
            if examine_all:
                examine_all = False
            elif num_changed == 0:
                examine_all = True
            
            # 打印进度
            if iteration % 10 == 0:
                print(f"迭代 {iteration}: 改变了 {num_changed} 个alpha值")
        
        # 提取支持向量
        support_mask = self.alphas > self.tol
        self.support_vectors = X[support_mask]
        self.support_vector_labels = y[support_mask]
        self.support_vector_alphas = self.alphas[support_mask]
        
        # 计算训练准确率
        train_accuracy = self.score(X, y)
        
        end_time = time.time()
        print(f"训练完成! 耗时: {end_time - start_time:.2f}秒")
        print(f"支持向量数量: {len(self.support_vectors)}")
        print(f"训练准确率: {train_accuracy:.4f}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        对新数据进行预测
        
        参数:
        X: 测试数据特征矩阵
        
        返回:
        预测标签数组
        """
        predictions = []
        for x in X:
            prediction = 0.0
            for sv, sv_label, sv_alpha in zip(
                self.support_vectors, 
                self.support_vector_labels, 
                self.support_vector_alphas
            ):
                prediction += sv_alpha * sv_label * self._kernel_function(x, sv)
            prediction += self.b
            predictions.append(np.sign(prediction))
        
        return np.array(predictions)
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算准确率
        
        参数:
        X: 测试数据特征矩阵
        y: 真实标签
        
        返回:
        准确率
        """
        predictions = self.predict(X)
        accuracy = np.mean(predictions == y)
        return accuracy


class LinearSVM:
    """线性SVM分类器（使用对偶形式）"""
    
    def __init__(self, C=1.0, tol=1e-4, max_iter=1000):
        """
        初始化线性SVM分类器
        
        参数:
        C: 正则化参数
        tol: 收敛容差
        max_iter: 最大迭代次数
        """
        self.C = C
        self.tol = tol
        self.max_iter = max_iter
        self.alphas = None
        self.w = None
        self.b = 0
        self.support_vectors = None
        self.support_vector_labels = None
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LinearSVM':
        """
        训练线性SVM模型
        
        参数:
        X: 训练数据特征矩阵
        y: 训练数据标签（-1或1）
        
        返回:
        self: 训练后的LinearSVM实例
        """
        n_samples, n_features = X.shape
        
        # 初始化alpha值
        self.alphas = np.zeros(n_samples)
        
        # 使用简单的启发式方法优化（简化版SMO）
        # 注意：这是一个简化的实现，对于大规模数据可能效率不高
        
        changed = True
        iteration = 0
        
        while changed and iteration < self.max_iter:
            changed = False
            
            for i in range(n_samples):
                # 计算当前样本的预测值
                prediction_i = np.dot(X[i], self._compute_w(X, y)) + self.b
                
                # 计算误差
                E_i = prediction_i - y[i]
                
                # 检查是否违反KKT条件
                if ((y[i] * E_i < -self.tol and self.alphas[i] < self.C) or 
                    (y[i] * E_i > self.tol and self.alphas[i] > 0)):
                    
                    # 选择第二个变量
                    j = np.random.choice([x for x in range(n_samples) if x != i])
                    
                    prediction_j = np.dot(X[j], self._compute_w(X, y)) + self.b
                    E_j = prediction_j - y[j]
                    
                    # 保存旧的alpha值
                    alpha_i_old = self.alphas[i].copy()
                    alpha_j_old = self.alphas[j].copy()
                    
                    # 计算边界L和H
                    if y[i] != y[j]:
                        L = max(0, self.alphas[j] - self.alphas[i])
                        H = min(self.C, self.C + self.alphas[j] - self.alphas[i])
                    else:
                        L = max(0, self.alphas[i] + self.alphas[j] - self.C)
                        H = min(self.C, self.alphas[i] + self.alphas[j])
                    
                    if L == H:
                        continue
                    
                    # 计算eta
                    eta = 2 * np.dot(X[i], X[j]) - np.dot(X[i], X[i]) - np.dot(X[j], X[j])
                    
                    if eta >= 0:
                        continue
                    
                    # 更新alpha_j
                    self.alphas[j] = alpha_j_old - y[j] * (E_i - E_j) / eta
                    
                    # 裁剪alpha_j
                    self.alphas[j] = np.clip(self.alphas[j], L, H)
                    
                    # 检查是否有显著变化
                    if abs(self.alphas[j] - alpha_j_old) < self.tol:
                        continue
                    
                    # 更新alpha_i
                    self.alphas[i] = alpha_i_old + y[i] * y[j] * (alpha_j_old - self.alphas[j])
                    
                    # 更新阈值b
                    b1 = self.b - E_i - y[i] * (self.alphas[i] - alpha_i_old) * np.dot(X[i], X[i]) - \
                         y[j] * (self.alphas[j] - alpha_j_old) * np.dot(X[i], X[j])
                    b2 = self.b - E_j - y[i] * (self.alphas[i] - alpha_i_old) * np.dot(X[i], X[j]) - \
                         y[j] * (self.alphas[j] - alpha_j_old) * np.dot(X[j], X[j])
                    
                    if 0 < self.alphas[i] < self.C:
                        self.b = b1
                    elif 0 < self.alphas[j] < self.C:
                        self.b = b2
                    else:
                        self.b = (b1 + b2) / 2
                    
                    changed = True
            
            iteration += 1
            if iteration % 10 == 0:
                print(f"迭代 {iteration}")
        
        # 计算权重向量w
        self.w = self._compute_w(X, y)
        
        # 提取支持向量
        support_mask = self.alphas > self.tol
        self.support_vectors = X[support_mask]
        self.support_vector_labels = y[support_mask]
        
        # 计算训练准确率
        train_accuracy = self.score(X, y)
        print(f"训练完成! 支持向量数量: {len(self.support_vectors)}")
        print(f"训练准确率: {train_accuracy:.4f}")
        
        return self
    
    def _compute_w(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        计算权重向量w
        
        参数:
        X: 训练数据
        y: 标签
        
        返回:
        权重向量w
        """
        w = np.zeros(X.shape[1])
        for i in range(len(self.alphas)):
            w += self.alphas[i] * y[i] * X[i]
        return w
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        对新数据进行预测
        
        参数:
        X: 测试数据特征矩阵
        
        返回:
        预测标签数组
        """
        predictions = np.dot(X, self.w) + self.b
        return np.sign(predictions)
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算准确率
        
        参数:
        X: 测试数据特征矩阵
        y: 真实标签
        
        返回:
        准确率
        """
        predictions = self.predict(X)
        accuracy = np.mean(predictions == y)
        return accuracy


# 辅助函数
def generate_linearly_separable_data(n_samples: int = 100, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成线性可分的二维数据
    
    参数:
    n_samples: 样本数量
    random_state: 随机种子
    
    返回:
    X: 特征矩阵
    y: 标签
    """
    np.random.seed(random_state)
    
    # 正类
    X_pos = np.random.randn(n_samples // 2, 2) + [2, 2]
    y_pos = np.ones(n_samples // 2)
    
    # 负类
    X_neg = np.random.randn(n_samples // 2, 2) + [-2, -2]
    y_neg = -np.ones(n_samples // 2)
    
    X = np.vstack([X_pos, X_neg])
    y = np.hstack([y_pos, y_neg])
    
    return X, y


def generate_nonlinear_data(n_samples: int = 100, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成非线性可分的二维数据（圆形分布）
    
    参数:
    n_samples: 样本数量
    random_state: 随机种子
    
    返回:
    X: 特征矩阵
    y: 标签
    """
    np.random.seed(random_state)
    
    # 内部圆（正类）
    r_inner = np.random.uniform(0, 1, n_samples // 2)
    theta_inner = np.random.uniform(0, 2 * np.pi, n_samples // 2)
    X_inner = np.column_stack([r_inner * np.cos(theta_inner), r_inner * np.sin(theta_inner)])
    y_inner = np.ones(n_samples // 2)
    
    # 外部圆（负类）
    r_outer = np.random.uniform(2, 3, n_samples // 2)
    theta_outer = np.random.uniform(0, 2 * np.pi, n_samples // 2)
    X_outer = np.column_stack([r_outer * np.cos(theta_outer), r_outer * np.sin(theta_outer)])
    y_outer = -np.ones(n_samples // 2)
    
    X = np.vstack([X_inner, X_outer])
    y = np.hstack([y_inner, y_outer])
    
    return X, y


def plot_decision_boundary(model, X: np.ndarray, y: np.ndarray, title: str = "SVM Decision Boundary"):
    """
    绘制决策边界（仅适用于二维数据）
    
    参数:
    model: 训练好的SVM模型
    X: 特征矩阵
    y: 标签
    title: 图表标题
    """
    plt.figure(figsize=(10, 8))
    
    # 绘制数据点
    for i in range(len(X)):
        if y[i] == 1:
            plt.scatter(X[i, 0], X[i, 1], c='blue', marker='o', s=50, alpha=0.6, edgecolors='black')
        else:
            plt.scatter(X[i, 0], X[i, 1], c='red', marker='x', s=50, alpha=0.6, linewidths=2)
    
    # 创建网格点
    h = 0.02
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    
    # 预测网格点
    grid_points = np.c_[xx.ravel(), yy.ravel()]
    Z = model.predict(grid_points)
    Z = Z.reshape(xx.shape)
    
    # 绘制决策边界
    plt.contourf(xx, yy, Z, alpha=0.3, cmap=plt.cm.Paired)
    plt.contour(xx, yy, Z, colors='black', linewidths=0.5)
    
    # 如果模型有支持向量，绘制它们
    if hasattr(model, 'support_vectors'):
        sv = model.support_vectors
        plt.scatter(sv[:, 0], sv[:, 1], s=200, facecolors='none', 
                   edgecolors='green', linewidths=2, label='支持向量')
    
    plt.title(title)
    plt.xlabel('特征1')
    plt.ylabel('特征2')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def plot_training_process(losses: List[float], title: str = "Training Loss"):
    """
    绘制训练损失曲线
    
    参数:
    losses: 损失值列表
    title: 图表标题
    """
    plt.figure(figsize=(10, 6))
    plt.plot(losses)
    plt.title(title)
    plt.xlabel('迭代次数')
    plt.ylabel('损失')
    plt.grid(True, alpha=0.3)
    plt.show()


def save_model_to_file(model, filename: str):
    """
    将训练好的模型保存到文件
    
    参数:
    model: 训练好的模型
    filename: 保存文件名
    """
    import pickle
    
    # 准备模型数据
    model_data = {
        'model_type': type(model).__name__,
        'params': {}
    }
    
    # 根据模型类型保存参数
    if isinstance(model, SVM):
        model_data['params'] = {
            'kernel': model.kernel,
            'C': model.C,
            'tol': model.tol,
            'max_iter': model.max_iter,
            'gamma': model.gamma,
            'alphas': model.alphas.tolist(),
            'b': model.b,
            'X_train': model.X_train.tolist() if model.X_train is not None else None,
            'y_train': model.y_train.tolist() if model.y_train is not None else None,
            'support_vectors': model.support_vectors.tolist() if model.support_vectors is not None else None,
            'support_vector_labels': model.support_vector_labels.tolist() if model.support_vector_labels is not None else None,
            'support_vector_alphas': model.support_vector_alphas.tolist() if model.support_vector_alphas is not None else None
        }
    elif isinstance(model, LinearSVM):
        model_data['params'] = {
            'C': model.C,
            'tol': model.tol,
            'max_iter': model.max_iter,
            'alphas': model.alphas.tolist(),
            'w': model.w.tolist(),
            'b': model.b,
            'support_vectors': model.support_vectors.tolist() if model.support_vectors is not None else None,
            'support_vector_labels': model.support_vector_labels.tolist() if model.support_vector_labels is not None else None
        }
    
    # 保存到文件
    with open(filename, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"模型已保存到: {filename}")


def load_model_from_file(filename: str):
    """
    从文件加载模型
    
    参数:
    filename: 模型文件名
    
    返回:
    加载的模型
    """
    import pickle
    
    with open(filename, 'rb') as f:
        model_data = pickle.load(f)
    
    # 根据模型类型重建模型
    if model_data['model_type'] == 'SVM':
        model = SVM(
            kernel=model_data['params']['kernel'],
            C=model_data['params']['C'],
            tol=model_data['params']['tol'],
            max_iter=model_data['params']['max_iter'],
            gamma=model_data['params']['gamma']
        )
        model.alphas = np.array(model_data['params']['alphas'])
        model.b = model_data['params']['b']
        model.X_train = np.array(model_data['params']['X_train']) if model_data['params']['X_train'] is not None else None
        model.y_train = np.array(model_data['params']['y_train']) if model_data['params']['y_train'] is not None else None
        model.support_vectors = np.array(model_data['params']['support_vectors']) if model_data['params']['support_vectors'] is not None else None
        model.support_vector_labels = np.array(model_data['params']['support_vector_labels']) if model_data['params']['support_vector_labels'] is not None else None
        model.support_vector_alphas = np.array(model_data['params']['support_vector_alphas']) if model_data['params']['support_vector_alphas'] is not None else None
        
        # 重新计算核矩阵（如果需要）
        if model.X_train is not None:
            model.K = model._compute_kernel_matrix(model.X_train)
        
    elif model_data['model_type'] == 'LinearSVM':
        model = LinearSVM(
            C=model_data['params']['C'],
            tol=model_data['params']['tol'],
            max_iter=model_data['params']['max_iter']
        )
        model.alphas = np.array(model_data['params']['alphas'])
        model.w = np.array(model_data['params']['w'])
        model.b = model_data['params']['b']
        model.support_vectors = np.array(model_data['params']['support_vectors']) if model_data['params']['support_vectors'] is not None else None
        model.support_vector_labels = np.array(model_data['params']['support_vector_labels']) if model_data['params']['support_vector_labels'] is not None else None
    
    print(f"模型已从 {filename} 加载")
    return model
```

## 3. 使用示例和测试

```python
"""
SVM使用示例和测试
"""

def main():
    """主函数：演示SVM的使用"""
    
    print("=== SVM算法演示 ===\n")
    
    # 1. 生成线性可分数据
    print("1. 生成线性可分数据")
    X_linear, y_linear = generate_linearly_separable_data(n_samples=100)
    
    # 2. 训练线性SVM
    print("\n2. 训练线性SVM")
    linear_svm = LinearSVM(C=1.0, max_iter=100)
    linear_svm.fit(X_linear, y_linear)
    
    # 3. 绘制决策边界
    print("\n3. 绘制线性SVM决策边界")
    plot_decision_boundary(linear_svm, X_linear, y_linear, "线性SVM决策边界")
    
    # 4. 生成非线性数据
    print("\n4. 生成非线性可分数据（圆形分布）")
    X_nonlinear, y_nonlinear = generate_nonlinear_data(n_samples=150)
    
    # 5. 训练RBF核SVM
    print("\n5. 训练RBF核SVM")
    rbf_svm = SVM(kernel='rbf', C=1.0, gamma=0.5, max_iter=100)
    rbf_svm.fit(X_nonlinear, y_nonlinear)
    
    # 6. 绘制决策边界
    print("\n6. 绘制RBF核SVM决策边界")
    plot_decision_boundary(rbf_svm, X_nonlinear, y_nonlinear, "RBF核SVM决策边界")
    
    # 7. 保存模型
    print("\n7. 保存模型到文件")
    save_model_to_file(rbf_svm, "rbf_svm_model.pkl")
    
    # 8. 加载模型并测试
    print("\n8. 加载模型并测试")
    loaded_model = load_model_from_file("rbf_svm_model.pkl")
    test_accuracy = loaded_model.score(X_nonlinear, y_nonlinear)
    print(f"加载模型的测试准确率: {test_accuracy:.4f}")
    
    # 9. 性能评估
    print("\n9. 性能评估")
    # 分割数据为训练集和测试集
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X_nonlinear, y_nonlinear, test_size=0.2, random_state=42
    )
    
    # 在测试集上评估
    test_accuracy = rbf_svm.score(X_test, y_test)
    print(f"测试集准确率: {test_accuracy:.4f}")
    
    print("\n=== SVM演示完成 ===")


# 数据预处理工具
def normalize_features(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    特征标准化（均值归一化）
    
    参数:
    X: 特征矩阵
    
    返回:
    X_normalized: 标准化后的特征矩阵
    mean: 均值
    std: 标准差
    """
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    X_normalized = (X - mean) / (std + 1e-8)  # 添加小常数避免除零
    return X_normalized, mean, std


def split_data(X: np.ndarray, y: np.ndarray, test_size: float = 0.2, 
               random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    分割数据为训练集和测试集
    
    参数:
    X: 特征矩阵
    y: 标签
    test_size: 测试集比例
    random_state: 随机种子
    
    返回:
    X_train, X_test, y_train, y_test: 训练集和测试集
    """
    np.random.seed(random_state)
    n_samples = X.shape[0]
    indices = np.random.permutation(n_samples)
    
    n_test = int(n_samples * test_size)
    test_indices = indices[:n_test]
    train_indices = indices[n_test:]
    
    X_train = X[train_indices]
    X_test = X[test_indices]
    y_train = y[train_indices]
    y_test = y[test_indices]
    
    return X_train, X_test, y_train, y_test


# 评估指标
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    计算分类指标
    
    参数:
    y_true: 真实标签
    y_pred: 预测标签
    
    返回:
    metrics: 包含各种指标的字典
    """
    # 计算混淆矩阵
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == -1) & (y_pred == -1))
    fp = np.sum((y_true == -1) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == -1))
    
    # 计算指标
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) >