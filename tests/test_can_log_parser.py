from io import StringIO

from can_log_parser import CanFrame, export_csv, parse_line, parse_log


def test_parse_compact_candump_frame():
    frame = parse_line("(1787373476.892516) vcan0 123#11223344")

    assert frame == CanFrame(can_id="123", dlc=4, data="11 22 33 44")


def test_invalid_frames_are_skipped_and_reported():
    errors = StringIO()
    frames = parse_log(
        ["vcan0 123#0102\n", "not a frame\n", "vcan0 124 [2] AA\n"],
        error_stream=errors,
    )

    assert frames == [CanFrame(can_id="123", dlc=2, data="01 02")]
    assert "line 2: unsupported CAN frame format" in errors.getvalue()
    assert "line 3: DLC does not match" in errors.getvalue()


def test_export_csv_includes_id_dlc_and_data():
    output = StringIO()
    export_csv([CanFrame("1ABCDE", 3, "AA BB CC")], output)

    assert output.getvalue() == "ID,DLC,DATA\n1ABCDE,3,AA BB CC\n"
