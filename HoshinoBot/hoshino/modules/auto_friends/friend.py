from hoshino import Service
from aiocqhttp.exceptions import Error as CQHttpError

sv = Service('auto_accept_requests', enable_on_default=True)

@sv.on_request('friend')
async def auto_accept_friend_request(ctx):
    """
    自动同意好友请求
    """
    try:
        # 打印 ctx.event 调试上下文内容
        sv.logger.info(f"好友请求事件: {ctx.event}")
        
        # 直接从 ctx.event 获取字段
        await sv.bot.set_friend_add_request(flag=ctx.event['flag'], approve=True)
        sv.logger.info(f"已自动同意好友申请：{ctx.event['user_id']}")
    except KeyError as e:
        sv.logger.error(f"事件缺少字段: {e}")
    except CQHttpError as e:
        sv.logger.error(f"自动同意好友申请失败：{e}")

@sv.on_request('group')
async def auto_accept_group_invite(ctx):
    """
    自动同意群邀请
    """
    try:
        # 打印 ctx.event 调试上下文内容
        sv.logger.info(f"群请求事件: {ctx.event}")
        
        # 直接从 ctx.event 获取字段
        if ctx.event['sub_type'] == 'invite':  # 群邀请
            await sv.bot.set_group_add_request(
                flag=ctx.event['flag'], 
                sub_type=ctx.event['sub_type'], 
                approve=True
            )
            sv.logger.info(f"已自动同意群邀请：群 {ctx.event['group_id']} 来自 {ctx.event['user_id']}")
        else:
            sv.logger.info(f"忽略了非邀请的群请求：{ctx.event['sub_type']}")
    except KeyError as e:
        sv.logger.error(f"事件缺少字段: {e}")
    except CQHttpError as e:
        sv.logger.error(f"自动同意群邀请失败：{e}")
