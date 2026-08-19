import base64
import wave

def json_sound_to_wav(payload, out_path):
    raw_bytes = base64.b64decode(payload["audio_data"])  # decode base64 audio payload to raw PCM bytes
    with wave.open(out_path, 'wb') as w:
        w.setnchannels(payload["channels"])  # mono/stereo channel count
        w.setsampwidth(payload["sample_width"])  # bytes per sample (e.g. 2 = 16-bit)
        w.setframerate(payload["frame_rate"])  # sample rate in Hz
        w.writeframes(raw_bytes)  # write PCM data to the WAV file