import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    general_exception_handler
)
from app.api.v1 import api_router
from app.models.flux_model import model_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的操作
    logger.info("Starting FLUX.1-Kontext API...")
    
    try:
        # 主动加载模型
        logger.info("Preloading FLUX model...")
        model_manager.load_model()
        logger.info("Model preloading completed")
        
        logger.info("API startup completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        logger.warning("Application will continue to start, but model may not be available")
        # 不抛出异常，让应用继续启动，但模型可能不可用
    
    yield
    
    # 关闭时的操作
    logger.info("Shutting down FLUX.1-Kontext API...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    FLUX.1-Kontext API - 基于FLUX.1-Kontext-dev模型的图片生成和编辑API
    
    ## 功能特性
    
    * **图片生成**: 根据文本提示词生成高质量图片
    * **图片编辑**: 基于输入图片和指令进行智能编辑
    * **图片变体**: 生成保持主体一致的多个变体图片
    * **OpenAI兼容**: API设计参照OpenAI图片生成接口标准
    
    ## 支持的图片格式
    
    * 输入: JPEG, PNG, WebP
    * 输出: PNG (URL或base64)
    
    ## 速率限制
    
    * 每小时100个请求（可配置）
    * 单次最大生成10张图片
    * 最大图片尺寸: 2048x2048
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加静态文件服务
if os.path.exists(settings.static_dir):
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# 注册异常处理器
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 包含API路由
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
async def root():
    """根路径 - API信息"""
    return {
        "message": "FLUX.1-Kontext API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/v1/health",
        "models": "/v1/models"
    }


@app.get("/ping", tags=["root"])
async def ping():
    """简单的ping接口"""
    return {"status": "ok", "message": "pong"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    import time
    
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录请求日志
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # 添加处理时间到响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """安全头中间件"""
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )