import time
import asyncio
from typing import List, Optional, Tuple
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import logging

from app.models.flux_model import model_manager
from app.models.schemas import (
    ImageGenerationRequest,
    ImageEditRequest,
    ImageVariationRequest,
    ResponseFormat
)
from app.utils.image_utils import (
    decode_base64_image,
    parse_image_size,
    validate_image_size,
    resize_image
)
from app.utils.response_utils import (
    create_image_response,
    validate_generation_params,
    log_request_info,
    create_success_log,
    calculate_processing_time
)
from app.core.exceptions import GenerationError, ImageProcessingError
from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    """图片生成服务类"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)  # 限制并发数
    
    async def generate_images(
        self,
        request: ImageGenerationRequest,
        base_url: str = ""
    ) -> dict:
        """生成图片"""
        start_time = time.time()
        
        try:
            # 记录请求信息
            log_request_info("generate_images", request.dict(), request.user)
            
            # 验证参数
            validate_generation_params(
                request.guidance_scale,
                request.num_inference_steps,
                request.n
            )
            
            # 解析图片尺寸
            width, height = parse_image_size(request.size)
            
            # 生成图片
            images = await self._generate_multiple_images(
                prompt=request.prompt,
                width=width,
                height=height,
                num_images=request.n,
                guidance_scale=request.guidance_scale,
                num_inference_steps=request.num_inference_steps,
                seed=request.seed
            )
            
            # 创建响应
            response = create_image_response(
                images=images,
                response_format=request.response_format,
                base_url=base_url
            )
            
            # 记录成功日志
            processing_time = calculate_processing_time(start_time)
            create_success_log("generate_images", processing_time, len(images), request.user)
            
            return response.dict()
            
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            raise GenerationError(f"Failed to generate images: {str(e)}")
    
    async def edit_image(
        self,
        request: ImageEditRequest,
        base_url: str = ""
    ) -> dict:
        """编辑图片"""
        start_time = time.time()
        
        try:
            # 记录请求信息
            log_request_info("edit_image", {k: v for k, v in request.dict().items() if k != 'image'}, request.user)
            
            # 验证参数
            validate_generation_params(
                request.guidance_scale,
                request.num_inference_steps,
                request.n
            )
            
            # 解码输入图片
            input_image = decode_base64_image(request.image)
            validate_image_size(input_image)
            
            # 调整图片尺寸（如果指定了size）
            if request.size:
                target_width, target_height = parse_image_size(request.size)
                if input_image.size != (target_width, target_height):
                    input_image = resize_image(input_image, (target_width, target_height))
            
            # 编辑图片
            images = await self._edit_multiple_images(
                image=input_image,
                prompt=request.prompt,
                num_images=request.n,
                guidance_scale=request.guidance_scale,
                num_inference_steps=request.num_inference_steps,
                seed=request.seed
            )
            
            # 创建响应
            response = create_image_response(
                images=images,
                response_format=request.response_format,
                base_url=base_url
            )
            
            # 记录成功日志
            processing_time = calculate_processing_time(start_time)
            create_success_log("edit_image", processing_time, len(images), request.user)
            
            return response.dict()
            
        except Exception as e:
            logger.error(f"Image editing failed: {str(e)}")
            raise GenerationError(f"Failed to edit image: {str(e)}")
    
    async def generate_variations(
        self,
        request: ImageVariationRequest,
        base_url: str = ""
    ) -> dict:
        """生成图片变体"""
        start_time = time.time()
        
        try:
            # 记录请求信息
            log_request_info("generate_variations", {k: v for k, v in request.dict().items() if k != 'image'}, request.user)
            
            # 验证参数
            validate_generation_params(
                request.guidance_scale,
                request.num_inference_steps,
                request.n
            )
            
            # 解码输入图片
            input_image = decode_base64_image(request.image)
            validate_image_size(input_image)
            
            # 调整图片尺寸（如果指定了size）
            if request.size:
                target_width, target_height = parse_image_size(request.size)
                if input_image.size != (target_width, target_height):
                    input_image = resize_image(input_image, (target_width, target_height))
            
            # 生成变体 - 支持多个提示词
            images = await self._generate_image_variations(
                image=input_image,
                prompts=request.prompts,
                guidance_scale=request.guidance_scale,
                num_inference_steps=request.num_inference_steps,
                variation_strength=request.variation_strength,
                seed=request.seed
            )
            
            # 创建响应
            response = create_image_response(
                images=images,
                response_format=request.response_format,
                base_url=base_url
            )
            
            # 记录成功日志
            processing_time = calculate_processing_time(start_time)
            create_success_log("generate_variations", processing_time, len(images), request.user)
            
            return response.dict()
            
        except Exception as e:
            logger.error(f"Variation generation failed: {str(e)}")
            raise GenerationError(f"Failed to generate variations: {str(e)}")
    
    async def _generate_multiple_images(
        self,
        prompt: str,
        width: int,
        height: int,
        num_images: int,
        guidance_scale: float,
        num_inference_steps: int,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """生成多张图片"""
        images = []
        
        for i in range(num_images):
            # 为每张图片设置不同的种子
            current_seed = seed + i if seed is not None else None
            
            # 在线程池中执行生成任务
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                self.executor,
                model_manager.generate_image,
                prompt,
                width,
                height,
                guidance_scale,
                num_inference_steps,
                current_seed
            )
            
            images.append(image)
        
        return images
    
    async def _edit_multiple_images(
        self,
        image: Image.Image,
        prompt: str,
        num_images: int,
        guidance_scale: float,
        num_inference_steps: int,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """编辑多张图片"""
        images = []
        
        for i in range(num_images):
            # 为每张图片设置不同的种子
            current_seed = seed + i if seed is not None else None
            
            # 在线程池中执行编辑任务
            loop = asyncio.get_event_loop()
            edited_image = await loop.run_in_executor(
                self.executor,
                model_manager.edit_image,
                image,
                prompt,
                guidance_scale,
                num_inference_steps,
                current_seed
            )
            
            images.append(edited_image)
        
        return images
    
    async def _generate_image_variations(
        self,
        image: Image.Image,
        prompts: List[str],
        guidance_scale: float,
        num_inference_steps: int,
        variation_strength: float,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """生成图片变体（多个提示词，每个提示词对应一个变体）"""
        images = []
        
        for i, prompt in enumerate(prompts):
            # 为每个提示词设置不同的种子
            current_seed = seed + i if seed is not None else None
            
            # 在线程池中执行变体生成任务
            loop = asyncio.get_event_loop()
            variation_image = await loop.run_in_executor(
                self.executor,
                model_manager.generate_variations,
                image,
                prompt,
                1,  # 每个提示词生成一张图片
                guidance_scale,
                num_inference_steps,
                variation_strength,
                current_seed
            )
            
            # generate_variations返回的是列表，取第一个元素
            if isinstance(variation_image, list):
                images.append(variation_image[0])
            else:
                images.append(variation_image)
        
        return images


# 全局图片服务实例
image_service = ImageService()