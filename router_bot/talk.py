# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
from .error import WrongUserError
from .user import User
from .user_service import UserService
from peewee import *

LOGGER = logging.getLogger('router_bot.talk')
database_proxy = Proxy()


class Talk(Model):
    partner1 = ForeignKeyField(User, related_name='talks_as_partner1')
    partner1_sent = IntegerField(default=0)
    partner2 = ForeignKeyField(User, related_name='talks_as_partner2')
    partner2_sent = IntegerField(default=0)
    searched_since = DateTimeField()
    begin = DateTimeField(default=datetime.datetime.utcnow)
    end = DateTimeField(index=True, null=True)

    class Meta:
        database = database_proxy

    @classmethod
    def get_ended_talks(cls, after=None):
        talks = cls.select()
        if after is None:
            talks = talks.where(Talk.end != None)
        else:
            talks = talks.where(Talk.end >= after)
        return talks

    @classmethod
    def get_not_ended_talks(cls, after=None):
        talks = cls.select().where(Talk.end == None)
        if after is not None:
            talks = talks.where(Talk.begin >= after)
        return talks

    @classmethod
    def get_talk(cls, user):
        try:
            talk = cls.get(((cls.partner1 == user) | (cls.partner2 == user)) & (cls.end == None))
        except DoesNotExist:
            return None
        else:
            user_service = UserService.get_instance()
            talk.partner1 = user_service.get_cached_user(talk.partner1)
            talk.partner2 = user_service.get_cached_user(talk.partner2)
            return talk

    def get_partner(self, user):
        """
        @raise WrongUserError
        """
        return User.get(id=self.get_partner_id(user))

    def get_partner_id(self, user):
        if user.id == self.partner1_id:
            return self.partner2_id
        elif user.id == self.partner2_id:
            return self.partner1_id
        else:
            raise WrongUserError()

    def get_sent(self, user):
        if user == self.partner1:
            return self.partner1_sent
        elif user == self.partner2:
            return self.partner2_sent
        else:
            raise WrongUserError()

    def increment_sent(self, user):
        if user == self.partner1:
            self.partner1_sent += 1
        elif user == self.partner2:
            self.partner2_sent += 1
        else:
            raise WrongUserError()
        self.save()

    def is_successful(self):
        return self.partner1_sent and self.partner2_sent
