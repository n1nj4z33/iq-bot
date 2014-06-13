#!/usr/bin/python
# -*- coding: utf8 -*-
""" iq-bot """
__author__ = 'ninja_zee'
from win32gui import FindWindow, FindWindowEx, SendMessage
from win32con import EM_GETLINE
import random
from struct import pack
from time import localtime, strftime, sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from optparse import OptionParser

#Config
URL = 'https://iqoption.com/ru'
TITLE_RUS = u'Алерт'
TITLE_ENG = 'Alert'
WINDOW_ID = '#32770'
TIMEOUT = 10
BUY_TEXT = 'Buy'
SELL_TEXT = 'Sell'
TURBO = u'Турбо опцион'
BIN = u'Бинарный опцион'
TEST_MESSAGES = ['Buy', 'Sell']
MODES = ['test', 'real', 'demo']

#Locators
LOGIN_BUTTON = '//button[@ng-click="login()"]'
EMAIL = '//input[@name="email"]'
PASSWORD = '//input[@name="password"]'
SUBMIT = '//button[@type="submit"]'
BUY_UP_BUTTON = '//button[contains(@ng-click,"call")]'
BUY_DOWN_BUTTON = '//button[contains(@ng-click,"put")]'
BUY_UP_CONFIRM_BUTTON = '//button[contains(@ng-show, "call")][text()="Купить"]'
BUY_DOWN_CONFIRM_BUTTON = '//button[contains(@ng-show, "put")][text()="Купить"]'
CONTINUE_DEMO_BUTTON = """//button[contains(@ng-click, "opt.game.newRate()")]
[text()="Продолжить демо-торги"]"""
CONTINUE_REAL_BUTTON = """//button[contains(@ng-click, "opt.game.newRate()")]
[text()="Новый опцион"]"""
BALANCE = '//a[contains(@value,"user.profile.balance")]'
CLOSE_BUTTON = '//button[@ng-click="close()"][text()="Закрыть"]' 
NAV_BAR = 'bs-example-navbar-collapse-1'
TURBO_BUTTON = '//a[@href="/ru/options/turbo"]'
BIN_BUTTON = '//a[@href="/ru/options/binary"]'
LANG_CNTRL = '//ul[@ng-controller="ChangeLangCtrl"]'
DROPDOWN_MENU = '//ul[@class="dropdown-menu"]'
ENG_LANG = '/li/a[text()="English"]'
RUS_LANG = '/li/a[text()="Русский"]'
CONSPIRACY_TIME_CNTRL = '//div[@ng-change="opt.onChangeTime(opt.data.expTime)"]'
SOUND_BUTTON = '//div[@ng-show="sound"]'
ACTIVE_CNTRL = '//ul[contains(@class, "all-actives")]'
PAIRS_TAB = '//a[contains(text(), "Валютные пары")]'
ACTIVE_BUTTON = '//div[contains(@class, "active")]/div/table'

class Iq():
    """
    Iq-bot class
    """

    def __init__(self, *args):
        self.user = OPTIONS.user
        self.pwd = OPTIONS.pwd
        self.mode = OPTIONS.mode
        self.option = OPTIONS.option
        self.lang = OPTIONS.lang
        self.active = OPTIONS.active
        self.sound = OPTIONS.sound
        self.chrome = OPTIONS.chrome
        self.time = strftime("%Y-%m-%d %H:%M:%S", localtime())
        self.chrome_options = webdriver.ChromeOptions()
        if self.chrome: 
            self.chrome_options.add_argument(self.chrome)
        self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
        self.browser.implicitly_wait(TIMEOUT)
        self.start_session(self.mode)

    @property
    def get_time(self):
        """ Получаем текущее локальное время """
        return self.time

    def check_login(self):
        """ Ищем кнопку логина """
        try:
            self.browser.find_element_by_xpath(LOGIN_BUTTON)
            return False
        except NoSuchElementException:
            assert 0, u'Не могу найти элемент %s' % LOGIN_BUTTON
            return True

    def get_balance(self):
        """ Получаем текущий баланс """
        balance = self.browser.find_element_by_xpath(BALANCE).text
        return balance

    def wait_navbar(self):
        """Ожидание появления NAV_BAR"""
        WebDriverWait(self.browser, 10).until(ec.presence_of_element_located(
            (By.ID, NAV_BAR)))

    def login_action(self):
        """ Логинимся """
        if not self.check_login():
            print u'%s Логинемся на %s' % (self.get_time, URL)
            self.browser.find_element_by_xpath(LOGIN_BUTTON).click()
            self.browser.find_element_by_xpath(EMAIL).send_keys(self.user)
            self.browser.find_element_by_xpath(PASSWORD).send_keys(self.pwd)
            self.browser.find_element_by_xpath(SUBMIT).click()
            self.wait_navbar()
        else:
            print u'%s Уже залогинен' % self.get_time

    def get_windows_title(self):
        """ Язык Title для окна MT Alert """
        if self.lang == 'eng':
            return TITLE_ENG
        return TITLE_RUS

    def get_message_text(self):
        """ Получаем win32 MT Alert window/panel/message Текст """
        title = self.get_windows_title()
        window = FindWindow(WINDOW_ID, title)
        panel = FindWindowEx(window, 0, "Edit", None)
        bufferlength = pack('i', 255)
        linetext = bufferlength + "".ljust(253)
        linelength = SendMessage(panel, EM_GETLINE,
                                 0, linetext)
        text = ''.join(linetext[:linelength])
        return text

    def continue_button_exist(self, mode):
        """ Ищем кнопку Продолжить торги """
        try:
            if mode == 'real':
                return self.browser.find_element_by_xpath(CONTINUE_REAL_BUTTON)
            else:
                return self.browser.find_element_by_xpath(CONTINUE_DEMO_BUTTON)
        except (NoSuchElementException, ElementNotVisibleException):
            return False
    
    def error_button_exist(self):
        """ Ищем кнопку Закрыть """
        try:
            self.browser.find_element_by_xpath(CLOSE_BUTTON)
            return True
        except (NoSuchElementException, ElementNotVisibleException):
            return False

    def error_window_close():
        """Зыкрываем окно с ошибкой"""
        try:
            self.browser.find_element_by_xpath(CLOSE_BUTTON).click()
        except (NoSuchElementException, ElementNotVisibleException):
            return False

    def continue_action(self, mode):
        """ Нажимаем кнопку Продолжить торги """
        while not self.continue_button_exist(mode):
            pass
        try:
            self.continue_button_exist(mode).click()
        except (NoSuchElementException, ElementNotVisibleException):
            return False

    def sell_buy_action(self, updated_message):
        """ Покупаем/продаем """
        if BUY_TEXT in updated_message:
            print u'%s Покупаем' % self.get_time
            self.browser.find_element_by_xpath(BUY_UP_BUTTON).click()
            sleep(1) # For test only
            try:
                self.browser.find_element_by_xpath(BUY_UP_CONFIRM_BUTTON)
            finally:
                self.browser.find_element_by_xpath(BUY_UP_CONFIRM_BUTTON).click()
        elif SELL_TEXT in updated_message:
            print u'%s Продаем' % self.get_time
            self.browser.find_element_by_xpath(BUY_DOWN_BUTTON).click()
            sleep(1) # For test only
            try:
                 self.browser.find_element_by_xpath(BUY_DOWN_CONFIRM_BUTTON)
            finally:
                self.browser.find_element_by_xpath(BUY_DOWN_CONFIRM_BUTTON).click()
        else:
            print u'%s Нет информации о продаже/покупке' % self.get_time

    def check_result(self, begin_balance):
        """ Получаем новый баланс """
        print u'%s Ждем результата' % self.get_time
        sleep(TIMEOUT)  # Необходимо подождать прогрузку баланса
        end_balance = self.get_balance()
        profit = float(end_balance) - float(begin_balance)
        if float(end_balance) > float(begin_balance):
            print u'%s Новый баланс = %s(''+''%s)' % (self.get_time,
                                                      end_balance, profit)
        else:
            print u'%s Новый баланс = %s(%s)' % (self.get_time,
                                                 end_balance, profit)

    def wait_message_update(self, work_message):
        """ Проверяем уникальность сообщения """
        print u'%s Ждем сообщение от MT alert' % self.get_time
        while work_message == self.get_message_text():
            pass
        print u'%s Сообщение от MT Alert: "%s"' % (self.get_time,
                                                   self.get_message_text())
        updated_message = self.get_message_text()
        return updated_message

    def select_option(self):
        """ Переходим в раздел опциона """
        if self.option == 'turbo':
            print u'%s Переходим на %s' % (self.get_time, TURBO)
            self.browser.find_element_by_xpath(TURBO_BUTTON).click()
        elif self.option == 'bin':
            print u'%s Переходим на %s' % (self.get_time, BIN)
            self.browser.find_element_by_xpath(BIN_BUTTON).click()
        else:
            assert 0, '%s Неверно указан опцион для торговли %s' % (self.get_time, self.option)

    def select_active(self):
        """ Выбираем актив торовли """
        if self.active:
            print u'%s Выбираем актив %s' % (self.get_time, self.active)
            try:
                self.browser.find_element_by_xpath(ACTIVE_CNTRL).click()
                try:
                    self.browser.find_element_by_xpath(PAIRS_TAB).click()
                    try:
                        self.browser.find_element_by_xpath(ACTIVE_BUTTON+'//span[text()="'+self.active.upper()+'"]').click()
                    except NoSuchElementException:
                        assert 0, u'%s Не могу найти элемент %s' % (self.get_time, PAIRS_TAB)        
                except NoSuchElementException:
                    assert 0, u'%s Не могу найти элемент %s' % (self.get_time, PAIRS_TAB)
            except NoSuchElementException:
                assert 0, u'%s Не могу найти элемент %s' % (self.get_time, ACTIVE_CNTRL)

    def select_conspiracy_time(self):
        """ Выбираем последнее время конспирации """
        try:
            button = self.browser.find_element_by_xpath(CONSPIRACY_TIME_CNTRL).click()
            try:
                times = self.browser.find_elements_by_xpath(CONSPIRACY_TIME_CNTRL+DROPDOWN_MENU+'//li/a') 
                element = times[3] # Последний элемент в списке
                print u'%s Выбираем время конспирации %s' % (self.get_time, element.text)
                element.click()
            except NoSuchElementException:
                assert 0, u'%s Не могу найти элемент %s' % (self.get_time, select_time)
        except NoSuchElementException:
            assert 0, u'%s Не могу найти элемент %s' % (self.get_time, button)
    
    def select_language(self):
        """ Выбираем язык страницы"""
        if self.lang == 'rus':
            try:
                button = self.browser.find_element_by_xpath(LANG_CNTRL)
                button.click()
                try:
                    rus_lang = self.browser.find_element_by_xpath(LANG_CNTRL+DROPDOWN_MENU+RUS_LANG)
                    rus_lang.click()
                except NoSuchElementException:
                    assert 0, u'%s Не могу найти элемент %s' % (self.get_time, rus_lang)
            except NoSuchElementException:
                assert 0, u'%s Не могу найти элемент %s' % (self.get_time, button)
    
    def turn_off_sound(self):
        """Выключаем звук"""
        if self.sound == 'off':
            try:
                print u'%s Выключаем звук' % (self.get_time)
                self.browser.find_element_by_xpath(SOUND_BUTTON).click()
            except (NoSuchElementException, ElementNotVisibleException):
                return False

    def start_session(self, mode):
        """ Запуск сессии """
        print u'%s Запускаемся в режме %s' % (self.get_time, mode)
        self.browser.get(URL)
        self.login_action()
        self.turn_off_sound()
        #self.select_language() #For future mb
        self.select_option()
        self.select_active()
        print u'%s Начальный баланс: %s' % (self.get_time, self.get_balance())
        print '-' * 19
        while True:
            begin_balance = self.get_balance()
            if mode == 'test':
                updated_message = random.choice(TEST_MESSAGES)
            else:
                work_message = self.get_message_text()
                updated_message = self.wait_message_update(work_message)
            self.select_conspiracy_time()
            self.sell_buy_action(updated_message)
            if self.error_button_exist():
                self.error_window_close()
                self.sell_buy_action(updated_message)
            self.continue_action(mode)
            self.check_result(begin_balance)
            print '-' * 19

    def stop_session(self):
        """ Close Browser """
        self.browser.quit()


if __name__ == '__main__':
    PARSER = OptionParser(usage="""Usage: iq.py
        -u <"""u"""Email пользователя>
        -p <"""u"""Пароль пользователя>
        -m <"""u"""Выбор режима работы [demo, real, test]>
        -o <"""u"""Выбор опциона [turbo, bin]>
        -l <"""u"""Выбор языка MT alert окна [eng, rus]>
        -a <"""u"""Выбор актива [eur/usd, aud/cad]>
        -c <"""u"""Опции для запуска Chrome>
        -s <"""u"""Вкл/Выкл звуки страницы [on, off]>""",
                          version='1.0')
    PARSER.add_option('-u', '--user',
                      dest='user',
                      default='',
                      help=u'Email пользователя', )
    PARSER.add_option('-p', '--pwd',
                      dest='pwd',
                      default='',
                      help=u'Пароль пользователя', )
    PARSER.add_option('-m', '--mode',
                      dest='mode',
                      default='',
                      help=u'Выбор режима работы [demo, real, test]', )
    PARSER.add_option('-o', '--option',
                      dest='option',
                      default='bin',
                      help=u'Выбор опциона (bin or turbo)', )
    PARSER.add_option('-l', '--lang',
                      dest='lang',
                      default='eng',
                      help=u'Выбор языка MT alert окна (rus or eng)', )
    PARSER.add_option('-a', '--active',
                      dest='active',
                      default='eur/usd',
                      help=u'Выбор актива', )
    PARSER.add_option('-c', '--chrome',
                      dest='chrome',
                      default='',
                      help=u'Опции для Chrome browser (http://peter.sh/experiments/chromium-command-line-switches/)', )
    PARSER.add_option('-s', '--sound',
                      dest='sound',
                      default='off',
                      help=u'Вкл/Выкл звуки страницы', )

    (OPTIONS, ARGS) = PARSER.parse_args()

    if not OPTIONS.user:
        PARSER.error(u'Не указан Email пользователя')
    if not OPTIONS.pwd:
        PARSER.error(u'Не указан Пароль пользователя')
    if not OPTIONS.mode:
        PARSER.error(u'Не указан Режим работы')
    if not OPTIONS.mode in MODES:
        PARSER.error(u'Неверно указан Режим работы')

    Iq(OPTIONS)
