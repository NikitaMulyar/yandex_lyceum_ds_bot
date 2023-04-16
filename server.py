import logging
import discord
from config import BOT_TOKEN
import requests
from discord.ext.tasks import loop
from discord.ext import commands
from datetime import timedelta
import pymorphy2
import urllib3
import certifi

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())

response = http.request('GET', 'https://discord.com/')
TASKS = {}
morph = pymorphy2.MorphAnalyzer()


@loop(seconds=1)
async def task(id_, message):
    if len(TASKS[id_]) != 0:
        nowtime = TASKS[id_][0] - timedelta(seconds=1)
        TASKS[id_][0] = nowtime
        if nowtime == timedelta(seconds=0, minutes=0, hours=0):
            TASKS[id_].pop(0)
            await message.channel.send(f"{message.author.mention}, Момент Х настал!")


class YLBotClient(discord.Client):
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        for guild in self.guilds:
            logger.info(f'{self.user} подключились к чату:\n{guild.name}(id: {guild.id})')
            logger.info('Готов показать вам котика!')

    async def on_member_join(self, member):
        await member.create_dm()
        await member.dm_channel.send(f'Привет, {member.name}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        d = 'https://dog.ceo/api/breeds/image/random'
        c = 'https://api.thecatapi.com/v1/images/search'
        if "соб" in message.content.lower() or "пес" in message.content.lower().replace('ё', 'е'):
            url = requests.get(d).json()['message']
            await message.channel.send(url)
        elif "кот" in message.content.lower() or "кош" in message.content.lower():
            url = requests.get(c).json()[0]['url']
            await message.channel.send(url)
        elif "set_timer" in message.content:
            id_ = message.author.id
            s = message.content.split()[2:]
            d = {}
            for i in range(0, len(s) - 1, 2):
                d[s[i + 1]] = float(s[i])
            if not d.get('hours'):
                d['hours'] = 0
            if not d.get('minutes'):
                d['minutes'] = 0
            if not d.get('seconds'):
                d['seconds'] = 0
            t = timedelta(seconds=d['seconds'], minutes=d['minutes'], hours=d['hours'])
            if not TASKS.get(id_):
                TASKS[id_] = [t]
                await message.channel.send(f"The timer should start in {' '.join(s)}")
            else:
                TASKS[id_].append(t)
                t_st = TASKS[id_][0]
                for i in range(1, len(TASKS[id_])):
                    t_st += TASKS[id_][i]
                await message.channel.send(f"The timer should start in {t_st.total_seconds()} seconds")
            task.start(id_, message)
        else:
            await message.channel.send("-100 social credit: Не кошка-жена и собака-жена!")
            return


intents = discord.Intents.default()
intents.members = True
client = YLBotClient(intents=intents)
bot = commands.Bot(command_prefix = '#!', intents=intents)
client.run(BOT_TOKEN)
