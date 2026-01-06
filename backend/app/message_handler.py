import logging
from typing import Optional

from app.config import settings
from app.models import QqMessage
from app.message_queue import message_queue
from app.vision_service import vision_service
from app.napcat_client import napcat_client

logger = logging.getLogger(__name__)


class MessageHandler:
    """消息处理器"""

    async def handle_qq_message(self, data: dict):
        """处理来自 QQ 的消息"""
        message_type = data.get("message_type")
        
        # 只处理群消息
        if message_type != "group":
            return

        group_id = data.get("group_id")
        
        # 检查是否是目标群
        if group_id != settings.qq_group_id:
            return

        sender = data.get("sender", {})
        user_id = str(sender.get("user_id", "0"))
        nickname = sender.get("nickname", "Unknown")
        card = sender.get("card", "")  # 群名片
        
        # 优先使用群名片
        display_name = card if card else nickname

        message_segments = data.get("message", [])
        
        # 处理消息段
        await self._process_message_segments(message_segments, display_name, user_id)

    async def _process_message_segments(self, segments: list, nickname: str, qq: str):
        """处理消息段"""
        text_parts = []
        
        for segment in segments:
            seg_type = segment.get("type")
            seg_data = segment.get("data", {})

            if seg_type == "text":
                # 纯文本
                text = seg_data.get("text", "").strip()
                if text:
                    text_parts.append(text)

            elif seg_type == "image":
                # 图片
                url = seg_data.get("url", "")
                summary = seg_data.get("summary", "")
                
                if summary and summary != "[图片]":
                    # 使用已有的摘要
                    description = summary
                elif url:
                    # 使用 Vision API 描述
                    description = await vision_service.describe_image(url)
                else:
                    description = "[图片]"

                msg = QqMessage(
                    type="image",
                    nickname=nickname,
                    qq=qq,
                    content="",
                    description=description
                )
                await message_queue.push(msg)

            elif seg_type == "mface":
                # 表情包
                summary = seg_data.get("summary", "")
                face_name = summary if summary else "表情包"

                msg = QqMessage(
                    type="face",
                    nickname=nickname,
                    qq=qq,
                    content="",
                    face_name=face_name
                )
                await message_queue.push(msg)

            elif seg_type == "face":
                # QQ 表情
                face_id = seg_data.get("id", "")
                face_name = self._get_face_name(face_id)

                msg = QqMessage(
                    type="face",
                    nickname=nickname,
                    qq=qq,
                    content="",
                    face_name=face_name
                )
                await message_queue.push(msg)

            elif seg_type == "video":
                # 视频 - 直接使用 VL 模型处理视频
                video_url = seg_data.get("url", "")
                cover_url = seg_data.get("cover", "")
                
                if video_url:
                    # 优先直接处理视频，失败时使用封面
                    description = await vision_service.describe_video_with_cover(
                        video_url, cover_url
                    )
                elif cover_url:
                    # 只有封面，使用图片描述
                    description = await vision_service.describe_image(cover_url)
                else:
                    description = "[视频]"

                msg = QqMessage(
                    type="video",
                    nickname=nickname,
                    qq=qq,
                    content="",
                    description=description
                )
                await message_queue.push(msg)

            elif seg_type == "record":
                # 语音
                msg = QqMessage(
                    type="chat",
                    nickname=nickname,
                    qq=qq,
                    content="[语音消息]"
                )
                await message_queue.push(msg)

            elif seg_type == "at":
                # @某人
                at_qq = seg_data.get("qq", "")
                at_name = seg_data.get("name", "")
                if at_qq == "all":
                    text_parts.append("@全体成员")
                else:
                    text_parts.append(f"@{at_name or at_qq}")

            elif seg_type == "reply":
                # 回复消息
                text_parts.append("[回复]")

            elif seg_type == "forward":
                # 合并转发
                msg = QqMessage(
                    type="chat",
                    nickname=nickname,
                    qq=qq,
                    content="[合并转发消息]"
                )
                await message_queue.push(msg)

            elif seg_type == "file":
                # 文件
                file_name = seg_data.get("name", "文件")
                msg = QqMessage(
                    type="chat",
                    nickname=nickname,
                    qq=qq,
                    content=f"[文件] {file_name}"
                )
                await message_queue.push(msg)

        # 合并所有文本部分
        if text_parts:
            combined_text = " ".join(text_parts)
            msg = QqMessage(
                type="chat",
                nickname=nickname,
                qq=qq,
                content=combined_text
            )
            await message_queue.push(msg)

    def _get_face_name(self, face_id: str) -> str:
        """获取 QQ 表情名称"""
        face_map = {
            "0": "惊讶", "1": "撇嘴", "2": "色", "3": "发呆", "4": "得意",
            "5": "流泪", "6": "害羞", "7": "闭嘴", "8": "睡", "9": "大哭",
            "10": "尴尬", "11": "发怒", "12": "调皮", "13": "呲牙", "14": "微笑",
            "15": "难过", "16": "酷", "18": "抓狂", "19": "吐", "20": "偷笑",
            "21": "可爱", "22": "白眼", "23": "傲慢", "24": "饥饿", "25": "困",
            "26": "惊恐", "27": "流汗", "28": "憨笑", "29": "悠闲", "30": "奋斗",
            "31": "咒骂", "32": "疑问", "33": "嘘", "34": "晕", "35": "折磨",
            "36": "衰", "37": "骷髅", "38": "敲打", "39": "再见", "41": "发抖",
            "42": "爱情", "43": "跳跳", "46": "猪头", "49": "拥抱", "53": "蛋糕",
            "54": "闪电", "55": "炸弹", "56": "刀", "57": "足球", "59": "便便",
            "60": "咖啡", "61": "饭", "63": "玫瑰", "64": "凋谢", "66": "爱心",
            "67": "心碎", "69": "礼物", "74": "太阳", "75": "月亮", "76": "赞",
            "77": "踩", "78": "握手", "79": "胜利", "85": "飞吻", "86": "怄火",
            "89": "西瓜", "96": "冷汗", "97": "擦汗", "98": "抠鼻", "99": "鼓掌",
            "100": "糗大了", "101": "坏笑", "102": "左哼哼", "103": "右哼哼",
            "104": "哈欠", "105": "鄙视", "106": "委屈", "107": "快哭了",
            "108": "阴险", "109": "亲亲", "110": "吓", "111": "可怜",
            "112": "菜刀", "113": "啤酒", "114": "篮球", "115": "乒乓",
            "116": "示爱", "117": "瓢虫", "118": "抱拳", "119": "勾引",
            "120": "拳头", "121": "差劲", "122": "爱你", "123": "NO",
            "124": "OK", "125": "转圈", "126": "磕头", "127": "回头",
            "128": "跳绳", "129": "挥手", "130": "激动", "131": "街舞",
            "132": "献吻", "133": "左太极", "134": "右太极", "136": "双喜",
            "137": "鞭炮", "138": "灯笼", "140": "K歌", "144": "喝彩",
            "145": "祈祷", "146": "爆筋", "147": "棒棒糖", "148": "喝奶",
            "151": "飞机", "158": "钞票", "168": "药", "169": "手枪",
            "171": "茶", "172": "眨眼睛", "173": "泪奔", "174": "无奈",
            "175": "卖萌", "176": "小纠结", "177": "喷血", "178": "斜眼笑",
            "179": "doge", "180": "惊喜", "181": "骚扰", "182": "笑哭",
            "183": "我最美", "184": "河蟹", "185": "羊驼", "187": "幽灵",
            "188": "蛋", "190": "菊花", "192": "红包", "193": "大笑",
            "194": "不开心", "197": "冷漠", "198": "呃", "199": "好棒",
            "200": "拜托", "201": "点赞", "202": "无聊", "203": "托脸",
            "204": "吃", "205": "送花", "206": "害怕", "207": "花痴",
            "208": "小样儿", "210": "飙泪", "211": "我不看", "212": "托腮",
            "214": "啵啵", "215": "糊脸", "216": "拍头", "217": "扯一扯",
            "218": "舔一舔", "219": "蹭一蹭", "220": "拽炸天", "221": "顶呱呱",
            "222": "抱抱", "223": "暴击", "224": "开枪", "225": "撩一撩",
            "226": "拍桌", "227": "拍手", "228": "恭喜", "229": "干杯",
            "230": "嘲讽", "231": "哼", "232": "佛系", "233": "掐一掐",
            "234": "惊呆", "235": "颤抖", "236": "啃头", "237": "偷看",
            "238": "扇脸", "239": "原谅", "240": "喷脸", "241": "生日快乐",
            "242": "头撞击", "243": "甩头", "244": "扔狗", "245": "加油必胜",
            "246": "加油抱抱", "247": "口罩护体", "260": "搬砖中", "261": "忙到飞起",
            "262": "脑阔疼", "263": "沧桑", "264": "捂脸", "265": "辣眼睛",
            "266": "哦哟", "267": "头秃", "268": "问号脸", "269": "暗中观察",
            "270": "emm", "271": "吃瓜", "272": "呵呵哒", "273": "我酸了",
            "274": "太南了", "276": "辣椒酱", "277": "汪汪", "278": "汗",
            "279": "打脸", "280": "击掌", "281": "无眼笑", "282": "敬礼",
            "283": "狂笑", "284": "面无表情", "285": "摸鱼", "286": "魔鬼笑",
            "287": "哦", "288": "请", "289": "睁眼", "290": "敲开心",
            "291": "震惊", "292": "让我康康", "293": "摸锦鲤", "294": "期待",
            "295": "拿到红包", "296": "真好", "297": "拜谢", "298": "元宝",
            "299": "牛啊", "300": "胖三斤", "301": "好闪", "302": "左拜年",
            "303": "右拜年", "304": "红包包", "305": "右亲亲", "306": "牛气冲天",
            "307": "喵喵", "308": "求红包", "309": "谢红包", "310": "新年烟花",
            "311": "打call", "312": "变形", "313": "嗑到了", "314": "仔细分析",
            "315": "加油", "316": "我没事", "317": "菜狗", "318": "崇拜",
            "319": "比心", "320": "庆祝", "321": "老色痞", "322": "拒绝",
            "323": "嫌弃", "324": "吃糖", "325": "惊吓", "326": "生气",
        }
        return face_map.get(str(face_id), f"表情{face_id}")

    async def send_to_qq(self, player: str, message: str):
        """发送消息到 QQ 群"""
        try:
            formatted = f"[MC] {player}: {message}"
            await napcat_client.send_group_message(settings.qq_group_id, formatted)
            logger.info(f"Sent to QQ: {formatted}")
        except Exception as e:
            logger.error(f"Failed to send to QQ: {e}")

    async def send_system_to_qq(self, message: str):
        """发送系统消息到 QQ 群"""
        try:
            await napcat_client.send_group_message(settings.qq_group_id, message)
            logger.info(f"Sent system message to QQ: {message}")
        except Exception as e:
            logger.error(f"Failed to send system message to QQ: {e}")


# 全局处理器实例
message_handler = MessageHandler()

