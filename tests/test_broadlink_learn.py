from broadlink.remote import pulses_to_data

from tools.broadlink_learn import learned_packet_summary


def test_learned_packet_summary_decodes_broadlink_packet():
    packet = pulses_to_data([520, 360, 520, 1370, 200000])

    summary = learned_packet_summary(packet)

    assert summary["packet_length"] == len(packet)
    assert summary["pulse_count"] == 5
    assert summary["total_duration_ms"] > 200
    assert summary["first_pulses_us"] == [492, 328, 492, 1346, 199995]
    assert len(summary["packet_sha256"]) == 64
