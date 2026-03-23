import torch
import torch.nn as nn

import torch.optim as optim


# Neural Network
class TradingAgent(nn.Module):

    def __init__(self):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(6, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 3)
        )

    def forward(self, x):
        return self.net(x)


# Load model
def load_agent():

    model = TradingAgent()

    try:
        model.load_state_dict(torch.load("predict/rl_agent.pth"))
        print("RL model loaded successfully")
    except Exception as e:
        print("RL model not trained yet:", e)

    model.eval()

    return model


# Build state for agent
def build_state(price, momentum, volatility, rsi, ma, user_price):

    price = price / 10000
    momentum = momentum / 100
    volatility = volatility / 10
    rsi = rsi / 100
    ma = ma / 10000
    user_price = user_price / 10000

    return torch.tensor([
        price,
        momentum,
        volatility,
        rsi,
        ma,
        user_price
    ], dtype=torch.float32)


# Agent decision
def agent_decision(model, state):

    with torch.no_grad():

        output = model(state)

    action = torch.argmax(output).item()

    return action


# Convert action to text
def action_name(action):

    if action == 0:
        return "HOLD"

    elif action == 1:
        return "BUY"

    elif action == 2:
        return "SELL"
    
optimizer = optim.Adam

def train_step(model, state, action, reward):

    state = state.unsqueeze(0)

    output = model(state)

    target = output.clone().detach()

    target[0][action] = reward

    loss = nn.MSELoss()(output, target)

    model.zero_grad()
    loss.backward()

    for param in model.parameters():
        param.data -= 0.001 * param.grad

    torch.save(model.state_dict(), "predict/rl_agent.pth")