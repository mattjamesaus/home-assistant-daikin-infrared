from broadlink.remote import data_to_pulses

from custom_components.daikin_infrared.protocol import DaikinClimateState, build_daikin_timings
from tools.broadlink_send import broadlink_packet_for_state, packet_summary


def test_broadlink_packet_for_state_wraps_generated_timings():
    state = DaikinClimateState(hvac_mode="cool", target_temperature=23, fan_mode="low")

    packet = broadlink_packet_for_state(state)
    pulses = data_to_pulses(packet)

    assert packet[0] == 0x26
    assert len(pulses) == len(build_daikin_timings(state))
    assert pulses[0] > 0
    assert 100000 < pulses[-1] < 120000


def test_packet_summary_reports_packet_shape():
    packet = broadlink_packet_for_state(
        DaikinClimateState(hvac_mode="heat", target_temperature=21, fan_mode="low")
    )

    summary = packet_summary(packet)

    assert summary["packet_length"] > 500
    assert summary["pulse_count"] == 584
    assert summary["total_duration_ms"] > 500
    assert len(summary["packet_sha256"]) == 64
