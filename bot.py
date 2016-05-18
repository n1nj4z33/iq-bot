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
logger.setLevel(logging.INFO)

skey = None

buyTime = 0
buyPrice = 0
buyed = False
exp_time_seconds = 0
last_candle = Candle([0, 0, 0, 0, 0])
current_candle = Candle([0, 0, 0, 0, 0])

martin_leverage = 0


def buy_active(_ws, direction, buy_time, exp_time_in_seconds):
    global lot
    global current_active
    logging.info("Посылаем запрос {} ... Lot: {}".format(direction, lot))
    _ws.send(json.dumps({"name": "buy",
                         "msg": {
                             "price": lot,
                             "exp": exp_time_in_seconds,
                             "act": current_active,
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
    global current_candle
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
    current_candle = parsed_candles[len(parsed_candles)-1]

    logging.debug("Last_candle: {}".format(last_candle))
    logging.debug("Current Candle: {}".format(current_candle))
    if not buyed:

        if last_candle.get_type() == CandleType.green:
            logging.info("Open call direction: buyTime: {}\t Exp_time:{}".format(datetime.datetime.fromtimestamp(buyTime), datetime.datetime.fromtimestamp(exp_time_seconds)))
            buy_active(ws, Direction.call, buyTime, exp_time_seconds)
        elif last_candle.get_type() == CandleType.red:
            logging.info("Open put direction: buyTime: {}\t Exp_time:{}".format(datetime.datetime.fromtimestamp(buyTime), datetime.datetime.fromtimestamp(exp_time_seconds)))
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
    global base_lot
    global last_candle
    global current_candle
    global current_active
    global martin_leverage
    raw = json.loads(message)
    # logging.debug(message)
    if 'timeSync' in raw['name']:
        servertime = int(raw['msg'])

        # Get EXP time from server time + 1 minute
        server_time = datetime.datetime.fromtimestamp(servertime / 1000)
        exp_time = server_time + datetime.timedelta(minutes=1)

        # if server_time.second > 30:
        #     exp_time = server_time + datetime.timedelta(minutes=2)

        exp_time = exp_time.replace(second=0, microsecond=0)
        exp_time_seconds = int(time.mktime(exp_time.timetuple()))

        buyTime = int(servertime / 1000)

        if server_time.second == 1:
            # logging.info('50 sec')
            # Запрашиваем последнюю закрытую свечу
            ws_get_candles(_ws, current_active, 60, 214, buyTime - 61, buyTime)

    elif 'profile' in raw['name']:
        if 'skey' in raw['msg']:
            skey = raw['msg']['skey']
            logging.debug("Skey: {}".format(skey))

    elif 'newChartData' in raw['name']:

        buyPrice = raw['msg']['value']
        current_candle.close = buyPrice
        logging.debug("Current Candle: {}".format(current_candle))

    elif 'buyComplete' in raw['name']:

        success = raw['msg']['isSuccessful']
        if success:
            logging.info("Куплено ...")
            logging.info("Лот: {}".format(lot))
            buyed = True

        else:
            logging.info(u"Не смог купить актив: {}".format(raw['msg']['message'][0]))

    elif 'listInfoData' in raw['name']:
        profit = raw['msg'][0]['profit']
        profit_amount = raw['msg'][0]['profit_amount']
        win_amount = raw['msg'][0]['win_amount']
        buyed = False
        logging.debug("Raw message: {}".format(raw['msg']))
        logging.info("Profit: {} Lot: {} Profit_amount {} Win_amount: {}".format(profit,lot,profit_amount,win_amount))

        if profit_amount == lot:
            logging.info("Ничья пробуем еще раз")
            lot = profit
            logging.info("Лот: {}".format(lot))

        elif profit_amount > 0:
            logging.info("Выиграли.")
            lot = base_lot
            martin_leverage = 0

        else:
            logging.info("Проиграли увеличиваем ставку")
            lot *= 2.5

            if martin_leverage < 5:
                martin_leverage += 1
            else:
                lot = base_lot
                martin_leverage = 0

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
    global current_active
    _ws.send(json.dumps({"name": "ssid", "msg": ssid}))
    _ws.send(json.dumps({"name": "subscribe", "msg": "deposited"}))
    _ws.send(json.dumps({"name": "subscribe", "msg": "tradersPulse"}))
    _ws.send(json.dumps({"name": "subscribe", "msg": "activeScheduleChange"}))

    _ws.send(json.dumps({"name": "setActives", "msg": {"actives": [current_active]}}))

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
    current_active = config['active']

    lot = config['lot']
    base_lot = lot
    logging.info("Запуск с параметрами: \tSSID: {}\tActive: {}\tLot:{}".format(ssid,current_active,lot))

    ws = websocket.WebSocketApp("wss://eu.iqoption.com/echo/websocket",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.on_open = on_open
    ws.run_forever()
