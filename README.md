# 20-21_jaquba - SecARC (Security Alerts and Remote Control)

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

## Indice 
> 1. [Descripción del proyecto](#descripción-del-proyecto)
> 2. [Características](#características)
> 3. [Pre-requisitos](#pre-requisitos)
> 4. [Instalación](#instalación)
> 5. [Configuración](#configuración)
> 6. [Ejecución y uso](#ejecución-y-uso)
> 7. [Arquitectura](#arquitectura)

# Descripción del proyecto

SecARC es una herramienta de detección y respuesta a incidentes de seguridad detectados en servidores Linux.
Actualmente permite, aunque es facilmente ampliable, las siguientes funcionalidades:

- Detectar nuevas conexiones SSH contra un servidor y responder a ellas de tres maneras:
    * Permitiendo la conexión.
    * Cerrando la conexión, pero permitiendo otras nuevas.
    * Bloqueando la IP, de modo que se rechacen todas las conexiones (incluyendo la actual).
- Monitorizar el uso de CPU de un servidor y generar una alerta cuando supere un umbral predefinido.
Ignora los picos de utilización, para evitar producir demasiadas alertas, y comprueba un uso de recursos sostenido.
Ofrece tres posibles respuestas:
    * No actuar, con lo que se permite dicho uso hasta la proxima alerta generada.
    * Reiniciar el servidor.
    * Apagar el servidor.
- Monitorizar las peticiones HTTP a un servidor web y generar una alerta cuando el número de errores 404 procedentes de una misma dirección IP, en un intervalo definido, supere el umbral indicado.
Esto puede indicar que se está produciendo un ataque de escaneo de recursos o de denegación de servicio.
Como respuesta solo ofrece dos posibilidades:
    * No actuar, permitiendo las conexiones hasta la próxima alerta.
    * Bloquear la IP, de modo que no pueda hacer más peticiones.
- Recibir las alertas y poder responder a ellas de manera rápida y sencilla, mediante la aplicacion de mensajería Telegram, con solo pulsar un botón.
Esto es beneficioso ante una amenaza, ya que reduce mucho el tiempo de respuesta, con lo que se minimiza el posible daño ocasionado.

Las ventajas de esta herramienta frente a otras disponibles en el mercado son:
- Facilidad de instalación, configuración y ampliación.
- De bajo coste y sin requerir hardware adicional.
- Control de las alertas y las respuestas sencillo y rápido.

# Características 

[![VS Code](https://img.shields.io/badge/Visual_Studio_Code-0078D4?style=for-the-badge&logo=visual%20studio%20code&logoColor=white)](https://code.visualstudio.com/)

Como entorno de desarollo se ha utilizado Visual Studio Code, ya que nos ofrece una serie de plugins que nos facilitan el desarrollo y las pruebas.

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

Como lenguaje principal para el desarrollo del proyecto se ha usado Python, concretamente la versión 3.11 por ser la última disponible en este momento.

[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)

Se ha utilizado Telegram como panel de control donde visualizar y responder las alertas recibidas, mediante el bot que se ha desarrollado.\
Para crear el bot se ha utilizado BotFather y la libreria [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

Se utiliza FastAPI para crear los endpoints de cada una de las API necesarias:
- /alert: Se ubica en la misma máquina que el bot y permite recibir las alertas
- /response: Ubicado en cada servidor a monitorizar para recibir las respuestas

El servidor utilizado para ejecutar las APIs ha sido [Uvicorn](https://www.uvicorn.org/) ya que es ligero, rápido y se integra perfectamente con FastAPI y Python.

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)

Utilizamos Nginx como servidor HTTP para simular una página web que esta recibiendo tráfico real y poder monitorizar los errores HTTP 404 que ocurren por cada IP cliente, de modo que se compruebe el funcionamiento del módulo de deteccion correspondiente.

# Pre-requisitos

- El bot se debe instalar en una máquina con acceso a Internet, para que pueda comunicarse con Telegram para enviar las alertas al usuario y recibir las respuestas elegidas por este.
- Los servidores a monitorizar tienen que tener conectividad de red con la máquina que ejecuta el bot, para poder enviar las alertas detectadas.
- La máquina que ejecuta el bot también debe tener conectividad con los servidores a monitorizar, para poder enviar las respuestas.
- Tener instalado Python 3, tanto en los servidores a monitorizar, como en la máquina que ejecutará el bot.
- [Solo para monitorizar errores HTTP 404] Tener instalado y correctamente configurado el servidor web Nginx.
Se puede seguir la siguiente [guia de instalación](https://linuxhint.com/install-nginx-linux-mint/), solo aplicable para Ubuntu y Linux Mint, revisar para otras distribuciones Linux.
- Tener el Token del bot a utilizar. Para ello se utiliza @BotFather, un bot que proporciona Telegram para configurar nuevos bots. Para crearlo, se puede seguir la siguiente [guia](https://atareao.es/tutorial/crea-tu-propio-bot-para-telegram/).

# Instalación

1. Clonar el repositorio
   
```bash
git clone https://github.com/MCYP-UniversidadReyJuanCarlos/20-21_jaquba.git
```

2. Copiar las carpetas necesarias en cada máquina:
    * Para el bot y la API REST /alert solo es necesaria la carpeta bot
    * Para los servidores a monitorizar se deben copiar las carpetas alert y response

3. Eliminar los módulos que no sean necesarios para cada servidor. Tener en cuenta que se debe eliminar tanto el módulo de detección (de la carpeta alert) como el de respuesta (carpeta response).
Por ejemplo, si queremos eliminar el módulo HTTP debemos:
    * Entrar en la carpeta alert y borrar el fichero web_server.py
    * Editar el fichero config.ini y eliminar las variables relacionadas: interval_HTTP, threshold_warning_HTTP y threshold_critical_HTTP
    * Entrar en la carpeta response y borrar el fichero web_server.py
    * Editar el fichero response.py para eliminar las referencias a dicho módulo del método get_response

4. Instalar las dependencias necesarias, para ello entraremos en cada una de las carpetas (bot, alert y response) y ejecutaremos el siguiente comando:
```bash
pip install -r requirements.txt
```

5. Configurar el Token del bot que queremos usar. Para ello abrimos el fichero config.ini que se encuentra en la carpeta bot y sustituimos {Bot Token} por dicho token.

# Configuración

Podemos personalizar el comportamiento de la herramienta si es necesario.

Se puede elegir el idioma del bot entre Español e Inglés.

# Ejecución y uso
If you have decided to download the tool from the Chrome Web Store there is nothing to do apart from enabling the extension.
If, on the other hand, you have downloaded the tool locally, follow the next steps:

```bash
cd 20-21_jaquba
```

# Arquitectura

![Arquitectura de SecARC](resources/arquitectura_SecARC.png "Arquitectura de la herramienta SecARC")

