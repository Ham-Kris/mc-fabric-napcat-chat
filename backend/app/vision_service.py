import base64
import logging
import httpx
from typing import Optional
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class VisionService:
    """OpenAI Vision API 服务 - 支持图片和视频多模态"""

    def __init__(self):
        # 图片处理客户端
        self.image_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        # 视频处理客户端（可能使用不同的模型/API）
        self._video_client: Optional[AsyncOpenAI] = None

    @property
    def video_client(self) -> AsyncOpenAI:
        """获取视频处理客户端（懒加载）"""
        if self._video_client is None:
            self._video_client = AsyncOpenAI(
                api_key=settings.get_video_api_key(),
                base_url=settings.get_video_base_url()
            )
        return self._video_client

    async def describe_image(self, image_url: str) -> str:
        """使用 Vision API 描述图片"""
        if not settings.openai_api_key:
            return "[未配置 OpenAI API，无法描述图片]"

        try:
            # 下载图片并转换为 base64
            image_data = await self._download_media(image_url)
            if not image_data:
                return "[无法获取图片]"

            base64_image = base64.b64encode(image_data).decode("utf-8")
            
            # 检测图片类型
            mime_type = self._detect_image_mime_type(image_data)

            response = await self.image_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个图片描述助手。请用简洁的中文（不超过50字）描述图片的主要内容。如果是表情包，描述表情包表达的情绪或含义。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请简洁描述这张图片的内容。"
                            }
                        ]
                    }
                ],
                max_tokens=100
            )

            description = response.choices[0].message.content
            logger.info(f"Image description: {description}")
            return description

        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return f"[图片描述失败: {str(e)[:30]}]"

    async def describe_video(self, video_url: str) -> str:
        """使用 VL 模型直接描述视频内容"""
        api_key = settings.get_video_api_key()
        if not api_key:
            return "[未配置视频 API，无法描述视频]"

        try:
            # 下载视频
            video_data = await self._download_media(
                video_url, 
                max_size_mb=settings.video_max_size_mb
            )
            if not video_data:
                return "[无法获取视频或视频过大]"

            base64_video = base64.b64encode(video_data).decode("utf-8")
            
            # 检测视频类型
            mime_type = self._detect_video_mime_type(video_data)
            
            logger.info(f"Processing video: {len(video_data)} bytes, type: {mime_type}")

            # 使用支持视频的 VL 模型
            response = await self.video_client.chat.completions.create(
                model=settings.get_video_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个视频描述助手。请用简洁的中文（不超过80字）描述视频的主要内容，包括场景、动作和关键信息。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": f"data:{mime_type};base64,{base64_video}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请简洁描述这个视频的内容。"
                            }
                        ]
                    }
                ],
                max_tokens=150
            )

            description = response.choices[0].message.content
            logger.info(f"Video description: {description}")
            return description

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Video API error: {error_msg}")
            
            # 如果模型不支持视频，尝试降级到图片处理（使用封面）
            if "video" in error_msg.lower() or "unsupported" in error_msg.lower():
                logger.info("Video not supported by model, trying fallback...")
                return await self._describe_video_fallback(video_url)
            
            return f"[视频描述失败: {error_msg[:30]}]"

    async def _describe_video_fallback(self, video_url: str) -> str:
        """视频描述降级方案 - 尝试提取关键帧或返回默认"""
        # 这里可以扩展：提取视频帧作为图片处理
        # 目前返回简单提示
        return "[视频 - 当前模型不支持视频描述]"

    async def describe_video_with_cover(self, video_url: str, cover_url: Optional[str] = None) -> str:
        """描述视频，优先直接处理视频，如果失败则使用封面"""
        # 首先尝试直接处理视频
        result = await self.describe_video(video_url)
        
        # 如果视频处理失败且有封面，使用封面
        if "失败" in result or "不支持" in result:
            if cover_url:
                logger.info("Falling back to video cover description")
                cover_result = await self.describe_image(cover_url)
                if "失败" not in cover_result:
                    return f"(封面) {cover_result}"
        
        return result

    async def describe_mface(self, summary: str) -> str:
        """描述表情包（使用 summary）"""
        if summary:
            return summary
        return "[表情包]"

    async def _download_media(self, url: str, max_size_mb: int = 50) -> Optional[bytes]:
        """下载媒体文件"""
        try:
            max_size = max_size_mb * 1024 * 1024  # 转换为字节
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 先获取文件大小
                head_response = await client.head(url, follow_redirects=True)
                content_length = head_response.headers.get("content-length")
                
                if content_length and int(content_length) > max_size:
                    logger.warning(f"Media too large: {content_length} bytes > {max_size} bytes")
                    return None
                
                # 下载文件
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    content = response.content
                    if len(content) > max_size:
                        logger.warning(f"Downloaded media too large: {len(content)} bytes")
                        return None
                    return content
                    
                logger.warning(f"Failed to download media: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Download media error: {e}")
            return None

    def _detect_image_mime_type(self, data: bytes) -> str:
        """检测图片 MIME 类型"""
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif data[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "image/webp"
        else:
            return "image/jpeg"  # 默认

    def _detect_video_mime_type(self, data: bytes) -> str:
        """检测视频 MIME 类型"""
        # MP4 (ftyp box)
        if len(data) > 8 and data[4:8] == b'ftyp':
            return "video/mp4"
        # WebM
        if data[:4] == b'\x1a\x45\xdf\xa3':
            return "video/webm"
        # AVI
        if data[:4] == b'RIFF' and data[8:12] == b'AVI ':
            return "video/avi"
        # MOV
        if len(data) > 8 and data[4:8] in (b'moov', b'mdat', b'free', b'wide'):
            return "video/quicktime"
        # 默认 MP4
        return "video/mp4"


# 全局服务实例
vision_service = VisionService()
