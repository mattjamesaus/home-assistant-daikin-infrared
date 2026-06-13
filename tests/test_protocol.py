from custom_components.daikin_infrared.protocol import (
    BIT_MARK,
    DAIKIN_ARC_PRE_MARK,
    DAIKIN_ARC_PRE_SPACE,
    HEADER_MARK,
    HEADER_SPACE,
    MESSAGE_SPACE,
    DaikinClimateState,
    build_arc_frames,
    build_arc_timings,
)


def test_cool_state_builds_arc_header_and_state_checksum():
    frames = build_arc_frames(
        DaikinClimateState(
            hvac_mode="cool",
            target_temperature=23.5,
            fan_mode="auto",
            swing_mode="off",
        )
    )

    assert frames.header == bytes(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x02,
            0xD0,
            0x02,
            0x03,
            0x80,
            0x03,
            0x82,
            0x30,
            0x41,
            0x1F,
            0x82,
            0xF4,
            0x00,
            0x24,
            0x00,
            0x18,
        ]
    )
    assert frames.state == bytes(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x00,
            0x39,
            0x2F,
            0x00,
            0xA0,
            0x00,
            0x00,
            0x06,
            0x60,
            0x00,
            0x0A,
            0xC4,
            0x80,
            0x24,
            0xF2,
        ]
    )


def test_off_state_clears_power_mode_but_keeps_target_temperature():
    frames = build_arc_frames(
        DaikinClimateState(
            hvac_mode="off",
            target_temperature=25,
            fan_mode="medium",
            swing_mode="vertical",
        )
    )

    assert frames.state[5] == 0x08
    assert frames.state[6] == 0x32
    assert frames.state[8] == 0x5F
    assert frames.state[-1] == sum(frames.state[:-1]) & 0xFF


def test_dry_and_fan_only_use_daikin_special_temperature_bytes():
    dry = build_arc_frames(DaikinClimateState(hvac_mode="dry")).state
    fan_only = build_arc_frames(DaikinClimateState(hvac_mode="fan_only")).state

    assert dry[5] == 0x29
    assert dry[6] == 0xC0
    assert fan_only[5] == 0x69
    assert fan_only[6] == 0x32


def test_fan_and_swing_modes_are_encoded_in_state_bytes():
    frames = build_arc_frames(
        DaikinClimateState(
            hvac_mode="heat",
            target_temperature=21,
            fan_mode="high",
            swing_mode="both",
        )
    )

    assert frames.state[5] == 0x49
    assert frames.state[8] == 0x7F
    assert frames.state[9] == 0x0F
    assert frames.state[-1] == sum(frames.state[:-1]) & 0xFF


def test_timings_are_signed_microseconds_for_home_assistant_infrared():
    timings = build_arc_timings(DaikinClimateState(hvac_mode="cool"))

    assert timings[:4] == [
        DAIKIN_ARC_PRE_MARK,
        -DAIKIN_ARC_PRE_SPACE,
        HEADER_MARK,
        -HEADER_SPACE,
    ]
    assert timings[-1] == BIT_MARK
    assert all(timing != 0 for timing in timings)
    assert MESSAGE_SPACE * -1 in timings

    byte_count = 20 + 19
    expected_count = 2 + 2 + (20 * 16) + 1 + 1 + 2 + (19 * 16) + 1
    assert len(timings) == expected_count
    assert byte_count == 39
