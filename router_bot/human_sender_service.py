# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from .error import HumanSenderServiceError
from .human_sender import HumanSender

LOGGER = logging.getLogger('router_bot.human_sender_service')


class HumanSenderService:
    _instance = None

    def __init__(self, bot):
        self._bot = bot
        self._human_senders = {}

    @classmethod
    def get_instance(cls, bot=None):
        if cls._instance is None:
            if bot is None:
                raise HumanSenderServiceError(
                    'Instance wasn\'t initialized. Provide arguments to '
                    'construct one.',
                    )
            else:
                cls._instance = cls(bot)
        return cls._instance

    def get_cache_size(self):
        return len(self._human_senders)

    def get_or_create_human_sender(self, human):
        try:
            human_sender = self._human_senders[human.telegram_id]
        except KeyError:
            human_sender = HumanSender(self._bot, human)
            self._human_senders[human.telegram_id] = human_sender
        return human_sender
