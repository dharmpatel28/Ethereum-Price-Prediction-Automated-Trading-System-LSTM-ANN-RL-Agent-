from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from web3 import Web3
from .models import TradingStrategy, Trade
from .trading_engine import get_eth_price
import json
from zoneinfo import ZoneInfo

# =========================
# Web3 / Smart Contract Setup
# =========================
with open("E:/eth_price_prediction/eth_prediction/predict/abi.json") as f:
    abi = json.load(f)

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))  # Ganache
contract = w3.eth.contract(address='0xe2AfAc562f58e44704Eff7A7A1BdB85A7A806859', abi=abi)


def home(request):
    return render(request, "home.html")


# =========================
# ML Prediction Endpoints
# =========================
from .ml import get_eth_advice  # your ML prediction function

def ml_home(request):
    """ML Prediction HTML page"""
    return render(request, "ml.html")

def get_advice(request):
    """Return ML prediction for ETH"""
    eth_address = request.GET.get('address')
    if not eth_address:
        return JsonResponse({"error": "Missing address"}, status=400)
    
    try:
        checksum_address = w3.to_checksum_address(eth_address)
        has_paid = contract.functions.checkHasPaidAdvice(checksum_address).call()
        if not has_paid:
            return JsonResponse({"error": "Pay 0.01 ETH first"}, status=402)
        
        result = get_eth_advice()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

        # Dummy fallback
        # return JsonResponse({
        #     "advice": "BUY",
        #     "current_price": 3524.67,
        #     "predicted_price": 3568.23,
        #     "current_time": "2026-03-15 18:30",
        #     "predicted_time": "2026-03-15 19:30"
        # })

# =========================
# RL Agent Endpoints
# =========================
def rl_home(request):
    """RL Agent HTML page"""
    return render(request, "rl.html")

@csrf_exempt
def enroll_rl_bot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        wallet = data.get('wallet_address')
        agent_enabled = data.get('agent_enabled', True)
        is_active = data.get('is_active', True)

        strategy, created = TradingStrategy.objects.get_or_create(wallet_address=wallet)
        strategy.agent_enabled = agent_enabled
        strategy.is_active = is_active
        strategy.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def get_bot_status(request):
    wallet = request.GET.get('wallet')
    if not wallet:
        return JsonResponse({'error': 'Missing wallet param'}, status=400)
    
    checksum_wallet = Web3.to_checksum_address(wallet)
    strategies = TradingStrategy.objects.filter(wallet_address__iexact=wallet)
    price = get_eth_price()
    
    trades = list(Trade.objects.filter(wallet_address__iexact=wallet).order_by('-created_at')[:5].values(
        'action', 'eth_amount', 'price', 'usd_value', 'created_at'
    ))
    
    strategy_data = []
    for s in strategies:
        strategy_data.append({
            'id': s.id,
            'wallet': s.wallet_address,
            'agent_enabled': s.agent_enabled,
            'is_active': s.is_active,
            'buy_price': float(s.buy_price),
            'sell_price': float(s.sell_price),
            'buy_eth_amount': getattr(s, 'buy_eth_amount', 0),
            'sell_eth_amount': getattr(s, 'sell_eth_amount', 0),
            'eth_amount': getattr(s, 'eth_amount', 0),
            'commission_percent': getattr(s, 'commission_percent', 2),
            'current_price': price,
            'is_trading': len(trades) > 0
        })
    
    return JsonResponse({'strategies': strategy_data, 'recent_trades': trades, 'current_price': price})

@csrf_exempt
def toggle_agent(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet = data.get('wallet_address')
            checksum_wallet = Web3.to_checksum_address(wallet)
            
            strategy = TradingStrategy.objects.filter(wallet_address__iexact=wallet).first()
            if not strategy:
                return JsonResponse({'error': 'No strategy found'}, status=404)
            
            strategy.agent_enabled = not strategy.agent_enabled
            strategy.save()
            
            return JsonResponse({'success': True, 'agent_enabled': strategy.agent_enabled})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def update_strategy(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            strategy_id = data.get("strategy_id")
            if not strategy_id:
                return JsonResponse({'success': False, 'error': 'Missing strategy_id'})

            strategy = TradingStrategy.objects.get(id=strategy_id)

            # Optional safety: verify wallet ownership
            wallet = str(data.get('wallet_address', '')).lower()
            if strategy.wallet_address.lower() != wallet:
                return JsonResponse({'success': False, 'error': 'Unauthorized wallet'})

            # Update values
            if data.get('buy_price') is not None:
                strategy.buy_price = data['buy_price']

            if data.get('sell_price') is not None:
                strategy.sell_price = data['sell_price']

            strategy.save()

            return JsonResponse({
                'success': True,
                'buy_price': strategy.buy_price,
                'sell_price': strategy.sell_price
            })

        except TradingStrategy.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Strategy not found'}, status=404)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
def create_full_strategy(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet = Web3.to_checksum_address(data['wallet_address'])
            
            strategy = TradingStrategy.objects.create(
                wallet_address=wallet,
                buy_price=data['buy_price'],
                sell_price=data['sell_price'],
                buy_eth_amount=data['buy_eth_amount'],
                sell_eth_amount=data['sell_eth_amount'],
                eth_amount=data['eth_amount'],
                commission_percent=data['commission_percent'],
                agent_enabled=True,
                is_active=True
            )
            
            return JsonResponse({'success': True, 'id': strategy.id, 'wallet': wallet[:10]+'...'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def delete_strategy(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            wallet = str(data.get("wallet_address", "")).lower()
            strategy_id = int(data.get("strategy_id"))

            strategy = TradingStrategy.objects.filter(id=strategy_id).first()

            if not strategy:
                return JsonResponse({"success": False, "error": "Strategy not found"})

            if strategy.wallet_address.lower() != wallet:
                return JsonResponse({"success": False, "error": "Wrong wallet"})

            strategy.delete()
            return JsonResponse({"success": True})
        
            print("RAW BODY:", request.body)
            print("PARSED:", data)

        except Exception as e:
            print("❌ ERROR:", str(e))
            return JsonResponse({"success": False, "error": str(e)})
@csrf_exempt
def api_recent_trades(request):
    wallet = request.GET.get('wallet')
    trades = Trade.objects.filter(wallet_address__iexact=wallet).order_by('-created_at')[:20]
    michigan_tz = ZoneInfo("America/Detroit")
    
    trade_data = []
    for t in trades:
        trade_data.append({
            'action': t.action,
            'eth_amount': float(t.eth_amount),
            'price': float(t.price),
            'usd_value': float(t.usd_value),
            'created_at': t.created_at.astimezone(michigan_tz).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({'trades': trade_data})