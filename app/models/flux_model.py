import torch
import logging
import threading
import os
from typing import List, Optional
from PIL import Image
import numpy as np
from diffusers import FluxKontextPipeline
from app.core.config import settings
from app.core.exceptions import ModelLoadError, GenerationError

logger = logging.getLogger(__name__)


class FluxModelManager:
    """FLUX模型管理器 - 单例模式"""
    
    _instance = None
    _pipeline = None
    _model_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FluxModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._lock = threading.Lock()
            # 延迟加载模型，不在初始化时加载
            logger.info("FluxModelManager initialized, model will be loaded on first use")
    
    def _ensure_model_loaded(self):
        """确保模型已加载"""
        if not self.is_loaded:
            with self._lock:
                if not self.is_loaded:  # 双重检查
                    self._load_model()
    
    def _load_model(self):
        """加载FLUX模型"""
        try:
            logger.info(f"Loading FLUX model: {settings.model_name}")
            
            # 设置torch数据类型
            torch_dtype = getattr(torch, settings.torch_dtype)
            
            # 展开用户目录路径
            model_path = os.path.expanduser(settings.model_name)
            
            # 加载模型
            self._pipeline = FluxKontextPipeline.from_pretrained(
                model_path,
                torch_dtype=torch_dtype
            )
            
            # 移动到指定设备
            if torch.cuda.is_available() and settings.device == "cuda":
                self._pipeline = self._pipeline.to("cuda")
                logger.info("Model loaded on CUDA")
            else:
                self._pipeline = self._pipeline.to("cpu")
                logger.info("Model loaded on CPU")
            
            self._model_loaded = True
            logger.info("FLUX model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FLUX model: {str(e)}")
            raise ModelLoadError(f"Failed to load model: {str(e)}")
    
    @property
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model_loaded and self._pipeline is not None
    
    @property
    def pipeline(self):
        """获取模型管道"""
        if not self.is_loaded:
            raise ModelLoadError("Model not loaded")
        return self._pipeline
    
    def load_model(self):
        """公共方法：主动加载模型"""
        if not self.is_loaded:
            logger.info("Starting model preload...")
            self._ensure_model_loaded()
            logger.info("Model preload completed")
        else:
            logger.info("Model already loaded")
    
    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 2.5,
        num_inference_steps: int = 28,
        seed: Optional[int] = None,
        **kwargs
    ) -> Image.Image:
        """生成图片"""
        self._ensure_model_loaded()
        
        try:
            # 设置随机种子
            generator = None
            if seed is not None:
                # 确保种子值在有效范围内 (0 到 2^32-1)
                safe_seed = abs(seed) % (2**32)
                generator = torch.Generator(device=self._pipeline.device)
                generator.manual_seed(safe_seed)
            
            # 生成图片
            result = self._pipeline(
                prompt=prompt,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
                **kwargs
            )
            
            return result.images[0]
            
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            raise GenerationError(f"Generation failed: {str(e)}")
    
    def edit_image(
        self,
        image: Image.Image,
        prompt: str,
        guidance_scale: float = 2.5,
        num_inference_steps: int = 28,
        seed: Optional[int] = None,
        **kwargs
    ) -> Image.Image:
        """编辑图片"""
        self._ensure_model_loaded()
        
        try:
            # 确保图片为RGB格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 设置随机种子
            generator = None
            if seed is not None:
                # 确保种子值在有效范围内 (0 到 2^32-1)
                safe_seed = abs(seed) % (2**32)
                generator = torch.Generator(device=self._pipeline.device)
                generator.manual_seed(safe_seed)
            
            # 编辑图片
            result = self._pipeline(
                image=image,
                prompt=prompt,
                width=image.size[0],
                height=image.size[1],
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
                **kwargs
            )
            
            return result.images[0]
            
        except Exception as e:
            logger.error(f"Image editing failed: {str(e)}")
            raise GenerationError(f"Editing failed: {str(e)}")
    
    def generate_variations(
        self,
        image: Image.Image,
        prompt: str,
        num_images: int = 1,
        guidance_scale: float = 2.5,
        num_inference_steps: int = 28,
        variation_strength: float = 0.7,
        seed: Optional[int] = None,
        **kwargs
    ) -> List[Image.Image]:
        """生成图片变体"""
        self._ensure_model_loaded()
        
        try:
            # 确保图片为RGB格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            images = []
            
            for i in range(num_images):
                # 为每张图片设置不同的种子
                current_seed = seed + i if seed is not None else None
                generator = None
                if current_seed is not None:
                    # 确保种子值在有效范围内 (0 到 2^32-1)
                    safe_seed = abs(current_seed) % (2**32)
                    generator = torch.Generator(device=self._pipeline.device)
                    generator.manual_seed(safe_seed)
                
                # 构建变体提示词
                variation_prompt = f"Based on this image, {prompt}. Keep the main subject but add variations."
                
                # 生成变体 - 移除不支持的strength参数
                result = self._pipeline(
                    image=image,
                    prompt=variation_prompt,
                    width=image.size[0],
                    height=image.size[1],
                    guidance_scale=guidance_scale,
                    num_inference_steps=num_inference_steps,
                    generator=generator,
                    **kwargs
                )
                
                images.append(result.images[0])
            
            return images
            
        except Exception as e:
            logger.error(f"Variation generation failed: {str(e)}")
            raise GenerationError(f"Variation generation failed: {str(e)}")


# 全局模型管理器实例
model_manager = FluxModelManager()