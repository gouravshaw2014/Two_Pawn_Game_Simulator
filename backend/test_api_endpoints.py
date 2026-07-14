#!/usr/bin/env python3
"""
Simple test script to verify AI API endpoints are working.
Run this after starting the server: python -m uvicorn backend.server:app --reload

Usage:
    python test_api_endpoints.py
"""

import requests
import json
import time
from typing import Dict, Any, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 5

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_section(title: str):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'='*60}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{title}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'='*60}{bcolors.ENDC}\n")

def print_success(message: str):
    print(f"{bcolors.OKGREEN}✓ {message}{bcolors.ENDC}")

def print_error(message: str):
    print(f"{bcolors.FAIL}✗ {message}{bcolors.ENDC}")

def print_info(message: str):
    print(f"{bcolors.OKCYAN}ℹ {message}{bcolors.ENDC}")

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Tuple[bool, Any]:
    """Make HTTP request and return (success, response_data)"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        if response.status_code < 300:
            return True, response.json()
        else:
            return False, response.json() if response.content else {"error": response.status_code}
    
    except requests.exceptions.ConnectionError:
        return False, {"error": "Connection refused - is server running?"}
    except requests.exceptions.Timeout:
        return False, {"error": "Request timeout"}
    except Exception as e:
        return False, {"error": str(e)}

def test_ai_status():
    """Test 1: GET /ai/status"""
    print_section("Test 1: GET /ai/status")
    
    success, response = make_request("GET", "/ai/status")
    
    if success:
        print_success("Request successful")
        print_info(f"Response: {json.dumps(response, indent=2)}")
        return True
    else:
        print_error(f"Request failed: {response}")
        return False

def test_ai_init():
    """Test 2: POST /ai/init"""
    print_section("Test 2: POST /ai/init")
    
    payload = {
        "model_path": "ML/models/data_iter100000/pawn_outcome_model.joblib",
        "strategy": "greedy",
        "enable": True
    }
    
    print_info(f"Request body: {json.dumps(payload, indent=2)}")
    success, response = make_request("POST", "/ai/init", payload)
    
    if success:
        print_success("Request successful")
        print_info(f"Response: {json.dumps(response, indent=2)}")
        return True
    else:
        print_error(f"Request failed: {response}")
        return False

def test_ai_suggest():
    """Test 3: POST /ai/suggest"""
    print_section("Test 3: POST /ai/suggest")
    
    payload = {}
    
    print_info("Requesting AI suggestion...")
    success, response = make_request("POST", "/ai/suggest", payload)
    
    if success:
        print_success("Request successful")
        print_info(f"Suggested action: {response.get('action')}")
        print_info(f"Win probability: {response.get('win_probability', 'N/A'):.1%}")
        
        if "evaluations" in response:
            print_info(f"Evaluations: {len(response['evaluations'])} actions evaluated")
            for eval in response["evaluations"][:3]:  # Show top 3
                print(f"  - {eval['action']}: {eval['win_probability']:.1%}")
        
        return True
    else:
        print_error(f"Request failed: {response}")
        return False

def test_ai_evaluate():
    """Test 4: POST /ai/evaluate"""
    print_section("Test 4: POST /ai/evaluate")
    
    payload = {}
    
    print_info("Evaluating all possible actions...")
    success, response = make_request("POST", "/ai/evaluate", payload)
    
    if success:
        print_success("Request successful")
        print_info(f"Total actions: {response.get('total_actions', 'N/A')}")
        
        if "evaluations" in response:
            print_info("All evaluations:")
            for i, eval in enumerate(response["evaluations"], 1):
                print(f"  {i}. {eval['action']}: {eval['win_probability']:.1%} (rank {eval.get('rank', 'N/A')})")
        
        best = response.get('best_action')
        if best:
            print_info(f"Best action: {best['action']} ({best['win_probability']:.1%})")
        
        return True
    else:
        print_error(f"Request failed: {response}")
        return False

def test_ai_strategy():
    """Test 5: POST /ai/strategy"""
    print_section("Test 5: POST /ai/strategy")
    
    strategies_to_test = [
        ("greedy", {}),
        ("explore", {"temperature": 1.5}),
        ("epsilon-greedy", {"epsilon": 0.1}),
    ]
    
    all_success = True
    for strategy_name, params in strategies_to_test:
        payload = {"strategy": strategy_name, **params}
        print_info(f"Testing strategy: {strategy_name}")
        
        success, response = make_request("POST", "/ai/strategy", payload)
        
        if success:
            print_success(f"  ✓ {strategy_name} set successfully")
        else:
            print_error(f"  ✗ Failed to set {strategy_name}: {response}")
            all_success = False
    
    return all_success

def test_ai_enable():
    """Test 6: POST /ai/enable"""
    print_section("Test 6: POST /ai/enable")
    
    # Disable
    print_info("Disabling AI...")
    success1, response1 = make_request("POST", "/ai/enable", {"enabled": False})
    
    if success1:
        print_success(f"AI disabled: {response1.get('enabled')}")
    else:
        print_error(f"Failed to disable: {response1}")
    
    # Enable
    time.sleep(0.5)
    print_info("Enabling AI...")
    success2, response2 = make_request("POST", "/ai/enable", {"enabled": True})
    
    if success2:
        print_success(f"AI enabled: {response2.get('enabled')}")
    else:
        print_error(f"Failed to enable: {response2}")
    
    return success1 and success2

def test_models_available():
    """Test 7: GET /ai/models/available"""
    print_section("Test 7: GET /ai/models/available")
    
    success, response = make_request("GET", "/ai/models/available")
    
    if success:
        print_success("Request successful")
        models = response.get('models', [])
        print_info(f"Available models: {len(models)}")
        
        for model in models:
            print(f"  - {model.get('name')}: {model.get('path')}")
        
        return True
    else:
        print_error(f"Request failed: {response}")
        return False

def test_strategies_available():
    """Test 8: GET /ai/strategies/available"""
    print_section("Test 8: GET /ai/strategies/available")
    
    success, response = make_request("GET", "/ai/strategies/available")
    
    if success:
        print_success("Request successful")
        strategies = response
        print_info(f"Available strategies: {len(strategies)}")
        
        for key, strategy in strategies.items():
            print(f"  - {strategy.get('name')}: {strategy.get('description')}")
        
        return True
    else:
        print_error(f"Request failed: {response}")
        return False

def main():
    """Run all tests"""
    print(f"\n{bcolors.BOLD}AI API Endpoint Test Suite{bcolors.ENDC}")
    print(f"Testing against: {BASE_URL}\n")
    
    # Check if server is running
    print_info("Checking server connection...")
    success, _ = make_request("GET", "/ai/status")
    if not success:
        print_error("Cannot connect to server. Make sure it's running:")
        print(f"{bcolors.WARNING}  python -m uvicorn backend.server:app --reload{bcolors.ENDC}")
        return
    
    print_success("Server is running!\n")
    
    # Run tests
    results = {
        "GET /ai/status": test_ai_status(),
        "GET /ai/models/available": test_models_available(),
        "GET /ai/strategies/available": test_strategies_available(),
        "POST /ai/init": test_ai_init(),
        "POST /ai/suggest": test_ai_suggest(),
        "POST /ai/evaluate": test_ai_evaluate(),
        "POST /ai/strategy": test_ai_strategy(),
        "POST /ai/enable": test_ai_enable(),
    }
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for endpoint, result in results.items():
        status = f"{bcolors.OKGREEN}PASS{bcolors.ENDC}" if result else f"{bcolors.FAIL}FAIL{bcolors.ENDC}"
        print(f"  {endpoint:<40} {status}")
    
    print(f"\n{bcolors.BOLD}Results: {passed}/{total} tests passed{bcolors.ENDC}\n")
    
    if passed == total:
        print(f"{bcolors.OKGREEN}{bcolors.BOLD}All tests passed! ✓{bcolors.ENDC}\n")
    else:
        print(f"{bcolors.WARNING}Some tests failed. Check output above.{bcolors.ENDC}\n")

if __name__ == "__main__":
    main()
