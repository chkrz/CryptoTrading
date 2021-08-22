from ..Util.DataType import *


class Listener:
    def __init__(self, bm, m_handler):
        self.bm = bm
        self.m_handler = m_handler

    async def user_listener(self):
        async with self.bm.user_socket() as user_stream:
            while True:
                res = await user_stream.recv()
                if res:
                    await self.m_handler.HandleSpotListenerUpdate(res)

    async def future_listener(self, bm, client, m_handler):
        async with self.bm.futures_socket() as future_stream:
            while True:
                res = await future_stream.recv()
                if res:
                    await self.m_handler.HandleFutureListenerUpdate(res)

    async def spot_depth_listener(self, symbol):
        async with self.bm.depth_socket(symbol) as spot_depth:
            while True:
                depth = await spot_depth.recv()
                if depth:
                    await self.m_handler.HandleDepthData(depth=depth, symbol_type=SymbolType.SPOT)

    '''
    async def future_depth(self, symbol):
        async with self.bm.future_depth_socket(symbol) as future_depth:
            while True:
                depth = await future_depth.recv()
                if depth:
                    self.m_handler.HandleDepthData(depth=depth, symbol_type=SymbolType.FUTURE)
             
    '''
    #写一个混合socket 然后自动判断并且调用对应的函数
