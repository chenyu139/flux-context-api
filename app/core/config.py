from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本配置
    app_name: str = "FLUX.1-Kontext API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 模型配置
    model_name: str = "~/.cache/modelscope/hub/black-forest-labs/FLUX.1-Kontext-dev"
    device: str = "cuda"
    torch_dtype: str = "bfloat16"
    
    # 图片配置
    max_image_size: int = 2048
    min_image_size: int = 256
    default_image_size: int = 1024
    max_batch_size: int = 4
    
    # 生成参数默认值
    default_guidance_scale: float = 2.5
    default_num_inference_steps: int = 28
    max_num_inference_steps: int = 50
    
    # 文件存储
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    output_dir: str = "static/outputs"
    
    # API配置
    api_v1_prefix: str = "/v1"
    cors_origins: list = ["*"]
    
    # 安全配置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: list = ["image/jpeg", "image/png", "image/webp"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)