#!/usr/bin/env python3
"""
FLUX.1-Kontext API 测试脚本

用法:
    python test_api.py --host localhost --port 8000
    python test_api.py --full-test  # 完整测试
    python test_api.py --load-test  # 负载测试
"""

import argparse
import asyncio
import base64
import json
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import requests
from PIL import Image


class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_test_image(self, size: tuple = (512, 512), color: str = "red") -> str:
        """创建测试图片并返回base64编码"""
        img = Image.new('RGB', size, color=color)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    async def test_health_check(self) -> bool:
        """测试健康检查接口"""
        try:
            async with self.session.get(f"{self.base_url}/ping") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", True, f"Status: {data.get('status')}")
                    return True
                else:
                    self.log_test("Health Check", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    async def test_detailed_health(self) -> bool:
        """测试详细健康检查"""
        try:
            async with self.session.get(f"{self.base_url}/v1/health/detailed") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Detailed Health", True, 
                                f"Model: {data.get('model_status')}, Device: {data.get('device')}")
                    return True
                else:
                    self.log_test("Detailed Health", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Detailed Health", False, str(e))
            return False
    
    async def test_models_list(self) -> bool:
        """测试模型列表接口"""
        try:
            async with self.session.get(f"{self.base_url}/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    self.log_test("Models List", True, f"Found {len(models)} models")
                    return True
                else:
                    self.log_test("Models List", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Models List", False, str(e))
            return False
    
    async def test_image_generation(self) -> bool:
        """测试图片生成接口"""
        try:
            payload = {
                "prompt": "A beautiful sunset over mountains",
                "n": 1,
                "size": "512x512",
                "response_format": "b64_json"
            }
            
            async with self.session.post(
                f"{self.base_url}/v1/images/generations",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    images = data.get('data', [])
                    self.log_test("Image Generation", True, f"Generated {len(images)} images")
                    return True
                else:
                    text = await response.text()
                    self.log_test("Image Generation", False, f"HTTP {response.status}: {text[:100]}")
                    return False
        except Exception as e:
            self.log_test("Image Generation", False, str(e))
            return False
    
    async def test_image_edit(self) -> bool:
        """测试图片编辑接口"""
        try:
            test_image = self.create_test_image()
            
            payload = {
                "image": test_image,
                "prompt": "Add a rainbow in the sky",
                "n": 1,
                "size": "512x512",
                "response_format": "b64_json"
            }
            
            async with self.session.post(
                f"{self.base_url}/v1/images/edits",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    images = data.get('data', [])
                    self.log_test("Image Edit", True, f"Edited {len(images)} images")
                    return True
                else:
                    text = await response.text()
                    self.log_test("Image Edit", False, f"HTTP {response.status}: {text[:100]}")
                    return False
        except Exception as e:
            self.log_test("Image Edit", False, str(e))
            return False
    
    async def test_image_variations(self) -> bool:
        """测试图片变体接口"""
        try:
            test_image = self.create_test_image()
            
            payload = {
                "image": test_image,
                "prompt": "Same subject, different style",
                "n": 2,
                "size": "512x512",
                "response_format": "b64_json"
            }
            
            async with self.session.post(
                f"{self.base_url}/v1/images/variations",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    images = data.get('data', [])
                    self.log_test("Image Variations", True, f"Generated {len(images)} variations")
                    return True
                else:
                    text = await response.text()
                    self.log_test("Image Variations", False, f"HTTP {response.status}: {text[:100]}")
                    return False
        except Exception as e:
            self.log_test("Image Variations", False, str(e))
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理"""
        try:
            # 测试无效的图片数据
            payload = {
                "image": "invalid_base64_data",
                "prompt": "Test prompt",
                "n": 1
            }
            
            async with self.session.post(
                f"{self.base_url}/v1/images/edits",
                json=payload
            ) as response:
                if response.status == 400:
                    self.log_test("Error Handling", True, "Correctly rejected invalid image")
                    return True
                else:
                    self.log_test("Error Handling", False, f"Expected 400, got {response.status}")
                    return False
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False
    
    async def run_basic_tests(self) -> Dict[str, bool]:
        """运行基础测试"""
        print("🚀 Running basic API tests...\n")
        
        results = {}
        results['health'] = await self.test_health_check()
        results['detailed_health'] = await self.test_detailed_health()
        results['models'] = await self.test_models_list()
        results['error_handling'] = await self.test_error_handling()
        
        return results
    
    async def run_full_tests(self) -> Dict[str, bool]:
        """运行完整测试"""
        print("🚀 Running full API tests...\n")
        
        results = await self.run_basic_tests()
        
        print("\n📸 Testing image generation features...\n")
        results['generation'] = await self.test_image_generation()
        results['edit'] = await self.test_image_edit()
        results['variations'] = await self.test_image_variations()
        
        return results
    
    async def run_load_test(self, concurrent_requests: int = 5, total_requests: int = 20):
        """运行负载测试"""
        print(f"🔥 Running load test: {concurrent_requests} concurrent, {total_requests} total...\n")
        
        async def single_request():
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}/ping") as response:
                    success = response.status == 200
                    duration = time.time() - start_time
                    return success, duration
            except Exception:
                duration = time.time() - start_time
                return False, duration
        
        # 运行并发请求
        all_tasks = []
        for batch in range(0, total_requests, concurrent_requests):
            batch_size = min(concurrent_requests, total_requests - batch)
            tasks = [single_request() for _ in range(batch_size)]
            batch_results = await asyncio.gather(*tasks)
            all_tasks.extend(batch_results)
            
            # 短暂延迟避免过载
            if batch + batch_size < total_requests:
                await asyncio.sleep(0.1)
        
        # 统计结果
        successful = sum(1 for success, _ in all_tasks if success)
        durations = [duration for _, duration in all_tasks]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        print(f"📊 Load test results:")
        print(f"   Success rate: {successful}/{total_requests} ({successful/total_requests*100:.1f}%)")
        print(f"   Average response time: {avg_duration:.3f}s")
        print(f"   Min response time: {min_duration:.3f}s")
        print(f"   Max response time: {max_duration:.3f}s")
        
        return successful / total_requests >= 0.95  # 95% success rate threshold


def print_summary(results: Dict[str, bool]):
    """打印测试总结"""
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the API implementation.")


async def main():
    parser = argparse.ArgumentParser(description="FLUX.1-Kontext API Tester")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--full-test", action="store_true", help="Run full tests including image generation")
    parser.add_argument("--load-test", action="store_true", help="Run load test")
    parser.add_argument("--concurrent", type=int, default=5, help="Concurrent requests for load test")
    parser.add_argument("--total", type=int, default=20, help="Total requests for load test")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    print(f"🔗 Testing API at: {base_url}")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with APITester(base_url) as tester:
        if args.load_test:
            success = await tester.run_load_test(args.concurrent, args.total)
            print(f"\n{'✅' if success else '❌'} Load test {'passed' if success else 'failed'}")
        elif args.full_test:
            results = await tester.run_full_tests()
            print_summary(results)
        else:
            results = await tester.run_basic_tests()
            print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())