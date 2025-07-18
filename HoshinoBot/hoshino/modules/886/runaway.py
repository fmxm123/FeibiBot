import aiohttp
from io import BytesIO
from PIL import Image
from hoshino import Service
from hoshino.typing import CQEvent
import base64

# 创建服务实例
sv = Service("886_plugin", help_="发送 '886' 获取生成的头像与文字消息")

def image_to_base64(image: Image.Image) -> str:
    """将 PIL 图片转换为 Base64 编码的字符串"""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    base64_str = base64.b64encode(buffer.getvalue()).decode()
    return base64_str

@sv.on_fullmatch("886")  # 精确匹配 "886"
async def send_avatar(bot, ev: CQEvent):
    # 获取用户 QQ 和昵称
    user_id = ev.user_id
    user_name = ev.sender["nickname"]

    # 获取用户头像
    avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"  # QQ头像URL
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as response:
            if response.status == 200:
                avatar_data = await response.read()
            else:
                await bot.send(ev, "获取头像失败，请稍后再试！")
                return

    # 加载头像并调整大小
    avatar = Image.open(BytesIO(avatar_data)).convert("RGBA")
    avatar = avatar.resize((300, 300), Image.LANCZOS)  # 调整为300x300

    # 将头像保存为 Base64
    avatar_base64 = image_to_base64(avatar)

    # 构造文字消息
    text_message = f"{user_name} ({user_id}) 跑路了！"

    # 发送头像和文字
    await bot.send(ev, f"[CQ:image,file=base64://{avatar_base64}]\n{text_message}")
