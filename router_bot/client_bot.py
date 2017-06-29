# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
from .concrete_user import ConcreteUser
from .error import MissingPartnerError, UserError, HumanSenderError
from .stats_service import StatsService
from .user import User
from peewee import CharField, ForeignKeyField, IntegerField, Proxy
from telegram_bot_server import Bot as BaseClientBot
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.client_bot')
database_proxy = Proxy()


class ClientBot(BaseClientBot, ConcreteUser):
    user = ForeignKeyField(User, primary_key=True, related_name='client_bots')
    bot_id = IntegerField(unique=True)
    secret = CharField(max_length=60)
    webhook = CharField(max_length=127)

    class Meta:
        database = database_proxy

    async def handle_message(self, message):
        """
        Args:
            message (str)

        """
        await self.user.send_to_partner(message)

    async def set_webhook(self, url):
        is_changed = await super(ClientBot, self).set_webhook(url)
        if is_changed:
            self.save()
        return is_changed

    async def notify_looking_for_partner(self):
        """
        Raises:
            UserError If can't notify human about looking for partner.

        """
        pass
        #raise NotImplementedError()

    async def notify_looking_for_partner_was_finished(self):
        pass

    async def notify_partner_found(self, partner):
        """
        Raises:
            UserError If user we're changing has blocked the bot.

        """
        pass
        #raise NotImplementedError()

    async def notify_talk_was_finished(self, by_self):
        """
        Args:
            by_self (bool)

        Raises:
            UserError If human we're notifying has blocked the bot.

        """
        await self.send('/end')
        #raise NotImplementedError()

    async def send(self, message):
        """
        Args:
            message (str)

        Raises:
            UserError if can't send message because of unknown content type.
            TelegramError if user has blocked the bot.

        """
        talk = self.user.get_talk()
        sender = talk.get_partner(self.user)
        await bot.send_message(
                chat=talk.chat_dict,
                from_dict=sender.user_dict,
                text=message,
                )
