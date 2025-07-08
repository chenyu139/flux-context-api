from fastapi import APIRouter, Depends
import time
import logging

from app.models.schemas import ModelsResponse, ModelInfo, HealthResponse
from app.api.dependencies import health_checker
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["models"])


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="获取可用模型列表",
    description="返回当前API支持的所有模型信息"
)
async def list_models():
    """获取可用模型列表
    
    返回当前API支持的所有模型的详细信息，包括模型ID、创建时间等。
    
    Returns:
        ModelsResponse: 包含模型列表的响应对象
    """
    models = [
        ModelInfo(
            id="flux-1-kontext-dev",
            object="model",
            created=int(time.time()),
            owned_by="black-forest-labs"
        )
    ]
    
    return ModelsResponse(
        object="list",
        data=models
    )


@router.get(
    "/models/{model_id}",
    response_model=ModelInfo,
    summary="获取特定模型信息",
    description="根据模型ID获取特定模型的详细信息"
)
async def get_model(model_id: str):
    """获取特定模型信息
    
    Args:
        model_id: 模型ID
        
    Returns:
        ModelInfo: 模型详细信息
        
    Raises:
        HTTPException: 当模型ID不存在时返回404错误
    """
    from fastapi import HTTPException
    
    # 目前只支持一个模型
    if model_id == "flux-1-kontext-dev":
        return ModelInfo(
            id="flux-1-kontext-dev",
            object="model",
            created=int(time.time()),
            owned_by="black-forest-labs"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查API服务和模型的健康状态"
)
async def health_check():
    """健康检查
    
    检查API服务的健康状态，包括模型加载状态、GPU可用性等。
    
    Returns:
        HealthResponse: 健康状态信息
    """
    try:
        # 获取健康状态
        health_info = await health_checker.check_model_health()
        
        # 确定整体状态
        status = "healthy" if health_info.get("model_loaded", False) else "unhealthy"
        
        return HealthResponse(
            status=status,
            model_loaded=health_info.get("model_loaded", False),
            gpu_available=health_info.get("gpu_available", False),
            version=settings.app_version
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            gpu_available=False,
            version=settings.app_version
        )


@router.get(
    "/health/detailed",
    summary="详细健康检查",
    description="获取详细的系统健康信息，包括GPU内存使用情况"
)
async def detailed_health_check():
    """详细健康检查
    
    返回更详细的系统健康信息，包括GPU内存使用、模型状态等。
    
    Returns:
        dict: 详细的健康状态信息
    """
    try:
        import torch
        import psutil
        
        # 获取基本健康信息
        health_info = await health_checker.check_model_health()
        
        # 添加系统信息
        system_info = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # 添加GPU详细信息
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "gpu_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "device_name": torch.cuda.get_device_name(),
                "memory_allocated_mb": torch.cuda.memory_allocated() / 1024 / 1024,
                "memory_reserved_mb": torch.cuda.memory_reserved() / 1024 / 1024,
                "memory_total_mb": torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            }
        
        return {
            "status": "healthy" if health_info.get("model_loaded", False) else "unhealthy",
            "timestamp": int(time.time()),
            "version": settings.app_version,
            "model": {
                "name": settings.model_name,
                "loaded": health_info.get("model_loaded", False),
                "device": settings.device
            },
            "system": system_info,
            "gpu": gpu_info,
            "settings": {
                "max_batch_size": settings.max_batch_size,
                "max_image_size": settings.max_image_size,
                "default_guidance_scale": settings.default_guidance_scale,
                "default_num_inference_steps": settings.default_num_inference_steps
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return {
            "status": "error",
            "timestamp": int(time.time()),
            "error": str(e),
            "version": settings.app_version
        }


# 添加文档示例
list_models.__doc__ += """

**示例响应:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "flux-1-kontext-dev",
      "object": "model",
      "created": 1589478378,
      "owned_by": "black-forest-labs"
    }
  ]
}
```
"""

health_check.__doc__ += """

**示例响应:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "version": "1.0.0"
}
```
"""