router-bot
==========

The bot for conversational artificial intelligence competition. router-bot was written on Python 3.6, `telepot <https://github.com/nickoala/telepot>`_ and `telegram-bot-server <https://github.com/quasiyoke/telegram-bot-server>`_.

Supported commands
------------------

In @BotFather compatible format::

    begin - Begin looking for next partner
    end - End talking
    help - Help

Admins specified at ``admins`` configuration property are able to use the following additional commands::

    add_bot TOKEN FIRST_NAME — Create new client bot authenticated by specified token.

Deployment
----------

::

    $ docker network create \
        --subnet=172.30.0.0/16 \
        router-bot-net
    $ docker run \
        --name=router-bot-mysql \
        --net=router-bot-net \
        --ip=172.30.0.20 \
        --env="MYSQL_ROOT_PASSWORD=ZEbMKcFQppk8m8PR3b" \
        --env="MYSQL_DATABASE=router-bot" \
        --env="MYSQL_USER=router-bot" \
        --env="MYSQL_PASSWORD=KbWj0Eua78YGLNLf3K" \
        --detach \
        mysql:5.7
    $ docker build --tag=router-bot .

After that write ``configuration/configuration.json`` file like that::

    {
        "admins": [
            314159,
            271828
        ],
        "database": {
            "host": "172.30.0.20",
            "name": "router-bot",
            "user": "router-bot",
            "password": "KbWj0Eua78YGLNLf3K"
        },
        "logging": {
            "version": 1,
            "formatters": {
                "simple": {
                    "class": "logging.Formatter",
                    "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "simple"
                }
            },
            "loggers": {
                "asyncio": {
                    "level": "DEBUG",
                    "handlers": []
                },
                "router_bot": {
                    "level": "DEBUG",
                    "handlers": []
                },
                "peewee": {
                    "level": "DEBUG",
                    "handlers": []
                }
            },
            "root": {
                "level": "DEBUG",
                "handlers": ["console"]
            }
        },
        "server": {
            "port": 8000
        },
        "token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    }

Now you may run the bot::

    $ docker run \
        --name=router-bot \
        --net=router-bot-net \
        --ip=172.30.0.10 \
        --volume=`pwd`/configuration:/configuration \
        --detach \
        router-bot
