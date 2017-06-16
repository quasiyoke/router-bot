# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
from .error import DbError, HumanSenderError, MissingPartnerError, UserError
from .stats_service import StatsService
from .user import User
from .user_service import UserService
from .human_sender_service import HumanSenderService
from peewee import CharField, DatabaseError, DateTimeField, DoesNotExist, ForeignKeyField, IntegerField, Model, Proxy
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.user')
WIZARD_CHOICES = (
    ('none', 'None'),
    ('setup', 'Setup'),
    )
database_proxy = Proxy()


class Human(Model):
    user = ForeignKeyField(User, primary_key=True, related_name='humen')
    telegram_id = IntegerField(unique=True)
    wizard = CharField(choices=WIZARD_CHOICES, default='none', max_length=20)
    wizard_step = CharField(max_length=20, null=True)

    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=5)
    UNMUTE_BONUSES_NOTIFICATIONS_DELAY = 60 * 60

    class Meta:
        database = database_proxy

    @classmethod
    def create(cls, *args, **kwargs):
        user = User.create()
        return super().create(
            user=user,
            *args,
            **kwargs,
            )

    @classmethod
    def get_or_create_human(self, telegram_id):
        """
        Raises:
            DbError

        """
        try:
            try:
                human = Human.get(Human.telegram_id == telegram_id)
            except DoesNotExist:
                human = Human.create(
                    telegram_id=telegram_id,
                    )
        except DatabaseError as err:
            raise DbError(f'Database problems during `get_or_create_human`: {err}') from err
        human.user = UserService.get_instance().get_cached_user(human.user)
        return human

    @classmethod
    def get_human(self, telegram_id):
        """
        Raises:
            DbError

        """
        try:
            human = Human.get(Human.telegram_id == telegram_id)
        except (DatabaseError, DoesNotExist) as err:
            raise DbError(f'Database problems during `get_human`: {err}') from err
        return human

    def get_sender(self):
        return HumanSenderService.get_instance().get_or_create_human_sender(self)

    async def notify_looking_for_partner(self):
        """
        Raises:
            UserError If can't notify human about looking for partner.

        """
        try:
            await self.get_sender().send_notification('Looking for a user for you.')
        except TelegramError as err:
            LOGGER.debug(
                'Set looking for partner. Can\'t notify user. %s',
                err,
                )
            self.looking_for_partner_from = None

    async def notify_looking_for_partner_was_finished(self):
        try:
            await self.get_sender().send_notification('Looking for partner was stopped.')
        except TelegramError as err:
            LOGGER.warning('End chatting. Can\'t notify user %d: %s', self.user.id, err)

    async def notify_partner_found(self, partner):
        """
        Raises:
            UserError If user we're changing has blocked the bot.

        """
        sender = self.get_sender()
        sentences = []

        if self.user.get_partner() is None:
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

    async def notify_talk_was_finished(self, by_self):
        """
        Raises:
            UserError If human we're notifying has blocked the bot.

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
            raise UserError(str(err)) from err

    async def send(self, message):
        """
        Raises:
            UserError if can't send message because of unknown content type.
            TelegramError if user has blocked the bot.

        """
        sender = self.get_sender()
        try:
            await sender.send(message)
        except HumanSenderError as err:
            raise UserError(f'Can\'t send content: {err}') from err
