# 使用官方Python基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件和pip配置
COPY requirements.txt pip.conf ./

# 配置pip使用中国大陆源
RUN mkdir -p ~/.pip && \
    cp pip.conf ~/.pip/pip.conf

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p static/uploads static/outputs

# 设置权限
RUN chmod +x start.sh

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ping || exit 1

# 启动命令
CMD ["./start.sh"]

# GPU版本的Dockerfile（可选）
# 如果需要GPU支持，使用以下基础镜像：
# FROM nvidia/cuda:11.8-devel-ubuntu20.04
# 
# # 安装Python 3.10
# RUN apt-get update && apt-get install -y \
#     software-properties-common && \
#     add-apt-repository ppa:deadsnakes/ppa && \
#     apt-get update && apt-get install -y \
#     python3.10 \
#     python3.10-pip \
#     python3.10-dev \
#     git \
#     wget \
#     curl \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*
# 
# # 创建python和pip的符号链接
# RUN ln -s /usr/bin/python3.10 /usr/bin/python && \
#     ln -s /usr/bin/pip3.10 /usr/bin/pip