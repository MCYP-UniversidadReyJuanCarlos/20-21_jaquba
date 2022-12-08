from pydantic import BaseModel
import json # to parse and generate JSON strings
from telegram import InlineKeyboardButton
from telegram.ext import CallbackContext
from aiocache import Cache # to share variables between threads
import i18n # to have localized messages
import logging # to generate traces of execution
import requests # to make HTTP requests, used to reply alerts


alert_levels = {1: 'INFO', 2: 'WARNING', 3: 'CRITICAL'}
debug = False

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
cache = Cache(Cache.MEMORY)

# Print debug messages
def log(message) -> None:
    global debug, logger
    if debug is False:
        logger.info(message)
    else:
        print(message)

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

def get_buttons(module: str, alert_type: str, id_alert: int) -> list:
    keyboard = []
    if module == 'SSH' and alert_type == 'new_connection':
        keyboard = [
            [
                InlineKeyboardButton(i18n.t('bot.ssh.option1'), callback_data=f'{id_alert}#close_connection'),
                InlineKeyboardButton(i18n.t('bot.ssh.option2'), callback_data=f'{id_alert}#block_port')
            ],
            [InlineKeyboardButton(i18n.t('bot.ssh.ignore'), callback_data=f'{id_alert}#ignore')]
        ]
    elif module == 'PerfMonitor' and alert_type == 'cpu':
        keyboard = [
            [
                InlineKeyboardButton(i18n.t('bot.perfMonitor.option1'), callback_data=f'{id_alert}#reboot'),
                InlineKeyboardButton(i18n.t('bot.perfMonitor.option2'), callback_data=f'{id_alert}#power_off')
            ],
            [InlineKeyboardButton(i18n.t('bot.perfMonitor.ignore'), callback_data=f'{id_alert}#ignore')]
        ]
    
    return keyboard

def get_detail_info(module: str, alert_type: str, data_json: str) -> str:
    detail = None

    data = json.loads(data_json)
    if module == 'SSH' and alert_type == 'new_connection':
        detail = i18n.t('bot.ssh.newConnection', ip=data['ip'], port=data['port'])
    elif module == 'PerfMonitor' and alert_type == 'cpu':
        detail = i18n.t('bot.perfMonitor.cpuUsage', usage=data['usage'])
    
    return detail

def send_response(alert: dict, option: str, port: str) -> requests.Response:
    module = alert['module']
    alert_type = alert['alert_type']
    ip = alert['ip']

    response = {
        'module': module,
        'alert_type': alert_type,
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

    url = f'http://{ip}:{port}/response'

    http_response = requests.post(url, headers=headers, data=json_data)
    return http_response