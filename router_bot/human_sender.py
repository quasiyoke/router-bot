# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
import telepot
from .error import HumanSenderError

LOGGER = logging.getLogger('router_bot.human_sender')


class HumanSender(telepot.helper.Sender):
    MESSAGE_TYPE_TO_METHOD_NAME = {
        'text': 'sendMessage',
        }
    MARKDOWN_RE = re.compile(r'([\[\*_`])')

    def __init__(self, bot, user):
        super(HumanSender, self).__init__(bot, user.telegram_id)
        self._bot = bot
        self._user = user

    @classmethod
    def _escape_markdown(cls, s):
        """
        Escapes string to prevent injecting Markdown into notifications.
        @see https://core.telegram.org/bots/api#using-markdown
        """
        if s is not str:
            s = str(s)
        s = cls.MARKDOWN_RE.sub(r'\\\1', s)
        return s

    async def send(self, message):
        """
        @raises HumanSenderError if message's content type is not supported.
        @raises TelegramError if user has blocked the bot.
        """
        if message.is_reply:
            raise HumanSenderError('Reply can\'t be sent.')
        try:
            method_name = HumanSender.MESSAGE_TYPE_TO_METHOD_NAME[message.type]
        except KeyError:
            raise HumanSenderError(f'Unsupported content_type: {message.type}')
        else:
            await getattr(self, method_name)(**message.sending_kwargs)

    async def send_notification(self, message, *args, disable_notification=None, disable_web_page_preview=None,
                                reply_markup=None):
        """
        @raise TelegramError if user has blocked the bot.
        """
        args = [HumanSender._escape_markdown(arg) for arg in args]
        message = message.format(*args)
        if reply_markup and 'keyboard' in reply_markup:
            reply_markup = {
                'keyboard': [
                    list(row.keys())
                    for row in reply_markup['keyboard']
                    ],
                'one_time_keyboard': True,
                }
        await self.sendMessage(
            f'*ConvAI:* {message}',
            disable_notification=disable_notification,
            disable_web_page_preview=disable_web_page_preview,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            )
