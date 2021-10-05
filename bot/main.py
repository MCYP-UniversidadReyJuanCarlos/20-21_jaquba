import configparser
from pathlib import Path
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

def start(update, context) -> None:
    logger.info('Nuevo chat con id = ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=config['TELEGRAM_BOT']['WelcomeMessage'])

def echo(update, context) -> None:
    logger.info('Respondiendo ' + update.message.text + ' en el chat ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def unknown(update, context) -> None:
    logger.info('Comando desconocido en el chat con id = ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=config['TELEGRAM_BOT']['UnknownCommand'])

def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    global logger
    logger = logging.getLogger(__name__)

    logger.info('Inicio config')

    global config
    config = configparser.ConfigParser()
    config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')
    bot_token = config['TELEGRAM_BOT']['Token']

    logger.info('El token es ' + bot_token)

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    logger.info('Configurado correctamente. Inicio sondeo.')

    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()