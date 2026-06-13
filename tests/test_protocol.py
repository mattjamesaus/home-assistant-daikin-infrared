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
            fan_mode="auto",
            swing_mode="off",
        )
    )

    assert frames.frame1 == bytes([0x11, 0xDA, 0x27, 0x00, 0xC5, 0x00, 0x00, 0xD7])
    assert frames.frame2 == bytes([0x11, 0xDA, 0x27, 0x00, 0x42, 0x49, 0x05, 0xA2])
    assert frames.frame3 == bytes(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x00,
            0x31,
            0x2E,
            0x00,
            0xA0,
            0x00,
            0x00,
            0x06,
            0x60,
            0x00,
            0x00,
            0xC0,
            0x00,
            0x00,
            0x37,
        ]
    )


def test_off_state_clears_power_mode_but_keeps_target_temperature():
    frames = build_daikin_frames(
        DaikinClimateState(
            hvac_mode="off",
            target_temperature=25,
            fan_mode="medium",
            swing_mode="vertical",
        )
    )

    assert frames.frame3[5] == 0x00
    assert frames.frame3[6] == 0x32
    assert frames.frame3[8] == 0x5F
    assert frames.frame3[-1] == sum(frames.frame3[:-1]) & 0xFF


def test_dry_and_fan_only_use_daikin_special_temperature_bytes():
    dry = build_daikin_frames(DaikinClimateState(hvac_mode="dry")).frame3
    fan_only = build_daikin_frames(DaikinClimateState(hvac_mode="fan_only")).frame3

    assert dry[5] == 0x21
    assert dry[6] == 0xC0
    assert fan_only[5] == 0x61
    assert fan_only[6] == 0x32


def test_fan_and_swing_modes_are_encoded_in_state_bytes():
    frames = build_daikin_frames(
        DaikinClimateState(
            hvac_mode="heat",
            target_temperature=21,
            fan_mode="high",
            swing_mode="both",
        )
    )

    assert frames.frame3[5] == 0x41
    assert frames.frame3[8] == 0x7F
    assert frames.frame3[9] == 0x0F
    assert frames.frame3[-1] == sum(frames.frame3[:-1]) & 0xFF


def test_timings_are_signed_microseconds_for_home_assistant_infrared():
    timings = build_daikin_timings(DaikinClimateState(hvac_mode="cool"))

    assert timings[:2] == [HEADER_MARK, -HEADER_SPACE]
    assert timings[-1] == BIT_MARK
    assert all(timing != 0 for timing in timings)
    assert timings.count(-MESSAGE_SPACE) == 2

    byte_count = 8 + 8 + 19
    expected_count = (
        2
        + (8 * 16)
        + 1
        + 1
        + 2
        + (8 * 16)
        + 1
        + 1
        + 2
        + (19 * 16)
        + 1
    )
    assert len(timings) == expected_count
    assert byte_count == 35
