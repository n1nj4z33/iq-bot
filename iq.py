#!/usr/bin/python
# -*- coding: utf8 -*-
__author__ = 'ninja_zee'
'''
some docstring
'''
import win32gui
import win32con
import struct
from time import localtime, strftime, sleep
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

#Config
URL = 'https://iqoption.com/ru'
LOGIN_EMAIL = ''
LOGIN_PWD = ''
TITLE = u'Алерт'
WINDOW_ID = '#32770'
TIMEOUT = 5
BUY_TEXT = 'Buy'
SELL_TEXT = 'Sell'

#Locators
LOGIN_BUTTON = '//button[@ng-click="login()"]'
EMAIL = '//input[@name="email"]'
PASSWORD = '//input[@name="password"]'
SUBMIT = '//button[@type="submit"]'
BUY_UP_BUTTON = '//button[contains(@ng-click,"call")]'
BUY_DOWN_BUTTON = '//button[contains(@ng-click,"put")]'
BUY_UP_CONFIRM_BUTTON = '//button[contains(@ng-show, "call")][text()="Купить"]'
BUY_DOWN_CONFIRM_BUTTON = '//button[contains(@ng-show, "put")][text()="Купить"]'
CONTINUE_BUTTON = '''//button[contains(@ng-click, "opt.game.newRate()")]
[text()="Продолжить демо-торги"]'''
BALANCE = '//a[contains(@value,"user.profile.balance")]'


class Iq():
    '''
    Base class for Meta
    '''
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.browser = webdriver.Chrome(chrome_options=self.options)
        self.browser.implicitly_wait(TIMEOUT)
        self.start_session()

    def get_time(self):
        '''Get current time'''
        return strftime("%Y-%m-%d %H:%M:%S", localtime())

    def check_login(self):
        '''Check if LOGIN_BUTTON exist in DOM'''
        try:
            self.browser.find_element_by_xpath(LOGIN_BUTTON)
            return False
        except NoSuchElementException:
            assert 0, "No such element " + LOGIN_BUTTON
            return True

    def get_balance(self):
        '''Get current balance'''
        balance = self.browser.find_element_by_xpath(BALANCE).text
        return balance

    def login_action(self):
        '''Loging on'''
        if not self.check_login():
            print '%s Login in to %s' % (self.get_time(), URL)
            self.browser.find_element_by_xpath(LOGIN_BUTTON).click()
            self.browser.find_element_by_xpath(EMAIL).send_keys(LOGIN_EMAIL)
            self.browser.find_element_by_xpath(PASSWORD).send_keys(LOGIN_PWD)
            self.browser.find_element_by_xpath(SUBMIT).click()
        else:
            print '%s Already login in...' % self.get_time()
        sleep(5) #wait animation loaded

    def get_message_text(self):
        '''Get win32 MT Alert window/panel/message Text'''
        window = win32gui.FindWindow(WINDOW_ID, TITLE)
        panel = win32gui.FindWindowEx(window, 0, "Edit", None)
        bufferlength = struct.pack('i', 255)
        linetext = bufferlength + "".ljust(253)
        linelength = win32gui.SendMessage(panel, win32con.EM_GETLINE, 0,
                                          linetext)
        text = ''.join((linetext[:linelength]))
        return text

    def sell_buy_action(self, action):
        '''Sell or Buy action'''
        if action == 'Buy':
            print '%s Buying...' % self.get_time()
            self.browser.find_element_by_xpath(BUY_UP_BUTTON).click()
            self.browser.find_element_by_xpath(BUY_UP_CONFIRM_BUTTON).click()
            #self.get_balance()
        elif action == 'Sell':
            print '%s Selling...' % self.get_time()
            self.browser.find_element_by_xpath(BUY_DOWN_BUTTON).click()
            self.browser.find_element_by_xpath(BUY_DOWN_CONFIRM_BUTTON).click()
            #self.get_balance()
        else:
            print '%s No Buy or Sell in message' % self.get_time()
        self.continue_action()

    def continue_button_exist(self):
        '''Find Continue trade button'''
        try:
            self.browser.find_element_by_xpath(CONTINUE_BUTTON)
            return True
        except NoSuchElementException:
            return False

    def continue_action(self):
        '''Wait until Continue Button is visible and click'''
        print '%s Wait for result...' % self.get_time()
        while not self.continue_button_exist():
            pass
        self.browser.find_element_by_xpath(CONTINUE_BUTTON).click()

    def make_decision(self):
        '''Decision to Sell or Buy action'''
        work_message = self.get_message_text()
        print '%s Message from MT Alert: %s' % (self.get_time(), work_message)
        if BUY_TEXT in work_message:
            self.sell_buy_action(BUY_TEXT)
        elif SELL_TEXT in work_message:
            self.sell_buy_action(SELL_TEXT) 
        else:
            print '%s Wait Message from MT Alert...' % self.get_time()
        return work_message
    
    def start_session(self):
        '''Begin trade'''
        print '%s Starting...' % self.get_time()
        self.browser.get(URL)
        self.login_action()
        self.get_balance()
        self.start_trade()

    def check_result(self, begin_balance):
        sleep(10) #wait cash loaded 
        end_balance = self.get_balance()
        profit = float(end_balance) - float(begin_balance)
        print '%s New balance = %s(%s)' % (self.get_time(), end_balance, profit) 

    def wait_message_update(self, work_message):
        print '%s Wait for update mesasge from MT alert...' % self.get_time()
        while work_message == self.get_message_text():
            pass
               
    def start_trade(self):
        '''Tranding here'''
        print '%s Current balance = %s' % (self.get_time(), self.get_balance())        
        while True:
            begin_balance = self.get_balance()
            work_message = self.make_decision()
            self.check_result(begin_balance)   
            self.wait_message_update(work_message)

    def stop_session(self):
        '''Close Browser'''
        self.browser.close()

if __name__ == '__main__':
    Iq()
