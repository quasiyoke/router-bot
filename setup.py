# router-bot
# Copyright (C) 2017 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License v3
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from router_bot.util import __version__
from setuptools import setup

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='router-bot',
    version=__version__,
    description='The bot for conversational artificial intelligence competition.',
    long_description=long_description,
    keywords=['telegram', 'bot', 'chat'],
    license='AGPLv3+',
    author='Pyotr Ermishkin',
    author_email='quasiyoke@gmail.com',
    url='https://github.com/quasiyoke/router-bot',
    packages=['router_bot'],
    entry_points={
        'console_scripts': ['router_bot = router_bot.router_bot:main'],
        },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Telepot',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: Chat',
        ],
    install_requires=[
        'docopt>=0.6.2,<0.7',
        'peewee>=2.7.4,<3.0',
        'pymysql>=0.7.11,<0.8',
        'telegram-bot-server>=0.1.0,<0.2',
        'telepot>=12.0,<13.0',
        ],
    dependency_links=[
        'https://github.com/quasiyoke/telegram-bot-server/tarball/master#egg=telegram-bot-server-0.1.0',
        ],
    )
