#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import yaml
import datetime
import logging

logger = logging.getLogger()
FORMAT = "%(asctime)s:%(levelname)s:\t [%(filename)s:%(lineno)s - \t%(funcName)s()\t\t] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

import websocket
import time

from classes import CandleType,Candle,Direction, Active

skey = None

buyTime = 0
buyPrice = 0
buyed = False
exp_time_seconds = 0
last_candle = Candle([0,0,0,0,0])
lot = 10

def buyActive(ws, direction, buyTime, expTimeInSeconds):
    global lot
    logging.info("Посылаем запрос {} ... Lot: {}".format(direction, lot))
    ws.send(json.dumps({"name": "buy",
                        "msg": {
                            "price": lot,
                            "exp": expTimeInSeconds,
                            "act": 1,
                            "type": "turbo",
                            "time": buyTime,
                            "direction": direction
                        }}))


def ws_get_candles(ws,active,duration,chunk_size, fromTime, till):
    ws.send(json.dumps({"name": "candles", "msg": {
        "active_id": active,
        "duration": duration,
        "chunk_size": chunk_size,
        "from": fromTime,
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
            logging.info("Open call direction: buyTime: {}\t Exp_time:{}".format(buyTime,exp_time_seconds))
            buyActive(ws, Direction.call, buyTime, exp_time_seconds)
        elif last_candle.get_type() == CandleType.red:
            logging.info("Open put direction: buyTime: {}\t Exp_time:{}".format(buyTime,exp_time_seconds))
            buyActive(ws, Direction.put, buyTime, exp_time_seconds)
        else:
            logging.debug("Wrong Candle type")


    logging.info("Got: {} candles".format(len(parsed_candles)))
    logging.info("Types: {}".format(candle_types))


def get_direction_from_candles(candle_types):
    pass




def on_message(ws, message):
    #print message
    global skey
    global buyPrice
    global buyTime
    global buyed
    global exp_time_seconds
    global lot
    global last_candle
    raw = json.loads(message)
    #logging.debug(message)
    if 'timeSync' in raw['name']:
        servertime = int(raw['msg'])

        # Get EXP time from server time + 1 minute
        server_time = datetime.datetime.fromtimestamp(servertime/1000)
        exp_time = server_time + datetime.timedelta(minutes=1)

        if server_time.second > 30:
            exp_time = server_time + datetime.timedelta(minutes=2)

        exp_time = exp_time.replace(second=0, microsecond=0)
        exp_time_seconds = int(time.mktime(exp_time.timetuple()))

        #print "Exp time: {} - {}".format(exp_time , exp_time_seconds)

        buyTime = int(servertime/1000)

        if server_time.second == 0:
            logging.info('00 sec')
            # Запрашиваем последнюю закрытую свечу
            ws_get_candles(ws, Active.EURUSD, 60, 214, buyTime - 60, buyTime)



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
            lot = lot * 2.5

    elif 'tradersPulse' in raw['name']:
        value = raw['msg']

    elif 'candles' in raw['name']:
        logging.debug(message)
        # OHLC
        get_candles(raw['msg']['data'])

    else:
        logging.debug(message)


def on_error(ws, error):
    print error


def on_close(ws):
    logging.info("### closed ###")


def on_open(ws):
    ws.send(json.dumps({"name":"ssid","msg":ssid}))
    ws.send(json.dumps({"name":"subscribe","msg":"deposited"}))
    ws.send(json.dumps({"name":"subscribe","msg":"tradersPulse"}))
    ws.send(json.dumps({"name":"subscribe","msg":"activeScheduleChange"}))

    # EURUSD-OTC
    #ws.send(json.dumps({"name":"setActives","msg":{"actives":[76]}}))
    # EURUSD
    ws.send(json.dumps({"name":"setActives","msg":{"actives":[1]}}))

    # candles
    # ["{\"name\":\"candles\",\"msg\":{\"active_id\":1,\"duration\":5,\"chunk_size\":100,\"from\":1462203520,\"till\":1462204000,\"layer\":\"layer-main-4\",\"gl\":\"true\"}}"]
    # ["{\"name\":\"candles\",\"msg\":{\"active_id\":1,\"duration\":120,\"chunk_size\":56,\"from\":1462258700,\"till\":1462264940,\"layer\":\"layer-prev-1\",\"gl\":\"true\"}}"]

    ws.send(json.dumps(dict(
        name='candles',
        msg=dict(
            active_id=1,
            duration=5,
            chunk_size=100,
            #from=1462203520,
            till=1462264940,
            layer='layer-main-4',
            gl=True
        )
    )))



    ws.send(json.dumps({"name":"subscribe","msg":"activeCommissionChange"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"iqguard"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"signal"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"timeSync"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"feedRecentBets"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"feedRecentBets2"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"feedTopTraders2"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"feedRecentBetsMulti"}))
    ws.send(json.dumps({"name":"unSubscribe","msg":"tournament"}))


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

