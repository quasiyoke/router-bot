# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from peewee import Model


class ConcreteUser(Model):
    """
    Abstract concrete user :)

    """

    @classmethod
    def create(cls, *args, **kwargs):
        user = User.create()
        return super().create(
            user=user,
            *args,
            **kwargs,
            )

    async def notify_looking_for_partner(self):
        """
        Raises:
            UserError If can't notify human about looking for partner.

        """
        raise NotImplementedError()

    async def notify_looking_for_partner_was_finished(self):
        raise NotImplementedError()

    async def notify_partner_found(self, partner):
        """
        Raises:
            UserError If user we're changing has blocked the bot.

        """
        raise NotImplementedError()

    async def notify_talk_was_finished(self, by_self):
        """
        Args:
            by_self (bool)

        Raises:
            UserError If human we're notifying has blocked the bot.

        """
        raise NotImplementedError()

    async def send(self, message):
        """
        Args:
            message (str)

        Raises:
            UserError if can't send message because of unknown content type.
            TelegramError if user has blocked the bot.

        """
        raise NotImplementedError()

    @property
    def user_dict(self):
        """Obtains dict of `Telegram's "User" type <https://core.telegram.org/bots/api#user>`_.

        """
        return {
            'bot_id': self.id,
            'first_name': 'Anonymous',
            }
