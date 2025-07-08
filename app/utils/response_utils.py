import time
from typing import List, Optional
from PIL import Image
from app.models.schemas import ImageResponse, ImageData, ResponseFormat
from app.utils.image_utils import encode_image_to_base64, save_image, create_image_url
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_image_response(
    images: List[Image.Image],
    response_format: ResponseFormat,
    base_url: str = "",
    revised_prompts: Optional[List[str]] = None
) -> ImageResponse:
    """创建图片响应对象"""
    try:
        image_data_list = []
        
        for i, image in enumerate(images):
            image_data = ImageData()
            
            if response_format == ResponseFormat.URL:
                # 保存图片并返回URL
                file_path = save_image(image)
                image_data.url = create_image_url(file_path, base_url)
            
            elif response_format == ResponseFormat.B64_JSON:
                # 返回base64编码
                image_data.b64_json = encode_image_to_base64(image, "PNG")
            
            # 添加修订后的提示词（如果有）
            if revised_prompts and i < len(revised_prompts):
                image_data.revised_prompt = revised_prompts[i]
            
            image_data_list.append(image_data)
        
        return ImageResponse(
            created=int(time.time()),
            data=image_data_list
        )
        
    except Exception as e:
        logger.error(f"Failed to create image response: {str(e)}")
        raise


def create_single_image_response(
    image: Image.Image,
    response_format: ResponseFormat,
    base_url: str = "",
    revised_prompt: Optional[str] = None
) -> ImageResponse:
    """创建单张图片响应对象"""
    revised_prompts = [revised_prompt] if revised_prompt else None
    return create_image_response([image], response_format, base_url, revised_prompts)


def format_error_response(message: str, error_type: str = "api_error", code: int = 400) -> dict:
    """格式化错误响应"""
    return {
        "error": {
            "message": message,
            "type": error_type,
            "code": code
        }
    }


def validate_generation_params(
    guidance_scale: float,
    num_inference_steps: int,
    n: int
) -> None:
    """验证生成参数"""
    from app.core.exceptions import InvalidParameters
    
    if not (1.0 <= guidance_scale <= 10.0):
        raise InvalidParameters(f"guidance_scale must be between 1.0 and 10.0, got {guidance_scale}")
    
    if not (1 <= num_inference_steps <= settings.max_num_inference_steps):
        raise InvalidParameters(f"num_inference_steps must be between 1 and {settings.max_num_inference_steps}, got {num_inference_steps}")
    
    if not (1 <= n <= settings.max_batch_size):
        raise InvalidParameters(f"n must be between 1 and {settings.max_batch_size}, got {n}")


def log_request_info(endpoint: str, params: dict, user_id: Optional[str] = None):
    """记录请求信息"""
    log_data = {
        "endpoint": endpoint,
        "user_id": user_id,
        "params": {
            k: v for k, v in params.items() 
            if k not in ['image']  # 不记录图片数据
        }
    }
    logger.info(f"API Request: {log_data}")


def calculate_processing_time(start_time: float) -> float:
    """计算处理时间"""
    return round(time.time() - start_time, 2)


def create_success_log(endpoint: str, processing_time: float, num_images: int, user_id: Optional[str] = None):
    """创建成功日志"""
    logger.info(f"API Success: {endpoint} - {num_images} images generated in {processing_time}s (user: {user_id})")


def get_base_url_from_request(request) -> str:
    """从请求中获取基础URL"""
    try:
        # 构建基础URL
        scheme = "https" if request.url.scheme == "https" else "http"
        host = request.headers.get("host", request.url.netloc)
        return f"{scheme}://{host}"
    except Exception:
        return ""


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    import re
    # 移除或替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:95] + ('.' + ext if ext else '')
    return filename


def create_batch_response(
    images_list: List[List[Image.Image]],
    response_format: ResponseFormat,
    base_url: str = ""
) -> List[ImageResponse]:
    """创建批量响应"""
    responses = []
    for images in images_list:
        response = create_image_response(images, response_format, base_url)
        responses.append(response)
    return responses