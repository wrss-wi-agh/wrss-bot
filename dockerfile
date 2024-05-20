FROM python:3.11

LABEL Maintainer="wrss.wiet"

WORKDIR /app

COPY wrss-bot.py /app
COPY config.py /app

RUN python3 -m pip install -U discord.py

CMD [ "python", "./wrss-bot.py"]