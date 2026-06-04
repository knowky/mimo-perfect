# 实现实时推荐 API

**任务**: 机器学习推荐系统
**时间**: 2026-06-05T00:58:40.333807

# 实现实时推荐 API

## 1. 需求分析
实时推荐 API 是推荐系统中的关键组件，它负责接收用户请求（如用户ID、上下文信息等），调用已训练好的推荐模型进行预测，并快速返回推荐结果。为确保高性能和可扩展性，我们需要选择合适的框架和算法，并考虑缓存、异步处理等优化策略。

## 2. 技术选型
- **框架**：FastAPI（高性能、异步支持、自动生成API文档）
- **推荐算法**：基于协同过滤的矩阵分解（例如ALS），或基于深度学习的模型（如神经协同过滤）。为简化演示，这里使用预先训练好的模型（例如用Surprise库训练的SVD模型）。
- **数据存储**：使用Redis缓存推荐结果，提高响应速度。
- **部署**：容器化（Docker）以便于扩展。

## 3. 详细实现步骤
### 3.1 环境准备
1. 安装依赖：FastAPI、Uvicorn、Redis、Surprise（用于训练简单模型）、Pickle（模型序列化）。
2. 训练一个简单的推荐模型并保存为文件（`model.pkl`）。这里以MovieLens数据集为例。

### 3.2 代码实现
#### 3.2.1 模型训练与保存（train_model.py）
```python
import pickle
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

# 加载示例数据集
data = Dataset.load_builtin('ml-100k')
trainset = data.build_full_trainset()

# 训练SVD模型
algo = SVD()
algo.fit(trainset)

# 保存模型
with open('model.pkl', 'wb') as f:
    pickle.dump(algo, f)

print("模型已保存为 model.pkl")
```

#### 3.2.2 实时推荐API服务（api.py）
```python
import pickle
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="实时推荐API")

# 加载模型
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    raise Exception("模型文件未找到，请先训练模型")

# Redis连接（可选，用于缓存）
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.ping()
    use_cache = True
except:
    use_cache = False
    print("未连接到Redis，将不使用缓存")

# 定义请求模型
class RecommendRequest(BaseModel):
    user_id: int
    n_items: int = 10  # 推荐物品数量
    exclude_rated: bool = True  # 是否排除已评分物品

# 定义响应模型
class RecommendItem(BaseModel):
    item_id: int
    score: float

class RecommendResponse(BaseModel):
    user_id: int
    recommendations: List[RecommendItem]

# 获取推荐列表的函数
def get_recommendations(user_id: int, n_items: int, exclude_rated: bool = True):
    # 尝试从缓存获取
    cache_key = f"recommend:{user_id}:{n_items}:{exclude_rated}"
    if use_cache:
        cached = redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

    # 获取所有物品ID（这里需要实际数据集中的物品列表，这里假设为1到1000）
    all_items = list(range(1, 1001))
    
    # 获取用户已评分物品（如果有数据集）
    # 这里假设有一个已评分物品列表，实际应从数据库或数据文件中读取
    # 为简化，我们假设没有已评分数据，或者通过模型获取已评分物品
    # 在Surprise中，我们可以通过训练集获取已评分物品，但这里演示省略
    
    # 预测每个物品的评分
    predictions = []
    for item_id in all_items:
        # 调用模型预测
        pred = model.predict(user_id, item_id)
        predictions.append((item_id, pred.est))
    
    # 按预测评分排序
    predictions.sort(key=lambda x: x[1], reverse=True)
    
    # 如果需要排除已评分物品，这里需要知道哪些是已评分的（假设一个列表）
    # 为演示，我们假设不排除
    # 实际应用中，应根据用户历史记录过滤
    
    # 取前n_items个
    top_predictions = predictions[:n_items]
    
    # 构建结果
    result = [{"item_id": item_id, "score": round(score, 3)} for item_id, score in top_predictions]
    
    # 缓存结果
    if use_cache:
        import json
        redis_client.setex(cache_key, 3600, json.dumps(result))  # 缓存1小时
    
    return result

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
    获取实时推荐
    """
    try:
        recommendations = get_recommendations(
            user_id=request.user_id,
            n_items=request.n_items,
            exclude_rated=request.exclude_rated
        )
        return RecommendResponse(
            user_id=request.user_id,
            recommendations=[RecommendItem(**item) for item in recommendations]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3.3 测试
1. 训练模型：运行 `python train_model.py`。
2. 启动API服务：运行 `python api.py`。
3. 使用curl或Postman测试：
   ```
   curl -X POST "http://localhost:8000/recommend" -H "Content-Type: application/json" -d '{"user_id": 1, "n_items": 5}'
   ```

### 3.4 性能优化
- **异步处理**：FastAPI本身支持异步，但模型预测可能是CPU密集型任务，可以考虑使用多进程或异步任务队列（如Celery）来避免阻塞事件循环。
- **批量预测**：如果模型支持批量预测（如TensorFlow Serving），可一次预测多个物品。
- **缓存策略**：使用Redis缓存推荐结果，对于相同请求直接返回缓存。
- **模型服务化**：对于深度学习模型，可以考虑使用TensorFlow Serving或TorchServe单独部署模型，API服务通过gRPC或HTTP调用。

### 3.5 部署
1. 容器化：编写Dockerfile。
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. 使用Docker Compose编排服务（包括Redis和API）。

## 4. 总结
我们实现了一个基于FastAPI的实时推荐API，使用Surprise训练的SVD模型进行预测，并可选地使用Redis进行缓存。该方案具有高性能、易于扩展的特点，适用于中小型推荐系统。对于更大规模的系统，需要考虑分布式模型服务和更复杂的缓存策略。