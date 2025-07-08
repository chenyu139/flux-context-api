from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.models.flux_model import model_manager
from app.core.exceptions import ModelLoadError
from app.utils.response_utils import get_base_url_from_request

logger = logging.getLogger(__name__)

# 可选的Bearer token认证
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """获取当前用户（可选认证）"""
    if credentials:
        # 这里可以添加token验证逻辑
        # 目前只是简单返回token作为用户ID
        return credentials.credentials[:20]  # 截取前20个字符作为用户ID
    return None


async def verify_model_loaded():
    """验证模型是否已加载"""
    if not model_manager.is_loaded:
        logger.error("Model not loaded when handling request")
        raise ModelLoadError("Model is not loaded. Please wait for model initialization.")
    return True


async def get_base_url(request: Request) -> str:
    """获取请求的基础URL"""
    return get_base_url_from_request(request)


async def validate_content_type(request: Request):
    """验证请求内容类型"""
    content_type = request.headers.get("content-type", "")
    
    # 对于POST请求，验证content-type
    if request.method == "POST":
        if not content_type.startswith("application/json") and not content_type.startswith("multipart/form-data"):
            raise HTTPException(
                status_code=415,
                detail="Unsupported Media Type. Expected application/json or multipart/form-data"
            )
    
    return True


async def log_request(request: Request, user_id: Optional[str] = Depends(get_current_user)):
    """记录请求信息"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(f"Request: {request.method} {request.url.path} - IP: {client_ip} - User: {user_id} - UA: {user_agent}")
    
    return {
        "ip": client_ip,
        "user_agent": user_agent,
        "user_id": user_id
    }


class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}
    
    async def check_rate_limit(self, request: Request):
        """检查速率限制"""
        import time
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (timestamp, count) for timestamp, count in self.requests[client_ip]
                if current_time - timestamp < self.window_seconds
            ]
        
        # 计算当前窗口内的请求数
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        current_requests = sum(count for _, count in self.requests[client_ip])
        
        if current_requests >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds."
            )
        
        # 记录当前请求
        self.requests[client_ip].append((current_time, 1))
        
        return True


# 创建速率限制器实例
rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)  # 每小时100个请求


async def check_rate_limit(request: Request):
    """检查速率限制的依赖函数"""
    return await rate_limiter.check_rate_limit(request)


async def validate_request_size(request: Request):
    """验证请求大小"""
    content_length = request.headers.get("content-length")
    
    if content_length:
        content_length = int(content_length)
        max_size = 50 * 1024 * 1024  # 50MB
        
        if content_length > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Request too large. Maximum size is {max_size} bytes."
            )
    
    return True


class HealthChecker:
    """健康检查器"""
    
    @staticmethod
    async def check_model_health() -> dict:
        """检查模型健康状态"""
        import torch
        
        try:
            model_loaded = model_manager.is_loaded
            gpu_available = torch.cuda.is_available()
            
            # 如果模型已加载，尝试一个简单的推理测试
            if model_loaded:
                try:
                    # 这里可以添加一个简单的模型测试
                    pass
                except Exception as e:
                    logger.warning(f"Model health check failed: {str(e)}")
                    model_loaded = False
            
            return {
                "model_loaded": model_loaded,
                "gpu_available": gpu_available,
                "gpu_count": torch.cuda.device_count() if gpu_available else 0,
                "memory_allocated": torch.cuda.memory_allocated() if gpu_available else 0,
                "memory_reserved": torch.cuda.memory_reserved() if gpu_available else 0
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "model_loaded": False,
                "gpu_available": False,
                "error": str(e)
            }


# 健康检查器实例
health_checker = HealthChecker()