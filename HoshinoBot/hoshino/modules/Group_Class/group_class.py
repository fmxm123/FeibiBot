from hoshino import Service
import random
import datetime

sv = Service('群阶级', help_='回复群内的阶级信息')

# 预定义的群阶级
group_classes = [
    '群下等人', 
    '群中等人', 
    '群上等人', 
    '群领导'
]

# 创建一个字典来记录用户当天的群阶级
user_group_class = {}

# 处理“群阶级”命令的事件
@sv.on_fullmatch('群阶级')
async def group_class(bot, event):
    uid = str(event.user_id)  # 获取用户ID
    today = str(datetime.date.today())  # 获取今天的日期
    
    # 如果今天该用户还没有记录群阶级，随机选择一个阶级
    if (uid, today) not in user_group_class:
        chosen_class = random.choice(group_classes)
        user_group_class[(uid, today)] = chosen_class
    else:
        # 如果已经有记录，直接使用当天的群阶级
        chosen_class = user_group_class[(uid, today)]
    
    # 返回用户当天的群阶级，同时 @ 对应用户
    await bot.send(event, f"你今天的群阶级是：{chosen_class}", at_sender=True)
