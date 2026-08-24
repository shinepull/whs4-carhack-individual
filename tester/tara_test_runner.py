import json
import time
from pathlib import Path

import isotp
import yaml

INTERFACE = "vcan0"
TESTER_TX_ID = 0x7E0
ECU_TX_ID = 0x7E8

POLICY_PATH = Path("policy/tara_to_testcases.yaml")
RESULT_PATH = Path("logs/test-results.json")


def load_testcases():
    with POLICY_PATH.open("r", encoding="utf-8") as file:
        policy = yaml.safe_load(file)

    return policy["testcases"]


def make_socket():
    address = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        rxid=ECU_TX_ID,
        txid=TESTER_TX_ID,
    )

    socket = isotp.socket()
    socket.bind(INTERFACE, address)
    socket.settimeout(2.0)

    return socket


def run_testcase(socket, testcase):
    request = bytes.fromhex(testcase["request"])
    expected = bytes.fromhex(testcase["expected_response_prefix"])

    result = {
        "id": testcase["id"],
        "category": testcase["category"],
        "asset": testcase["asset"],
        "threat_scenario": testcase["threat_scenario"],
        "cybersecurity_goal": testcase["cybersecurity_goal"],
        "request_hex": request.hex(" ").upper(),
        "expected_response_prefix": expected.hex(" ").upper(),
        "timestamp": time.time(),
    }

    try:
        socket.send(request)
        response = socket.recv()

        passed = response.startswith(expected)

        result["actual_response"] = response.hex(" ").upper()
        result["verdict"] = "PASS" if passed else "FAIL"

    except Exception as error:
        result["actual_response"] = None
        result["verdict"] = "ERROR"
        result["error"] = str(error)

    return result


def main():
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    testcases = load_testcases()
    socket = make_socket()

    results = []

    for testcase in testcases:
        result = run_testcase(socket, testcase)
        results.append(result)

        print(f"[{result['id']}] {result['verdict']}")
        print(f"  REQ: {result['request_hex']}")
        print(f"  EXP: {result['expected_response_prefix']}")
        print(f"  ACT: {result['actual_response']}")

    with RESULT_PATH.open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    pass_count = sum(item["verdict"] == "PASS" for item in results)

    print()
    print(f"Summary: {pass_count}/{len(results)} passed")
    print(f"Result file: {RESULT_PATH}")


if __name__ == "__main__":
    main()