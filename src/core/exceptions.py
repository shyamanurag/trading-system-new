class TradingSystemException(Exception):
    pass

class OrderExecutionException(TradingSystemException):
    pass

class OrderError(TradingSystemException):
    pass

