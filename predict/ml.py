# ethapp/ml.py
import torch
import torch.nn as nn
import numpy as np
import requests
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64


class LSTMwithANN(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=64, num_layers=1, batch_first=True)
        self.fc1 = nn.Linear(64, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x):
        _, (final_hidden_state, _) = self.lstm(x)
        x = self.fc1(final_hidden_state[-1])
        x = self.relu(x)
        x = self.fc2(x)
        return x


def fetch_eth_data(days=90):
    """Fetch recent Ethereum market data from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
    params = {"vs_currency": "usd", "days": str(days)}
    data = requests.get(url, params=params).json()
    price = [p[1] for p in data["prices"]]
    timestamp = [p[0] for p in data["prices"]]
    return np.array(price).reshape(-1, 1), np.array(timestamp)


def get_eth_advice():
    """Run the trained LSTM model and return ETH advice."""
    device = torch.device("cpu")
    model = LSTMwithANN().to(device)

    saved_model_path = "E:/eth_price_prediction/eth_prediction/predict/eth_model.pth"
    model.load_state_dict(torch.load(saved_model_path, map_location=device))
    model.eval()

    price, timestamp = fetch_eth_data()
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_prices = scaler.fit_transform(price)

    seq_length = 1680
    X_all = [scaled_prices[i:i+seq_length] for i in range(len(scaled_prices) - seq_length)]
    X_test = torch.tensor(np.array(X_all), dtype=torch.float32)

    last_seq = X_test[-1].unsqueeze(0).to(device)
    predicted_next_price = model(last_seq).detach().cpu().numpy()
    predicted_next_price = scaler.inverse_transform(predicted_next_price)

    current_price = price[-1][0]

    # Prepare time info
    # Prepare time info using real Michigan time
    michigan_time = datetime.now(ZoneInfo("America/Detroit"))
    predicted_time = michigan_time + timedelta(hours=1)


    advice = "BUY" if predicted_next_price[0][0] > current_price else "SELL"

    # Prepare data for plotting
    actual_prices_plot = price[seq_length:].flatten()
    predicted_prices_plot = scaler.inverse_transform(model(X_test).detach().cpu().numpy()).flatten()

    actual_prices_with_pred_time = np.append(actual_prices_plot, np.nan)
    predicted_prices_with_pred_time = np.append(predicted_prices_plot, predicted_next_price[0][0])

    plot_timestamps = timestamp[seq_length:]
    next_timestamp = timestamp[-1] + 3600 * 1000
    plot_timestamps = np.append(plot_timestamps, next_timestamp)
    plot_datetimes = [datetime.utcfromtimestamp(ts / 1000).astimezone(ZoneInfo("America/Detroit")) for ts in plot_timestamps]

    # Create the figure
    plt.figure(figsize=(15, 6))
    plt.plot(plot_datetimes, actual_prices_with_pred_time, label="Actual ETH Price")
    plt.plot(plot_datetimes, predicted_prices_with_pred_time, label="Predicted ETH Price")
    plt.scatter(plot_datetimes[-1], predicted_next_price[0][0], color='red', label='Predicted Next Price')
    plt.title("Ethereum Price: Actual vs Predicted")
    plt.xlabel("Time (Michigan)")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(rotation=45)

    # Save plot to memory buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    # Return everything including the plot image
    return {
        "current_price": float(current_price),
        "predicted_price": float(predicted_next_price[0][0]),
        "current_time": michigan_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "predicted_time": predicted_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "advice": advice,
        "plot_image": image_base64,  # ✅ include the chart
    }

