import asyncio
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException
from binance.enums import *
import concurrent.futures
import logging
import time
from retrying import retry

class Grid:
    def __init__(self, center, step, n_step=10, net = 0):
        self.step = step
        self.n_step = n_step
        self.current_center = 0
        self.price_grid = {i: center + i*step for i in range(-n_step, n_step+1)}
        self.order_pair = {0: None, 1: None}
        self.buy_amount = 0
        self.sell_amount = 0
        self.buy_num = net
        self.sell_num = 0
        self.net = self.sell_num-self.buy_num
        self.total_pnl = 0
        self.check_net = self.net

    def update_trade(self, price, quantity, direction):
        if direction == 0:
            self.buy_amount += price*quantity
            self.buy_num += 1
        else:
            self.sell_amount += price*quantity
            self.sell_num += 1
        self.net = self.sell_num - self.buy_num
        self.total_pnl = self.sell_amount - self.buy_amount


async def order_check(client, symbol, grid, order_quantity):
    missing_flag = False
    while True:
        await asyncio.sleep(5)
        info("Checking Order Number 1")
        try:
            order_id1 = grid.order_pair[0][0]
            order_id2 = grid.order_pair[1][0]
            if order_id1 and order_id2:
                order1 = await client.get_order(symbol=symbol, orderId=order_id1)
                order2 = await client.get_order(symbol=symbol, orderId=order_id2)
            elif order_id1:
                order1 = await client.get_order(symbol=symbol, orderId=order_id1)
                order2 = None
            else:
                continue
        except:
            info("Checking Order Number 1: get orders failed")
            continue

        if order1 and order1["status"] == "FILLED":
            await asyncio.sleep(2)
            if grid.order_pair[0][0] == order_id1:
                missing_flag = True
                missing_direction = 0
        elif order2 and order2["status"] == "FILLED":
            await asyncio.sleep(2)
            if grid.order_pair[1][0] == order_id2:
                missing_flag = True
                missing_direction = 1

        if missing_flag:
            info("Checking Order Number 2 Success | Get Trade Failed")
            info(order1)
            info(order2)
            print("Generating Orders from Checking")

            if missing_direction == 1:
                direction = 1
                grid.current_center += 1
            else:
                direction = 0
                grid.current_center -= 1

            grid.update_trade(grid.price_grid[grid.current_center], order_quantity, direction)

            msg = "Current Status from order check: " + str(grid.net) + " " + \
                  str(grid.total_pnl) + " " + str(min(grid.sell_num, grid.buy_num))
            info(msg)
            print(msg)

            sell_price = grid.price_grid[grid.current_center + 1]
            buy_price = grid.price_grid[grid.current_center - 1]

            if grid.check_net <= -1:
                c = asyncio.create_task(spot_cancel_order(client, symbol, grid, grid.order_pair[1 - direction][0]))
                await c

            if grid.net >= 0:
                b = asyncio.create_task(spot_create_order(client, symbol, grid, 0, buy_price, order_quantity))
                await b
            else:
                b = asyncio.create_task(
                    spot_create_order(client, symbol, grid, 0, buy_price, order_quantity))
                s = asyncio.create_task(
                    spot_create_order(client, symbol, grid, 1, sell_price, order_quantity))
                await asyncio.gather(b, s)
            grid.check_net = grid.net
            missing_flag = False


async def user_listener(bm, client, symbol, grid, order_quantity):
    async with bm.user_socket() as user_stream:
        while True:
            res = await user_stream.recv()

            if not res:
                continue
            if res["e"] == "executionReport" and res["s"] == symbol:
                info(res)
                if res["S"] == "BUY":
                    direction = 0
                else:
                    direction = 1
                if res["X"] == "FILLED":
                    info("Get Filled Trade")
                    if res["i"] == grid.order_pair[direction][0]:
                        print("New Trade")
                        info("Get My New Trade")

                        if direction == 0:
                            grid.current_center -= 1
                        else:
                            grid.current_center += 1

                        if (grid.current_center == grid.n_step) or (grid.current_center == -grid.n_step):
                            return

                        grid.update_trade(float(res["L"]), order_quantity, direction)
                        info("Current Status: " + str(grid.net) + " " +
                             str(grid.total_pnl) + " " + str(min(grid.sell_num, grid.buy_num)))
                        print("Current Status: " + str(grid.net) + " " +
                              str(grid.total_pnl) + " " + str(min(grid.sell_num, grid.buy_num)))

                        sell_price = grid.price_grid[grid.current_center + 1]
                        buy_price = grid.price_grid[grid.current_center - 1]

                        grid.order_pair[direction]= (None, None)
                        if grid.check_net <= -1:
                            c = asyncio.create_task(spot_cancel_order(client, symbol, grid, grid.order_pair[1-direction][0]))
                            await c

                        if grid.net >= 0:
                            b = asyncio.create_task(spot_create_order(client, symbol, grid, 0, buy_price, order_quantity))
                            await b
                        else:
                            b = asyncio.create_task(
                                spot_create_order(client, symbol, grid, 0, buy_price, order_quantity))
                            s = asyncio.create_task(
                                spot_create_order(client, symbol, grid, 1, sell_price, order_quantity))
                            await asyncio.gather(b, s)
                        grid.check_net = grid.net

async def spot_create_order(client, symbol, grid, direction, price, order_quantity):
    try:
        if direction == 0:
            side = 'BUY'
        elif direction == 1:
            side = 'SELL'
        order = await client.create_order(symbol=symbol,
                                          side=side,
                                          type=ORDER_TYPE_LIMIT,
                                          timeInForce=TIME_IN_FORCE_GTC,
                                          quantity=order_quantity,
                                          price=price)
        info("Order Created")
        info(order)
        grid.order_pair[direction] = (order["orderId"], order)
        return 1
    except BinanceAPIException as e:
        info("Order Creation Failed")
        info(e.status_code)
        info(e.message)
        if "insufficient balance" in e.message:
            return 1
        return 0


async def spot_cancel_order(client, symbol, grid, order_id):
    try:
        result = await client.cancel_order(symbol=symbol, orderId=order_id)
        if result["status"] == "CANCELED":
            info("Order Canceled")
            if result["side"] == "BUY":
                direction = 0
            else:
                direction = 1
            if grid.order_pair[direction][0] == result["orderId"]:
                grid.order_pair[direction] = (None, None)
        return 1
    except BinanceAPIException as e:
        info("Order Cancel Failed")
        info(e.status_code)
        info(e.message)
        return 0


executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def info(msg, *args):
    executor.submit(logging.info, str(msg), *args)


async def main():
    api_key = ''
    api_secret = ''

    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)
    client2 = Client(api_key, api_secret)
    bm = BinanceSocketManager(client, user_timeout=60)
    '''
    order_quantity = 0.001
    symbol = "BTCBUSD"
    center = 35333
    step = 50
    net =  118
    
    '''
    
    order_quantity = 0.015
    symbol = "ETHBUSD"
    center = 2218 2233
    step = 3
    net = 140  # 负数代表买入了一些
    
    # mid_price = depth["bids"][0] + depth["asks"][0]
    grid = Grid(center=center, step=step, n_step=300, net=net)

    user = asyncio.create_task(user_listener(bm, client, symbol, grid, order_quantity))

    log_path = "C:/Users/Administrator/PycharmProjects/pythonProject/"
    logging.basicConfig(level=logging.INFO,
                        filename=log_path + "GridTrading" + symbol + 'Bull.log',
                        filemode='a+',
                        format='%(asctime)s - %(levelname)s: %(message)s'
                        )
    time.sleep(3)

    asyncio.create_task(spot_create_order(client, symbol, grid, 0, grid.price_grid[-1], order_quantity))
    if grid.net < 0:
        asyncio.create_task(spot_create_order(client, symbol, grid, 1, grid.price_grid[1], order_quantity))

    asyncio.create_task(order_check(client, symbol, grid, order_quantity))
    await user

asyncio.run(main())