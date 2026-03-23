# Step 3: COMPLETE ETH Trading Environment (self-contained)
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

# MINI Data Fetch (self-contained)
def get_eth_data():
    print("📊 Fetching fresh ETH data...")
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
    params = {"vs_currency": "usd", "days": "90"}  # Max hourly allowed
    data = requests.get(url, params=params).json()
    
    prices = np.array([p[1] for p in data['prices']])
    volumes = np.array([v[1] for v in data['total_volumes']])
    
    df = pd.DataFrame({
        'price': prices,
        'volume': volumes,
        'return': np.append([0], np.diff(prices)/prices[:-1]),
        'ma_short': pd.Series(prices).rolling(10).mean(),
        'ma_long': pd.Series(prices).rolling(50).mean()
    }).dropna().reset_index(drop=True)
    
    print(f"✅ Data ready: {len(df)} hourly candles")
    return df

# Get fresh data
df = get_eth_data()

# Trading Environment Class
class ETHTradingEnv(gym.Env):
    def __init__(self, df, initial_capital=1000, risk_mult=0.7, max_steps=500):
        super(ETHTradingEnv, self).__init__()
        self.df = df.reset_index(drop=True)
        self.initial_capital = initial_capital
        self.risk_mult = risk_mult
        self.max_steps = max_steps
        
        self.current_step = 0
        self.capital = initial_capital
        self.position = 0
        self.net_worth = initial_capital
        self.prev_nw = initial_capital
        
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(9,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
    
    def reset(self):
        self.current_step = 50
        self.capital = self.initial_capital
        self.position = 0
        self.net_worth = self.initial_capital
        self.prev_nw = self.initial_capital
        return self._get_obs()
    
    def _get_obs(self):
        row = self.df.iloc[self.current_step]
        price_norm = row['price'] / 5000
        pos_norm = (self.position * row['price']) / self.initial_capital
        cap_norm = self.capital / self.initial_capital
        nw_norm = self.net_worth / self.initial_capital
        step_norm = self.current_step / self.max_steps
        
        return np.array([
            price_norm, row['return'], row['ma_short']/5000, row['ma_long']/5000,
            pos_norm, cap_norm, nw_norm, float(self.risk_mult), step_norm
        ], dtype=np.float32)
    
    def step(self, action):
        current_price = self.df.iloc[self.current_step]['price']
        action = np.clip(action[0], -1, 1)
        
        trade_size = abs(action) * self.capital * 0.05 * self.risk_mult
        
        if action > 0.1 and self.capital > trade_size:
            eth_bought = trade_size / current_price
            self.position += eth_bought
            self.capital -= trade_size
        elif action < -0.1 and self.position > 0:
            eth_sold = min(trade_size / current_price, self.position)
            self.position -= eth_sold
            self.capital += eth_sold * current_price
        
        self.current_step += 1
        done = self.current_step >= self.max_steps or self.net_worth < 10
        
        next_price = self.df.iloc[min(self.current_step, len(self.df)-1)]['price']
        self.net_worth = self.capital + self.position * next_price
        
        portfolio_return = (self.net_worth - self.prev_nw) / self.prev_nw
        self.prev_nw = self.net_worth
        
        reward = portfolio_return * self.risk_mult - abs(action) * 0.001
        reward = np.clip(reward, -0.5, 0.5)
        
        return self._get_obs(), reward, done, {'net_worth': self.net_worth}

# Test it!
print("🧪 Testing Complete Environment...")
env = ETHTradingEnv(df, risk_mult=0.7)
obs = env.reset()
print("✅ Environment ready!")
print("State shape:", obs.shape)
print("Sample state:", obs[:4])

# Quick random test
total_reward = 0
for step in range(50):
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
    total_reward += reward
    if done: break

print(f"✅ Test complete: Reward={total_reward:.3f}, Final NW=${info['net_worth']:.0f}")
