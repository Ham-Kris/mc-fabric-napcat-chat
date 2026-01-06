# MC-QQ Chat Bridge

🎮 Minecraft 服务器与 QQ 群消息双向同步桥接工具

基于 [NapCatQQ](https://github.com/NapNeko/NapCatQQ) 实现 QQ 群消息收发，使用 OpenAI Vision API 将图片/表情包/视频自动转换为文字描述。

## ✨ 功能特性

- **双向消息同步**: MC 服务器 ↔ QQ 群消息实时同步
- **玩家事件通知**: 玩家加入/离开服务器时通知 QQ 群
- **图片智能描述**: 使用 OpenAI Vision API 自动描述 QQ 群图片内容
- **表情包转换**: 将 QQ 表情包转换为文字描述
- **视频多模态描述**: 直接使用 VL 模型分析视频内容（支持 gpt-4o、gemini-2.0-flash 等）
- **灵活模型配置**: 可独立配置图片和视频的 API 端点及模型
- **完整身份显示**: QQ 消息显示昵称和 QQ 号

## 📦 项目结构

```
mc-fabric-chat/
├── fabric-mod/          # Minecraft Fabric Mod
│   ├── src/
│   │   └── main/
│   │       ├── java/    # Java 源码
│   │       └── resources/
│   ├── build.gradle
│   └── gradle.properties
├── backend/             # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes.py
│   │   ├── napcat_client.py
│   │   ├── message_handler.py
│   │   ├── message_queue.py
│   │   └── vision_service.py
│   ├── requirements.txt
│   └── run.py
└── README.md
```

## 🚀 快速开始

### 前置要求

1. **Minecraft 服务器**: 1.21.1 + Fabric Loader
2. **NapCatQQ**: 已配置并运行的 NapCat 实例
3. **Python**: 3.11+
4. **Java**: JDK 21+
5. **OpenAI API Key**: 用于图片描述功能（可选）

### 1. 配置 NapCat

确保 NapCat 已正确配置正向 WebSocket:

```yaml
# NapCat 配置
ws:
  enable: true
  host: "0.0.0.0"
  port: 3001
```

### 2. 部署后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp config.example.env .env

# 编辑配置
vim .env
```

配置文件 `.env`:

```env
# FastAPI 服务配置
HOST=0.0.0.0
PORT=8765
API_TOKEN=your-secret-token

# NapCat WebSocket 配置
NAPCAT_WS_URL=ws://localhost:3001
NAPCAT_ACCESS_TOKEN=your-napcat-token

# QQ 群配置
QQ_GROUP_ID=123456789

# OpenAI API 配置 (图片描述)
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 视频处理配置 (可选，不配置则使用上面的 OpenAI 配置)
# 支持视频的模型: gpt-4o, gemini-2.0-flash, qwen-vl-max 等
# VIDEO_API_KEY=your-video-api-key
# VIDEO_BASE_URL=https://api.openai.com/v1
# VIDEO_MODEL=gpt-4o
VIDEO_MAX_SIZE_MB=20
```

启动后端:

```bash
python run.py
```

### 3. 构建 Fabric Mod

```bash
cd fabric-mod

# 构建 mod
./gradlew build

# 生成的 jar 文件在 build/libs/ 目录
```

### 4. 安装 Mod

> ⚠️ **仅需服务端安装**：这是一个纯服务端 mod，客户端无需安装，原版客户端即可加入服务器。

1. 将 `mc-qq-chat-1.0.0.jar` 复制到服务器 `mods/` 目录
2. 启动服务器，会生成配置文件
3. 编辑 `config/mc-qq-chat.json`:

```json
{
  "backendUrl": "http://localhost:8765",
  "backendToken": "your-secret-token",
  "syncPlayerJoinLeave": true,
  "syncDeathMessages": true,
  "syncAchievements": true,
  "pollInterval": 1000
}
```

4. 重启服务器

## 📝 消息格式

### MC → QQ

```
[MC] 玩家名: 消息内容
```

### QQ → MC

```
§b[QQ] §e昵称§7(QQ号)§f: 消息内容
```

图片/视频消息:

```
§b[QQ] §e昵称§7(QQ号)§f: §d[图片] §7AI描述的内容
§b[QQ] §e昵称§7(QQ号)§f: §c[视频] §7视频封面描述
```

## 🔧 API 接口

### 健康检查

```http
GET /api/health
```

### 轮询消息

```http
GET /api/messages/poll
Authorization: Bearer <token>
```

### 发送消息

```http
POST /api/messages/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "player_chat",
  "player": "Steve",
  "message": "Hello!"
}
```

## 🛠️ 开发

### 后端开发

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
```

### Mod 开发

```bash
cd fabric-mod
./gradlew runServer  # 运行开发服务器
./gradlew runClient  # 运行开发客户端
```

## 📋 支持的消息类型

| QQ 消息类型 | MC 显示 |
|------------|---------|
| 文本消息 | 原文显示 |
| 图片 | [图片] + AI描述 |
| 表情包 | [表情包名称] |
| QQ表情 | [表情名称] |
| 视频 | [视频] + AI视频内容描述 |
| 语音 | [语音消息] |
| 文件 | [文件] 文件名 |
| @某人 | @昵称 |
| 合并转发 | [合并转发消息] |

## ⚠️ 注意事项

1. 确保后端和 NapCat 在同一网络或可相互访问
2. API Token 请使用强密码
3. OpenAI API 调用会产生费用，可关闭图片描述功能
4. 建议在防火墙后运行后端服务

## 📄 License

MIT License

## 🙏 致谢

- [NapCatQQ](https://github.com/NapNeko/NapCatQQ) - 现代化的 QQ 协议端实现
- [Fabric](https://fabricmc.net/) - Minecraft mod 开发框架
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Python Web 框架

