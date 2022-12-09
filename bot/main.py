# external telegram bot library
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

import configparser # to read config files
from pathlib import Path

# to create a fastapi (REST) server
from fastapi import FastAPI
from fastapi import Body
import uvicorn
import asyncio # to manage async functions
import i18n # to have localized messages

import utils

#   VARIABLES GLOBALES     #
config = configparser.ConfigParser() # to read config file
api = FastAPI()
meta = utils.Meta()
############################

# Append new chats to list
async def append_chat(id: int, context: CallbackContext) -> None:
    chats = await meta.get_list('chats')
    if not any([True if id == chat["id"] else False for chat in chats]):
        await meta.add_elem('chats', {'id': id, 'context': context})
    utils.log(await meta.get_list('chats'))

# Invoked when recieves termination signal from user
def stop_execution(signum, frame) -> None:
    utils.log(f'Recibo signal {signum}')
    asyncio.run(meta.clear())

# Executed when a new chat is open
def start(update: Update, context: CallbackContext) -> None:
    utils.log(f'Nuevo chat con id = {update.effective_chat.id}')
    asyncio.run(append_chat(update.effective_chat.id, context))

    context.bot.send_message(chat_id=update.effective_chat.id,
        text=i18n.t('bot.welcome'))

# Executed when an unknown command is recieved
def unknown(update: Update, context: CallbackContext) -> None:
    asyncio.run(append_chat(update.effective_chat.id, context))
    utils.log(f'Comando desconocido en el chat con id = {update.effective_chat.id}')
    context.bot.send_message(chat_id=update.effective_chat.id, text=i18n.t('bot.unknownCmd'))


@api.post("/alert", status_code=201)
async def get_alert(alert: dict = Body(...)):
    module = alert['module']
    alert_type = alert['alert_type']
    severity = utils.alert_levels[alert["severity"]]
    print(f'Recibida alerta {module}.{alert_type} desde {alert["ip"]} con severidad {severity}')

    detail = utils.get_detail_info(module, alert_type, alert['data'])
    message = i18n.t('bot.newAlert', module=module, alertType=alert_type, severity=severity, moreInfo=detail)

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

        keyboard = utils.get_buttons(module, alert_type, id_alert)
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
        return

    module = alert['module']
    alert_type = alert['alert_type']
    ip = alert['ip']
    utils.log(f'{module}.{alert_type} from IP: {ip}')
    port = config['SERVERS']['DefaultPort']

    http_response = utils.send_response(alert, option, port)

    if http_response.status_code == 200:
        context.user_data['alert'][id_alert] = None
        query.edit_message_text(text=i18n.t('bot.replyingAlert', module=module, alertType=alert_type, option=option))
    else:
        query.edit_message_text(text=i18n.t('bot.notReplied', module=module))


# Entry point
def main() -> None:
    global config

    i18n.load_path.append('translations')

    utils.log('Inicio config')

    config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')

    bot_token = config['TELEGRAM_BOT']['Token']
    utils.log(f'El token es {bot_token}')

    updater = Updater(token=bot_token, use_context=True, user_sig_handler=stop_execution)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_handler(CallbackQueryHandler(reply_alert))

    utils.log('Configurado correctamente. Inicio sondeo.')

    updater.start_polling()

    uvicorn.run("main:api", host="0.0.0.0", port=5000, log_level="info")

    # Run the bot until the user presses Ctrl-C or
    # the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()
    utils.log("Termina la ejecucion")

if __name__ == '__main__':
    main()