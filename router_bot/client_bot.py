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


class ClientBot(ConcreteUser, BaseClientBot):
    """
    Telegram bot managed by router-bot.

    """

    user = ForeignKeyField(User, primary_key=True, related_name='client_bots')
    bot_id = IntegerField(unique=True)
    secret = CharField(max_length=60)
    webhook = CharField(max_length=127, null=True)

    class Meta:
        database = database_proxy

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Args:
            token (str): Telegram bot token like that: "123456789:AAEfqU70n2V6dUK8u4n0u7N581JqPU06766".
            first_name (str): Bot's first name.
            update_service (telegram_bot_server.UpdateService)

        Returns:
            ClientBot instance or `None` in case of bad token.

        """
        user = User.create()
        return cls.create_by_token(
            user=user,
            *args,
            **kwargs,
            )

    def __init__(self, *args, user, **kwargs):
        super(ClientBot, self).__init__(*args, **kwargs)
        BaseClientBot.__init__(self, *args, **kwargs)
        self.user = user
        self.save(force_insert=True)

    async def handle_message(self, message):
        """
        Handler for incoming message.

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

    async def send(self, message):
        """
        Send message to the client Telegram bot.

        Args:
            message (str)

        Raises:
            UserError if can't send message because of unknown content type.
            TelegramError if user has blocked the bot.

        """
        talk = self.user.get_talk()
        sender = talk.get_partner(self.user)
        await self.send_message(
            chat=talk.chat_dict,
            from_dict=sender.user_dict,
            text=message,
            )
