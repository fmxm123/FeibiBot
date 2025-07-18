import aiohttp
import json
import datetime
import logging

# Epic 商店免费游戏 API（中文）
API_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=zh-CN&country=CN&allowCountries=CN"

# 设置日志记录器
logger = logging.getLogger('epicfree')


async def fetch_free_games():
    """从 Epic API 拉取免费游戏列表"""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(API_URL) as resp:
                if resp.status != 200:
                    error_msg = f"Epic API 请求失败，状态码: {resp.status}"
                    logger.error(error_msg)
                    return None, error_msg

                data = await resp.json()
                elements = data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
                if not elements:
                    error_msg = "Epic API 返回数据为空或结构异常"
                    logger.error(error_msg)
                    return None, error_msg

                return elements, None

    except aiohttp.ClientError as e:
        error_msg = f"Epic API 网络错误: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except json.JSONDecodeError:
        error_msg = "Epic API 返回 JSON 解析失败"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Epic API 异常: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def get_game_thumbnail(game):
    """提取缩略图链接"""
    key_images = game.get("keyImages", [])
    return next((img.get("url") for img in key_images if img.get("type") == "Thumbnail"), "")


def format_game_info(game):
    """格式化游戏信息为可发送文本"""
    title = game.get("title", "未知游戏")
    description = game.get("description", "暂无描述")
    if len(description) > 50:
        description = description[:50] + "..."

    # 原价（单位：分）
    price_info = game.get("price", {}).get("totalPrice", {})
    original_price = price_info.get("originalPrice", 0) // 100  # 分转元

    # 截止时间
    end_date = "未知"
    try:
        promotions = game.get("promotions", {})
        promo_offers = promotions.get("promotionalOffers", [])
        if promo_offers:
            end = promo_offers[0]["promotionalOffers"][0].get("endDate")
            end_date = format_date(end)
    except:
        pass

    # 商店链接处理
    product_slug = game.get("productSlug")
    if product_slug and product_slug != "[]":
        store_url = f"https://store.epicgames.com/zh-CN/p/{product_slug}"
    else:
        offer_mappings = game.get("offerMappings", [])
        if offer_mappings:
            slug = offer_mappings[0].get("pageSlug", "")
            store_url = f"https://store.epicgames.com/zh-CN/browse?offerId={slug}"
        else:
            store_url = "https://store.epicgames.com/zh-CN/free-games"

    return (
        f"🎮 {title}\n"
        f"⏰ 免费截止: {end_date}\n"
        f"💰 原价: ¥{original_price}\n"
        f"📖 简介: {description}\n"
        f"🔗 领取: {store_url}"
    )


def format_date(date_str):
    """将 ISO 格式时间转换为北京时间"""
    if not date_str:
        return "未知"
    try:
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        dt = datetime.datetime.fromisoformat(date_str)
        dt_beijing = dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
        return dt_beijing.strftime("%m-%d %H:%M")
    except Exception:
        return date_str.split("T")[0][5:] if "T" in date_str else "未知"
