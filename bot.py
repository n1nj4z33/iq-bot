#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import yaml
import datetime
import logging
import websocket
import time

from classes import CandleType, Candle, Direction, Active

logger = logging.getLogger()
FORMAT = "%(asctime)s:%(levelname)s:\t [%(filename)s:%(lineno)s - \t%(funcName)s()\t] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

skey = None

buyTime = 0
buyPrice = 0
buyed = False
exp_time_seconds = 0
last_candle = Candle([0, 0, 0, 0, 0])
lot = 10


def buy_active(_ws, direction, buy_time, exp_time_in_seconds):
    global lot
    logging.info("Посылаем запрос {} ... Lot: {}".format(direction, lot))
    _ws.send(json.dumps({"name": "buy",
                         "msg": {
                             "price": lot,
                             "exp": exp_time_in_seconds,
                             "act": 1,
                             "type": "turbo",
                             "time": buy_time,
                             "direction": direction
                         }}))


def ws_get_candles(_ws, active, duration, chunk_size, fromtime, till):
    _ws.send(json.dumps({"name": "candles", "msg": {
        "active_id": active,
        "duration": duration,
        "chunk_size": chunk_size,
        "from": fromtime,
        "till": till
    }}))


def parse_candle(candle):
    return Candle(candle)


def get_candles(candles):
    global last_candle
    global buyTime
    global buyed
    global exp_time_seconds

    parsed_candles = []
    candle_types = []
    for candle in candles:
        parsed_candle = parse_candle(candle)
        logging.debug("{}:{}:{}:{}:{}:{}".format(parsed_candle.timestamp,
                                                 parsed_candle.open,
                                                 parsed_candle.high,
                                                 parsed_candle.low,
                                                 parsed_candle.close,
                                                 parsed_candle.get_type()))
        candle_types.append(parsed_candle.get_type())
        parsed_candles.append(parsed_candle)
    last_candle = parsed_candles[0]

    logging.info("Last_candle: {}".format(last_candle))

    if not buyed:

        if last_candle.get_type() == CandleType.green:
            logging.info("Open call direction: buyTime: {}\t Exp_time:{}".format(buyTime, exp_time_seconds))
            buy_active(ws, Direction.call, buyTime, exp_time_seconds)
        elif last_candle.get_type() == CandleType.red:
            logging.info("Open put direction: buyTime: {}\t Exp_time:{}".format(buyTime, exp_time_seconds))
            buy_active(ws, Direction.put, buyTime, exp_time_seconds)
        else:
            logging.debug("Wrong Candle type")

    logging.info("Got: {} candles".format(len(parsed_candles)))
    logging.info("Types: {}".format(candle_types))


def on_message(_ws, message):
    global skey
    global buyPrice
    global buyTime
    global buyed
    global exp_time_seconds
    global lot
    global last_candle
    raw = json.loads(message)
    # logging.debug(message)
    if 'timeSync' in raw['name']:
        servertime = int(raw['msg'])

        # Get EXP time from server time + 1 minute
        server_time = datetime.datetime.fromtimestamp(servertime / 1000)
        exp_time = server_time + datetime.timedelta(minutes=1)

        if server_time.second > 30:
            exp_time = server_time + datetime.timedelta(minutes=2)

        exp_time = exp_time.replace(second=0, microsecond=0)
        exp_time_seconds = int(time.mktime(exp_time.timetuple()))

        buyTime = int(servertime / 1000)

        if server_time.second == 5:
            logging.info('01 sec')
            # Запрашиваем последнюю закрытую свечу
            ws_get_candles(_ws, Active.EURUSD, 60, 214, buyTime - 65, buyTime)

    elif 'profile' in raw['name']:
        if 'skey' in raw['msg']:
            skey = raw['msg']['skey']
            logging.debug("Skey: {}".format(skey))

    elif 'newChartData' in raw['name']:

        buyPrice = raw['msg']['value']

    elif 'buyComplete' in raw['name']:

        success = raw['msg']['isSuccessful']
        if success:
            logging.info("Куплено ...")
            buyed = True

        else:
            logging.info(u"Не смог купить актив: {}".format(raw['msg']['message'][0]))

    elif 'listInfoData' in raw['name']:
        profit = raw['msg'][0]['profit']
        buyed = False
        if profit > 0:
            logging.info("Выиграли.")
            lot = 10
        else:
            logging.info("Проиграли увеличиваем ставку")
            lot *= 2.5

    elif 'tradersPulse' in raw['name']:
        pass

    elif 'candles' in raw['name']:
        logging.debug(message)

        get_candles(raw['msg']['data'])

    else:
        logging.debug(message)


def on_error(_ws, error):
    logging.error(error, _ws)


def on_close(_ws):
    logging.info("### {} closed ###".format(_ws))


def on_open(_ws):
    _ws.send(json.dumps({"name": "ssid", "msg": ssid}))
    _ws.send(json.dumps({"name": "subscribe", "msg": "deposited"}))
    _ws.send(json.dumps({"name": "subscribe", "msg": "tradersPulse"}))
    _ws.send(json.dumps({"name": "subscribe", "msg": "activeScheduleChange"}))

    # EURUSD-OTC
    # ws.send(json.dumps({"name":"setActives","msg":{"actives":[76]}}))
    # EURUSD
    _ws.send(json.dumps({"name": "setActives", "msg": {"actives": [1]}}))

    _ws.send(json.dumps({"name": "subscribe", "msg": "activeCommissionChange"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "iqguard"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "signal"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "timeSync"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "feedRecentBets"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "feedRecentBets2"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "feedTopTraders2"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "feedRecentBetsMulti"}))
    _ws.send(json.dumps({"name": "unSubscribe", "msg": "tournament"}))


if __name__ == "__main__":
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)

    ssid = config['ssid']

    ws = websocket.WebSocketApp("wss://eu.iqoption.com/echo/websocket",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.on_open = on_open
    ws.run_forever()
