# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""router_bot.router_bot: provides entry point main()."""

import asyncio
import logging
import logging.config
import sys
from .bot import Bot
from .configuration import Configuration
from .db import DB
from .error import ConfigurationObtainingError, DBError
from .stranger_sender_service import StrangerSenderService
from .util import __version__
from docopt import docopt
from router_bot import stranger, stranger_service

DOC = '''router-bot

Usage:
  router_bot CONFIGURATION
  router_bot install CONFIGURATION
  router_bot -h | --help | --version

Arguments:
  CONFIGURATION  Path to configuration.json file.
'''
LOGGER = logging.getLogger('router_bot')


def main():
    logging.basicConfig(level=logging.DEBUG)
    arguments = docopt(DOC, version=__version__)

    try:
        configuration = Configuration(arguments['CONFIGURATION'])
    except ConfigurationObtainingError as err:
        sys.exit(f'Can\'t obtain configuration. {err}')

    logging.config.dictConfig(configuration.logging)

    try:
        db = DB(configuration)
    except DBError as err:
        sys.exit(f'Can\'t construct DB. {err}')

    try:
        if arguments['install']:
            LOGGER.info('Installing router-bot')
            try:
                db.install()
            except DBError as err:
                sys.exit(f'Can\'t install databases. {err}')
        else:
            LOGGER.info('Executing router-bot')
            loop = asyncio.get_event_loop()

            bot = Bot(configuration)
            asyncio.ensure_future(bot.run())

            try:
                loop.run_forever()
            except KeyboardInterrupt:
                LOGGER.info('Execution was finished by keyboard interrupt')
    finally:
        db.flush()
