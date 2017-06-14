# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .client_bot import ClientBot
from .error import DbError
from .human import Human
from .stats import Stats
from .talk import Talk
from .user import User
from peewee import DatabaseError, MySQLDatabase
from playhouse.shortcuts import RetryOperationalError
from router_bot import client_bot, human, stats, talk, user

LOGGER = logging.getLogger('router_bot.db')


class RetryingDB(RetryOperationalError, MySQLDatabase):
    """Automatically reconnecting database class.
    @see http://docs.peewee-orm.com/en/latest/peewee/database.html#automatic-reconnect

    """
    pass


class Db:
    def __init__(self, configuration):
        self._db = RetryingDB(
            configuration.database_name,
            host=configuration.database_host,
            user=configuration.database_user,
            password=configuration.database_password,
            )
        # Connect to database just to check if configuration has errors.
        try:
            self._db.connect()
        except DatabaseError as err:
            raise DbError(f'DatabaseError during connecting to database. {err}') from err
        client_bot.database_proxy.initialize(self._db)
        human.database_proxy.initialize(self._db)
        stats.database_proxy.initialize(self._db)
        talk.database_proxy.initialize(self._db)
        user.database_proxy.initialize(self._db)

    def install(self):
        try:
            self._db.create_tables((User, ClientBot, Human, Stats, Talk))
        except DatabaseError as err:
            raise DbError(f'DatabaseError during creating tables. {err}') from err

    def flush(self):
        self._db.close()
