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

#   VARIABLES GLOBALES     #
logger = None # to log application status and info
config = configparser.ConfigParser() # to read config file
threadConnListener = None # thread to accept connections
lock = threading.Lock() # to prevent concurrent access to the previous variable
awaitConnections = True # flag to indicate end of accept connections
serversocket = None # this socket acts as a server to recieve new connections
poolListeners = None # pool of threads to process accepted connections
debug = False
############################

# Print debug messages
def log(str):
    global debug, logger
    if debug is False:
        logger.info(str)
    else:
        print(str)

# Invoked when recieves termination signal from user
def stop_execution(signum, frame):
    global threadConnListener, serversocket, lock, awaitConnections
    log('Recibo signal ' + str(signum))
    if threadConnListener.is_alive():
        log('threadConnListener alive, intento terminarlo')
        serversocket.close()
        lock.acquire()
        awaitConnections = False
        lock.release()
        threadConnListener.join()

# Handle the new connection to receive the alert and send it to chat
def recieve_alert(clientsocket, address):
    host, port = address
    log('Recibo alerta de ' + host + ':' + str(port))
    chunk = clientsocket.recv(1024)
    string = chunk.decode('utf-8')
    log('Recibo el mensaje ' + string)
    clientsocket.shutdown(socket.SHUT_RD)
    clientsocket.close()

def accept_connection():
    global serversocket, poolListeners
    # acepta una nueva conexion y lanza un hilo para leer
    try:
        (clientsocket, address) = serversocket.accept()
        log('Acepto una nueva conexion y lanzo un hilo para lectura')
        poolListeners.submit(recieve_alert, clientsocket, address)
    except Exception:
        log("Salgo del accept")

# Wait for new connections (to recieve alerts)
def listen_connections():
    global serversocket, poolListeners, lock, awaitConnections
    log('Estoy en el hilo para aceptar conexiones')

    # crea el socket de comunicacion
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to this machine with hostname and port
    port = int(config['SERVERS']['DefaultPort'])
    serversocket.bind(('', port))
    # escucha conexiones hasta un maximo de 5 encoladas
    serversocket.listen(5)

    poolListeners = ThreadPoolExecutor(max_workers=4)

    while True:
        log('Bucle de escucha')
        lock.acquire()
        if awaitConnections is False:
            lock.release()
            log('Termino de aceptar conexiones')
            # espera que terminen todos los hilos lanzados
            poolListeners.shutdown(wait=True)
            log('Han terminado los hilos de recepcion')
            return
        lock.release()

        accept_connection()
        
        log('Sigo escuchando conexiones')
        sleep(5)


# Executed when a new chat is open
def start(update, context) -> None:
    global config
    log('Nuevo chat con id = ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=config['TELEGRAM_BOT']['WelcomeMessage'])

# Executed whenever message is recieved
def echo(update, context) -> None:
    log('Respondiendo ' + update.message.text + ' en el chat ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# Executed when an unknown command is recieved
def unknown(update, context) -> None:
    global config
    log('Comando desconocido en el chat con id = ' + str(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=config['TELEGRAM_BOT']['UnknownCommand'])

# Entry point
def main() -> None:
    global logger, config, threadConnListener, lock, awaitConnections

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    logger = logging.getLogger(__name__)

    log('Inicio config')

    config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')

    bot_token = config['TELEGRAM_BOT']['Token']
    log('El token es ' + bot_token)

    updater = Updater(token=bot_token, use_context=True, user_sig_handler=stop_execution)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    log('Configurado correctamente. Inicio sondeo.')

    updater.start_polling()

    threadConnListener = threading.Thread(target=listen_connections)

    log("Lanza el hilo que espera conexiones")
    threadConnListener.start()

    # Run the bot until the user presses Ctrl-C or
    # the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

    # Comprobamos si ha terminado el hilo y si no volvemos a esperar que termine
    if threadConnListener.is_alive():
        lock.acquire()
        awaitConnections = False
        lock.release()
        log("Esperando a que termine el hilo")
        threadConnListener.join()

    log("Termina la ejecucion")

if __name__ == '__main__':
    main()