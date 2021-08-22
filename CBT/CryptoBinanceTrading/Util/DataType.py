from enum import Enum


class SymbolType(Enum):
    SPOT = 0
    FUTURE = 1


class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderItem:
    def __init__(self, orderId, symbol, direction, order_type, timeInForce, quantity, price, policyId, res=None):
        self.orderId = orderId
        self.symbol = symbol
        self.direction = direction
        self.order_type = order_type
        self.timeInForce = timeInForce
        self.quantity = quantity
        self.price = price
        self.res = res
        self.policyId = policyId

    def UpdateRes(self, res):
        self.res = res

    def UpdateCustomField(self):
        pass


class Purpose(Enum):
    FA_OPEN = 0
    FA_CLOSE = 1


class SpotPerpetualArbOrderItem(OrderItem):
    def __init__(self, orderId, symbol, direction, order_type, timeInForce, quantity, price, purpose: Purpose, res=None):
        OrderItem.__init__(self, orderId, symbol, direction, order_type, timeInForce, quantity, price, res)
        self.purpose = purpose

    def UpdateCustomField(self, purpose: Purpose):
        self.purpose = purpose
