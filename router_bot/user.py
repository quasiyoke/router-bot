# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import json
import logging
from .error import MissingPartnerError, UserError, HumanSenderError
from .human_sender_service import HumanSenderService
from .stats_service import StatsService
from peewee import CharField, DateTimeField, IntegerField, Model, Proxy
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.user')
WIZARD_CHOICES = (
    ('none', 'None'),
    ('setup', 'Setup'),
    )
database_proxy = Proxy()


class User(Model):
    """
    "Abstract" router-bot user.

    """

    looking_for_partner_from = DateTimeField(null=True)

    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=5)
    UNMUTE_BONUSES_NOTIFICATIONS_DELAY = 60 * 60

    class Meta:
        database = database_proxy

    async def end_talk(self):
        if self.looking_for_partner_from is not None:
            # If user is looking for partner
            self.looking_for_partner_from = None
            await self.get_concrete_user(). \
                notify_looking_for_partner_was_finished()
        elif self.get_partner() is not None:
            # If user is chatting now
            try:
                await self.get_concrete_user(). \
                    notify_talk_was_finished(by_self=True)
            except UserError as err:
                LOGGER.warning('End chatting. Can\'t notify user %d: %s', self.id, err)
        await self.set_partner(None)

    def get_concrete_user(self):
        """
        Raises:
            UserError If there's no human or client bot of such user.

        """
        try:
            concrete_user = self.humen.get()
        except DoesNotExist:
            try:
                concrete_user = self.client_bots.get()
            except DoesNotExist:
                reason = f'User {self.id} doesn\'t have neither human nor client bot.'
                LOGGER.error(reason)
                raise UserError(reason=reason)
        return concrete_user

    def get_partner(self):
        talk = self.get_talk()
        return None if talk is None else talk.get_partner(self)

    def get_talk(self):
        from .talk import Talk
        return Talk.get_talk(self)

    async def kick(self):
        try:
            await self.get_concrete_user(). \
                notify_talk_was_finished(by_self=False)
        except UserError as err:
            LOGGER.warning('Kick. Can\'t notify user %d: %s', self.id, err)

    async def notify_partner_found(self, partner):
        """
        Raises:
            UserError If there's no human or client bot of such user or if human we're changing has blocked the bot.

        """
        await self.get_concrete_user(). \
            notify_partner_found(partner)

    async def send(self, message):
        """
        Raises:
            UserError if can't send message because of unknown content type.
            TelegramError if user has blocked the bot.

        """
        await self.get_concrete_user(). \
            send(message)

    async def send_to_partner(self, message):
        """
        Args:
            message (str)

        Raises:
            MissingPartnerError if there's no partner for this user.
            UserError if can't send content.
            TelegramError if the partner has blocked the bot.

        """
        partner = self.get_partner()
        if partner is None:
            raise MissingPartnerError()
        try:
            await partner.send(message)
        except:
            raise
        else:
            self.get_talk().increment_sent(self)

    async def set_looking_for_partner(self):
        try:
            await self.get_concrete_user(). \
                notify_looking_for_partner()
        except UserError as err:
            self.looking_for_partner_from = None
            LOGGER.warning('Can\'t notify ')
        else:
            # Before setting `looking_for_partner_from`, check if it's already set
            # to prevent lowering priority.
            if self.looking_for_partner_from is None:
                self.looking_for_partner_from = datetime.datetime.utcnow()
        await self.set_partner(None)

    async def set_partner(self, partner):
        """Sets partner for a user. Always saves the model.

        """
        current_partner = self.get_partner()
        if current_partner == partner:
            self.save()
            return
        if current_partner is not None:
            partners_partner = current_partner.get_partner()
            # If partner isn't talking with the user because of some
            # error, we shouldn't kick him.
            if partners_partner == self:
                await current_partner.kick()
            else:
                LOGGER.error(
                    'User %d has a partner %d which partners with %d, not us!',
                    self.id,
                    current_partner.id,
                    partners_partner.id,
                    )
            talk = self.get_talk()
            if talk is not None:
                talk.end = datetime.datetime.utcnow()
                talk.save()
        if partner is not None:
            from .talk import Talk
            Talk.create(
                partner1=self,
                partner2=partner,
                searched_since=partner.looking_for_partner_from,
                )
            if self.looking_for_partner_from is not None:
                self.looking_for_partner_from = None
            partner.looking_for_partner_from = None
            partner.save()
        self.save()
