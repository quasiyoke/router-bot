# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
from .error import MissingPartnerError, UserError, HumanSenderError
from .stats_service import StatsService
from .user import User
from .human_sender_service import HumanSenderService
from peewee import CharField, ForeignKeyField, IntegerField, Model, Proxy
from telegram_bot_server import Bot as BaseClientBot
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.client_bot')
database_proxy = Proxy()


class ClientBot(BaseClientBot, Model):
    user = ForeignKeyField(User, primary_key=True, related_name='client_bots')
    bot_id = IntegerField(unique=True)
    secret = CharField(max_length=60)
    webhook = CharField(max_length=127)

    class Meta:
        database = database_proxy

    async def set_webhook(self, url):
        is_changed = await super(ClientBot, self).set_webhook(url)
        if is_changed:
            self.save()
        return is_changed
