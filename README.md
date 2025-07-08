# FLUX.1-Kontext API

🎨 **专业级图像生成与编辑API服务** - 基于FLUX.1模型的高性能图像处理平台

## ✨ 核心特性

- 🚀 **高性能图像生成** - 支持文本到图像的快速生成
- 🎭 **智能图像编辑** - 基于提示词的精确图像修改
- 🔄 **图像变体生成** - 保持主体一致性的多样化变体创建
- 🌐 **RESTful API** - 兼容OpenAI标准的API接口
- ⚡ **GPU/CPU支持** - 自动检测并优化硬件使用
- 🐳 **容器化部署** - 支持Docker和Docker Compose
- 📊 **监控与日志** - 完整的请求追踪和性能监控
- 🔒 **安全可靠** - 内置限流、验证和错误处理

## 🏗️ 项目架构

```
FLUX.1-Kontext-Dev/
├── app/                    # 应用核心代码
│   ├── api/               # API路由层
│   │   ├── v1/           # v1版本接口
│   │   └── dependencies.py # 依赖注入
│   ├── core/             # 核心配置
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑层
│   └── utils/            # 工具函数
├── static/               # 静态文件存储
├── docker-compose.yml    # 容器编排
├── Dockerfile           # CPU版本镜像
├── Dockerfile.gpu       # GPU版本镜像
├── start.sh            # 启动脚本
└── test_api.py         # API测试工具
```

## 🚀 快速开始

### 方式一：本地运行

1. **克隆项目**
```bash
git clone <repository-url>
cd FLUX.1-Kontext-Dev
```

2. **自动安装和启动**
```bash
# 完整安装（推荐）
./start.sh

# 或者手动安装
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. **访问API**
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/ping

### 方式二：Docker部署

**CPU版本**
```bash
# 使用docker-compose
docker-compose --profile cpu up -d

# 或直接使用docker
docker build -t flux-api .
docker run -p 8000:8000 -v $(pwd)/static:/app/static flux-api
```

**GPU版本**
```bash
# 确保安装了nvidia-docker
docker-compose --profile gpu up -d

# 或直接使用docker
docker build -f Dockerfile.gpu -t flux-api-gpu .
docker run --gpus all -p 8000:8000 -v $(pwd)/static:/app/static flux-api-gpu
```

**完整部署（包含Nginx）**
```bash
docker-compose --profile gpu --profile nginx up -d
```

## 📡 API接口

### 🎨 图像生成
```bash
curl -X POST "http://localhost:8000/v1/images/generations" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "n": 1,
    "size": "512x512",
    "response_format": "b64_json"
  }'
```

### ✏️ 图像编辑
```bash
curl -X POST "http://localhost:8000/v1/images/edits" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "<base64_encoded_image>",
    "prompt": "Add a rainbow in the sky",
    "n": 1,
    "size": "512x512"
  }'
```

### 🔄 图像变体
```bash
curl -X POST "http://localhost:8000/v1/images/variations" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "<base64_encoded_image>",
    "prompt": "Same subject, different artistic style",
    "n": 3,
    "size": "512x512"
  }'
```

### 📋 其他接口
- `GET /v1/models` - 获取可用模型列表
- `GET /v1/health` - 健康检查
- `GET /ping` - 简单状态检查

## 🧪 测试

**运行API测试**
```bash
# 基础测试
python test_api.py

# 完整测试（包括图像生成）
python test_api.py --full-test

# 负载测试
python test_api.py --load-test --concurrent 10 --total 50
```

**使用pytest**
```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## ⚙️ 配置

### 环境变量

复制 `.env.example` 到 `.env` 并根据需要修改：

```bash
cp .env.example .env
```

主要配置项：
- `DEVICE`: 设备类型 (cuda/cpu/auto)
- `MODEL_NAME`: 模型名称
- `MAX_IMAGE_SIZE`: 最大图像尺寸
- `BATCH_SIZE`: 批处理大小
- `DEBUG`: 调试模式

### 性能优化

**GPU优化**
```bash
# 设置GPU内存增长
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

**CPU优化**
```bash
# 设置线程数
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

## 📊 监控

### 启用监控服务
```bash
docker-compose --profile monitoring up -d
```

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### 日志查看
```bash
# 查看应用日志
docker-compose logs -f flux-api-gpu

# 查看Nginx日志
docker-compose logs -f nginx
```

## 🔧 开发

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements.txt
pip install black isort flake8 mypy

# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/
mypy app/
```

### 添加新功能
1. 在 `app/api/v1/` 中添加新的路由
2. 在 `app/services/` 中实现业务逻辑
3. 在 `app/models/schemas.py` 中定义数据模型
4. 添加相应的测试用例

## 🐛 故障排除

### 常见问题

**1. 模型加载失败**
```bash
# 检查模型文件
ls ~/.cache/huggingface/

# 清理缓存重新下载
rm -rf ~/.cache/huggingface/transformers/
```

**2. GPU内存不足**
```bash
# 减少批处理大小
export BATCH_SIZE=1

# 或使用CPU
export DEVICE=cpu
```

**3. 端口被占用**
```bash
# 查找占用进程
lsof -i :8000

# 使用其他端口
export PORT=8001
```

### 日志级别
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 查看实时日志
tail -f logs/app.log
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 支持

如有问题，请通过以下方式联系：
- 提交 [GitHub Issue](../../issues)
- 查看 [API文档](http://localhost:8000/docs)
- 运行测试脚本进行诊断

---

⭐ 如果这个项目对你有帮助，请给个星标支持！