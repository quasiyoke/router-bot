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
        await request.bot.handle_message(request.data['text'])
        return Response()
