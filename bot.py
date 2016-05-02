#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import yaml
import datetime
import logging

logger = logging.getLogger()
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)


import websocket
import time
import requests
import enum

from enum import Enum

class Direction(Enum):
    call = 'call'
    put = 'put'

skey = None

buyTime = 0
buyPrice = 0
buyed = False
exp_time_seconds = 0

def buyActive(ws, direction, buyTime, expTimeInSeconds):
    logging.info("Посылаем запрос на покупку ...")
    ws.send(json.dumps({"name": "buy",
                        "msg": {
                            "price": 10,
                            "exp": expTimeInSeconds,
                            "act": 1,
                            "type": "turbo",
                            "time": buyTime,
                            "direction": direction
                        }}))

def on_message(ws, message):
    #print message
    global skey
    global buyPrice
    global buyTime
    global buyed
    global exp_time_seconds
    raw = json.loads(message)
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

    elif 'profile' in raw['name']:
        if 'skey' in raw['msg']:
            skey = raw['msg']['skey']
            logging.debug("Skey: {}".format(skey))

    elif 'newChartData' in raw['name']:

        buyPrice = raw['msg']['value']
        if not buyed:
            buyActive(ws,Direction.call,buyTime,exp_time_seconds)
            buyed = True

    elif 'buyComplete' in raw['name']:
        logging.debug(message)
        success = raw['msg']['isSuccessful']
        if success:
            logging.info("Куплено ...")

        else:
            logging.info(u"Не смог купить актив: {}".format(raw['msg']['message'][0]))

    elif 'listInfoData' in raw['name']:
        profit = raw['msg'][0]['profit']
        if profit > 0:
            logging.info("Выиграли.")
        else:
            logging.info("Проиграли увеличиваем ставку")

    elif raw['name'] == 'tradersPulse':
        value = raw['msg']

    else:
        print message


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

