# from coinbase.rest import RESTClient
# import uuid

# client = RESTClient(api_key=COINBASE_API_KEY, api_secret=settings.COINBASE_API_SECRET)


# def buy_eth(amount_usd):
#     order_id = str(uuid.uuid4())

#     order = client.market_order_buy(
#         client_order_id=order_id,
#         product_id="ETH-USD",
#         quote_size=str(amount_usd)
#     )

#     print("BUY order placed")
#     print(order)