# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging
from .error import StrangerSenderServiceError
from .stats import Stats
from peewee import DoesNotExist

COUNT_INTERVALS = (4, 16, 64, 256)
LOGGER = logging.getLogger('router_bot.stats_service')


def get_talks_stats(talks, get_value, intervals):
    distribution = {interval: 0 for interval in intervals}
    distribution['more'] = 0
    average = 0
    count = 0
    for talk in talks:
        value = get_value(talk)
        increment_distribution(distribution, value, intervals)
        average += value
        count += 1
    try:
        average /= count
    except ZeroDivisionError:
        pass
    return {
        'distribution': distribution,
        'average': average,
        'count': count,
        }


def increment(d, key):
    try:
        d[key] += 1
    except KeyError:
        d[key] = 1


def increment_distribution(d, value, intervals):
    for interval in intervals:
        if value <= interval:
            break
    else:
        interval = 'more'
    d[interval] += 1


class StatsService:
    INTERVAL = datetime.timedelta(hours=1)

    def __init__(self):
        try:
            self._stats = Stats.select().order_by(Stats.created.desc()).get()
        except DoesNotExist:
            self._stats = None
            self._update_stats()

    @classmethod
    def get_instance(cls):
        try:
            instance = cls._instance
        except AttributeError:
            instance = StatsService()
            cls._instance = instance
        return instance

    def get_stats(self):
        return self._stats

    async def run(self):
        while True:
            next_stats_time = self._stats.created + type(self).INTERVAL
            now = datetime.datetime.utcnow()
            if next_stats_time > now:
                await asyncio.sleep((next_stats_time - now).total_seconds())
            self._update_stats()

    def _update_stats(self):
        from .stranger_service import StrangerService
        from .stranger_sender_service import StrangerSenderService
        from .talk import Talk
        stats = Stats()
        stranger_service = StrangerService.get_instance()

        talks_waiting = get_talks_stats(
            Talk.get_not_ended_talks(after=None if self._stats is None else self._stats.created),
            lambda talk: (talk.begin - talk.searched_since).total_seconds(),
            (10, 60, 60 * 5, 60 * 30, 60 * 60 * 3, ),
            )

        ended_talks = Talk.get_ended_talks(after=None if self._stats is None else self._stats.created)
        talks_duration = get_talks_stats(
            ended_talks,
            lambda talk: (talk.end - talk.begin).total_seconds(),
            (10, 60, 60 * 5, 60 * 30, ),
            )
        talks_sent = get_talks_stats(
            ended_talks,
            lambda talk: talk.partner1_sent + talk.partner2_sent,
            COUNT_INTERVALS,
            )

        stats_dict = {
            'talks_duration': talks_duration,
            'talks_sent': talks_sent,
            'talks_waiting': talks_waiting,
            }
        stats.set_data(stats_dict)
        stats.save()
        self._stats = stats
        LOGGER.info('Stats were updated')
