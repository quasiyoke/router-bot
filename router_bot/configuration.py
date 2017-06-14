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
                configuration_json = json.load(reader(f))
        except OSError as err:
            LOGGER.error('Troubles with opening \"%s\": %s', path, err)
            raise ConfigurationObtainingError(f'Troubles with opening \"{path}\"') from err
        except ValueError as err:
            LOGGER.error('Troubles with parsing \"%s\": %s', path, err)
            raise ConfigurationObtainingError(f'Troubles with parsing \"{path}\"') from err

        try:
            self.database_host = configuration_json['database']['host']
            self.database_name = configuration_json['database']['name']
            self.database_user = configuration_json['database']['user']
            self.database_password = configuration_json['database']['password']
            self.logging = configuration_json['logging']
            self.server = ServerConfiguration(configuration_json['server'])
            self.token = configuration_json['token']
        except (KeyError, TypeError) as err:
            LOGGER.error('Troubles with obtaining parameters: %s', err)
            raise ConfigurationObtainingError(f'Troubles with obtaining parameters \"{err}\"') from err
