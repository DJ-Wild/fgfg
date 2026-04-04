import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from javascript import require, On

# Подключаем компоненты Node.js
mineflayer = require('mineflayer')

# Настройки Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Глобальная переменная для хранения экземпляра MC бота
mc_instance = None


@bot.event
async def on_ready():
    print(f'Discord бот {bot.user} запущен!')


async def speak_in_discord(text):
    """Озвучка текста в голосовой канал"""
    for vc in bot.voice_clients:
        if vc.is_connected():
            filename = f"tts_{hash(text)}.mp3"
            tts = gTTS(text=text, lang='ru')
            tts.save(filename)

            while vc.is_playing():
                await asyncio.sleep(0.5)

            # Настройка голоса (Pitch + Speed)
            options = "-af asetrate=44100*1.2,atempo=0.8"
            vc.play(discord.FFmpegPCMAudio(filename, options=options),
                    after=lambda e: os.remove(filename))


@bot.command()
async def main(ctx, host: str = "NFTAcademy.aternos.me"):
    """Команда для подключения к Minecraft"""
    global mc_instance

    if mc_instance:
        await ctx.send("Бот уже подключен к Minecraft!")
        return

    await ctx.send(f"Подключаюсь к серверу {host}...")

    # Создаем бота Minecraft
    mc_instance = mineflayer.createBot({
        'host': host,
        'port': 25565,
        'username': 'ChatRelayBot',
        'version': '1.21.5'  # Попробуйте оставить пустым для автоопределения
    })

    # Настраиваем обработчик чата через декоратор внутри команды
    @On(mc_instance, 'chat')
    def handle_chat(this, username, message, *args):
        if username == mc_instance.username:
            return

        print(f"[MC] {username}: {message}")

        # Передаем задачу в Discord
        coro = speak_in_discord(f"Игрок {username} пишет: {message}")
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

    @On(mc_instance, 'spawn')
    def on_spawn(this):
        print("Бот успешно заспавнился в Minecraft!")
        asyncio.run_coroutine_threadsafe(ctx.send("Я зашел на сервер Minecraft!"), bot.loop)

    @On(mc_instance, 'kicked')
    def on_kick(this, reason, *args):
        global mc_instance
        print(f"Кикнули с сервера: {reason}")
        mc_instance = None


@bot.command()
async def join(ctx):
    """Бот заходит в ваш голосовой канал"""
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("Зашел в голосовой канал. Жду сообщений из МС!")
    else:
        await ctx.send("Сначала зайдите в голосовой канал!")


@bot.command()
async def stop_mc(ctx):
    """Отключить бота от Minecraft"""
    global mc_instance
    if mc_instance:
        mc_instance.quit()
        mc_instance = None
        await ctx.send("Отключился от Minecraft.")
    else:
        await ctx.send("Я и так не в игре.")


bot.run('MTQ4MzU2MjQ5Njg0NDUwMTExMg.G92ONh.UUUgi3Jxq69AhAw2H8nIHBBzbwZIMX0Yc4pPts')
