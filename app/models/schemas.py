from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Union
from enum import Enum
import base64
import io
from PIL import Image


class ResponseFormat(str, Enum):
    """响应格式枚举"""
    URL = "url"
    B64_JSON = "b64_json"


class ImageSize(str, Enum):
    """图片尺寸枚举"""
    SIZE_256 = "256x256"
    SIZE_512 = "512x512"
    SIZE_1024 = "1024x1024"
    SIZE_1792_1024 = "1792x1024"
    SIZE_1024_1792 = "1024x1792"


class BaseImageRequest(BaseModel):
    """基础图片请求模型"""
    prompt: str = Field(..., description="生成或编辑的提示词", min_length=1, max_length=4000)
    n: int = Field(1, description="生成图片数量", ge=1, le=10)
    size: Optional[str] = Field("1024x1024", description="图片尺寸")
    response_format: ResponseFormat = Field(ResponseFormat.URL, description="响应格式")
    user: Optional[str] = Field(None, description="用户标识")


class ImageGenerationRequest(BaseImageRequest):
    """图片生成请求模型"""
    guidance_scale: float = Field(2.5, description="引导强度", ge=1.0, le=10.0)
    num_inference_steps: int = Field(28, description="推理步数", ge=1, le=50)
    seed: Optional[int] = Field(None, description="随机种子")


class ImageEditRequest(BaseImageRequest):
    """图片编辑请求模型"""
    image: str = Field(..., description="base64编码的输入图片")
    guidance_scale: float = Field(2.5, description="引导强度", ge=1.0, le=10.0)
    num_inference_steps: int = Field(28, description="推理步数", ge=1, le=50)
    seed: Optional[int] = Field(None, description="随机种子")
    
    @validator('image')
    def validate_image(cls, v):
        """验证base64图片格式"""
        try:
            # 移除可能的data URL前缀
            if v.startswith('data:image'):
                v = v.split(',')[1]
            
            # 解码base64
            image_data = base64.b64decode(v)
            
            # 验证是否为有效图片
            image = Image.open(io.BytesIO(image_data))
            image.verify()
            
            return v
        except Exception:
            raise ValueError("Invalid base64 image format")


class ImageVariationRequest(BaseImageRequest):
    """图片变体生成请求模型"""
    image: str = Field(..., description="base64编码的参考图片")
    guidance_scale: float = Field(2.5, description="引导强度", ge=1.0, le=10.0)
    num_inference_steps: int = Field(28, description="推理步数", ge=1, le=50)
    seed: Optional[int] = Field(None, description="随机种子")
    variation_strength: float = Field(0.7, description="变体强度", ge=0.1, le=1.0)
    
    @validator('image')
    def validate_image(cls, v):
        """验证base64图片格式"""
        try:
            if v.startswith('data:image'):
                v = v.split(',')[1]
            
            image_data = base64.b64decode(v)
            image = Image.open(io.BytesIO(image_data))
            image.verify()
            
            return v
        except Exception:
            raise ValueError("Invalid base64 image format")


class ImageData(BaseModel):
    """图片数据模型"""
    url: Optional[str] = Field(None, description="图片URL")
    b64_json: Optional[str] = Field(None, description="base64编码的图片")
    revised_prompt: Optional[str] = Field(None, description="修订后的提示词")


class ImageResponse(BaseModel):
    """图片响应模型"""
    created: int = Field(..., description="创建时间戳")
    data: List[ImageData] = Field(..., description="生成的图片数据")


class ModelInfo(BaseModel):
    """模型信息模型"""
    id: str = Field(..., description="模型ID")
    object: str = Field("model", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    owned_by: str = Field(..., description="拥有者")


class ModelsResponse(BaseModel):
    """模型列表响应模型"""
    object: str = Field("list", description="对象类型")
    data: List[ModelInfo] = Field(..., description="模型列表")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field("healthy", description="服务状态")
    model_loaded: bool = Field(..., description="模型是否已加载")
    gpu_available: bool = Field(..., description="GPU是否可用")
    version: str = Field(..., description="API版本")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: dict = Field(..., description="错误信息")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "message": "Invalid image format",
                    "type": "invalid_request_error",
                    "code": 400
                }
            }
        }