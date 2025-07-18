from hoshino import Service, priv
from hoshino.typing import CQEvent

sv = Service('_help_', manage_priv=priv.SUPERUSER, visible=False)

TOP_MANUAL = '''
====================
= 菲比使用说明 =
====================
发送[]内的关键词触发，不要艾特BOT，会识别不出指令

==== 二次元老婆 ====
-[抽老婆] 看看今天的二次元老婆是谁
-[交换老婆] @某人 + 交换老婆
-[牛老婆] 50%概率牛到别人老婆(5次/日)
-[查老婆] 加@某人可以查别人老婆，不加查自己
-[离婚] 清除当天老婆信息，可以重新抽老婆
-[用户档案] 统计用户的一些数据，@某人可以查看他人的数据
-[老婆图鉴] 查看老婆解锁情况，@某人可以查看他人的数据
-[老婆档案] 统计老婆的一些数据，后接老婆名字可以查看具体角色的数据
-[切换NTR图鉴开关状态] 开启图鉴统计NTR所得（群管理可用）

==== 今日老婆群友 ====
-[我的今日]+任意词组 看看今天的词组是谁
-[换老婆] 换一个群友

==== 群友买卖系统 ====
-[交易所签到] 每日领取金币（10~50），奴隶也可签到攒钱赎回
-[奴隶购买]+@对象 购买群友作为奴隶，金币不足将无法购买
-[我的资产] 查看自己当前金币余额、身价、奴隶列表
-[查看身价]+@对象 查看群友的当前身价、所属关系和交易次数
-[群友排行榜] 查看本群金币前10排行榜
-[奴隶派遣] 派遣奴隶外出打工，有几率赚取金币，也可能失败赔钱。随机派遣，有多少奴隶能派遣多少次
-[赎回自己] 花费金币赎回自己，恢复自由身份

==== Epic免费游戏 ====
群友指令
-[epic免费游戏] 查看目前epic在送的免费游戏
群管理指令
-[开启订阅epic免费游戏] 每次epic更换新的免费游戏当天中午12点在群内自动推送新的免费游戏信息
-[关闭订阅epic免费游戏] 取消新免费游戏的推送

==== 下辈子重来 ====
-[投胎出生地] 看看下辈子投胎出生在哪里

==== 头像表情包 ====
-[表情包制作] 查看表情包列表
-[表情名]+自己或者@他人 生成对应头像表情包

==== 今日运势 ====
群友指令
-[今日运势/抽签/运势] 一般抽签
-[xx抽签]，例如：碧蓝抽签、东方抽签等
-[主题列表] 查看可选的抽签主题
-[查看主题] 查看群抽签主题
群管理指令
-[设置xx签] 设置群抽签主题
-[重置主题] 重置群抽签主题

==== 塔罗牌 ====
群友指令
[塔罗牌/塔罗牌占卜 (牌阵号)] 使用指定牌阵进行一次塔罗牌占卜，未指定牌阵号时使用默认牌阵
[塔罗牌牌阵] 查看可用的塔罗牌牌阵
[塔罗卡面列表] 查看可用的塔罗牌卡面
[随机塔罗牌 (编号)] 欣赏一张随机塔罗牌及其信息，后附编号时可指定塔罗牌
群管理指令
[切换塔罗牌卡面 (卡面号)] 切换本群所用塔罗牌卡面
[切换塔罗牌规则 (规则名)] 切换本群所用塔罗牌规则，可选：标准、仅大阿卡纳、仅小阿卡纳

==== 群阶级 ====
-[群阶级] 查看自己今天的群阶级

==== 跑路咯 ====
-[886] 跑路咯！

==== 反馈内容 ====
[来杯咖啡+反馈内容] 向BOT管理员反馈，必要时会通过BOT进行回复。

=====================
BOT运维帮助群：903260419
※菲比基于开源BOT系统：HoshinoBot
开源地址：github.com/Ice9Coffee/HoshinoBot
'''.strip()
# 魔改请保留 github.com/Ice9Coffee/HoshinoBot 项目地址


def gen_service_manual(service: Service, gid: int):
    spit_line = '=' * max(0, 18 - len(service.name))
    manual = [f"|{'○' if service.check_enabled(gid) else '×'}| {service.name} {spit_line}"]
    if service.help:
        manual.append(service.help)
    return '\n'.join(manual)


def gen_bundle_manual(bundle_name, service_list, gid):
    manual = [bundle_name]
    service_list = sorted(service_list, key=lambda s: s.name)
    for s in service_list:
        if s.visible:
            manual.append(gen_service_manual(s, gid))
    return '\n'.join(manual)


@sv.on_prefix('help', '帮助')
@sv.on_suffix('help', '帮助')
async def send_help(bot, ev: CQEvent):
    gid = ev.group_id
    arg = ev.message.extract_plain_text().strip()
    bundles = Service.get_bundles()
    services = Service.get_loaded_services()
    if not arg:
        await bot.send(ev, TOP_MANUAL)
    elif arg in bundles:
        msg = gen_bundle_manual(arg, bundles[arg], gid)
        await bot.send(ev, msg)
    elif arg in services:
        s = services[arg]
        msg = gen_service_manual(s, gid)
        await bot.send(ev, msg)
    # else: ignore
