from .Strategy import *
from ..Util.util import *
from ..Util.DataType import *
import asyncio
from binance.enums import *


class Grid:
    def __init__(self, center, step, n_step=10, net=0):
        self.step = step
        self.n_step = n_step
        self.current_center = 0
        self.price_grid = {i: center + i * step for i in range(-n_step, n_step + 1)}
        self.order_pair = {0: None, 1: None}
        self.buy_amount = 0
        self.sell_amount = 0
        self.buy_num = net
        self.sell_num = 0
        self.net = self.sell_num - self.buy_num
        self.total_pnl = 0
        self.check_net = self.net

    def update_trade(self, price, quantity, direction):
        if direction == 0:
            self.buy_amount += price * quantity
            self.buy_num += 1
        else:
            self.sell_amount += price * quantity
            self.sell_num += 1
        self.net = self.sell_num - self.buy_num
        self.total_pnl = self.sell_amount - self.buy_amount


async def order_check(gt, client, grid):
    while True:
        missing_flag = False
        await asyncio.sleep(5)
        info("Checking Order Number 1")
        try:
            po1 = grid.order_pair[0]
            po2 = grid.order_pair[1]
            if po1 and po2:
                order1 = await client.get_order(symbol=gt.symbol, orderId=po1.orderId)
                order2 = await client.get_order(symbol=gt.symbol, orderId=po2.orderId)
            elif po1:
                order1 = await client.get_order(symbol=gt.symbol, orderId=po1.orderId)
                order2 = None
            elif po2:
                order1 = None
                order2 = await client.get_order(symbol=gt.symbol, orderId=po2.orderId)
            else:
                continue
        except:
            info("Checking Order Number 1: get orders failed")
            continue

        if order1 and order1["status"] == "FILLED":
            await asyncio.sleep(2)
            if grid.order_pair[0] is po1:
                missing_flag = True
                missing_direction = 0
        elif order2 and order2["status"] == "FILLED":
            await asyncio.sleep(2)
            if grid.order_pair[1] is po2:
                missing_flag = True
                missing_direction = 1

        if missing_flag:
            info("Checking Order Number 2 Success | Get Trade Failed")
            info(order1)
            info(order2)
            print("Generating Orders from Checking")

            if missing_direction == 1:
                missing_po = po1
            else:
                missing_po = po2
            await gt.OnSpotOrderFilled(missing_po)


class GridTrading(StrategyBase):
    def __init__(self, policyId, m_handler, grid: Grid, order_quantity, symbol):
        StrategyBase.__init__(self, policyId, m_handler)
        self.grid = grid
        self.order_quantity = order_quantity
        self.symbol = symbol

    async def Start(self):
        await self.GridOrderCreation()

    async def OnSpotOrderFilled(self, po):
        info("Get Filled Trade")
        print("New Trade")

        if po.direction == Direction.BUY:
            self.grid.current_center -= 1
        else:
            self.grid.current_center += 1

        if (self.grid.current_center == self.grid.n_step) or (self.grid.current_center == -self.grid.n_step):
            return

        self.grid.update_trade(po.price, self.order_quantity, po.direction)
        info("Current Status: " + str(self.grid.net) + " " +
             str(self.grid.total_pnl) + " " + str(min(self.grid.sell_num, self.grid.buy_num)))
        print("Current Status: " + str(self.grid.net) + " " +
              str(self.grid.total_pnl) + " " + str(min(self.grid.sell_num, self.grid.buy_num)))

        self.grid.order_pair[po.direction] = None

        pp = self.grid.order_pair[1-po.direction]
        if pp:
            await self.m_handler.SpotCancelOrder(pp)
        else:
            creation = asyncio.create_task(self.GridOrderCreation())
            await creation

    async def OnSpotOrderCanceled(self, po):
        self.grid.order_pair[po.direction] = None
        await self.GridOrderCreation()

    async def GridOrderCreation(self):
        sell_price = self.grid.price_grid[self.grid.current_center + 1]
        buy_price = self.grid.price_grid[self.grid.current_center - 1]

        if self.grid.net >= 0:
            self.m_handler.pid += 1
            pbuy = OrderItem(self.m_handler.pid, self.symbol, Direction.BUY, ORDER_TYPE_LIMIT,
                             TIME_IN_FORCE_GTC, self.order_quantity, buy_price, self.policyId)
            await self.m_handler.SpotCreateOrder(pbuy)
        else:
            self.m_handler.pid += 1
            pbuy = OrderItem(self.m_handler.pid, self.symbol, Direction.BUY, ORDER_TYPE_LIMIT,
                             TIME_IN_FORCE_GTC, self.order_quantity, buy_price, self.policyId)
            self.m_handler.pid += 1
            psell = OrderItem(self.m_handler.pid, self.symbol, Direction.SELL, ORDER_TYPE_LIMIT,
                              TIME_IN_FORCE_GTC, self.order_quantity, sell_price, self.policyId)
            b = asyncio.create_task(self.m_handler.SpotCreateOrder(pbuy))
            s = asyncio.create_task(self.m_handler.SpotCreateOrder(psell))
            await asyncio.gather(b, s)

    async def OnSpotOrderCreated(self, po):
        self.grid.order_pair[po.direction] = po

    async def OnOrderCreationException(self, po, symbol_type, status_code):
        if status_code == 400:
            return 1
        else:
            return 0
