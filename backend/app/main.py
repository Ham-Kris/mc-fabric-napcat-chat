import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import json

from app.config import settings
from app.routes import router
from app.napcat_client import napcat_client
from app.message_handler import message_handler

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting MC-QQ Chat Bridge Backend...")
    
    # 设置消息处理器
    napcat_client.set_message_handler(message_handler.handle_qq_message)
    
    # 启动 NapCat 客户端连接
    napcat_task = asyncio.create_task(napcat_client.connect())
    
    logger.info(f"Backend started on {settings.host}:{settings.port}")
    logger.info(f"NapCat WebSocket: {settings.napcat_ws_url}")
    logger.info(f"Target QQ Group: {settings.qq_group_id}")
    
    yield
    
    # 关闭连接
    logger.info("Shutting down MC-QQ Chat Bridge Backend...")
    napcat_task.cancel()
    await napcat_client.close()


app = FastAPI(
    title="MC-QQ Chat Bridge",
    description="Bridge between Minecraft and QQ groups via NapCat",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path == "/api/messages/send" and request.method == "POST":
        body = await request.body()
        headers = dict(request.headers)
        logger.info(f"Raw POST body: {body}, headers: {headers}")
        # 重新创建request以便后续使用
        async def receive():
            return {"type": "http.request", "body": body}
        request = Request(request.scope, receive)
    response = await call_next(request)
    return response

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "MC-QQ Chat Bridge",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

