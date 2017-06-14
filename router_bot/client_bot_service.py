# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .client_bot import ClientBot
from .error import HumanSenderServiceError
from .human_sender import HumanSender
from telegram_bot_server import BotService, BotServiceError

LOGGER = logging.getLogger('router_bot.client_bot_service')


class ClientBotService(BotService):
    def __init__(self, *args, **kwargs):
        """
        Args:
            update_service (telegram_bot_server.UpdateService)

        Raises:
            BotServiceError if provided list is wrong.

        """
        super(ClientBotService, self).__init__(bot_cls=ClientBot, *args, **kwargs)

    async def get_all_bots(self):
        return ClientBot.select()

    async def get_bot(self, bot_id):
        """
        Args:
            bot_id (int): Bot's ID.

        Returns:
            Bot instance or `None`.

        """
        return ClientBot.get(bot_id)
