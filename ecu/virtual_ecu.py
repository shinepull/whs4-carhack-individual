import json
import time
from pathlib import Path

import isotp

INTERFACE = "vcan0"
TESTER_TX_ID = 0x7E0
ECU_TX_ID = 0x7E8
LOG_PATH = Path("logs/ecu.jsonl")


def write_log(event, payload):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": time.time(),
        "event": event,
        "payload_hex": payload.hex(" "),
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def handle_request(request):
    if request == bytes.fromhex("10 03"):
        return bytes.fromhex("50 03 00 32 01 F4")

    if request == bytes.fromhex("3E 00"):
        return bytes.fromhex("7E 00")

    if request == bytes.fromhex("22 F1 90"):
        return bytes.fromhex("62 F1 90") + b"TESTVIN123456789"

    service_id = request[0] if request else 0x00
    return bytes([0x7F, service_id, 0x11])


def main():
    address = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        rxid=TESTER_TX_ID,
        txid=ECU_TX_ID,
    )

    socket = isotp.socket()
    socket.bind(INTERFACE, address)

    print(
        f"Virtual ECU started: RX=0x{TESTER_TX_ID:03X}, "
        f"TX=0x{ECU_TX_ID:03X}, interface={INTERFACE}"
    )

    while True:
        request = socket.recv()
        write_log("request", request)

        response = handle_request(request)
        socket.send(response)
        write_log("response", response)

        print(
            f"REQ: {request.hex(' ').upper()} "
            f"-> RES: {response.hex(' ').upper()}"
        )


if __name__ == "__main__":
    main()