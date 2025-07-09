from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Optional
import logging

from app.models.schemas import (
    ImageGenerationRequest,
    ImageEditRequest,
    ImageVariationRequest,
    ImageResponse,
    ErrorResponse
)
from app.services.image_service import image_service
from app.api.dependencies import (
    verify_model_loaded,
    get_base_url,
    get_current_user,
    check_rate_limit,
    validate_request_size,
    log_request
)
from app.core.exceptions import APIException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.post(
    "/generations",
    response_model=ImageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="生成图片",
    description="根据文本提示词生成图片"
)
async def generate_images(
    request_data: ImageGenerationRequest,
    request: Request,
    base_url: str = Depends(get_base_url),
    user_id: Optional[str] = Depends(get_current_user),
    _: bool = Depends(verify_model_loaded),
    __: bool = Depends(check_rate_limit),
    ___: bool = Depends(validate_request_size),
    ____: dict = Depends(log_request)
):
    """生成图片
    
    根据提供的文本提示词生成一张或多张图片。
    
    Args:
        request_data: 图片生成请求参数
        
    Returns:
        ImageResponse: 包含生成图片的响应对象
        
    Raises:
        HTTPException: 当请求参数无效或生成失败时
    """
    try:
        # 设置用户ID
        if user_id:
            request_data.user = user_id
        
        # 调用图片生成服务
        result = await image_service.generate_images(request_data, base_url)
        
        return result
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/edits",
    response_model=ImageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        413: {"model": ErrorResponse, "description": "Image Too Large"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="编辑图片",
    description="根据输入图片和文本提示词编辑图片"
)
async def edit_image(
    request_data: ImageEditRequest,
    request: Request,
    base_url: str = Depends(get_base_url),
    user_id: Optional[str] = Depends(get_current_user),
    _: bool = Depends(verify_model_loaded),
    __: bool = Depends(check_rate_limit),
    ___: bool = Depends(validate_request_size),
    ____: dict = Depends(log_request)
):
    """编辑图片
    
    基于输入图片和文本提示词对图片进行编辑修改。
    
    Args:
        request_data: 图片编辑请求参数，包含base64编码的图片和编辑指令
        
    Returns:
        ImageResponse: 包含编辑后图片的响应对象
        
    Raises:
        HTTPException: 当图片格式无效、请求参数错误或编辑失败时
    """
    try:
        # 设置用户ID
        if user_id:
            request_data.user = user_id
        
        # 调用图片编辑服务
        result = await image_service.edit_image(request_data, base_url)
        
        return result
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in edit_image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/variations",
    response_model=ImageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        413: {"model": ErrorResponse, "description": "Image Too Large"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="生成图片变体",
    description="基于参考图片和提示词生成多个变体图片"
)
async def generate_variations(
    request_data: ImageVariationRequest,
    request: Request,
    base_url: str = Depends(get_base_url),
    user_id: Optional[str] = Depends(get_current_user),
    _: bool = Depends(verify_model_loaded),
    __: bool = Depends(check_rate_limit),
    ___: bool = Depends(validate_request_size),
    ____: dict = Depends(log_request)
):
    """生成图片变体
    
    基于参考图片和文本提示词生成多个保持主体一致但有变化的图片。
    
    Args:
        request_data: 图片变体生成请求参数，包含参考图片、提示词和生成数量
        
    Returns:
        ImageResponse: 包含生成的变体图片的响应对象
        
    Raises:
        HTTPException: 当图片格式无效、请求参数错误或生成失败时
    """
    try:
        # 设置用户ID
        if user_id:
            request_data.user = user_id
        
        # 调用图片变体生成服务
        result = await image_service.generate_variations(request_data, base_url)
        
        return result
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_variations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# 添加一些示例到OpenAPI文档
generate_images.__doc__ += """

**示例请求:**
```json
{
  "prompt": "一只可爱的小猫坐在花园里",
  "n": 2,
  "size": "1024x1024",
  "response_format": "url",
  "guidance_scale": 2.5,
  "num_inference_steps": 28
}
```

**示例响应:**
```json
{
  "created": 1589478378,
  "data": [
    {
      "url": "https://api.example.com/static/outputs/image1.png"
    },
    {
      "url": "https://api.example.com/static/outputs/image2.png"
    }
  ]
}
```
"""

edit_image.__doc__ += """

**示例请求:**
```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "prompt": "给这只猫戴上一顶帽子",
  "n": 1,
  "size": "1024x1024",
  "response_format": "url",
  "guidance_scale": 2.5
}
```
"""

generate_variations.__doc__ += """

**示例请求:**
```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "prompts": [
    "保持主体，改变背景为海滩",
    "保持主体，改变背景为森林",
    "保持主体，改变背景为城市夜景"
  ],
  "size": "1024x1024",
  "response_format": "url",
  "variation_strength": 0.7
}
```

**注意:** 每个提示词对应生成一张变体图片，图片数量等于提示词数量。
"""