import time
import django
import os
import sys

# Add project root to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eth_prediction.settings")

django.setup()

from predict.trading_engine import check_strategies


def run_bot():

    print("Auto Trading Bot Started")

    while True:

        try:

            print("Running strategy check...")

            check_strategies()

        except Exception as e:

            print("Error:", e)

        print("Waiting 30 seconds...\n")

        time.sleep(30)


if __name__ == "__main__":
    run_bot()