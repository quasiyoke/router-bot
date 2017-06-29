# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
from .client_bot import ClientBot
from .error import UserError, UserServiceError
from .user import MissingPartnerError
from .human_handler import HumanHandler
from .user_service import UserService
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.admin_handler')


class AdminHandler(HumanHandler):
    async def _handle_command_clear(self, message):
        someone_was_cleared = False
        for telegram_id in re.split(r'\s+', message.command_args):
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                await self._sender.send_notification('Is it really telegram_id: \"{0}\"?', telegram_id)
                continue
            try:
                user = UserService.get_instance().get_user(telegram_id)
            except UserServiceError as e:
                await self._sender.send_notification('User {0} wasn\'t found: {1}', telegram_id, e)
                continue
            await user.end_talk()
            await self._sender.send_notification('User {0} was cleared', telegram_id)
            LOGGER.debug('Clear: %d -> %d', self._user.id, telegram_id)
            someone_was_cleared = True
        if not someone_was_cleared:
            await self._sender.send_notification('Use it this way: `/clear 31416 27183`')

    async def _handle_command_add_bot(self, message):
        try:
            token, first_name = re.split(r'\s+', message.command_args)
        except (ValueError, TypeError):
            await self._sender.send_notification('Use it this way: /add_bot token first_name')
        try:
            ClientBot.create(token, first_name, self.update_service)
        except Exception as err:
            await self._sender.send_notification('The bot wasn\'t created. {0}', err)

        for telegram_id in re.split(r'\s+', message.command_args):
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                await self._sender.send_notification('Is it really telegram_id: \"{0}\"?', telegram_id)
                continue
            try:
                user = UserService.get_instance().get_user(telegram_id)
            except UserServiceError as e:
                await self._sender.send_notification('User {0} wasn\'t found: {1}', telegram_id, e)
                continue
            await user.end_talk()
            await self._sender.send_notification('User {0} was cleared', telegram_id)
            LOGGER.debug('Clear: %d -> %d', self._user.id, telegram_id)
            someone_was_cleared = True
        if not someone_was_cleared:
            await self._sender.send_notification('Use it this way: `/clear 31416 27183`')
