#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

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
            logging.info("Не смог купить актив: {}".format(raw['msg']))

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

    # ["{\"name\":\"ssid\",\"msg\":\"571c72efaf819381a5b445905eecda3c\"}"]

    ws.send(json.dumps({"name":"ssid","msg":"571c72efaf819381a5b445905eecda3c"}))
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
    #websocket.enableTrace(True)

    login_data = {
        'email': 'ivan.suhum@gmail.com',
        'password': 'hPHprb2Z7JXdq8',
        'remember_me': 1
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    r = requests.post('https://iqoption.com/api/login', login_data, headers=headers)

    logging.info("SSID: {}".format(r.cookies['ssid']))
    ssid = r.cookies['ssid']


    ws = websocket.WebSocketApp("wss://eu.iqoption.com/echo/websocket",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
                                #cookie="skey=b10847bd8a14e4180fcd25ac35bc3239;ssid=571c72efaf819381a5b445905eecda3c")
    ws.on_open = on_open
    ws.run_forever()

# buy
# {"price":10,"refund_value":0,"act":76,"exp":1462018860,"type":"turbo","direction":"call","value":1.144001,"time":1462018815,"skey":"bc2dc700fb3f2486fe02900ccf0ed713"}}"

# get chart data active 76 OTC EUR/USD
# "{"name":"setActives","msg":{"actives":[76]}}"

# profile
# "{"name":"profile","msg":{"avatar":"","confirmation_required":0,"popup":{"1":{"name":"mobile_firstdeposit first
# variant Popup","bonus_code":"WelcomeSplashCode2","countdown":40}},"money":{"deposit":{"min":10,"max":1000000},
# "withdraw":{"min":10,"max":1000000}},"user_group":"Default","welcome_splash":0,"functions":{"is_bonus_block":0,
# "is_trading_bonus_block":0,"is_vip_mode":0,"is_no_currency_change":0,"popup_ids":["1"],"ext_fields":[]},
# "finance_state":"","balance":1049,"bonus_wager":0,"balance_id":12756392,"balance_type":1,"messages":0,"id":10057756,
# "demo":1,"public":1,"group_id":1,"name":"Ivan Suhum","nickname":null,"currency":"EUR","currency_char":"â¬",
# "mask":"â¬ %s","city":"","user_id":10057756,"first_name":"Ivan","last_name":"Suhum","phone":" ",
# "email":"ivan.suhum@gmail.com","created":1461948865,"last_visit":false,"site_id":1,"tz":"Europe/Helsinki",
# "locale":"ru_RU","birthdate":false,"country_id":14,"currency_id":1,"gender":"male","address":"","postal_index":"",
# "timediff":0,"tz_offset":180,"balances":[{"id":12756392,"type":1,"amount":1040200000,"currency":"EUR",
# "description":null}],"infeed":1,"confirmed_phones":[],"need_phone_confirmation":false,"rate_in_one_click":false,
# "kyc_confirmed":false,"kyc":{"status":0,"isRegulatedUser":true,"isProfileNeeded":false,"isPhoneNeeded":false,
# "isDocumentsNeeded":false,"isDocumentsDeclined":false,"isProfileFilled":false,"isPhoneFilled":false,
# "isDocumentsUploaded":false,"isPhoneConfirmationSkipped":false,"isPhoneConfirmed":false,"isDocumentsUploadSkipped":false,
# "isDocumentsApproved":false},"trade_restricted":false,"socials":[],"flag":"AT","cashback_level_info":{"enabled":false},
# "trial":false,"user_circle":"No exp",
# "ssid":"5d585ae1197ba5dec3e86d8ce826f412", !!!
# "skey":"14a62cec5def4ea5c7614c01a3c7bd05", !!!
# "connection_info":["91.184.201.2","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:
