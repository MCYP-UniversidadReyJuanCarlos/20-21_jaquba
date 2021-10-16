import configparser # to read config files
from pathlib import Path

# external telegram bot library
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import logging # to generate traces of execution
import re # for regex validations
from time import sleep

import threading # to create threads
from concurrent.futures import ThreadPoolExecutor, Future # to use thread pools 

import socket # to communicate with alert and response modules

# Invoked when recieves termination signal from user
def stop_execution(signum, frame):
    logger.info('Recibo signal ' + str(signum))
    threadConnListener.join(5)
    if threadConnListener.is_alive():
        logger.info('threadConnListener alive, intento terminarlo')
        lock.acquire()
        awaitConnections = False
        lock.release()
        threadConnListener.join(5)

# Handle the new connection to receive the alert and send it to chat
def recieve_alert(clientsocket, address):
    host, port = address
    logger.info('Recibo alerta de ' + host + ':' + str(port))
    chunk = clientsocket.recv(1024)
    string = chunk.decode('utf-8')
    logger.info('Recibo el mensaje ' + string)

# Wait for new connections (to recieve alerts)
def listen_connections():
    logger.info('Estoy en el hilo para aceptar conexiones')
    # crea el socket de comunicacion
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to this machine with hostname and port
    port = int(config['SERVERS']['DefaultPort'])
    serversocket.bind(('', port))
    # escucha conexiones hasta un maximo de 5 encoladas
    serversocket.listen(5)

    global poolListeners
    poolListeners = ThreadPoolExecutor(max_workers=4)

    while True:
        logger.info('Bucle de escucha')
        with lock:
            if awaitConnections is False:
                logger.info('Termino de aceptar conexiones')
                # espera que terminen todos los hilos lanzados
                poolListeners.shutdown(wait=True)
                logger.info('Han terminado los hilos de recepcion')
                return
        # acepta una nueva conexion y lanza un hilo para leer
        (clientsocket, address) = serversocket.accept()
        logger.info('Acepto una nueva conexion y lanzo un hilo para lectura')
        future = poolListeners.submit(recieve_alert, clientsocket, address)
        logger.info('submit = ' + str(future.running()) + ' ' + str(future.done()))
        logger.info('result = ' + future.result())
        logger.info('Sigo escuchando conexiones')
        sleep(5)

# Executed when a new chat is open
def start(update, context) -> None:
    logger.info('Nuevo chat con id = ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=config['TELEGRAM_BOT']['WelcomeMessage'])

# Executed whenever message is recieved
def echo(update, context) -> None:
    logger.info('Respondiendo ' + update.message.text + ' en el chat ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# Executed when an unknown command is recieved
def unknown(update, context) -> None:
    logger.info('Comando desconocido en el chat con id = ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=config['TELEGRAM_BOT']['UnknownCommand'])

# Entry point
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

    updater = Updater(token=bot_token, use_context=True, user_sig_handler=stop_execution)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    logger.info('Configurado correctamente. Inicio sondeo.')

    updater.start_polling()

    # Retrieves the list of servers, split it by comma and filter only the valid IPs
    listOfIPs = [ip.strip() for ip in config['SERVERS']['IPs'].split(',') \
        if re.match('^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$', ip.strip())]

    logger.info('IPs encontradas: ' + str(listOfIPs))

    global threadConnListener
    threadConnListener = threading.Thread(target=listen_connections)

    global awaitConnections
    awaitConnections = True

    # se usa para no acceder desde varios hilos a la variable anterior
    global lock
    lock = threading.Lock()

    logger.info("Lanza el hilo que espera conexiones")
    threadConnListener.start()

     # Run the bot until the user presses Ctrl-C or
    # the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

    # Comprobamos si ha terminado el hilo y si no volvemos a esperar que termine
    if threadConnListener.is_alive():
        lock.acquire()
        awaitConnections = False
        lock.release()
        logger.info("Esperando a que termine el hilo")
        threadConnListener.join(5)

    logging.info("Termina la ejecucion")


if __name__ == '__main__':
    main()