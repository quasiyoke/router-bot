# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .error import PartnerObtainingError, StrangerError, StrangerServiceError
from .stranger import Stranger
from peewee import DatabaseError, DoesNotExist

LOGGER = logging.getLogger('router_bot.stranger_service')


class StrangerService:
    def __init__(self):
        # We need to lock strangers for matching to prevent attempts to create
        # second conversation with single partner.
        self._locked_strangers_ids = set()
        self._strangers_cache = {}
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
        return [stranger.id for stranger in Stranger.select()]

    def get_cached_stranger(self, stranger):
        try:
            return self._strangers_cache[stranger.id]
        except KeyError:
            self._strangers_cache[stranger.id] = stranger
            return stranger

    def get_cache_size(self):
        return len(self._strangers_cache)

    def get_full_strangers(self):
        return Stranger.select()

    def get_or_create_stranger(self, telegram_id):
        try:
            try:
                stranger = Stranger.get(Stranger.telegram_id == telegram_id)
            except DoesNotExist:
                stranger = Stranger.create(
                    telegram_id=telegram_id,
                    )
        except DatabaseError as err:
            raise StrangerServiceError(f'Database problems during `get_or_create_stranger`: {err}')
        return self.get_cached_stranger(stranger)

    def get_stranger(self, telegram_id):
        try:
            stranger = Stranger.get(Stranger.telegram_id == telegram_id)
        except (DatabaseError, DoesNotExist) as err:
            raise StrangerServiceError(f'Database problems during `get_stranger`: {err}')
        return self.get_cached_stranger(stranger)

    def _match_partner(self, stranger):
        """Tries to find a partner for obtained stranger or raises PartnerObtainingError.

        Raises:
            PartnerObtainingError if there's no proper partner.

        Returns:
            Stranger

        """
        from .talk import Talk

        possible_partners = Stranger.select().where(
            Stranger.id != stranger.id,
            Stranger.looking_for_partner_from != None,
            )
        possible_partners = possible_partners.order_by(
            Stranger.looking_for_partner_from,
            )

        partner = None
        for possible_partner in possible_partners:
            if possible_partner.id not in self._locked_strangers_ids:
                partner = possible_partner
                break
        if partner is None:
            raise PartnerObtainingError()
        self._locked_strangers_ids.add(partner.id)
        return self.get_cached_stranger(partner)

    async def match_partner(self, stranger):
        """Finds partner for the stranger. Does handling of strangers who have blocked the bot.

        Raises:
            PartnerObtainingError if there's no proper partners.
            StrangerServiceError if the stranger has blocked the bot.

        """
        while True:
            partner = self._match_partner(stranger)
            try:
                await partner.notify_partner_found(stranger)
            except StrangerError as err:
                # Potential partner has blocked the bot. Let's look for next
                # potential partner.
                LOGGER.info('Bad potential partner for %d. %s', stranger.id, err)
                await partner.end_talk()
                self._locked_strangers_ids.discard(partner.id)
                continue
            break
        try:
            await stranger.notify_partner_found(partner)
        except StrangerError as err:
            self._locked_strangers_ids.discard(partner.id)
            # Stranger has blocked the bot.
            raise StrangerServiceError(f'Can\'t notify seeking for partner stranger: {err}')
        await stranger.set_partner(partner)
        self._locked_strangers_ids.discard(partner.id)
        LOGGER.debug('Found partner: %d -> %d.', stranger.id, partner.id)
