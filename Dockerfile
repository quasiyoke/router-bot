FROM python:3.6
MAINTAINER Pyotr Ermishkin <quasiyoke@gmail.com>

COPY router_bot /router_bot/
COPY docker-entrypoint.sh /
COPY router_bot_runner.py /
COPY README.rst /
COPY setup.py /

VOLUME /configuration

RUN python /setup.py install

CMD ["/docker-entrypoint.sh"]
