# Dockerfile 多阶段构建配置，优化镜像体积和构建速度
# 阶段1：依赖构建阶段
FROM python:3.10-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（仅构建阶段需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt，利用Docker缓存，仅当依赖变更时重新安装
COPY requirements.txt .

# 安装依赖到当前目录，后续直接复制到运行阶段
RUN pip install --user --no-cache-dir -r requirements.txt

# 阶段2：运行阶段（最小镜像）
FROM python:3.10-slim AS runtime

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"

# 安装运行时仅需要的最小系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的依赖
COPY --from=builder /root/.local /root/.local

# 复制项目代码
COPY . .

# 暴露服务端口
EXPOSE 8000

# 配置健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
