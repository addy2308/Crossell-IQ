#!/usr/bin/env python3
"""
Load Testing Helper Script
Provides utilities for running different load test scenarios
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_locust_test(
    host: str = "http://localhost:8000",
    users: int = 10,
    spawn_rate: int = 2,
    duration: str = "1m",
    test_type: str = "default",
    headless: bool = False
):
    """
    Run Locust load test
    
    Args:
        host: API host URL
        users: Number of concurrent users
        spawn_rate: Spawn rate (users/sec)
        duration: Test duration (e.g., "1m", "5m", "1h")
        test_type: Type of test (default, stress, endurance)
        headless: Run without web UI
    """
    
    locustfile = Path(__file__).parent / "locustfile.py"
    
    cmd = [
        "locust",
        "-f", str(locustfile),
        "-H", host,
        "-u", str(users),
        "-r", str(spawn_rate),
        "--run-time", duration,
    ]
    
    # Select test class based on type
    if test_type == "stress":
        cmd.extend(["-c", "StressTest"])
    elif test_type == "quick":
        cmd.extend(["-c", "QuickLoadTest"])
    else:
        cmd.extend(["-c", "NetflixAPIUser"])
    
    if headless:
        cmd.append("--headless")
    
    print(f"🚀 Starting Locust load test...")
    print(f"   Host: {host}")
    print(f"   Users: {users}")
    print(f"   Spawn rate: {spawn_rate} users/sec")
    print(f"   Duration: {duration}")
    print(f"   Type: {test_type}")
    print()
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")


def print_test_scenarios():
    """Print available test scenarios"""
    
    scenarios = {
        "Light Load": {
            "users": 5,
            "spawn_rate": 1,
            "duration": "2m",
            "description": "Baseline performance with 5 concurrent users"
        },
        "Moderate Load": {
            "users": 20,
            "spawn_rate": 2,
            "duration": "5m",
            "description": "Normal operating conditions with 20 concurrent users"
        },
        "High Load": {
            "users": 50,
            "spawn_rate": 5,
            "duration": "5m",
            "description": "Peak load simulation with 50 concurrent users"
        },
        "Stress Test": {
            "users": 100,
            "spawn_rate": 10,
            "duration": "3m",
            "description": "Breaking point test with 100 concurrent users"
        },
        "Spike Test": {
            "users": 200,
            "spawn_rate": 50,
            "duration": "2m",
            "description": "Sudden traffic spike with 200 users"
        },
        "Endurance Test": {
            "users": 30,
            "spawn_rate": 3,
            "duration": "30m",
            "description": "Long-running test to check for memory leaks (30 min)"
        }
    }
    
    print("\n" + "="*70)
    print("AVAILABLE LOAD TEST SCENARIOS")
    print("="*70 + "\n")
    
    for i, (name, config) in enumerate(scenarios.items(), 1):
        print(f"{i}. {name}")
        print(f"   Users: {config['users']}")
        print(f"   Spawn Rate: {config['spawn_rate']} users/sec")
        print(f"   Duration: {config['duration']}")
        print(f"   📝 {config['description']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Netflix API Load Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_test_runner.py --host http://localhost:8000 --users 10 --duration 2m
  python load_test_runner.py --scenario "stress" --headless
  python load_test_runner.py --list-scenarios
        """
    )
    
    parser.add_argument(
        "--host",
        default="http://localhost:8000",
        help="API host URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of concurrent users (default: 10)"
    )
    
    parser.add_argument(
        "--spawn-rate",
        type=int,
        default=2,
        help="Spawn rate in users per second (default: 2)"
    )
    
    parser.add_argument(
        "--duration",
        default="1m",
        help="Test duration (default: 1m, examples: 5m, 1h)"
    )
    
    parser.add_argument(
        "--type",
        choices=["default", "stress", "quick"],
        default="default",
        help="Load test type (default: default)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without web UI"
    )
    
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available test scenarios"
    )
    
    parser.add_argument(
        "--scenario",
        choices=["light", "moderate", "high", "stress", "spike", "endurance"],
        help="Run a predefined scenario"
    )
    
    args = parser.parse_args()
    
    if args.list_scenarios:
        print_test_scenarios()
        return
    
    # Handle predefined scenarios
    scenario_config = {
        "light": {"users": 5, "spawn_rate": 1, "duration": "2m"},
        "moderate": {"users": 20, "spawn_rate": 2, "duration": "5m"},
        "high": {"users": 50, "spawn_rate": 5, "duration": "5m"},
        "stress": {"users": 100, "spawn_rate": 10, "duration": "3m"},
        "spike": {"users": 200, "spawn_rate": 50, "duration": "2m"},
        "endurance": {"users": 30, "spawn_rate": 3, "duration": "30m"}
    }
    
    if args.scenario:
        config = scenario_config[args.scenario]
        run_locust_test(
            host=args.host,
            users=config["users"],
            spawn_rate=config["spawn_rate"],
            duration=config["duration"],
            test_type=args.type,
            headless=args.headless or args.scenario in ["stress", "spike", "endurance"]
        )
    else:
        run_locust_test(
            host=args.host,
            users=args.users,
            spawn_rate=args.spawn_rate,
            duration=args.duration,
            test_type=args.type,
            headless=args.headless
        )


if __name__ == "__main__":
    main()
