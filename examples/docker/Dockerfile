FROM python:3.11

WORKDIR /usr/src/app
RUN pip install kraken-rebalance-bot==0.5.7.2

COPY main.py .

CMD [ "python", "./main.py" ]

