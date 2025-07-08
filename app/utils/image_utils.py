import base64
import io
import os
import uuid
from typing import Tuple, Optional
from PIL import Image
import numpy as np
from app.core.config import settings
from app.core.exceptions import InvalidImageFormat, ImageTooLarge, ImageProcessingError


def decode_base64_image(base64_string: str) -> Image.Image:
    """解码base64图片"""
    try:
        # 移除可能的data URL前缀
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        # 解码base64
        image_data = base64.b64decode(base64_string)
        
        # 检查文件大小
        if len(image_data) > settings.max_file_size:
            raise ImageTooLarge(f"Image size {len(image_data)} exceeds maximum {settings.max_file_size} bytes")
        
        # 创建PIL图片对象
        image = Image.open(io.BytesIO(image_data))
        
        # 验证图片格式
        if image.format.lower() not in ['jpeg', 'jpg', 'png', 'webp']:
            raise InvalidImageFormat(f"Unsupported image format: {image.format}")
        
        return image
        
    except Exception as e:
        if isinstance(e, (InvalidImageFormat, ImageTooLarge)):
            raise
        raise InvalidImageFormat(f"Failed to decode base64 image: {str(e)}")


def encode_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """将PIL图片编码为base64字符串"""
    try:
        buffer = io.BytesIO()
        
        # 确保图片为RGB模式（PNG需要）
        if format.upper() == "PNG" and image.mode in ("RGBA", "LA"):
            # 保持透明度
            pass
        elif image.mode != "RGB":
            image = image.convert("RGB")
        
        # 保存到缓冲区
        image.save(buffer, format=format, quality=95 if format.upper() == "JPEG" else None)
        
        # 编码为base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
        
    except Exception as e:
        raise ImageProcessingError(f"Failed to encode image to base64: {str(e)}")


def save_image(image: Image.Image, filename: Optional[str] = None, directory: str = None) -> str:
    """保存图片到文件系统并返回文件路径"""
    try:
        if directory is None:
            directory = settings.output_dir
        
        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
        
        # 生成文件名
        if filename is None:
            filename = f"{uuid.uuid4().hex}.png"
        
        # 完整文件路径
        file_path = os.path.join(directory, filename)
        
        # 确保图片为RGB模式
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # 保存图片
        image.save(file_path, "PNG", quality=95)
        
        return file_path
        
    except Exception as e:
        raise ImageProcessingError(f"Failed to save image: {str(e)}")


def resize_image(image: Image.Image, target_size: Tuple[int, int], maintain_aspect_ratio: bool = True) -> Image.Image:
    """调整图片尺寸"""
    try:
        if maintain_aspect_ratio:
            # 保持宽高比
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # 如果需要精确尺寸，创建新图片并居中粘贴
            if image.size != target_size:
                new_image = Image.new("RGB", target_size, (255, 255, 255))
                paste_x = (target_size[0] - image.size[0]) // 2
                paste_y = (target_size[1] - image.size[1]) // 2
                new_image.paste(image, (paste_x, paste_y))
                return new_image
            
            return image
        else:
            # 直接调整到目标尺寸
            return image.resize(target_size, Image.Resampling.LANCZOS)
            
    except Exception as e:
        raise ImageProcessingError(f"Failed to resize image: {str(e)}")


def validate_image_size(image: Image.Image) -> bool:
    """验证图片尺寸是否在允许范围内"""
    width, height = image.size
    
    # 检查最小尺寸
    if width < settings.min_image_size or height < settings.min_image_size:
        raise InvalidImageFormat(f"Image size {width}x{height} is too small. Minimum size is {settings.min_image_size}x{settings.min_image_size}")
    
    # 检查最大尺寸
    if width > settings.max_image_size or height > settings.max_image_size:
        raise InvalidImageFormat(f"Image size {width}x{height} is too large. Maximum size is {settings.max_image_size}x{settings.max_image_size}")
    
    return True


def parse_image_size(size_string: str) -> Tuple[int, int]:
    """解析图片尺寸字符串 (例如: "1024x1024")"""
    try:
        if 'x' not in size_string:
            raise ValueError("Invalid size format")
        
        width_str, height_str = size_string.split('x')
        width = int(width_str)
        height = int(height_str)
        
        # 验证尺寸范围
        if width < settings.min_image_size or height < settings.min_image_size:
            raise ValueError(f"Size too small. Minimum: {settings.min_image_size}x{settings.min_image_size}")
        
        if width > settings.max_image_size or height > settings.max_image_size:
            raise ValueError(f"Size too large. Maximum: {settings.max_image_size}x{settings.max_image_size}")
        
        return (width, height)
        
    except Exception as e:
        raise InvalidImageFormat(f"Invalid image size format '{size_string}': {str(e)}")


def create_image_url(file_path: str, base_url: str = "") -> str:
    """创建图片访问URL"""
    # 获取相对于static目录的路径
    relative_path = os.path.relpath(file_path, settings.static_dir)
    
    # 构建URL
    url = f"{base_url}/static/{relative_path}".replace('\\', '/')
    
    return url


def cleanup_temp_files(file_paths: list):
    """清理临时文件"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # 记录错误但不抛出异常
            import logging
            logging.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")


def get_image_info(image: Image.Image) -> dict:
    """获取图片信息"""
    return {
        "width": image.size[0],
        "height": image.size[1],
        "mode": image.mode,
        "format": image.format,
        "size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else None
    }