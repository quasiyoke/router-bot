# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from telegram_bot_server import Response
from telegram_bot_server import Server as BaseServer

LOGGER = logging.getLogger('router_bot.server')


class Server(BaseServer):
    async def _handle_send_message(self, request):
        """
        Raises:
            aiohttp.web.HTTPException

        """
        LOGGER.info('"sendMessage" method. Bot ID %s. Text: "%s".', request.bot.id, request.data['text'])
        for bot in await self._bot_service.get_all_bots():
            if bot == request.bot:
                continue
            await bot.send_message(
                chat=request.bot.chat_dict,
                from_dict=request.bot.user_dict,
                text=request.data['text'],
                )
        return Response()
