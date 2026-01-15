from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # FastAPI 服务配置
    host: str = "0.0.0.0"
    port: int = 8765
    api_token: str = "your-secret-token"

    # NapCat WebSocket 配置
    napcat_ws_url: str = "ws://localhost:3001"
    napcat_access_token: Optional[str] = None

    # QQ 群配置
    qq_group_id: int = 123456789
    bot_qq: int = 0  # 机器人QQ号，用于检测@机器人
    admin_qq: str = ""  # 管理员QQ号，多个用逗号分隔，可控制服务器
    
    # MC 服务器路径配置
    mc_server_dir: str = "/www/wwwroot/mc/server"  # MC服务器目录
    mc_screen_name: str = "mc"  # screen会话名称

    # OpenAI API 配置 - 图片描述
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # 视频描述配置（可选，如不配置则使用图片模型配置）
    # 支持直接处理视频的 VL 模型，如 gpt-4o, gemini-2.0-flash 等
    video_api_key: Optional[str] = None
    video_base_url: Optional[str] = None
    video_model: Optional[str] = None

    # 视频处理配置
    video_max_size_mb: int = 20  # 视频最大尺寸 (MB)
    video_supported_formats: str = "mp4,webm,mov,avi"  # 支持的视频格式

    # 日志级别
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_video_api_key(self) -> str:
        """获取视频处理的 API Key"""
        return self.video_api_key or self.openai_api_key

    def get_video_base_url(self) -> str:
        """获取视频处理的 Base URL"""
        return self.video_base_url or self.openai_base_url

    def get_video_model(self) -> str:
        """获取视频处理的模型名称"""
        return self.video_model or self.openai_model


settings = Settings()
