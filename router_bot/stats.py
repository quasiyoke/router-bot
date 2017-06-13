# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json
import logging
from peewee import *

LOGGER = logging.getLogger('router_bot.stats')

database_proxy = Proxy()


class Stats(Model):
    data_json = TextField()
    created = DateTimeField(default=datetime.datetime.utcnow, index=True)

    class Meta:
        database = database_proxy

    def get_data(self):
        try:
            return self._data_cache
        except AttributeError:
            self._data_cache = json.loads(self.data_json)
            return self._data_cache

    def set_data(self, data):
        self._data_cache = data
        self.data_json = json.dumps(data)
