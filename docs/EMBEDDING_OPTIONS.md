# Embedding 方案选择

## 当前方案：Simple Embedding（默认）
- **优点**：无需下载、本地计算、零依赖
- **缺点**：语义理解较弱，基于简单哈希
- **适用**：本地快速启动、对语义搜索要求不高

## 方案2：豆包 Embedding API（推荐用于生产）
如需更好的语义搜索，修改 `src/storage/memory.py`：

```python
# 使用豆包 Embedding API
from src.utils.llm import LLMClient

class DoubaoEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.client = LLMClient()
    
    def __call__(self, input: Documents) -> Embeddings:
        # 调用豆包 embedding API
        embeddings = []
        for text in input:
            response = self.client.embed(text)
            embeddings.append(response.embedding)
        return embeddings

# 在 MemorySystem.__init__ 中使用
ef = DoubaoEmbeddingFunction()
```

## 方案3：OpenAI Embedding API
```python
import openai

class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=input
        )
        return [item.embedding for item in response.data]
```

## 建议
- **开发/测试**：使用 Simple Embedding（当前）
- **生产环境**：使用豆包/OpenAI Embedding API

