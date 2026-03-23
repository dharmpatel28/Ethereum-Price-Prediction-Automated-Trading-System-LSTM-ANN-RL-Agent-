from coinbase.rest import RESTClient
from django.conf import settings
from .models import TradingStrategy

from predict.simulation_wallet import SimulationWallet
wallet = SimulationWallet()

from .rl_agent import load_agent, build_state, agent_decision, action_name
agent_model = load_agent()

from .models import Trade
from .rl_agent import train_step

client = RESTClient(
    api_key=settings.COINBASE_API_KEY,
    api_secret=settings.COINBASE_API_SECRET
)


def get_eth_price():
    product = client.get_product("ETH-USD")
    return float(product["price"])


def check_strategies():
    price = get_eth_price()
    print("Current ETH price:", price)

    strategies = TradingStrategy.objects.filter(is_active=True)

    for s in strategies:
        print("\nChecking strategy for:", s.wallet_address)

        # ========= RULE-BASED BUY / SELL FIRST =========
        if price <= s.buy_price:
            # BUY
            if wallet.usd_balance >= s.buy_eth_amount * price:
                usd_amount = s.buy_eth_amount * price
                wallet.buy_eth(price, usd_amount)
                print(f"Rule BUY: {s.buy_eth_amount} ETH at ${price}")
                Trade.objects.create(
                    wallet_address=s.wallet_address,
                    action="BUY",
                    price=price,
                    eth_amount=s.buy_eth_amount,
                    usd_value=usd_amount
                )
            else:
                print("Not enough USD for rule BUY")
            continue  # skip RL for this strategy in this cycle

        if price >= s.sell_price:
            # SELL
            if wallet.eth_balance >= s.sell_eth_amount:
                usd_value = s.sell_eth_amount * price
                wallet.sell_eth(price, s.sell_eth_amount)
                print(f"Rule SELL: {s.sell_eth_amount} ETH at ${price}")
                Trade.objects.create(
                    wallet_address=s.wallet_address,
                    action="SELL",
                    price=price,
                    eth_amount=s.sell_eth_amount,
                    usd_value=usd_value
                )
            else:
                print("Not enough ETH for rule SELL")
            continue  # skip RL for this strategy in this cycle

        # ========= RL-BASED DECISION (ONLY IF NO RULE FIRED) =========
        if s.agent_enabled:
            momentum = price - (price - 5)
            volatility = 2
            rsi = 50
            ma = price - 3

            state = build_state(
                price,
                momentum,
                volatility,
                rsi,
                ma,
                s.buy_price
            )

            action = agent_decision(agent_model, state)
            print("Action value:", action)
            decision = action_name(action)
            print("Decision:", decision)
            print("RL decision:", decision)

            if decision == "BUY":
                if wallet.usd_balance >= s.buy_eth_amount * price:
                    usd_amount = s.buy_eth_amount * price
                    wallet.buy_eth(price, usd_amount)
                    print(f"RL BUY: {s.buy_eth_amount} ETH at ${price}")
                    Trade.objects.create(
                        wallet_address=s.wallet_address,
                        action="BUY",
                        price=price,
                        eth_amount=s.buy_eth_amount,
                        usd_value=usd_amount
                    )
                else:
                    print("Not enough USD for RL BUY")

            elif decision == "SELL":
                if wallet.eth_balance >= s.sell_eth_amount:
                    usd_value = s.sell_eth_amount * price
                    wallet.sell_eth(price, s.sell_eth_amount)
                    print(f"RL SELL: {s.sell_eth_amount} ETH at ${price}")
                    Trade.objects.create(
                        wallet_address=s.wallet_address,
                        action="SELL",
                        price=price,
                        eth_amount=s.sell_eth_amount,
                        usd_value=usd_value
                    )
                else:
                    print("Not enough ETH for RL SELL")

            else:
                print("HOLD for", s.wallet_address)
        else:
            print("Agent disabled; HOLD for", s.wallet_address)
