# 基础镜像选择Python3.10 slim版本，兼顾体积和兼容性
FROM python:3.10-slim

# 设置工作目录，所有后续操作都在该目录下执行
WORKDIR /app

# 安装系统依赖：gcc用于编译部分Python包，git用于代码拉取，清理缓存减小镜像体积
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖声明文件到工作目录，分层构建加快镜像构建速度
COPY requirements.txt .

# 安装Python依赖，使用--no-cache-dir减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目全部代码到工作目录
COPY . .

# 设置环境变量，Python输出不缓冲，方便日志查看
ENV PYTHONUNBUFFERED=1

# 暴露服务端口，根据项目实际情况修改，这里默认用8000
EXPOSE 8000

# 容器默认启动命令，可根据实际项目启动脚本修改
CMD ["python", "cli.py", "run"]