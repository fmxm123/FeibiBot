import os
import random
from datetime import datetime
from hoshino import Service
from hoshino.config import RES_DIR
from hoshino.typing import CQEvent

sv = Service('投胎出生地', help_='发送[投胎出生地]，查看转生后的出生地')

MY_WIFE_DIR = os.path.join(RES_DIR, 'img', 'flag')

@sv.on_fullmatch(['投胎出生地'])
async def send_birthplace(bot, ev: CQEvent):
    if not os.path.exists(MY_WIFE_DIR):
        await bot.send(ev, '国旗资源库未找到，请检查路径 RES_DIR/img/flag')
        return

    img_files = [
        f for f in os.listdir(MY_WIFE_DIR)
        if os.path.isfile(os.path.join(MY_WIFE_DIR, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    if not img_files:
        await bot.send(ev, '出生地为空，请添加一些国旗到 flag 文件夹。')
        return

    uid = ev.user_id
    today = datetime.now().strftime('%Y-%m-%d')
    seed = f"{uid}_{today}"
    random.seed(seed)
    chosen_file = random.choice(img_files)

    name_without_ext = os.path.splitext(chosen_file)[0]
    image_path = os.path.join(MY_WIFE_DIR, chosen_file)
    image_path_fixed = image_path.replace("\\", "/")

    msg = f'[CQ:at,qq={uid}] 你投胎后的出生地是：{name_without_ext}'
    await bot.send(ev, f'{msg}\n[CQ:image,file=file:///{image_path_fixed}]')
