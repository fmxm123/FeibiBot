import hoshino
from hoshino import Service, priv, get_bot
from hoshino.typing import CQEvent
from .epic_api import fetch_free_games, format_game_info, get_game_thumbnail
import os
import json
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

__plugin_name__ = 'Epic免费游戏查询'
__plugin_usage__ = """
指令: 
[epic免费游戏] - 获取Epic当前免费游戏信息
[开启订阅epic免费游戏] - 开启每周自动推送 (仅群管)
[关闭订阅epic免费游戏] - 关闭每周自动推送 (仅群管)
""".strip()

sv = Service('epicfree', help_=__plugin_usage__)

# 订阅状态存储文件
SUBSCRIPTION_FILE = os.path.join(os.path.dirname(__file__), 'epic_subscriptions.json')

# 初始化订阅数据
def load_subscriptions():
    if os.path.exists(SUBSCRIPTION_FILE):
        try:
            with open(SUBSCRIPTION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

# 保存订阅数据
def save_subscriptions(subscriptions):
    with open(SUBSCRIPTION_FILE, 'w', encoding='utf-8') as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=2)

subscriptions = load_subscriptions()

# 设置定时任务
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

# 每周四中午12点推送免费游戏
@scheduler.scheduled_job('cron', day_of_week='thu', hour=12, minute=0)
async def weekly_epic_push():
    bot = get_bot()
    current_games = await get_current_free_games()
    
    if not current_games:
        return
    
    for group_id, enabled in subscriptions.items():
        if enabled:
            try:
                await bot.send_group_msg(group_id=int(group_id), message="【Epic每周免费游戏更新】")
                for game in current_games[:3]:
                    text_msg = format_game_info(game)
                    await bot.send_group_msg(group_id=int(group_id), message=text_msg)

                    thumbnail_url = get_game_thumbnail(game)
                    if thumbnail_url:
                        await bot.send_group_msg(group_id=int(group_id), message=f"[CQ:image,file={thumbnail_url}]")
                await bot.send_group_msg(group_id=int(group_id), message="-"*30)
            except Exception as e:
                hoshino.logger.error(f"群{group_id}自动推送失败: {str(e)}")

# 获取当前免费游戏
async def get_current_free_games():
    games, error = await fetch_free_games()
    if error:
        return []
    current_games = []
    for game in games:
        if game.get("price", {}).get("totalPrice", {}).get("discountPrice", 1) == 0:
            promotions = game.get("promotions", {})
            if promotions and promotions.get("promotionalOffers"):
                current_games.append(game)
    return current_games

# 开启订阅
@sv.on_fullmatch('开启订阅epic免费游戏')
async def enable_subscription(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, "⚠️ 只有群主或管理员可以管理订阅")
        return
    group_id = str(ev.group_id)
    subscriptions[group_id] = True
    save_subscriptions(subscriptions)
    await bot.send(ev, "✅ 已开启Epic免费游戏订阅，每周四中午12点自动推送最新免费游戏")

# 关闭订阅
@sv.on_fullmatch('关闭订阅epic免费游戏')
async def disable_subscription(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, "⚠️ 只有群主或管理员可以管理订阅")
        return
    group_id = str(ev.group_id)
    subscriptions[group_id] = False
    save_subscriptions(subscriptions)
    await bot.send(ev, "❌ 已关闭Epic免费游戏订阅，不再自动推送")

# 手动查询当前免费游戏
@sv.on_fullmatch(('epic免费游戏', 'epic游戏', 'epic免费'))
async def send_free_games(bot, ev: CQEvent):
    await bot.send(ev, "正在获取Epic免费游戏信息，请稍候...")
    current_games = await get_current_free_games()
    if not current_games:
        await bot.send(ev, "目前没有可免费领取的游戏，请稍后再查！")
        return
    await bot.send(ev, "🎮【Epic当前免费游戏】🎮")
    for game in current_games[:3]:
        try:
            text_msg = format_game_info(game)
            await bot.send(ev, text_msg)
            thumbnail_url = get_game_thumbnail(game)
            if thumbnail_url:
                await bot.send(ev, f"[CQ:image,file={thumbnail_url}]")
        except Exception as e:
            hoshino.logger.error(f"发送游戏信息失败: {str(e)}")
            await bot.send(ev, f"发送游戏信息时出错: {str(e)}")

# 自动启动定时任务（懒加载兼容）
def _start_scheduler_later():
    async def _delayed_start():
        await asyncio.sleep(1)
        if not scheduler.running:
            try:
                scheduler.start()
                hoshino.logger.info("✅ Epic定时任务已自动启动")
            except Exception as e:
                hoshino.logger.error(f"❌ 启动定时任务失败: {str(e)}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_delayed_start())
        else:
            # 兼容未启动的事件循环，注册启动回调
            def on_start():
                loop.create_task(_delayed_start())
            loop.call_soon(on_start)
    except Exception as e:
        hoshino.logger.error(f"❌ 无法注册定时任务启动逻辑: {str(e)}")
