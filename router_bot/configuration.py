# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import json
import logging
from .error import ConfigurationObtainingError
from telegram_bot_server import DictConfiguration as ServerConfiguration

LOGGER = logging.getLogger('router_bot.configuration')


class Configuration:
    def __init__(self, path):
        reader = codecs.getreader('utf-8')
        try:
            with open(path, 'rb') as f:
                configuration_dict = json.load(reader(f))
        except OSError as err:
            reason = f'Troubles with opening \"{path}\"'
            LOGGER.exception(reason)
            raise ConfigurationObtainingError(reason) from err
        except ValueError as err:
            reason = f'Troubles with parsing \"{path}\"'
            LOGGER.exception(reason)
            raise ConfigurationObtainingError(reason) from err

        try:
            self.admins_telegram_ids = configuration_dict['admins']
            self.database_host = configuration_dict['database']['host']
            self.database_name = configuration_dict['database']['name']
            self.database_user = configuration_dict['database']['user']
            self.database_password = configuration_dict['database']['password']
            self.logging = configuration_dict['logging']
            self.server = ServerConfiguration(configuration_dict['server'])
            self.token = configuration_dict['token']
        except (KeyError, TypeError) as err:
            reason = 'Troubles with obtaining parameters'
            LOGGER.exception(reason)
            raise ConfigurationObtainingError(reason) from err
