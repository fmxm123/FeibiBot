import random
from datetime import datetime
from hoshino import Service
from nonebot import MessageSegment
from hoshino.typing import CQEvent
from .data_handler import (
    get_user_data, update_user_data, add_user_coin, set_today_signed,
    has_signed_today, _load_users
)
from .config import *

sv = Service('群友交易所', enable_on_default=True)

@sv.on_fullmatch('交易所签到')
async def sign(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    if has_signed_today(gid, uid):
        await bot.send(ev, '你今天已经来过交易所了，明天再来吧！')
        return
    reward = random.randint(SIGN_REWARD_MIN, SIGN_REWARD_MAX)
    add_user_coin(gid, uid, reward)
    set_today_signed(gid, uid)
    await bot.send(ev, f'签到成功！你获得了 {reward} 枚金币。')

@sv.on_prefix('奴隶购买')
async def buy_slave(bot, ev: CQEvent):
    if not ev.message or not ev.message[0].type == 'at':
        await bot.send(ev, '请 @ 想要购买的对象。')
        return

    gid = ev.group_id
    buyer_id = ev.user_id
    target_id = int(ev.message[0].data['qq'])

    if buyer_id == target_id:
        await bot.send(ev, '你不能购买自己。')
        return

    buyer = get_user_data(gid, buyer_id)
    target = get_user_data(gid, target_id)

    if target['owner'] == buyer_id:
        await bot.send(ev, '你已经是他的主人了，无法重复购买。')
        return

    today = datetime.now().strftime('%Y-%m-%d')
    if target.get('last_trade_date') == today:
        await bot.send(ev, '该用户今天已经被转卖过了，请明天再来。')
        return

    base_price = target['price']
    fee = int(base_price * 0.2) if target['owner'] else 0
    total_price = base_price + fee

    if buyer['coin'] < total_price:
        await bot.send(ev, f'你没有足够的金币来购买对方（需要 {total_price}）')
        return

    old_owner = target['owner']
    if old_owner and old_owner != buyer_id:
        add_user_coin(gid, old_owner, base_price)

    add_user_coin(gid, buyer_id, -total_price)
    buyer = get_user_data(gid, buyer_id)
    if buyer['coin'] < 0:
        update_user_data(gid, buyer_id, 'coin', 0)

    if old_owner and old_owner != buyer_id:
        old_owner_data = get_user_data(gid, old_owner)
        if target_id in old_owner_data['owned']:
            old_owner_data['owned'].remove(target_id)
            update_user_data(gid, old_owner, 'owned', old_owner_data['owned'])

    target['owner'] = buyer_id
    target['price'] += 10
    target['trade_count'] += 1
    target['last_trade_date'] = today

    update_user_data(gid, target_id, 'owner', buyer_id)
    update_user_data(gid, target_id, 'price', target['price'])
    update_user_data(gid, target_id, 'trade_count', target['trade_count'])
    update_user_data(gid, target_id, 'last_trade_date', today)

    buyer['owned'].append(target_id)
    update_user_data(gid, buyer_id, 'owned', buyer['owned'])

    await bot.send(ev, f'购买成功！你已成为 {MessageSegment.at(target_id)} 的主人（花费 {total_price} 金币，其中 {fee} 金币为手续费）')

@sv.on_fullmatch('我的资产')
async def my_assets(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    data = get_user_data(gid, uid)
    coin = data['coin']
    price = data['price']
    owned = data['owned']
    msg = f"金币余额：{coin} 金币\n当前身价：{price} 金币\n我的奴隶："
    if owned:
        slave_names = []
        for sid in owned:
            try:
                info = await bot.get_group_member_info(group_id=gid, user_id=sid)
                name = info.get('card') or info.get('nickname') or str(sid)
                slave_names.append(name)
            except:
                slave_names.append(str(sid))
        msg += '、'.join(slave_names)
    else:
        msg += '无'
    await bot.send(ev, msg)

@sv.on_prefix('查看身价')
async def check_price(bot, ev: CQEvent):
    if not ev.message or ev.message[0].type != 'at':
        await bot.send(ev, '请 @ 一位用户。')
        return
    gid = ev.group_id
    target_id = int(ev.message[0].data['qq'])
    data = get_user_data(gid, target_id)
    price = data['price']
    owner = data['owner']
    trade_count = data['trade_count']
    msg = f"{MessageSegment.at(target_id)}\n当前身价：{price} 金币\n被交易次数：{trade_count}\n"
    if owner:
        msg += f"当前主人：{MessageSegment.at(owner)}"
    else:
        msg += "当前为自由身"
    await bot.send(ev, msg)

@sv.on_fullmatch('群友排行榜')
async def show_ranking(bot, ev: CQEvent):
    gid = ev.group_id
    users = _load_users(gid)
    rank = sorted(users.items(), key=lambda x: x[1]['coin'], reverse=True)
    msg = "【金币排行榜 TOP10】\n"
    for i, (uid, udata) in enumerate(rank[:10], 1):
        try:
            info = await bot.get_group_member_info(group_id=gid, user_id=int(uid))
            name = info.get('card') or info.get('nickname') or uid
        except:
            name = uid
        msg += f"{i}. {name} - {udata['coin']} 金币\n"
    await bot.send(ev, msg)

@sv.on_fullmatch('奴隶派遣')
async def dispatch_slave(bot, ev: CQEvent):
    gid = ev.group_id
    master_id = ev.user_id
    master = get_user_data(gid, master_id)
    today = datetime.now().strftime('%Y-%m-%d')

    # 兼容老数据：如果是list就重置
    raw_record = master.get('dispatch_today')
    if isinstance(raw_record, dict):
        dispatch_record = raw_record
        if dispatch_record.get('date') != today:
            dispatch_record = {'date': today, 'slaves': []}
    else:
        # 老版本存的是list或None
        dispatch_record = {'date': today, 'slaves': []}

    available_slaves = [s for s in master['owned'] if s not in dispatch_record['slaves']]
    if not available_slaves:
        await bot.send(ev, '今天已派遣所有奴隶，明天再来吧！')
        return

    slave_id = random.choice(available_slaves)
    try:
        info = await bot.get_group_member_info(group_id=gid, user_id=slave_id)
        slave_name = info.get('card') or info.get('nickname') or str(slave_id)
    except:
        slave_name = str(slave_id)

    def mk_event(text_template, delta_func):
        def inner(name):
            delta = delta_func()
            return text_template.format(name=name, value=abs(delta)), delta
        return inner

    events = [
        mk_event('{name} 摊煎饼果子火了，赚了 {value} 金币！', lambda: random.randint(15, 50)),
        mk_event('{name} 打金团通宵刷副本，赚了 {value} 金币！', lambda: random.randint(20, 45)),
        mk_event('{name} 被人包养了一天，收入 {value} 金币！', lambda: random.randint(30, 60)),
        mk_event('{name} 去酒吧兼职唱歌，赚了 {value} 金币。', lambda: random.randint(15, 40)),
        mk_event('{name} 给富婆看风水，收了 {value} 金币。', lambda: random.randint(25, 50)),
        mk_event('{name} 网络创业成功，为你赚了 {value} 金币！', lambda: random.randint(30, 60)),
        mk_event('{name} 去市场贩卖表情包，赚了 {value} 金币。', lambda: random.randint(10, 25)),
        mk_event('{name} 靠脸吃饭走红，赚了 {value} 金币！', lambda: random.randint(25, 45)),
        mk_event('{name} 挂机挖矿偷偷赚钱，赚了 {value} 金币。', lambda: random.randint(15, 35)),
        mk_event('{name} 被客户鸽了，白跑一趟。', lambda: 0),
        mk_event('{name} 一天都在等活，最终无功而返。', lambda: 0),
        mk_event('{name} 被黑中介骗了，亏了 {value} 金币！', lambda: -random.randint(10, 25)),
        mk_event('{name} 出门撞车，赔了 {value} 金币。', lambda: -random.randint(15, 30)),
        mk_event('{name} 投资失败，损失了 {value} 金币！', lambda: -random.randint(20, 35)),
        mk_event('{name} 派遣失败，对方跑路，亏了 {value} 金币。', lambda: -random.randint(10, 30)),
    ]
    event_func = random.choice(events)
    msg, delta = event_func(slave_name)
    add_user_coin(gid, master_id, delta)

    # 不足0自动归零
    master = get_user_data(gid, master_id)
    if master['coin'] < 0:
        update_user_data(gid, master_id, 'coin', 0)

    # 更新派遣记录
    dispatch_record['slaves'].append(slave_id)
    update_user_data(gid, master_id, 'dispatch_today', dispatch_record)

    await bot.send(ev, msg)

@sv.on_fullmatch('赎回自己')
async def redeem(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    data = get_user_data(gid, uid)
    price = 100 + data['trade_count']
    if not data['owner']:
        await bot.send(ev, '你本来就是自由身，不需要赎回。')
        return
    if data['coin'] < price:
        coin = data['coin']
        await bot.send(ev, f'你需要 {price} 金币赎回自己，但你只有 {coin}。')
        return
    owner = data['owner']
    add_user_coin(gid, uid, -price)
    add_user_coin(gid, owner, price)
    owner_data = get_user_data(gid, owner)
    if uid in owner_data['owned']:
        owner_data['owned'].remove(uid)
        update_user_data(gid, owner, 'owned', owner_data['owned'])
    data['owner'] = None
    update_user_data(gid, uid, 'owner', None)
    await bot.send(ev, f'你花费了 {price} 金币赎回了自己，现在你是自由人了！')

