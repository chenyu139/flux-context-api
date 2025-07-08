from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """基础API异常类"""
    
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class ModelLoadError(APIException):
    """模型加载错误"""
    
    def __init__(self, detail: str = "Failed to load model"):
        super().__init__(status_code=500, detail=detail, error_code="MODEL_LOAD_ERROR")


class ImageProcessingError(APIException):
    """图片处理错误"""
    
    def __init__(self, detail: str = "Image processing failed"):
        super().__init__(status_code=400, detail=detail, error_code="IMAGE_PROCESSING_ERROR")


class InvalidImageFormat(APIException):
    """无效图片格式"""
    
    def __init__(self, detail: str = "Invalid image format"):
        super().__init__(status_code=400, detail=detail, error_code="INVALID_IMAGE_FORMAT")


class ImageTooLarge(APIException):
    """图片过大"""
    
    def __init__(self, detail: str = "Image size exceeds maximum limit"):
        super().__init__(status_code=413, detail=detail, error_code="IMAGE_TOO_LARGE")


class GenerationError(APIException):
    """生成错误"""
    
    def __init__(self, detail: str = "Image generation failed"):
        super().__init__(status_code=500, detail=detail, error_code="GENERATION_ERROR")


class InvalidParameters(APIException):
    """无效参数"""
    
    def __init__(self, detail: str = "Invalid parameters"):
        super().__init__(status_code=422, detail=detail, error_code="INVALID_PARAMETERS")


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API异常处理器"""
    logger.error(f"API Exception: {exc.detail} (Code: {exc.error_code})")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": exc.error_code or "api_error",
                "code": exc.status_code
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_error",
                "code": 500
            }
        }
    )