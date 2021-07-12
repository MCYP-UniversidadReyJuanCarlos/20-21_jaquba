import configparser
from pathlib import Path
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

def start(update, context) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=config['TELEGRAM_BOT']['WelcomeMessage'])

def echo(update, context) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def unknown(update, context) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text=config['TELEGRAM_BOT']['UnknownCommand'])

def main() -> None:
    config = configparser.ConfigParser()
    config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')
    bot_token = config['TELEGRAM_BOT']['Token']

    print(bot_token)

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()