import struct
import datetime


def build_waveform_bin(fmax, timestamp, channel_data, num_channels=4, version=1.0):
    
    n_samples = len(channel_data[0])
    for ch in channel_data:
        assert len(ch) == n_samples, "all channels must have the same sample count"  # all channels must be equal length
    assert len(channel_data) == num_channels  # sanity check channel count matches expected

    header = struct.pack(
        ">9f",  # big-endian, 9 floats
        version,
        float(num_channels),
        float(fmax),
        float(timestamp.month),
        float(timestamp.day),
        float(timestamp.year),
        float(timestamp.hour),
        float(timestamp.minute),
        float(timestamp.second),
    )

    # interleave: ch1[0], ch2[0], ch3[0], ch4[0], ch1[1], ch2[1], ...
    interleaved = []
    for i in range(n_samples):
        for ch in channel_data:
            interleaved.append(ch[i])  # build sample-interleaved sequence across channels

    body = struct.pack(f">{len(interleaved)}f", *interleaved)  # pack interleaved samples as big-endian floats

    return header + body  # header + interleaved waveform data


def test_build_waveform_data():

    # quick round-trip smoke test
    n = 1000
    fake_channels = [[float(i) * 0.001 for i in range(n)] for _ in range(4)]
    ts = datetime.datetime(2025, 11, 24, 4, 54, 29)

    raw = build_waveform_bin(40000.0, ts, fake_channels)
    print(f"Built {len(raw)} bytes for {n} samples/channel x 4 channels")
    print(f"Expected: {36 + n * 4 * 4} bytes")

    output_path = r"C:\Users\PCduffy\Projects\CloudPull\waveform.bin"
    with open(output_path, "wb") as f:
        f.write(raw)
    print(f"Wrote {len(raw)} bytes to {output_path}")


if __name__ == "__main__":
    test_build_waveform_data()