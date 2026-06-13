from broadlink.remote import pulses_to_data

from tools.decode_broadlink_capture import decode_packet


def test_decode_packet_parses_daikin_blocks():
    pulses = []
    pulses.append(520)
    for _ in range(5):
        pulses.extend([360, 520])
    pulses.append(26800)

    for length in (8, 8, 19):
        pulses.extend([3360, 1760, 520])
        for byte in [0] * length:
            for bit in range(8):
                pulses.append(1370 if byte & (1 << bit) else 360)
                pulses.append(520)
        if length != 19:
            pulses.append(37150)

    decoded_pulses, blocks = decode_packet(pulses_to_data(pulses))

    assert len(decoded_pulses) == len(pulses)
    assert [len(block) for block in blocks] == [8, 8, 19]
    assert blocks[0] == [0] * 8
    assert blocks[1] == [0] * 8
    assert blocks[2] == [0] * 19

