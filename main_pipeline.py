"""
main_pipeline.py
Test runner for the Scraper & Validator pipeline layer
"""

from validator import SentinelValidator

def run_pipeline_test():
    # 1. Define schema requirements for your target data
    schema_contract = {
        "title": str,
        "price": (int, float),
        "rating": (int, float),
        "availability": str
    }

    validator = SentinelValidator(expected_schema=schema_contract)

    print("\n==============================")
    print("TEST 1: Normal Page Layout (Healthy)")
    print("==============================")
    mock_live_data_green = {
        "title": "Quantum AI Development Board",
        "price": 129.99,
        "rating": 4.8,
        "availability": "In Stock"
    }

    score, status, errors = validator.validate_data(mock_live_data_green)
    print(f"Sentinel Health Score : {score}%")
    print(f"Trust Gate Status     : {status} (Green = Safe for AI)")
    print(f"Validation Errors     : {errors if errors else 'None'}")

    print("\n==============================")
    print("TEST 2: Broken Page Layout (Site Redesign Simulation)")
    print("==============================")
    # Simulating a layout break where price is missing and rating is corrupted text
    mock_live_data_red = {
        "title": "Quantum AI Development Board",
        "price": None, 
        "rating": "Error 404 Layout Shift", 
        "availability": "In Stock"
    }

    score, status, errors = validator.validate_data(mock_live_data_red)
    print(f"Sentinel Health Score : {score}%")
    print(f"Trust Gate Status     : {status} (Red = Blocked, Trigger Self-Healing)")
    print(f"Validation Errors     : {errors}")
    print("Action Triggered      : Bright Data Scraper Studio self-heal loop activated.")

if __name__ == "__main__":
    run_pipeline_test()
