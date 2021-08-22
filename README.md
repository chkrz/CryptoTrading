# CryptoTrading

基于binance api的策略开发

[biance api doc](https://binance-docs.github.io/apidocs/spot/en/#change-log)

[python-binance](https://python-binance.readthedocs.io/en/latest/)

## GridTrading.py

网格交易实现，填入api_key/api_secret/log_path后应该可以运行

order_check

轮询判断订单状态，防止没有收到订单状态更新的回报

user_listener

 接收订单状态回报

spot_create_order/spot_cancel_order

下单/撤单

## CBT

正在开发中的策略结构

诸如下单撤单等的逻辑基本各个策略都是一致的。目标是通过定义基本的父类，以及父类之间互相调用的关系，在后续具体策略开发时只需要定义子类并继承/实现父类的方法，提高开发效率







