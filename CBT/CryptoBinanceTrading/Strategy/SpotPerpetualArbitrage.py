from .Strategy import *
from ..Util.util import *
from ..Util.DataType import *
import asyncio
from binance.enums import *


class ArbTH:
    def __init__(self):
        self.open_insert_th
        self.open_insert_std_th
        self.open_th
        self.open_std_th

        self.close_insert_th
        self.close_insert_std_th
        self.close_th
        self.close_std_th

        self.cancel_th
        self.cancel_std_th
        self.cancel_close_th
        self.cancel_close_std_th

class FAIndicator:
    def __init__(self, th, n):
        self.th = th
        self.mv_bias = 0
        self.mv_horizon = 0
        self.mv_sum = 0
        self.mv_sumq = 0
        self.n = n
        self.diff_q = []
        self.diff_sq = []
        self.bias_q = []
        self.std = 0

        self.pv = -1
        self.bv = -1

        self.pv_bid = 0
        self.pv_ask = 0

        self.bv_bid = 0
        self.bv_ask = 0

    def update_base(self, value):
        self.bv_bid = depth["bids"][0]
        self.bv_ask = depth["asks"][0]
        self.bv = (self.bv_bid + self.bv_ask)/2
        #if特别花时间不能这么更新
        if self.pv >= 0:
            self.insert_diff(self.bv - self.pv)

    def update_partner(self, value):
        self.pv_bid = depth["bids"][0]
        self.pv_ask = depth["asks"][0]
        self.pv = (self.pv_bid + self.pv_ask)/2
        if self.bv >= 0:
            self.insert_diff(self.bv - self.pv)

    def insert_diff(self, diff):
        if len(self.diff_q) >= self.n:
            ov = self.diff_q.pop(0)
            ovs = self.diff_sq.pop(0)

        self.diff_q.append(diff)
        self.diff_sq.append(diff**2)

        self.mv_sum = self.mv_sum + diff - ov
        self.mv_sumq = self.mv_sum + self.diff_sq[-1] - ovs

        self.mv_horizon = self.mv_sum/self.n
        self.std = (self.mv_sumq/n - self.mv_horizon**2)**0.5

    def IsGreen(oc, direction):
        if oc == "open" and direction == "sell":
            flag = (self.diff_q[-1] - self.mv_horizon) < -max(self.open_insert_th, self.open_insert_std_th*self.mv_bias)
        elif oc == "open" and direction == "buy":
            flag = (self.diff_q[-1] - self.mv_horizon) > max(self.open_insert_th, self.open_insert_std_th*self.mv_bias)
        elif oc == "close" and direction == "sell":
            flag = (self.diff_q[-1] - self.mv_horizon) < -max(self.close_insert_th, self.close_insert_std_th*self.mv_bias)
        elif oc == "close" and direction == "buy":
            flag = (self.diff_q[-1] - self.mv_horizon) > max(self.close_insert_th, self.close_insert_std_th*self.mv_bias)
        return flag

    def GetPrice(oc, direction):
        if oc == "open" and direction == "sell":
            return self.bv_bid - self.mv_horizon + max(self.open_th, self.open_std_th*self.mv_bias)
        elif oc == "open" and direction == "buy":
            return self.bv_ask - self.mv_horizon - max(self.open_th, self.open_std_th*self.mv_bias)
        elif oc == "close" and direction == "sell":
            return self.bv_ask - self.mv_horizon + max(self.close_th, self.close_std_th*self.mv_bias)
        elif oc == "close" and direction == "buy":
            return self.bv_bid - self.mv_horizon - max(self.close_th, self.close_std_th*self.mv_bias)
    
    def IsRed(p, oc, direction):
        price = self.GetPrice(oc, direction)
        judge = p - price
        if oc == "open":
            judge = abs(p - price) > max(self.th.cancel_th, self.th.cancel_std_th)
        elif oc == "close":
            judge = abs(p - price) > max(self.th.cancel_close_th, self.th.cancel_close_std_th)
        return judge

#针对btcbusd 现货挂单 期货打单
class SpotPerpetualArbitrage(StrategyBase):
    def __init__(self, policyId, m_handler, symbol, mv_indicator, order_quantity, th):
        StrategyBase.__init__(self, policyId, m_handler)
        self.symbol = symbol
        self.mv_indicator = mv_indicator
        self.th = th
        self.direction = 

    async def Start(self):
        asyncio.sleep(500)

    async def OnSpotOrderFilled(self, po):
        #打单
        pf = OrderItem()
        creation = asyncio.create_task(self.)
        await creation

    async def OnFutureOrderFilled(self, po):
        #挂单

    async def OnSpotDepth(self, depth):
        # 更新FAIndicator 并判断撤单
        self.mv_indicator.update_partner(depth)
        self.mv_indicator.IsGreen
        
        po = self.mv_putQueue[0]
        #有order
        if IsRed():
            await self.m_handler.cancelorder

        #无order就直接判断green
        if IsGreen():
            


    async def OnFutureDepth(self, depth):
        #更新FAIndicator 并判断撤单
        self.mv_indicator.update_base(depth)

    async def OnSpotOrderCanceled(self, po):
        #重新挂单
        if IsGreen():


    async def OnFutureOrderCanceled(self, po):
        #重新打单
        