# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
from .error import StrangerError, StrangerServiceError
from .stranger import MissingPartnerError
from .stranger_handler import StrangerHandler
from .stranger_service import StrangerService
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.admin_handler')


class AdminHandler(StrangerHandler):
    async def _handle_command_clear(self, message):
        someone_was_cleared = False
        for telegram_id in re.split(r'\s+', message.command_args):
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                await self._sender.send_notification('Is it really telegram_id: \"{0}\"?', telegram_id)
                continue
            try:
                stranger = StrangerService.get_instance().get_stranger(telegram_id)
            except StrangerServiceError as e:
                await self._sender.send_notification('Stranger {0} wasn\'t found: {1}', telegram_id, e)
                continue
            await stranger.end_talk()
            await self._sender.send_notification('Stranger {0} was cleared', telegram_id)
            LOGGER.debug('Clear: %d -> %d', self._stranger.id, telegram_id)
            someone_was_cleared = True
        if not someone_was_cleared:
            await self._sender.send_notification('Use it this way: `/clear 31416 27183`')
