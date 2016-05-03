import datetime
from enum import Enum


class Direction(Enum):
    call = 'call'
    put = 'put'

class CandleType(Enum):
    green = "Green"
    red = "Red"

class Candle:
    def __init__(self, data):
        self.time = data[0]
        self.timestamp = datetime.datetime.fromtimestamp(self.time)
        self.open = data[1]
        self.close = data[2]
        self.high = data[3]
        self.low = data[4]

    def get_type(self):
        if self.close >= self.open:
            return CandleType.green
        else:
            return CandleType.red

    def __repr__(self):
        return "Time: {} \t Open: {}\t High: {}\t Low: {}\t Close: {}".format(self.time,
                                                                              self.open,
                                                                              self.high,
                                                                              self.low,
                                                                              self.close)

    def __str__(self):
        return "Time: {} \t Open: {}\t High: {}\t Low: {}\t Close: {}".format(self.time,
                                                                              self.open,
                                                                              self.high,
                                                                              self.low,
                                                                              self.close)

class Active(Enum):
    EURUSD = 1
    AUDUSD = 99
    EURUSD_OTC = 76