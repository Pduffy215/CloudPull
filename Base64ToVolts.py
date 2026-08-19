import base64
import struct

INT32_MIN = -2147483648
INT32_MAX = 2147483647
INT32_SCALE = 2147483648  # 2**31, matches the int16 code's use of 32768 (2**15)


def volts_to_int32(volts, full_scale=3.3):
    # scale volts into the int32 range, clamping to avoid overflow
    if isinstance(volts, list):
        scaled = [round((v / full_scale) * INT32_SCALE) for v in volts]  # scale each sample
        scaled = [max(INT32_MIN, min(INT32_MAX, x)) for x in scaled]  # clamp each sample
        return scaled
    else:
        scaled = round((volts / full_scale) * INT32_SCALE)  # scale single value
        scaled = max(INT32_MIN, min(INT32_MAX, scaled))  # clamp single value
        return scaled


def int32_to_volts(values, full_scale=3.3):
    # convert int32 samples back to volts using the same scale factor
    if isinstance(values, list):
        return [(v / INT32_SCALE) * full_scale for v in values]  # scale each sample back to volts
    else:
        return (values / INT32_SCALE) * full_scale  # scale single value back to volts


def int32_array_to_base64(data):
    # pack int32 samples as little-endian binary, then base64-encode
    n = len(data)
    packed = struct.pack(f"<{n}i", *data)  # pack as n little-endian int32s
    return base64.b64encode(packed).decode("ascii")  # encode to base64 string


def base64_to_int32_array(encoded):
    # decode base64 back into a list of int32 samples
    raw = base64.b64decode(encoded)
    if len(raw) % 4 != 0:  # sanity check: must be a whole number of int32s
        raise ValueError(
            f"Decoded {len(raw)} bytes, which is not a multiple of 4 -- "
            f"this base64 string doesn't represent a whole number of "
            f"int32 samples (likely truncated)."
        )
    n = len(raw) // 4
    return list(struct.unpack(f"<{n}i", raw))  # unpack as n little-endian int32s


def test_int32_roundtrip():
    full_scale = 0.2
    quantization_step = full_scale / INT32_SCALE

    should_be = [0.11590485274791718, 0.12656699120998383, 0.13379764556884766, 0.13879169523715973, 0.1427440345287323, 0.14740106463432312, 0.15161384642124176, 0.15316107869148254, 0.1527014970779419, 0.1526402235031128, 0.15074065327644348, 0.1454402208328247, 0.13698403537273407, 0.12391678243875504]

    as_int32 = volts_to_int32(should_be, full_scale)
    b64 = int32_array_to_base64(as_int32)
    decoded_int32 = base64_to_int32_array(b64)
    recovered = int32_to_volts(decoded_int32, full_scale)

    print(f"should be:  {should_be}")
    print(f"int32:      {as_int32}")
    print(f"base64:     {b64}")
    print(f"recovered:  {recovered}")

    assert decoded_int32 == as_int32, "base64 round trip changed the int32 values"

    errors = [abs(a - b) for a, b in zip(should_be, recovered)]
    print(f"errors:     {errors}")
    print(f"quantization step at this full_scale: {quantization_step:.3e}")

    for e in errors:
        assert e <= quantization_step / 2 + 1e-15, f"error {e} exceeds half a quantization step"

    print("test_int32_roundtrip PASSED")


if __name__ == "__main__":
    test_int32_roundtrip()
    print()
    print("ALL TESTS PASSED")