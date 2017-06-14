# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Provides entry point main().

"""

import asyncio
import logging
import logging.config
import sys
from .bot import Bot
from .client_bot_service import ClientBotService
from .configuration import Configuration
from .db import Db
from .error import ConfigurationObtainingError, DbError
from .human_sender_service import HumanSenderService
from .server import Server
from .stats_service import StatsService
from .util import __version__
from docopt import docopt
from router_bot import user, user_service
from telegram_bot_server import SimpleUpdateService

DOC = '''router-bot

Usage:
  router_bot CONFIGURATION
  router_bot install CONFIGURATION
  router_bot -h | --help | --version

Arguments:
  CONFIGURATION  Path to configuration.json file.
'''
LOGGER = logging.getLogger('router_bot.router_bot')


def main():
    logging.basicConfig(level=logging.DEBUG)
    arguments = docopt(DOC, version=__version__)

    try:
        configuration = Configuration(arguments['CONFIGURATION'])
    except ConfigurationObtainingError as err:
        sys.exit(f'Can\'t obtain configuration. {err}')

    logging.config.dictConfig(configuration.logging)

    try:
        db = Db(configuration)
    except DbError as err:
        sys.exit(f'Can\'t construct DB. {err}')

    try:
        if arguments['install']:
            LOGGER.info('Installing router-bot')
            try:
                db.install()
            except DbError as err:
                sys.exit(f'Can\'t install databases. {err}')
        else:
            LOGGER.info('Executing router-bot')
            loop = asyncio.get_event_loop()

            bot = Bot(configuration)
            asyncio.ensure_future(bot.run())

            stats_service = StatsService.get_instance()
            asyncio.ensure_future(stats_service.run())

            update_service = SimpleUpdateService()
            bot_service = ClientBotService(update_service=update_service)
            server = Server(
                bot_service=bot_service,
                configuration=configuration.server,
                update_service=update_service,
                )

            try:
                loop.run_forever()
            except KeyboardInterrupt:
                LOGGER.info('Execution was finished by keyboard interrupt')
    finally:
        db.flush()
