from custom_components.daikin_infrared.protocol import (
    BIT_MARK,
    HEADER_MARK,
    HEADER_SPACE,
    MESSAGE_SPACE,
    DaikinClimateState,
    build_daikin_frames,
    build_daikin_timings,
)


def test_cool_state_builds_three_daikin_frames_and_checksum():
    frames = build_daikin_frames(
        DaikinClimateState(
            hvac_mode="cool",
            target_temperature=23,
            fan_mode="speed_1",
            swing_mode="off",
        )
    )

    assert frames.frame1 == bytes([0x11, 0xDA, 0x27, 0x00, 0xC5, 0x10, 0x00, 0xE7])
    assert frames.frame2 == bytes([0x11, 0xDA, 0x27, 0x00, 0x42, 0xE1, 0x32, 0x67])
    assert frames.frame3 == bytes(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x00,
            0x39,
            0x2E,
            0x00,
            0x30,
            0x00,
            0x00,
            0x06,
            0x60,
            0x00,
            0x00,
            0xC1,
            0x80,
            0x00,
            0x50,
        ]
    )


def test_off_state_clears_power_bit_but_keeps_last_active_mode():
    frames = build_daikin_frames(
        DaikinClimateState(
            hvac_mode="heat",
            power_on=False,
            target_temperature=25,
            fan_mode="speed_1",
            swing_mode="vertical",
        )
    )

    assert frames.frame3[5] == 0x48
    assert frames.frame3[6] == 0x32
    assert frames.frame3[8] == 0x3F
    assert frames.frame3[-1] == sum(frames.frame3[:-1]) & 0xFF


def test_dry_and_fan_only_use_daikin_special_temperature_bytes():
    dry = build_daikin_frames(DaikinClimateState(hvac_mode="dry")).frame3
    fan_only = build_daikin_frames(DaikinClimateState(hvac_mode="fan_only")).frame3

    assert dry[5] == 0x29
    assert dry[6] == 0xC0
    assert fan_only[5] == 0x69
    assert fan_only[6] == 0x32


def test_fan_and_swing_modes_are_encoded_in_state_bytes():
    frames = build_daikin_frames(
        DaikinClimateState(
            hvac_mode="heat",
            target_temperature=21,
            fan_mode="speed_5",
            swing_mode="both",
        )
    )

    assert frames.frame3[5] == 0x49
    assert frames.frame3[8] == 0x7F
    assert frames.frame3[9] == 0x0F
    assert frames.frame3[-1] == sum(frames.frame3[:-1]) & 0xFF


def test_remote_native_fan_modes_match_arc466_values():
    expected_fan_bytes = {
        "speed_1": 0x30,
        "speed_2": 0x40,
        "speed_3": 0x50,
        "speed_4": 0x60,
        "speed_5": 0x70,
        "auto": 0xA0,
        "quiet": 0xB0,
    }

    for fan_mode, expected_byte in expected_fan_bytes.items():
        frames = build_daikin_frames(DaikinClimateState(fan_mode=fan_mode))

        assert frames.frame3[8] == expected_byte
        assert frames.frame3[-1] == sum(frames.frame3[:-1]) & 0xFF


def test_timings_are_signed_microseconds_for_home_assistant_infrared():
    timings = build_daikin_timings(DaikinClimateState(hvac_mode="cool"))

    assert timings[:12] == [
        BIT_MARK,
        -460,
        BIT_MARK,
        -460,
        BIT_MARK,
        -460,
        BIT_MARK,
        -460,
        BIT_MARK,
        -460,
        BIT_MARK,
        -26400,
    ]
    assert timings[12:15] == [HEADER_MARK, -HEADER_SPACE, BIT_MARK]
    assert timings[-1] == -109500
    assert all(timing != 0 for timing in timings)
    assert timings.count(-MESSAGE_SPACE) == 2

    byte_count = 8 + 8 + 19
    expected_count = (
        12
        + 2
        + 1
        + (8 * 16)
        + 1
        + 2
        + 1
        + (8 * 16)
        + 1
        + 2
        + 1
        + (19 * 16)
        + 1
    )
    assert len(timings) == expected_count
    assert byte_count == 35
