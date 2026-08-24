import json
import time
from pathlib import Path

import isotp

INTERFACE = "vcan0"
ECU_TX_ID = 0x7E8
TESTER_TX_ID = 0x7E0
LOG_PATH = Path("logs/tester.jsonl")

TEST_CASES = [
    ("extended_session", "10 03"),
    ("tester_present", "3E 00"),
    ("read_vin", "22 F1 90"),
    ("unsupported_service", "99 00"),
]


def write_log(name, request, response):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": time.time(),
        "test_name": name,
        "request_hex": request.hex(" "),
        "response_hex": response.hex(" "),
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def main():
    address = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        rxid=ECU_TX_ID,
        txid=TESTER_TX_ID,
    )

    socket = isotp.socket()
    socket.bind(INTERFACE, address)

    for name, request_hex in TEST_CASES:
        request = bytes.fromhex(request_hex)

        socket.send(request)
        response = socket.recv()

        write_log(name, request, response)

        print(f"[{name}]")
        print(f"  REQ: {request.hex(' ').upper()}")
        print(f"  RES: {response.hex(' ').upper()}")


if __name__ == "__main__":
    main()