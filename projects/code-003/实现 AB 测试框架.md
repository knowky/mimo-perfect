# 实现 A/B 测试框架

**任务**: 机器学习推荐系统
**时间**: 2026-06-05T01:00:50.485968

# 机器学习推荐系统A/B测试框架实现

## 1. 项目概述

A/B测试框架是推荐系统中至关重要的组成部分，用于评估新算法、策略或功能变更的效果。本框架提供完整的A/B测试生命周期管理，包括实验设计、流量分配、指标收集、统计分析和结果可视化。

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    A/B 测试框架架构                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  实验配置   │  │  流量分配   │  │  指标收集   │     │
│  │   模块     │  │   模块     │  │   模块     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │              │              │                 │
│  ┌─────────────────────────────────────────────┐       │
│  │              核心数据处理层                   │       │
│  └─────────────────────────────────────────────┘       │
│         │              │              │                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  统计分析   │  │  结果评估   │  │  可视化     │     │
│  │   模块     │  │   模块     │  │   模块     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 3. 核心功能模块

### 3.1 实验配置管理

```python
# 文件: ab_test/config/experiment_config.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from datetime import datetime, timedelta

class TrafficAllocation(Enum):
    """流量分配策略"""
    RANDOM = "random"
    HASH_BASED = "hash_based"
    PERCENTAGE = "percentage"

class StatisticalTest(Enum):
    """统计检验方法"""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    Z_TEST = "z_test"

@dataclass
class ExperimentVariant:
    """实验变体配置"""
    variant_id: str
    variant_name: str
    description: str
    model_version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    traffic_percentage: float = 0.0
    
@dataclass
class ExperimentMetric:
    """实验指标配置"""
    metric_id: str
    metric_name: str
    description: str
    metric_type: str  # "primary", "secondary", "guardrail"
    calculation_method: str
    unit: str = ""
    higher_is_better: bool = True
    
@dataclass
class ExperimentConfig:
    """实验配置"""
    experiment_id: str
    experiment_name: str
    description: str
    hypothesis: str
    
    # 实验参数
    primary_metric: str
    secondary_metrics: List[str] = field(default_factory=list)
    guardrail_metrics: List[str] = field(default_factory=list)
    
    # 变体配置
    control_variant: ExperimentVariant
    treatment_variants: List[ExperimentVariant]
    
    # 流量配置
    traffic_allocation: TrafficAllocation = TrafficAllocation.RANDOM
    traffic_percentage: float = 10.0  # 总流量百分比
    
    # 统计配置
    statistical_test: StatisticalTest = StatisticalTest.T_TEST
    confidence_level: float = 0.95
    minimum_detectable_effect: float = 0.05
    power: float = 0.8
    
    # 时间配置
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_days: int = 14
    
    # 实验状态
    status: str = "draft"  # draft, running, paused, completed, archived
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "experiment_id": self.experiment_id,
            "experiment_name": self.experiment_name,
            "description": self.description,
            "hypothesis": self.hypothesis,
            "primary_metric": self.primary_metric,
            "secondary_metrics": self.secondary_metrics,
            "guardrail_metrics": self.guardrail_metrics,
            "control_variant": {
                "variant_id": self.control_variant.variant_id,
                "variant_name": self.control_variant.variant_name,
                "description": self.control_variant.description,
                "parameters": self.control_variant.parameters
            },
            "treatment_variants": [
                {
                    "variant_id": variant.variant_id,
                    "variant_name": variant.variant_name,
                    "description": variant.description,
                    "parameters": variant.parameters
                } for variant in self.treatment_variants
            ],
            "traffic_allocation": self.traffic_allocation.value,
            "traffic_percentage": self.traffic_percentage,
            "statistical_test": self.statistical_test.value,
            "confidence_level": self.confidence_level,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "power": self.power,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_days": self.duration_days,
            "status": self.status
        }
    
    def calculate_sample_size(self) -> Dict[str, int]:
        """
        计算所需样本量
        使用公式: n = 2 * (Z_{1-α/2} + Z_{1-β})^2 * p(1-p) / δ^2
        """
        import scipy.stats as stats
        
        # 标准正态分布的Z值
        z_alpha = stats.norm.ppf(1 - (1 - self.confidence_level) / 2)
        z_beta = stats.norm.ppf(self.power)
        
        # 假设基准转化率为0.1
        p = 0.1
        
        # 计算所需样本量
        n_per_group = (z_alpha + z_beta)**2 * 2 * p * (1 - p) / (self.minimum_detectable_effect**2)
        
        total_users = int(n_per_group) * (len(self.treatment_variants) + 1)
        
        return {
            "per_group": int(n_per_group),
            "total": total_users,
            "required_daily": total_users / self.duration_days
        }
```

### 3.2 流量分配系统

```python
# 文件: ab_test/traffic/traffic_allocator.py

import hashlib
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from ab_test.config.experiment_config import ExperimentConfig, TrafficAllocation

@dataclass
class UserAssignment:
    """用户分配结果"""
    user_id: str
    experiment_id: str
    variant_id: str
    variant_name: str
    assignment_time: float
    is_control: bool
    metadata: Dict[str, str] = None

class TrafficAllocator:
    """流量分配器"""
    
    def __init__(self):
        self.assignment_cache: Dict[str, Dict[str, UserAssignment]] = {}
        self.experiment_weights: Dict[str, Dict[str, float]] = {}
    
    def assign_user_to_variant(
        self, 
        user_id: str, 
        experiment_config: ExperimentConfig,
        experiment_id: Optional[str] = None
    ) -> UserAssignment:
        """
        将用户分配到实验变体
        
        Args:
            user_id: 用户ID
            experiment_config: 实验配置
            experiment_id: 实验ID，如果为None则使用配置中的ID
            
        Returns:
            UserAssignment: 用户分配结果
        """
        exp_id = experiment_id or experiment_config.experiment_id
        
        # 检查是否已分配
        if exp_id in self.assignment_cache and user_id in self.assignment_cache[exp_id]:
            return self.assignment_cache[exp_id][user_id]
        
        # 计算分配
        variant_id, variant_name, is_control = self._calculate_variant(
            user_id, 
            experiment_config
        )
        
        # 创建分配记录
        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=exp_id,
            variant_id=variant_id,
            variant_name=variant_name,
            assignment_time=np.datetime64('now').astype(float),
            is_control=is_control,
            metadata={
                "allocation_method": experiment_config.traffic_allocation.value,
                "traffic_percentage": str(experiment_config.traffic_percentage)
            }
        )
        
        # 缓存分配
        if exp_id not in self.assignment_cache:
            self.assignment_cache[exp_id] = {}
        self.assignment_cache[exp_id][user_id] = assignment
        
        return assignment
    
    def _calculate_variant(
        self, 
        user_id: str, 
        config: ExperimentConfig
    ) -> Tuple[str, str, bool]:
        """
        计算用户应分配的变体
        
        Returns:
            Tuple: (variant_id, variant_name, is_control)
        """
        # 根据分配策略计算
        if config.traffic_allocation == TrafficAllocation.HASH_BASED:
            return self._hash_based_allocation(user_id, config)
        elif config.traffic_allocation == TrafficAllocation.RANDOM:
            return self._random_allocation(config)
        else:  # PERCENTAGE
            return self._percentage_allocation(user_id, config)
    
    def _hash_based_allocation(
        self, 
        user_id: str, 
        config: ExperimentConfig
    ) -> Tuple[str, str, bool]:
        """基于哈希的分配"""
        # 生成哈希值
        hash_input = f"{config.experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # 归一化到0-100
        normalized = hash_value % 10000 / 100
        
        # 检查是否在流量范围内
        if normalized >= config.traffic_percentage:
            # 不参与实验
            return "not_in_experiment", "Not in Experiment", False
        
        # 在流量范围内，计算变体
        total_weight = 0
        variants = []
        
        # 控制组权重
        control_weight = config.control_variant.traffic_percentage or (100 / (len(config.treatment_variants) + 1))
        variants.append((config.control_variant.variant_id, 
                        config.control_variant.variant_name, 
                        True, 
                        control_weight))
        total_weight += control_weight
        
        # 实验组权重
        for variant in config.treatment_variants:
            weight = variant.traffic_percentage or (100 / (len(config.treatment_variants) + 1))
            variants.append((variant.variant_id, 
                           variant.variant_name, 
                           False, 
                           weight))
            total_weight += weight
        
        # 归一化权重
        normalized_weights = [v[3] / total_weight for v in variants]
        
        # 根据哈希值选择变体
        cumulative = 0
        variant_hash = hash_value % 100000 / 1000  # 更精细的精度
        
        for (variant_id, variant_name, is_control, weight), normalized_weight in zip(variants, normalized_weights):
            cumulative += normalized_weight * 100
            if variant_hash < cumulative:
                return variant_id, variant_name, is_control
        
        # 默认返回控制组
        return variants[0][0], variants[0][1], variants[0][2]
    
    def _random_allocation(
        self, 
        config: ExperimentConfig
    ) -> Tuple[str, str, bool]:
        """随机分配"""
        # 检查是否在流量范围内
        if np.random.random() * 100 >= config.traffic_percentage:
            return "not_in_experiment", "Not in Experiment", False
        
        # 构建变体列表
        variants = [(config.control_variant.variant_id, 
                    config.control_variant.variant_name, 
                    True)]
        
        for variant in config.treatment_variants:
            variants.append((variant.variant_id, 
                           variant.variant_name, 
                           False))
        
        # 随机选择
        idx = np.random.randint(0, len(variants))
        return variants[idx]
    
    def _percentage_allocation(
        self, 
        user_id: str, 
        config: ExperimentConfig
    ) -> Tuple[str, str, bool]:
        """基于百分比的分配"""
        # 类似哈希分配，但使用简单的用户ID哈希
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        normalized = hash_value % 10000 / 100
        
        # 检查是否在流量范围内
        if normalized >= config.traffic_percentage:
            return "not_in_experiment", "Not in Experiment", False
        
        # 在流量范围内，按百分比分配
        all_variants = [
            (config.control_variant.variant_id, 
             config.control_variant.variant_name, 
             True, 
             config.control_variant.traffic_percentage or 50.0)
        ]
        
        for variant in config.treatment_variants:
            all_variants.append((variant.variant_id, 
                               variant.variant_name, 
                               False, 
                               variant.traffic_percentage or (50.0 / len(config.treatment_variants))))
        
        # 计算累积百分比
        cumulative = 0
        variant_normalized = normalized * 100 / config.traffic_percentage
        
        for variant_id, variant_name, is_control, percentage in all_variants:
            cumulative += percentage
            if variant_normalized < cumulative:
                return variant_id, variant_name, is_control
        
        # 默认返回控制组
        return all_variants[0][0], all_variants[0][1], all_variants[0][2]
    
    def get_assignment_stats(self, experiment_id: str) -> Dict:
        """获取分配统计信息"""
        if experiment_id not in self.assignment_cache:
            return {"total_assignments": 0, "variants": {}}
        
        assignments = self.assignment_cache[experiment_id]
        variant_counts = {}
        
        for assignment in assignments.values():
            if assignment.variant_id not in variant_counts:
                variant_counts[assignment.variant_id] = {
                    "count": 0,
                    "is_control": assignment.is_control,
                    "variant_name": assignment.variant_name
                }
            variant_counts[assignment.variant_id]["count"] += 1
        
        return {
            "total_assignments": len(assignments),
            "variants": variant_counts
        }
```

### 3.3 指标收集系统

```python
# 文件: ab_test/metrics/metrics_collector.py

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from collections import defaultdict

@dataclass
class MetricEvent:
    """指标事件"""
    user_id: str
    experiment_id: str
    variant_id: str
    metric_name: str
    metric_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "experiment_id": self.experiment_id,
            "variant_id": self.variant_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.events: Dict[str, List[MetricEvent]] = defaultdict(list)
        self.metric_definitions: Dict[str, Dict[str, Any]] = {}
        self.user_metrics: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
    
    def register_metric(
        self, 
        metric_name: str, 
        metric_type: str,
        description: str = "",
        aggregation: str = "sum"  # sum, mean, count, min, max, rate
    ):
        """
        注册指标定义
        
        Args:
            metric_name: 指标名称
            metric_type: 指标类型 (primary, secondary, guardrail)
            description: 指标描述
            aggregation: 聚合方式
        """
        self.metric_definitions[metric_name] = {
            "type": metric_type,
            "description": description,
            "aggregation": aggregation
        }
    
    def track_event(
        self,
        user_id: str,
        experiment_id: str,
        variant_id: str,
        metric_name: str,
        metric_value: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        跟踪指标事件
        
        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            variant_id: 变体ID
            metric_name: 指标名称
            metric_value: 指标值
            metadata: 元数据
        """
        event = MetricEvent(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metadata=metadata or {}
        )
        
        # 存储事件
        self.events[experiment_id].append(event)
        
        # 更新用户指标
        self.user_metrics[experiment_id][variant_id][user_id].append(metric_value)
    
    def track_conversion(
        self,
        user_id: str,
        experiment_id: str,
        variant_id: str,
        conversion_type: str = "conversion",
        value: float = 1.0
    ):
        """跟踪转化事件"""
        self.track_event(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            metric_name=conversion_type,
            metric_value=value,
            metadata={"event_type": "conversion"}
        )
    
    def track_engagement(
        self,
        user_id: str,
        experiment_id: str,
        variant_id: str,
        engagement_type: str,
        value: float
    ):
        """跟踪参与度事件"""
        self.track_event(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            metric_name=f"engagement_{engagement_type}",
            metric_value=value,
            metadata={"event_type": "engagement", "engagement_type": engagement_type}
        )
    
    def get_experiment_metrics(
        self, 
        experiment_id: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        获取实验指标数据
        
        Args:
            experiment_id: 实验ID
            metric_name: 指标名称筛选
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            DataFrame: 指标数据
        """
        if experiment_id not in self.events:
            return pd.DataFrame()
        
        events = self.events[experiment_id]
        
        # 过滤指标名称
        if metric_name:
            events = [e for e in events if e.metric_name == metric_name]
        
        # 过滤时间范围
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        if not events:
            return pd.DataFrame()
        
        # 转换为DataFrame
        data = []
        for event in events:
            data.append({
                "user_id": event.user_id,
                "experiment_id": event.experiment_id,
                "variant_id": event.variant_id,
                "metric_name": event.metric_name,
                "metric_value": event.metric_value,
                "timestamp": event.timestamp
            })
        
        return pd.DataFrame(data)
    
    def calculate_variant_metrics(
        self, 
        experiment_id: str,
        metric_name: str,
        aggregation: str = "mean"
    ) -> Dict[str, Dict[str, float]]:
        """
        计算每个变体的指标统计
        
        Args:
            experiment_id: 实验ID
            metric_name: 指标名称
            aggregation: 聚合方式
            
        Returns:
            Dict: 变体指标统计
        """
        df = self.get_experiment_metrics(experiment_id, metric_name)
        
        if df.empty:
            return {}
        
        result = {}
        
        for variant_id, group in df.groupby("variant_id"):
            values = group["metric_value"].values
            
            if aggregation == "sum":
                agg_value = np.sum(values)
            elif aggregation == "mean":
                agg_value = np.mean(values)
            elif aggregation == "count":
                agg_value = len(values)
            elif aggregation == "min":
                agg_value = np.min(values)
            elif aggregation == "max":
                agg_value = np.max(values)
            elif aggregation == "rate":
                # 假设是转化率计算
                agg_value = np.mean(values > 0) if len(values) > 0 else 0
            else:
                agg_value = np.mean(values)
            
            result[variant_id] = {
                "aggregated_value": agg_value,
                "count": len(values),
                "std": np.std(values) if len(values) > 1 else 0,
                "min": np.min(values) if len(values) > 0 else 0,
                "max": np.max(values) if len(values) > 0 else 0,
                "median": np.median(values) if len(values) > 0 else 0
            }
        
        return result
    
    def get_user_metric_history(
        self, 
        experiment_id: str, 
        variant_id: str, 
        user_id: str
    ) -> Dict[str, List[float]]:
        """获取用户指标历史"""
        if (experiment_id in self.user_metrics and 
            variant_id in self.user_metrics[experiment_id] and 
            user_id in self.user_metrics[experiment_id][variant_id]):
            return {
                "metric_values": self.user_metrics[experiment_id][variant_id][user_id],
                "count": len(self.user_metrics[experiment_id][variant_id][user_id])
            }
        return {"metric_values": [], "count": 0}
```

### 3.4 统计分析引擎

```python
# 文件: ab_test/analysis/statistical_engine.py

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm, t, chi2_contingency
import warnings

class StatisticalEngine:
    """统计分析引擎"""
    
    def __init__(self):
        self.results_cache: Dict[str, Dict] = {}
    
    def t_test(
        self, 
        control_data: np.ndarray, 
        treatment_data: np.ndarray,
        alternative: str = "two-sided",
        equal_var: bool = False
    ) -> Dict[str, float]:
        """
        执行t检验
        
        Args:
            control_data: 对照组数据
            treatment_data: 实验组数据
            alternative: 备择假设 ('two-sided', 'less', 'greater')
            equal_var: 是否假设方差相等
            
        Returns:
            Dict: 统计结果
        """
        # 执行t检验
        t_stat, p_value = stats.ttest_ind(
            control_data, 
            treatment_data, 
            alternative=alternative,
            equal_var=equal_var
        )
        
        # 计算效应量 (Cohen's d)
        pooled_std = np.sqrt(
            ((len(control_data) - 1) * np.std(control_data, ddof=1)**2 + 
             (len(treatment_data) - 1) * np.std(treatment_data, ddof=1)**2) / 
            (len(control_data) + len(treatment_data) - 2)
        )
        
        effect_size = (np.mean(treatment_data) - np.mean(control_data)) / pooled_std if pooled_std > 0 else 0
        
        # 计算置信区间
        se = np.sqrt(np.var(control_data, ddof=1)/len(control_data) + 
                    np.var(treatment_data, ddof=1)/len(treatment_data))
        
        df = len(control_data) + len(treatment_data) - 2
        t_critical = t.ppf(0.975, df)  # 95%置信区间
        
        mean_diff = np.mean(treatment_data) - np.mean(control_data)
        ci_low = mean_diff - t_critical * se
        ci_high = mean_diff + t_critical * se
        
        return {
            "t_statistic": t_stat,
            "p_value": p_value,
            "effect_size_cohens_d": effect_size,
            "confidence_interval": (ci_low, ci_high),
            "mean_difference": mean_diff,
            "control_mean": np.mean(control_data),
            "treatment_mean": np.mean(treatment_data),
            "control_std": np.std(control_data, ddof=1),
            "treatment_std": np.std(treatment_data, ddof=1),
            "control_count": len(control_data),
            "treatment_count": len(treatment_data),
            "degrees_of_freedom": df
        }
    
    def chi_square_test(
        self, 
        control_successes: int, 
        control_total: int,
        treatment_successes: int, 
        treatment_total: int
    ) -> Dict[str, float]:
        """
        执行卡方检验
        
        Args:
            control_successes: 对照组成功次数
            control_total: 对照组总次数
            treatment_successes: 实验组成功次数
            treatment_total: 实验组总次数
            
        Returns:
            Dict: 统计结果
        """
        # 创建列联表
        observed = np.array([
            [control_successes, control_total - control_successes],
            [treatment_successes, treatment_total - treatment_successes]
        ])
        
        # 执行卡方检验
        chi2, p_value, dof, expected = chi2_contingency(observed, correction=False)
        
        # 计算转化率
        control_rate = control_successes / control_total if control_total > 0 else 0
        treatment_rate = treatment_successes / treatment_total if treatment_total > 0 else 0
        
        # 计算相对提升
        relative_improvement = (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0
        
        # 计算风险比 (RR)
        rr = treatment_rate / control_rate if control_rate > 0 else float('inf')
        
        # 计算优势比 (OR)
        odds_control = control_successes / (control_total - control_successes) if (control_total - control_successes) > 0 else 0
        odds_treatment = treatment_successes / (treatment_total - treatment_successes) if (treatment_total - treatment_successes) > 0 else 0
        odds_ratio = odds_treatment / odds_control if odds_control > 0 else float('inf')
        
        return {
            "chi_square": chi2,
            "p_value": p_value,
            "degrees_of_freedom": dof,
            "control_rate": control_rate,
            "treatment_rate": treatment_rate,
            "relative_improvement": relative_improvement,
            "risk_ratio": rr,
            "odds_ratio": odds_ratio,
            "control_successes": control_successes,
            "control_total": control_total,
            "treatment_successes": treatment_successes,
            "treatment_total": treatment_total,
            "expected_frequencies": expected.tolist()
        }
    
    def bayesian_analysis(
        self, 
        control_data: np.ndarray, 
        treatment_data: np.ndarray,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        n_samples: int = 10000
    ) -> Dict[str, float]:
        """
        执行贝叶斯分析
        
        Args:
            control_data: 对照组数据（二进制，0/1）
            treatment_data: 实验组数据（二进制，0/1）
            prior_alpha: Beta分布先验α
            prior_beta: Beta分布先验β
            n_samples: 采样数量
            
        Returns:
            Dict: 贝叶斯分析结果
        """
        # 计算后验分布参数
        control_successes = np.sum(control_data)
        control_failures = len(control_data) - control_successes
        
        treatment_successes = np.sum(treatment_data)
        treatment_failures = len(treatment_data) - treatment_successes
        
        # 后验参数
        control_alpha = prior_alpha + control_successes
        control_beta = prior_beta + control_failures
        
        treatment_alpha = prior_alpha + treatment_successes
        treatment_beta = prior_beta + treatment_failures
        
        # 从后验分布采样
        control_samples = np.random.beta(control_alpha, control_beta, n_samples)
        treatment_samples = np.random.beta(treatment_alpha, treatment_beta, n_samples)
        
        # 计算概率
        prob_treatment_better = np.mean(treatment_samples > control_samples)
        prob_control_better = 1 - prob_treatment_better
        
        # 计算损失 (期望损失)
        loss_treatment = np.mean(np.maximum(control_samples - treatment_samples, 0))
        loss_control = np.mean(np.maximum(treatment_samples - control_samples, 0))
        
        # 计算提升
        expected_lift = np.mean((treatment_samples - control_samples) / control_samples)
        
        # 计算可信区间
        diff_samples = treatment_samples - control_samples
        ci_low = np.percentile(diff_samples, 2.5)
        ci_high = np.percentile(diff_samples, 97.5)
        
        return {
            "prob_treatment_better": prob_treatment_better,
            "prob_control_better": prob_control_better,
            "expected_loss_treatment": loss_treatment,
            "expected_loss_control": loss_control,
            "expected_lift": expected_lift,
            "credible_interval": (ci_low, ci_high),
            "control_mean": np.mean(control_samples),
            "treatment_mean": np.mean(treatment_samples),
            "control_std": np.std(control_samples),
            "treatment_std": np.std(treatment_samples),
            "sample_size_control": len(control_data),
            "sample_size_treatment": len(treatment_data)
        }
    
    def calculate_sample_size_required(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.8,
        alternative: str = "two-sided"
    ) -> Dict[str, int]:
        """
        计算所需样本量
        
        Args:
            baseline_rate: 基准转化率
            minimum_detectable_effect: 最小可检测效应（相对提升）
            alpha: 显著性水平
            power: 统计功效
            alternative: 备择假设
            
        Returns:
            Dict: 样本量信息
        """
        # 处理率
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        
        # 计算Z值
        z_alpha = norm.ppf(1 - alpha/2) if alternative == "two-sided" else norm.ppf(1 - alpha)
        z_beta = norm.ppf(power)
        
        # 计算合并方差
        p_bar = (p1 + p2) / 2
        
        # 样本量公式
        n = (z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) + 
             z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2 / (p2 - p1)**2
        
        # 向上取整
        n_per_group = int(np.ceil(n))
        
        return {
            "per_group": n_per_group,
            "total": n_per_group * 2,
            "baseline_rate": baseline_rate,
            "expected_treatment_rate": p2,
            "absolute_difference": p2 - p1,
            "relative_difference": minimum_detectable_effect,
            "alpha": alpha,
            "power": power
        }
    
    def calculate_statistical_significance(
        self,
        p_value: float,
        confidence_level: float = 0.95,
        method: str = "frequentist"
    ) -> Dict[str, Any]:
        """
        判断统计显著性
        
        Args:
            p_value: p值
            confidence_level: 置信水平
            method: 方法
            
        Returns:
            Dict: 显著性结果
        """
        alpha = 1 - confidence_level
        is_significant = p_value < alpha
        
        # 计算证据强度
        if p_value < 0.001:
            evidence_strength = "Very Strong"
        elif p_value < 0.01:
            evidence_strength = "Strong"
        elif p_value < 0.05:
            evidence_strength = "Moderate"
        elif p_value < 0.1:
            evidence_strength = "Weak"
        else:
            evidence_strength = "Not Significant"
        
        return {
            "is_significant": is_significant,
            "p_value": p_value,
            "alpha": alpha,
            "confidence_level": confidence_level,
            "evidence_strength": evidence_strength,
            "method": method,
            "recommendation": "Reject null hypothesis" if is