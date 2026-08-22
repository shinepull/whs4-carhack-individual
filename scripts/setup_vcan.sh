#!/usr/bin/env bash
set -e

if ! ip link show vcan0 > /dev/null 2>&1; then
    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
fi

sudo ip link set vcan0 up
ip link show vcan0