import hoshino
import asyncio

bot = hoshino.init()
app = bot.asgi

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot.run(use_reloader=False, loop=loop)
