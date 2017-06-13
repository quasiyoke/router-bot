# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class ConfigurationObtainingError(Exception):
    pass


class DBError(Exception):
    pass


class MissingCommandError(Exception):
    pass


class MissingPartnerError(Exception):
    pass


class PartnerObtainingError(Exception):
    pass


class StrangerError(Exception):
    pass


class StrangerHandlerError(Exception):
    pass


class StrangerSenderError(Exception):
    pass


class StrangerSenderServiceError(Exception):
    pass


class StrangerServiceError(Exception):
    pass


class UnknownCommandError(Exception):
    def __init__(self, command):
        super(UnknownCommandError, self).__init__()
        self.command = command


class UnsupportedContentError(Exception):
    pass


class WrongStrangerError(Exception):
    pass
