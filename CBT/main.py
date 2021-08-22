import asyncio
from time import *

from CryptoBinanceTrading import *

from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException
from binance.enums import *


async def main():
    api_key = ''
    api_secret = ''
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)
    bm = BinanceSocketManager(client, user_timeout=60)

    order_quantity = 0.015
    symbol = "ETHBUSD"
    center = 2245
    step = 3
    net = 130  # 负数代表买入了一些

    hub = FHub()
    hub.AddSymbol(symbol)
    grid = Grid(center=center, step=step, n_step=300, net=net)
    gt = GridTrading(policyId=0, m_handler=hub, grid=grid, order_quantity=order_quantity, symbol=symbol)
    hub.AddFPolicy(gt)
    spot_handler = SpotHandler(hub, client)
    hub.AddSpotHandler(spot_handler)

    log_path = "C:/Users/caihu/Desktop/"
    logging.basicConfig(level=logging.DEBUG,
                        filename=log_path + "GridTradingBull.log",
                        filemode='a+',
                        format='%(asctime)s - %(levelname)s: %(message)s'
                        )

    listener = Listener(bm, hub)
    user = asyncio.create_task(listener.user_listener())
    await asyncio.sleep(3)

    await gt.Start()
    await user

asyncio.run(main())