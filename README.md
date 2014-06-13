#iq-bot(Python)

###Required:
* selenium
* pywin32

###Usage:
python iq.py
* -u <'Email' пользователя>
* -p <Пароль пользователя>
* -m <Выбор режима работы [demo, real, test]>
* -o <Выбор опциона [turbo, bin]>
* -l <Выбор языка MT alert окна [eng, rus]>
* -a <Выбор актива [eur/usd, aud/cad, etc]>
* -c <Опции для запуска Chrome>
Полный список опций запуска Crome (http://peter.sh/experiments/chromium-command-line-switches/)
* -s <Вкл/Выкл звуки страницы [on, off]>
####Example:
```./iq.py -u user_name -p password -m test```

####Info:
Режимы работы 
* demo (Демо счет)
* real (Реальный счет)
* test (Тестовый режим без сообщений от МТ)

