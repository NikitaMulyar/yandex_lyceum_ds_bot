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
import random

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
USER_LANG = {}
COMMANDS = {"#!numerals": ('<слово> <число>', 'Согласовать слово с числительным'),
            "#!alive": ("<слово>", "Определить, является слово одуш. или неодуш."),
            "#!noun": ("<слово> <падеж [nomn, gent, datv, accs, ablt, loct]> <число [single, plural]>",
                       "Вывести слово в заданном падеже и числе"),
            "#!inf": ("<слово>", "Начальная форма слова"),
            "#!morph": ("<слово>", "Полный морфологический разбор слова"),
            "#!set_lang": ("<<src lang>-<dest lang>>", "Change src and dest lang"),
            "#!text": ("<word>", "Translate <word> from the src lang to dest"),
            "/start": ("", "Начать игру со смайлами"),
            "/stop": ("", "Закончить игру со смайлами"),
            "#!place": ("<city>", "Задать место прогноза"),
            "#!current": ("", "Посмотреть текущую погоду в месте прогноза"),
            "#!forecast": ("<days: int>", "Посмотреть прогноз в месте прогноза на указанное кол-во дней")}
morph = pymorphy2.MorphAnalyzer()
API_KEY = 'AQVNzhfpiSw09Z_EBDWdUtal9XPJR_I5lVASpWlT'
FOLDER_ID = 'b1go7l39akkvmdgv9j16'
rand_nums = random.sample(range(300, 400), k=40)
EMOJIS = ['1F' + str(rand_nums[i]) for i in range(40)]
CONV = 0
USER_SCORE = {}
USER_WEATHER = {}
API_GEO = '40d1649f-0493-4b70-98ba-98533de7710b'
URL_GEOCODER = 'http://geocode-maps.yandex.ru/1.x/'


def get_coords(address):
    geocoder_params = {
        "apikey": API_GEO,
        "geocode": address,
        "format": "json"}

    try:
        res = requests.get(URL_GEOCODER, params=geocoder_params).json()
        toponym = res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
        return float(toponym_lattitude), float(toponym_longitude)
    except Exception:
        return -1


class CaseError(Exception):
    pass


class NumberError(Exception):
    pass


class NotFound(Exception):
    pass


@loop(seconds=1)
async def task(id_, message):
    if len(TASKS[id_]) != 0:
        nowtime = TASKS[id_][0] - timedelta(seconds=1)
        TASKS[id_][0] = nowtime
        if nowtime == timedelta(seconds=0, minutes=0, hours=0):
            TASKS[id_].pop(0)
            await message.channel.send(f"{message.author.mention}, Момент Х настал!")


def send_help():
    text = '**Команды:**\n'
    for el in COMMANDS:
        text += f"`{el} {COMMANDS[el][0]}`\n> {COMMANDS[el][1]}\n\n"
    text += f"`#!help_bot`\n> Вывести все команды"
    return text


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
        global CONV
        if message.author == self.user:
            return
        d = 'https://dog.ceo/api/breeds/image/random'
        c = 'https://api.thecatapi.com/v1/images/search'
        msg = message.content
        if msg.startswith('#!help_bot'):
            await message.channel.send(send_help())
            return
        if msg.split()[0] in COMMANDS.keys():
            msg2 = msg.split()
            cmd = msg2[0]
            if cmd == "#!numerals":
                try:
                    if len(msg2) < 3:
                        raise IndexError
                    w = morph.parse(msg2[1])[0]
                    n = int(msg2[2])
                    w_after = w.make_agree_with_number(n).word
                    await message.channel.send(f'{n} {w_after.lower()}', reference=message)
                    return
                except ValueError:
                    await message.channel.send('Аргумент `<число>` должен иметь тип `int`,'
                                               ' `<слово>` - тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<слово> <число>`')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "#!alive":
                try:
                    if len(msg2) < 2:
                        raise IndexError
                    w = morph.parse(msg2[1])[0]
                    fl = w.tag.animacy
                    if fl is None:
                        raise TypeError
                    w_fl = morph.parse("живой")[0] if fl == 'anim' else morph.parse("неживой")[0]
                    if w.tag.number == 'sing':
                        w_fl = w_fl.inflect({w.tag.gender, w.tag.number, 'nomn'})
                    else:
                        w_fl = w_fl.inflect({w.tag.number, 'nomn'})
                    await message.channel.send(f'{msg2[1].capitalize()} {w_fl.word}', reference=message)
                    return
                except ValueError:
                    await message.channel.send('Аргумент `<слово>` - тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<слово>`')
                    return
                except TypeError:
                    await message.channel.send('Слово должно быть существительным')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "#!noun":
                try:
                    padezhi = '[nomn, gent, datv, accs, ablt, loct]'
                    nums = '[single, plural]'
                    if len(msg2) < 4:
                        raise IndexError
                    w = morph.parse(msg2[1])[0]
                    if w.tag.animacy is None:
                        raise TypeError
                    if msg2[2] not in padezhi:
                        raise CaseError
                    if msg2[3] not in nums:
                        raise NumberError
                    w_fl = w.inflect({msg2[3][:4], msg2[2]})
                    await message.channel.send(w_fl.word, reference=message)
                    return
                except CaseError:
                    await message.channel.send('Неверный падеж')
                    return
                except NumberError:
                    await message.channel.send('Неверное число')
                    return
                except ValueError:
                    await message.channel.send('Все аргументы должны иметь тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<слово> <падеж> <число>`')
                    return
                except TypeError:
                    await message.channel.send('Слово должно быть существительным')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "#!inf":
                try:
                    if len(msg2) < 2:
                        raise IndexError
                    w = morph.parse(msg2[1])[0]
                    await message.channel.send(w.normal_form, reference=message)
                    return
                except ValueError:
                    await message.channel.send('Все аргументы должны иметь тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<слово>`')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "#!morph":
                try:
                    if len(msg2) < 2:
                        raise IndexError
                    p = morph.parse(msg2[1])[0]
                    txt = f"*Часть речи*: {p.tag.POS}\n" \
                          f"*Одушевленность*: {p.tag.animacy}\n" \
                          f"*Вид*: {p.tag.aspect}\n" \
                          f"*Падеж*: {p.tag.case}\n" \
                          f"*Род*: {p.tag.gender}\n" \
                          f"*Включенность говорящего в действие (возвратность?)*: {p.tag.involvement}\n" \
                          f"*Наклонение*: {p.tag.mood}\n" \
                          f"*Число*: {p.tag.number}\n" \
                          f"*Лицо*: {p.tag.person}\n" \
                          f"*Время*: {p.tag.tense}\n" \
                          f"*Переходность*: {p.tag.transitivity}\n" \
                          f"*Залог*: {p.tag.voice}".split('\n')
                    new = []
                    for i in txt:
                        if 'None' not in i:
                            new.append(i)
                    await message.channel.send("\n".join(new), reference=message)
                    return
                except ValueError:
                    await message.channel.send('Все аргументы должны иметь тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<слово>`')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "#!set_lang":
                try:
                    if len(msg2) < 2:
                        raise IndexError
                    if len(msg2[1].split('-')) != 2:
                        raise IndexError
                    USER_LANG[message.author.id] = {'src': msg2[1].split('-')[0],
                                                    'dest': msg2[1].split('-')[1]}
                    await message.channel.send("Type `#!text` and text for translate", reference=message)
                    return
                except ValueError:
                    await message.channel.send('Все аргументы должны иметь тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<<src lang>-<dest lang>>`')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "#!text":
                try:
                    if len(msg2) < 2:
                        raise IndexError
                    if USER_LANG.get(message.author.id) is None:
                        USER_LANG[message.author.id] = {'src': 'en', 'dest': 'ru'}
                    body = {"targetLanguageCode": USER_LANG[message.author.id]['dest'],
                            "languageCode": USER_LANG[message.author.id]['src'], "texts": " ".join(msg2[1:]),
                            "folderId": FOLDER_ID}
                    headers = {"Content-Type": "application/json",
                               "Authorization": f"Api-Key {API_KEY}"}
                    response = requests.post(
                        'https://translate.api.cloud.yandex.net/translate/v2/translate',
                        json=body, headers=headers)
                    res = response.json()['translations'][0]['text']
                    await message.channel.send(res, reference=message)
                    return
                except ValueError:
                    await message.channel.send('Все аргументы должны иметь тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов:'
                                               '`<<src lang>-<dest lang>>`')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            elif cmd == "/start":
                print(CONV)
                if CONV == 0:
                    await message.channel.send('Начинаем игру! Присылай номер эмодзи.')
                    CONV = 1
                    USER_SCORE[message.author.id] = {'User': 0, 'Bot': 0}
                    return
            elif cmd == "/stop":
                if CONV == 1:
                    CONV = 0
                    u = USER_SCORE[message.author.id]['User']
                    b = USER_SCORE[message.author.id]['Bot']
                    await message.channel.send(f"Игра окончена.\nСчет: Вы {u} - Бот {b}")
                    if u == b:
                        await message.channel.send(f"Ничья.")
                    elif u > b:
                        await message.channel.send(f"Вы выиграли.")
                    else:
                        await message.channel.send(f"Бот выиграл.")
                    return
            elif cmd == "#!forecast":
                if not USER_WEATHER.get(message.author.id):
                    await message.channel.send("Сначала задайте город прогноза")
                    return
            elif cmd == "#!current":
                if not USER_WEATHER.get(message.author.id):
                    await message.channel.send("Сначала задайте город прогноза")
                    return
                params = {"lat": USER_WEATHER[message.author.id][0],
                          "lon": USER_WEATHER[message.author.id][1],
                          "lang": "ru_RU",
                          "limit": "7",
                          "hours": "true",
                          "extra": "true"}
                headers = {"X-Yandex-API-Key": "97fa72d6-6cec-42c1-90ac-969b3a5c9418"}
                res = requests.get('https://api.weather.yandex.ru/v2/forecast', params=params, headers=headers).json()
                print(res)
            elif cmd == "#!place":
                try:
                    if len(msg2) < 2:
                        raise IndexError
                    res = get_coords(" ".join(msg2[1:]))
                    if res == -1:
                        raise NotFound
                    await message.channel.send(f"Место задано на: {' '.join(msg2[1:])}", reference=message)
                    USER_WEATHER[message.author.id] = res
                    return
                except NotFound:
                    await message.channel.send('Такое место не найдено.')
                    return
                except ValueError:
                    await message.channel.send('Все аргументы должны иметь тип `str`')
                    return
                except IndexError:
                    await message.channel.send('Перепроверьте последовательность и кол-во аргументов: `<city>`')
                    return
                except Exception as e:
                    await message.channel.send(f'Возникла ошибка:\n`{e}`')
                    return
            return
        if "соб" in msg.lower() or "пес" in msg.lower().replace('ё', 'е'):
            url = requests.get(d).json()['message']
            await message.channel.send(url)
        elif "кот" in msg.lower() or "кош" in msg.lower():
            url = requests.get(c).json()[0]['url']
            await message.channel.send(url)
        elif "set_timer" in msg:
            id_ = message.author.id
            s = msg.split()[2:]
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
        elif CONV:
            global EMOJIS
            try:
                n = int(message.content)
                if n < 1:
                    raise ValueError
                em_u = n % len(EMOJIS)
                symb_u = EMOJIS[em_u]
                EMOJIS.pop(em_u)
                symb_b = random.choice(EMOJIS)
                EMOJIS.pop(EMOJIS.index(symb_b))
                if symb_u > symb_b:
                    USER_SCORE[message.author.id]['User'] += 1
                else:
                    USER_SCORE[message.author.id]['Bot'] += 1
                u_s = USER_SCORE[message.author.id]['User']
                u_b = USER_SCORE[message.author.id]['Bot']
                await message.channel.send(f"Ваш эмодзи: {chr(int(symb_u, 16))}\nЭмодзи бота: {chr(int(symb_b, 16))}\nСчет: Вы {u_s} - Бот {u_b}")
            except ValueError:
                await message.channel.send(f"Код эмодзи должен быть положительным целым числом.")
            if len(EMOJIS) == 0:
                CONV = 0
                u = USER_SCORE[message.author.id]['User']
                b = USER_SCORE[message.author.id]['Bot']
                await message.channel.send(f"Игра окончена.")
                if u == b:
                    await message.channel.send(f"Ничья.")
                elif u > b:
                    await message.channel.send(f"Вы выиграли.")
                else:
                    await message.channel.send(f"Бот выиграл.")
                USER_SCORE[message.author.id]['User'] = 0
                USER_SCORE[message.author.id]['Bot'] = 0
                EMOJIS = EMOJIS = ['1F6' + str(rand_nums[i]) for i in range(20)]
        else:
            await message.channel.send("-100 social credit: Не кошка-жена и собака-жена!")
            return


intents = discord.Intents.default()
intents.members = True
client = YLBotClient(intents=intents)
bot = commands.Bot(command_prefix = '#!', intents=intents)
client.run(BOT_TOKEN)
