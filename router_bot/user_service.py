# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .error import PartnerObtainingError, UserError, UserServiceError
from .user import User

LOGGER = logging.getLogger('router_bot.user_service')


class UserService:
    def __init__(self):
        # We need to lock users for matching to prevent attempts to create
        # second conversation with single partner.
        self._locked_users_ids = set()
        self._users_cache = {}
        type(self)._instance = self

    @classmethod
    def get_instance(cls):
        try:
            return cls._instance
        except AttributeError:
            cls._instance = cls()
            return cls._instance

    @property
    def admins_telegram_ids(self):
        return [user.id for user in User.select()]

    def get_cached_user(self, user):
        try:
            return self._users_cache[user.id]
        except KeyError:
            self._users_cache[user.id] = user
            return user

    def get_cache_size(self):
        return len(self._users_cache)

    def get_full_users(self):
        return User.select()

    def _match_partner(self, user):
        """Tries to find a partner for obtained user or raises PartnerObtainingError.

        Raises:
            PartnerObtainingError if there's no proper partner.

        Returns:
            User

        """
        from .talk import Talk

        possible_partners = User.select().where(
            User.id != user.id,
            User.looking_for_partner_from != None,
            )
        possible_partners = possible_partners.order_by(
            User.looking_for_partner_from,
            )

        partner = None
        for possible_partner in possible_partners:
            if possible_partner.id not in self._locked_users_ids:
                partner = possible_partner
                break
        if partner is None:
            raise PartnerObtainingError()
        self._locked_users_ids.add(partner.id)
        return self.get_cached_user(partner)

    async def match_partner(self, user):
        """Finds partner for the user. Does handling of users who have blocked the bot.

        Raises:
            PartnerObtainingError if there's no proper partners.
            UserServiceError if the user has blocked the bot.

        """
        while True:
            partner = self._match_partner(user)
            try:
                await partner.notify_partner_found(user)
            except UserError as err:
                # Potential partner has blocked the bot. Let's look for next
                # potential partner.
                LOGGER.info('Bad potential partner for %d. %s', user.id, err)
                await partner.end_talk()
                self._locked_users_ids.discard(partner.id)
                continue
            break
        try:
            await user.notify_partner_found(partner)
        except UserError as err:
            self._locked_users_ids.discard(partner.id)
            # User has blocked the bot.
            raise UserServiceError(f'Can\'t notify seeking for partner user: {err}')
        await user.set_partner(partner)
        self._locked_users_ids.discard(partner.id)
        LOGGER.debug('Found partner: %d -> %d.', user.id, partner.id)
