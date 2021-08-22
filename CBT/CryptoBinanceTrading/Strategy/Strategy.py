from ..Util.DataType import *


class StrategyBase:
    def __init__(self, policyId, m_handler):
        self.mv_putQueue = {} #存放该策略的order
        self.policyId = policyId
        self.m_handler = m_handler

    async def OnSpotOrderUpdated(self, po: OrderItem):
        if po.res["X"] == "NEW":
            await self.OnSpotOrderCreated(po)
        elif po.res["X"] == "TRADED":
            await self.OnSpotOrderTraded(po)
        elif po.res["X"] == "FILLED":
            await self.OnSpotOrderFilled(po)
        elif po.res["X"] == "CANCELED":
            self.m_handler.mv_orderContainer.remove(po.orderId)
            await self.OnSpotOrderCanceled(po)

    async def OnFutureOrderUpdated(self, po: OrderItem):
        if po.res["o"]["X"] == "NEW":
            await self.OnFutureOrderCreated(po)
        elif po.res["o"]["X"] == "TRADED":
            await self.OnFutureOrderTraded(po)
        elif po.res["o"]["X"] == "FILLED":
            await self.OnFutureOrderFilled(po)
        elif po.res["o"]["X"] == "CANCELED":
            await self.OnFutureOrderCanceled(po)

    async def OnSpotOrderFilled(self, po):
        pass

    async def OnSpotOrderTraded(self, po):
        pass

    async def OnSpotOrderCanceled(self, po):
        pass

    async def OnAccountUpdated(self, res):
        pass

    async def OnBalanceUpdated(self, res):
        pass

    async def OnSpotDepth(self, depth):
        pass

    async def OnSpotOrderCreated(self, po):
        pass

    async def OnFutureOrderFilled(self, po):
        pass

    async def OnFutureOrderTraded(self, po):
        pass

    async def OnFutureOrderCanceled(self, po):
        pass

    async def OnFutureDepth(self, depth):
        pass

    async def OnFutureOrderCreated(self, po):
        pass

    async def OnAccountConfig(self, res):
        pass

    async def OnOrderCreationException(self, po: OrderItem, symbol_type):
        return 0

    async def SpotCreateOrder(self, po: OrderItem):
        self.mv_putQueue[po.orderId] = po
        await self.m_handler.SpotCreateOrder(po)

    async def FutureCreateOrder(self, po: OrderItem):
        self.mv_putQueue[po.orderId] = po
        await self.m_handler.FutureCreateOrder(po)
