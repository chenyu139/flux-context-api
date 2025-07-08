from fastapi import APIRouter
from app.api.v1 import images, models

# 创建v1版本的API路由器
api_router = APIRouter()

# 包含所有v1接口
api_router.include_router(images.router)
api_router.include_router(models.router)

# 导出路由器
__all__ = ["api_router"]