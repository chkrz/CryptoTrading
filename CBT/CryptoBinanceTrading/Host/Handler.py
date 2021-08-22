from ..Util.util import *
from ..Util.DataType import *
import asyncio
#from binance.exceptions import BinanceAPIException
#from binance.enums import *
import warnings


class FHub:
    def __init__(self):
        self.pid = 0
        self.symbol_book = set()
        self.mv_orderContainer = {}
        self.mv_policys = {}
        self.s_handler = None
        self.f_handler = None

    def AddSpotHandler(self, handler):
        self.s_handler = handler

    def AddFutureHandler(self, handler):
        self.f_handler = handler

    def AddSymbol(self, symbol: str):
        self.symbol_book.add(symbol)

    def AddFPolicy(self, policy):
        if policy.policyId in self.mv_policys:
            warnings.warn('PolicyID %d already exists' % policy.policyId, DeprecationWarning)
        self.mv_policys[policy.policyId] = policy

    def IsNativeOrder(self, order_symbol: str, orderId):
        if order_symbol in self.symbol_book and orderId in self.mv_orderContainer:
            return True
        else:
            return False

    def UpdateOrderContainer(self, res):
        if res["i"] in self.mv_orderContainer:
            self.mv_orderContainer[res["i"]].UpdateRes(res)
        else:
            print("error")

    async def HandleSpotListenerUpdate(self, res):
        if res:
            if res["e"] == "outboundAccountPosition":
                await self.s_handler.HandleAccountUpdate(res)
            elif res["e"] == "balanceUpdate":
                await self.s_handler.HandleBalanceUpdate(res)
            elif res["e"] == "executionReport":
                await self.s_handler.HandleOrderUpdate(res)

    async def HandleFutureListenerUpdate(self, res):
        if res:
            if res["e"] == "ACCOUNT_UPDATE":
                await self.f_handler.HandleAccountUpdate(res)
            elif res["e"] == "ORDER_TRADE_UPDATE":
                await self.f_handler.HandleOrderUpdate(res)
            elif res["e"] == "ACCOUNT_CONFIG_UPDATE":
                await self.f_handler.HandleAccountConfigUpdate(res)

    async def HandleDepthUpdate(self, depth, symbol_type: SymbolType):
        if symbol_type == SymbolType.SPOT:
            await self.s_handler.HandleDepthData(depth)
        elif symbol_type == SymbolType.FUTURE:
            await self.f_handler.HandleDepthData(depth)

    async def SpotCreateOrder(self, po: OrderItem):
        self.mv_orderContainer[po.orderId] = po
        await self.s_handler.CreateOrder(po)

    async def FutureCreateOrder(self, po: OrderItem):
        self.mv_orderContainer[po.orderId] = po
        await self.f_handler.CreateOrder(po)

    async def SpotCancelOrder(self, po: OrderItem):
        await self.s_handler.CancelOrder(po)


class SFHandler:
    def __init__(self, m_handler: FHub, client):
        self.m_handler = m_handler
        self.client = client


class SpotHandler(SFHandler):
    def __init__(self, m_handler: FHub, client):
        SFHandler.__init__(self, m_handler, client)

    async def HandleOrderUpdate(self, res):
        if self.m_handler.IsNativeOrder(order_symbol=res["s"], orderId=res["i"]):
            self.m_handler.UpdateOrderContainer(res)
            po = self.m_handler.mv_orderContainer[res["i"]]
            await self.m_handler.mv_policys[po.policyId].OnSpotOrderUpdated(po)
            
    async def HandleAccountUpdate(self, res):
        #后续要修改成 循环创建 await all
        for strategy in self.m_handler.mv_policys.values():
            await strategy.OnAccountUpdated(res)

    async def HandleBalanceUpdate(self, res):
        for strategy in self.m_handler.mv_policys.values():
            await strategy.OnBalanceUpdated(res)

    async def HandleDepthData(self, depth):
        for strategy in self.m_handler.mv_policys.values():
            await strategy.OnSpotDepth(depth)

    @retry(times=3, retry_on_result=0)
    async def CreateOrder(self, po):
        try:
            if po.direction == Direction.BUY:
                direction = "BUY"
            else:
                direction = "SELL"
            order = await self.client.create_order(symbol=po.symbol,
                                                   side=direction,
                                                   type=po.order_type,
                                                   timeInForce=po.timeInForce,
                                                   quantity=po.quantity,
                                                   price=po.price,
                                                   newClientOrderId=po.orderId)
            info("Order Created")
            info(order)
            return 1
        except BinanceAPIException as e:
            info("Order Creation Failed")
            info(e.status_code)
            info(e.message)
            ooce = asyncio.create_task(self.m_handler.mv_policys[po.policyId].
                                       OnOrderCreationException(po, SymbolType.SPOT, e.status_code))
            await ooce
            return ooce.result()

    @retry(times=3, retry_on_result=0)
    async def CancelOrder(self, po):
        try:
            result = await self.client.cancel_order(symbol=po.symbol, orderId=po.orderId)
            return 1
        except BinanceAPIException as e:
            info("Order Cancel Failed")
            info(e.status_code)
            info(e.message)
            ooce = asyncio.create_task(self.m_handler.mv_policys[po.policyId].
                                       OnOrderCancelException(po, SymbolType.SPOT, e.status_code))
            await ooce
            return ooce.result()


class FutureHandler(SFHandler):
    def __init__(self, m_handler: FHub, client):
        SFHandler.__init__(self, m_handler, client)

    async def HandleAccountUpdate(self):
        pass

    async def HandleOrderUpdate(self, res):
        if self.m_handler.IsNativeOrder(order_symbol=res["s"], orderId=res["i"]):
            self.m_handler.UpdateOrderContainer(res)
            po = self.m_handler.mv_orderContainer[res["i"]]
            await self.m_handler.mv_policys[po.policyId].OnFutureOrderUpdated(po)

    async def HandleAccountConfigUpdate(self, res):
        for strategy in self.m_handler.mv_policys.values():
            strategy.OnAccountConfig(res)

    async def HandleDepthData(self, depth):
        for strategy in self.m_handler.mv_policys.values():
            strategy.OnFutureDepth(depth)

    @retry(times=3, retry_on_result=0)
    async def CreateOrder(self, po: OrderItem):
        try:
            order = await self.client.create_future_order(symbol=po.symbol,
                                                          side=po.direction,
                                                          type=po.order_type,
                                                          timeInForce=po.timeInForce,
                                                          quantity=po.quantity,
                                                          price=po.price,
                                                          newClientOrderId=po.orderId)
            info("Order Created")
            info(order)
            return 1
        except BinanceAPIException as e:
            info("Order Creation Failed")
            info(e.status_code)
            info(e.message)
            ooce = asyncio.create_task(self.m_handler.mv_policys[po.policyId].
                                       OnOrderCreationException(po, SymbolType.FUTURE))
            await ooce
            return ooce.result()

    @retry(times=3, retry_on_result=0)
    async def CancelOrder(self, po):
        try:
            result = await self.client.futures_cancel_order(symbol=po.symbol, orderId=po.orderId)
            return 1
        except BinanceAPIException as e:
            info("Order Cancel Failed")
            info(e.status_code)
            info(e.message)
            ooce = asyncio.create_task(self.m_handler.mv_policys[po.policyId].
                                       OnOrderCancelException(po, SymbolType.SPOT, e.status_code))
            await ooce
            return ooce.result()
