# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging
import re
import sys
import telepot
import telepot.aio
from .error import MissingPartnerError, PartnerObtainingError, \
    StrangerError, StrangerHandlerError, StrangerServiceError, \
    UnknownCommandError, UnsupportedContentError
from .message import Message
from .stranger_sender import StrangerSender
from .stranger_sender_service import StrangerSenderService
from .stranger_service import StrangerService
from .util import __version__
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.stranger_handler')


class StrangerHandler(telepot.aio.helper.UserHandler):
    HOUR_TIMEDELTA = datetime.timedelta(hours=1)
    LONG_WAITING_TIMEDELTA = datetime.timedelta(minutes=10)

    def __init__(self, seed_tuple, *args, **kwargs):
        super(StrangerHandler, self).__init__(seed_tuple, *args, **kwargs)
        bot, initial_msg, seed = seed_tuple
        self._from_id = initial_msg['from']['id']
        try:
            self._stranger = StrangerService.get_instance(). \
                get_or_create_stranger(self._from_id)
        except StrangerServiceError as err:
            LOGGER.error('Problems with StrangerHandler construction: %s', err)
            sys.exit('Problems with StrangerHandler construction: {err}')
        self._sender = StrangerSenderService.get_instance(bot). \
            get_or_create_stranger_sender(self._stranger)

    async def handle_command(self, message):
        handler_name = '_handle_command_' + message.command
        try:
            handler = getattr(self, handler_name)
        except AttributeError as err:
            raise UnknownCommandError(message.command) from err
        await handler(message)

    async def _handle_command_begin(self, message):
        try:
            await StrangerService.get_instance().match_partner(self._stranger)
        except PartnerObtainingError:
            LOGGER.debug('Looking for partner: %d', self._stranger.id)
            await self._stranger.set_looking_for_partner()
        except StrangerServiceError as err:
            LOGGER.warning('Can\'t set partner for %d. %s', self._stranger.id, err)

    async def _handle_command_end(self, message):
        partner = self._stranger.get_partner()
        LOGGER.debug(
            '/end: %d -x-> %s',
            self._stranger.id,
            'none' if partner is None else partner.id,
            )
        await self._stranger.end_talk()

    async def _handle_command_help(self, message):
        try:
            await self._sender.send_notification(
                '*Help*\n\n'
                'Use /begin to start looking for a conversational partner, once '
                'you\'re matched you can use /end to finish the conversation.\n\n'
                'If you have any suggestions or require help, visit [Conversational Intelligence Challenge website]'
                '(http://convai.io). When asking questions, please provide this number: {0}.\n\n'
                'You\'re welcome to inspect and improve [router-bot v. {1} source code]'
                '(https://github.com/quasiyoke/router-bot).',
                self._from_id,
                __version__,
                disable_web_page_preview=True,
                )
        except TelegramError as err:
            LOGGER.warning('Handle /help command. Can\'t notify stranger. %s', err)

    async def _handle_command_start(self, message):
        LOGGER.debug('/start: %d', self._stranger.id)
        try:
            await self._sender.send_notification(
                '*Manual*\n\nHi, I’m Conversational Intelligence Challenge master-bot. Use /begin to start looking '
                'for a conversational partner, once you\'re matched you can use /end to end the conversation.'
                )
        except TelegramError as err:
            LOGGER.warning('Handle /start command. Can\'t notify stranger. %s', err)

    async def on_close(self, error):
        pass

    async def on_chat_message(self, message_dict):
        content_type, chat_type, chat_id = telepot.glance(message_dict)

        if chat_type != 'private':
            return

        print(message_dict)

        try:
            message = Message(message_dict)
        except UnsupportedContentError:
            await self._sender.send_notification('Messages of this type aren\'t supported.')
            return

        if message.command:
            try:
                await self.handle_command(message)
            except UnknownCommandError:
                await self._sender.send_notification('Unknown command. Look /help for the full list of commands.')
        else:
            try:
                await self._stranger.send_to_partner(message)
            except MissingPartnerError:
                pass
            except StrangerError:
                await self._sender.send_notification('Messages of this type aren\'t supported.')
            except TelegramError:
                LOGGER.warning(
                    'Send message. Can\'t send to partner: %d -> %d',
                    self._stranger.id,
                    self._stranger.get_partner().id,
                    )
                await self._sender.send_notification(
                    'Your partner has blocked me! How did you do that?!',
                    )
                await self._stranger.end_talk()

    async def on_edited_chat_message(self, message_dict):
        LOGGER.info('User tried to edit their message.')
        await self._sender.send_notification(
            'Messages editing isn\'t supported',
            )

    async def on_inline_query(self, query):
        pass
