# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import re
import sys
import telepot
from .error import MissingPartnerError, UserError
from .human_sender_service import HumanSenderService
from .wizard import Wizard
from telepot.exception import TelegramError

LOGGER = logging.getLogger('router_bot.human_setup_wizard')


class HumanSetupWizard(Wizard):
    """Wizard which guides human through process of customizing her parameters. Activates automatically for novices.

    """

    def __init__(self, user):
        super(HumanSetupWizard, self).__init__()
        self._user = user
        self._sender = HumanSenderService.get_instance().get_or_create_human_sender(user)

    async def activate(self):
        self._user.wizard = 'setup'
        self._user.wizard_step = 'languages'
        self._user.save()
        await self._prompt()

    async def deactivate(self):
        self._user.wizard = 'none'
        self._user.wizard_step = None
        self._user.save()
        try:
            await self._sender.send_notification(
                'Thank you. Use /begin to start looking for a conversational partner, '
                'once you\'re matched you can use /end to end the conversation.',
                reply_markup={'hide_keyboard': True},
                )
        except TelegramError as e:
            LOGGER.warning('Deactivate. Can\'t notify user. %s', e)

    async def handle(self, message):
        """
        @returns `True` if message was interpreted in this method. `False` if message still needs
            interpretation.
        """
        if self._user.wizard == 'none':  # Wizard isn't active. Check if we should activate it.
            if self._user.is_novice():
                await self.activate()
                return True
            else:
                return False
        elif self._user.wizard != 'setup':
            return False
        try:
            if self._user.wizard_step == 'languages':
                pass
            elif self._user.wizard_step == 'sex':
                pass
            elif self._user.wizard_step == 'partner_sex':
                pass
            else:
                LOGGER.warning(
                    'Undknown wizard_step value was found: \"%s\"',
                    self._user.wizard_step,
                )
        except TelegramError as e:
            LOGGER.warning('handle() Can not notify user. %s', e)
        return True

    async def handle_command(self, message):
        """
        @returns `True` if command was interpreted in this method. `False` if command still needs
            interpretation.
        """
        if self._user.wizard == 'none':
            # Wizard isn't active. Check if we should activate it.
            return (await self.handle(message)) and message.command != 'start'
        elif self._user.is_full():
            if self._user.wizard == 'setup':
                await self.deactivate()
            return False
        else:
            try:
                await self._sender.send_notification(
                    'Finish setup process please. After that you can start using bot.',
                    )
            except TelegramError as e:
                LOGGER.warning('Handle command. Cant notify user. %s', e)
            await self._prompt()
            return True

    async def _prompt(self):
        wizard_step = self._user.wizard_step
        try:
            if wizard_step == 'languages':
                pass
            elif wizard_step == 'sex':
                await self._sender.send_notification(
                    'Set up your sex. If you pick \"Not Specified\" you can\'t choose '
                    'your partner\'s sex.',
                    reply_markup=SEX_KEYBOARD,
                    )
            elif wizard_step == 'partner_sex':
                await self._sender.send_notification(
                    'Choose your partner\'s sex',
                    reply_markup=SEX_KEYBOARD,
                    )
        except TelegramError as e:
            LOGGER.warning('_prompt() Can not notify user. %s', e)
