class SimulationWallet:

    def __init__(self):
        self.usd_balance = 10000
        self.eth_balance = 0
        self.last_buy_price = None

    def buy_eth(self, price, usd_amount):

        if usd_amount > self.usd_balance:
            print("Not enough USD")
            return 0

        eth_bought = usd_amount / price

        self.usd_balance -= usd_amount
        self.eth_balance += eth_bought

        self.last_buy_price = price

        print(f"BOUGHT {eth_bought:.6f} ETH at ${price}")

        return 0   # reward neutral

    def sell_eth(self, price, eth_amount):

        if eth_amount > self.eth_balance:
            print("Not enough ETH")
            return 0

        usd_received = eth_amount * price

        self.eth_balance -= eth_amount
        self.usd_balance += usd_received

        reward = 0

        if self.last_buy_price:
            reward = price - self.last_buy_price

        print(f"SOLD {eth_amount:.6f} ETH at ${price}")
        print("Reward:", reward)

        return reward

    def status(self):

        print("USD Balance:", self.usd_balance)
        print("ETH Balance:", self.eth_balance)