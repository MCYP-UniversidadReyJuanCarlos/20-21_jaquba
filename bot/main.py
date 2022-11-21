import configparser # to read config files
from pathlib import Path

# external telegram bot library
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

import logging # to generate traces of execution
import re # for regex validations

# to create a fastapi (REST) server
from fastapi import FastAPI
from fastapi import Body
from pydantic import BaseModel
import uvicorn

import requests
import json

from aiocache import Cache # to share variables between threads
import asyncio # to manage async functions

import i18n # to have localized messages

class Meta:
    def __init__(self):
        pass

    async def get_list(self, name) -> list:
        return await cache.get(name, default=[])

    async def add_elem(self, name, value: dict) -> None:
        list_cached = await cache.get(name, default=[])
        list_cached.append(value)
        await cache.set(name, list_cached)

    async def set_list(self, name, list_val) -> None:
        await cache.set(name, list_val)

    async def clear(self) -> bool:
        return await cache.clear()

class Alert(BaseModel):
    ip: str # ip address of the server which get the alert
    module: str # name of the alert module which get the alert
    alert_type: str # type of alert
    severity: int # severity of the alert (1 = info, 2 = warning, 3 = error)
    data: str # data of the alert to be sent to the chat


#   VARIABLES GLOBALES     #
logger = None # to log application status and info
config = configparser.ConfigParser() # to read config file
debug = False
api = FastAPI()
cache = Cache(Cache.MEMORY)
meta = Meta()
############################

# Print debug messages
def log(message) -> None:
    global debug, logger
    if debug is False:
        logger.info(message)
    else:
        print(message)

# Append new chats to list
async def append_chat(id: int, context: CallbackContext) -> None:
    chats = await meta.get_list('chats')
    if not any([True if id == chat["id"] else False for chat in chats]):
        await meta.add_elem('chats', {'id': id, 'context': context})
    log(await meta.get_list('chats'))

# Invoked when recieves termination signal from user
def stop_execution(signum, frame) -> None:
    log(f'Recibo signal {signum}')
    asyncio.run(meta.clear())

# Executed when a new chat is open
def start(update: Update, context: CallbackContext) -> None:
    log(f'Nuevo chat con id = {update.effective_chat.id}')
    asyncio.run(append_chat(update.effective_chat.id, context))

    context.bot.send_message(chat_id=update.effective_chat.id,
        text=i18n.t('bot.welcome'))

# Executed when an unknown command is recieved
def unknown(update: Update, context: CallbackContext) -> None:
    asyncio.run(append_chat(update.effective_chat.id, context))
    log(f'Comando desconocido en el chat con id = {update.effective_chat.id}')
    context.bot.send_message(chat_id=update.effective_chat.id, text=i18n.t('bot.unknownCmd'))

def get_buttons(module: str, id_alert: int) -> list:
    keyboard = []
    if module == 'SSH':
        keyboard = [
            [
                InlineKeyboardButton(i18n.t('bot.ssh.option1'), callback_data=f'{id_alert}#close_connection'),
                InlineKeyboardButton(i18n.t('bot.ssh.option2'), callback_data=f'{id_alert}#block_port')
            ],
            [InlineKeyboardButton(i18n.t('bot.ssh.ignore'), callback_data=f'{id_alert}#ignore')]
        ]
    return keyboard

@api.post("/alert", status_code=201)
async def get_alert(alert: dict = Body(...)):
    alert_type = alert['alert_type']
    module = alert['module']
    print(f'Recibida alerta {alert_type} (modulo {module}) ' \
        + f'desde {alert["ip"]} con severidad {alert["severity"]}')

    message = i18n.t('bot.newAlert', alertType=module)

    chats = await meta.get_list('chats')
    print(chats)
    for chat in chats:
        id_chat = chat["id"]
        print(f'Enviando mensaje a {id_chat}')
        
        chat_ctx = chat['context']

        id_alert = chat_ctx.user_data.get('id_alert', 0) + 1

        if 'alert' not in chat_ctx.user_data:
            chat_ctx.user_data['alert'] = {}

        chat_ctx.user_data['alert'][id_alert] = alert
        chat_ctx.user_data['id_alert'] = id_alert

        keyboard = get_buttons(module, id_alert)
        markup = InlineKeyboardMarkup(keyboard)
        chat_ctx.bot.send_message(chat_id=id_chat, text=message, reply_markup=markup)

    return '{"status": "OK"}'

def reply_alert(update: Update, context: CallbackContext) -> None:
    global config
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    query.answer()

    id_alert, option = query.data.split('#')
    id_alert = int(id_alert)

    alert = context.user_data['alert'][id_alert]
    if id_alert not in context.user_data['alert'] or alert is None:
        query.edit_message_text(text=i18n.t('bot.alertReplied'))

    module = alert['module']
    ip = alert['ip']
    log(f'IP: {ip}')

    response = {
        'module': module,
        'alert_type': alert['alert_type'],
        'severity': alert['severity'],
        'ip': ip,
        'option': option,
        'data': alert['data']
    }

    json_data = json.dumps(response)
    headers = {
            'User-Agent': 'pythonAlertClass',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    port = config['SERVERS']['DefaultPort']
    url = f'http://{ip}:{port}/response'
    log(f'URL: {url}')
    http_response = requests.post(url, headers=headers, data=json_data)
    if http_response.status_code == 200:
        context.user_data['alert'][id_alert] = None
        query.edit_message_text(text=i18n.t('bot.replyingAlert', module=module, option=option))
    else:
        query.edit_message_text(text=i18n.t('bot.notReplied', module=module))


# Entry point
def main() -> None:
    global logger, config

    i18n.load_path.append('translations')

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    logger = logging.getLogger(__name__)

    log('Inicio config')

    config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')

    bot_token = config['TELEGRAM_BOT']['Token']
    log(f'El token es {bot_token}')

    updater = Updater(token=bot_token, use_context=True, user_sig_handler=stop_execution)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_handler(CallbackQueryHandler(reply_alert))

    log('Configurado correctamente. Inicio sondeo.')

    updater.start_polling()

    uvicorn.run("main:api", host="0.0.0.0", port=5000, log_level="info")

    # Run the bot until the user presses Ctrl-C or
    # the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

    log("Termina la ejecucion")

if __name__ == '__main__':
    main()