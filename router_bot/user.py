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
from .stats_service import StatsService
from .human_sender_service import HumanSenderService
from peewee import CharField, DateTimeField, IntegerField, Model, Proxy
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.user')
WIZARD_CHOICES = (
    ('none', 'None'),
    ('setup', 'Setup'),
    )
database_proxy = Proxy()


class User(Model):
    looking_for_partner_from = DateTimeField(null=True)

    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=5)
    UNMUTE_BONUSES_NOTIFICATIONS_DELAY = 60 * 60

    class Meta:
        database = database_proxy

    async def end_talk(self):
        if self.looking_for_partner_from is not None:
            # If user is looking for partner
            self.looking_for_partner_from = None
            try:
                await self.get_sender().send_notification('Looking for partner was stopped.')
            except TelegramError as err:
                LOGGER.warning('End chatting. Can\'t notify user %d: %s', self.id, err)
        elif self.get_partner() is not None:
            # If user is chatting now
            try:
                await self._notify_talk_ended(by_self=True)
            except UserError as err:
                LOGGER.warning('End chatting. Can\'t notify user %d: %s', self.id, err)
        await self.set_partner(None)

    def get_partner(self):
        try:
            return self._partner
        except AttributeError:
            talk = self.get_talk()
            self._partner = None if talk is None else talk.get_partner(self)
            return self._partner

    def get_sender(self):
        return HumanSenderService.get_instance().get_or_create_human_sender(self)

    def get_talk(self):
        try:
            return self._talk
        except AttributeError:
            from .talk import Talk
            self._talk = Talk.get_talk(self)
            return self._talk

    async def kick(self):
        try:
            await self._notify_talk_ended(by_self=False)
        except UserError as err:
            LOGGER.warning('Kick. Can\'t notify user %d: %s', self.id, err)
        self._talk = None
        self._partner = None

    async def _notify_talk_ended(self, by_self):
        """
        Raises:
            UserError If user we're changing has blocked the bot.

        """
        sender = self.get_sender()
        sentences = []

        if by_self:
            sentences.append('Chat was finished.')
        else:
            sentences.append('Your partner has left chat.')

        sentences.append('Feel free to /begin a new talk.')

        try:
            await sender.send_notification(' '.join(sentences))
        except TelegramError as err:
            raise UserError(str(err))

    async def notify_partner_found(self, partner):
        """
        Raises:
            UserError If user we're changing has blocked the bot.

        """
        sender = self.get_sender()
        sentences = []

        if self.get_partner() is None:
            sentences.append('Your partner is here.')
        else:
            sentences.append('Here\'s another user.')

        if partner.looking_for_partner_from:
            looked_for_partner_for = datetime.datetime.utcnow() - partner.looking_for_partner_from
            if looked_for_partner_for >= type(self).LONG_WAITING_TIMEDELTA:
                # Notify User if his partner did wait too much and could be asleep.
                minutes = round(looked_for_partner_for.total_seconds() / 60)
                long_waiting_notification = f'Your partner\'s been looking for you for {minutes} min. Say him ' \
                    '\"Hello\" -- if he doesn\'t respond to you, launch search again by /begin command.'
                sentences.append(long_waiting_notification)

        if len(sentences) < 2:
            sentences.append('Have a nice chat!')

        try:
            await sender.send_notification(' '.join(sentences))
        except TelegramError as err:
            raise UserError(f'Can\'t notify user {self.id}. {err}') from err

    async def send(self, message):
        """
        @raise UserError if can't send message because of unknown content type.
        @raise TelegramError if user has blocked the bot.
        """
        sender = self.get_sender()
        try:
            await sender.send(message)
        except HumanSenderError as err:
            raise UserError(f'Can\'t send content: {err}') from err

    async def send_to_partner(self, message):
        """
        @raise MissingPartnerError if there's no partner for this user.
        @raise UserError if can't send content.
        @raise TelegramError if the partner has blocked the bot.
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
        # Before setting `looking_for_partner_from`, check if it's already set
        # to prevent lowering priority.
        if self.looking_for_partner_from is None:
            self.looking_for_partner_from = datetime.datetime.utcnow()
        try:
            await self.get_sender().send_notification('Looking for a user for you.')
        except TelegramError as err:
            LOGGER.debug(
                'Set looking for partner. Can\'t notify user. %s',
                err,
                )
            self.looking_for_partner_from = None
        await self.set_partner(None)

    async def set_partner(self, partner):
        """Sets partner for a user. Always saves the model.

        """
        if self.get_partner() == partner:
            self.save()
            return
        if self._partner is not None:
            if self._partner.get_partner() == self:
                # If partner isn't talking with the user because of some
                # error, we shouldn't kick him.
                await self._partner.kick()
            if self._talk is not None:
                self._talk.end = datetime.datetime.utcnow()
                self._talk.save()
        if partner is None:
            self._talk = None
            self._partner = None
            self.save()
        else:
            from .talk import Talk
            self._talk = Talk.create(
                partner1=self,
                partner2=partner,
                searched_since=partner.looking_for_partner_from,
                )
            self._partner = partner
            if self.looking_for_partner_from is not None:
                self.looking_for_partner_from = None
                self.save()
            partner._talk = self._talk
            partner._partner = self
            partner.looking_for_partner_from = None
            partner.save()
