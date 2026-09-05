# NRC State-Aware UDS Fuzzing

A state-aware UDS fuzzing framework guided by Negative Response Code (NRC) feedback.

## CAN log parser

`can_log_parser.py` reads common `candump` text formats, skips malformed frames with
an error on standard error, and writes the valid frame ID, DLC, and data bytes to CSV.

```bash
python can_log_parser.py logs/candump.log frames.csv
```

Supported frame forms include both compact (`vcan0 123#11223344`) and spaced
(`vcan0 123 [4] 11 22 33 44`) candump output.
