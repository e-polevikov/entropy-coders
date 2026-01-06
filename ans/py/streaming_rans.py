import sys
import time

from bisect import bisect
from utils import estimate_freqs, calc_cumul

class rANSParams:
    def __init__(self, symbols):
        self.freqs = estimate_freqs(symbols, freqs_target_sum=1 << 16)
        self.cumul = calc_cumul(self.freqs)

    def get(self, symbol):
        return self.freqs[symbol], self.cumul[symbol]


class rANSEncoder:
    def __init__(self, params):
        self.params = params
        self.encoded = []

    def encode(self, symbols):
        state = 1 << 16

        for symbol in symbols:
            freq, cumul = self.params.get(symbol)

            if state >= freq << 32:
                self.encoded.append(state & 0xffffffff)
                state >>= 32

            state = cumul + state % freq + ((state // freq) << 16)

        return self._to_bytes(state)

    def _to_bytes(self, last_state):
        self.encoded = b''.join(list(map(
            lambda x: x.to_bytes(length=4, byteorder='little'),
            self.encoded
        )))

        self.encoded += last_state.to_bytes(length=8, byteorder='little')

        return self.encoded
    

class rANSDecoder:
    def __init__(self, params, encoded, num_symbols):
        self.params = params
        self.num_symbols = num_symbols
        self.encoded = []

        for i in range(0, len(encoded) - 8, 4):
            self.encoded.append(
                int.from_bytes(encoded[i:i + 4], byteorder='little')
            )

        self.idx = 1
        self.last_state = int.from_bytes(encoded[-8:], byteorder='little')

        slot_to_symbol = [0 for _ in range(1 << 16)]

        for symbol in range(256):
            for slot in range(self.params.cumul[symbol], self.params.cumul[symbol + 1]):
                slot_to_symbol[slot] = symbol

        self.slot_to_symbol = slot_to_symbol

    def decode(self):
        symbols = []

        state = self.last_state

        for _ in range(self.num_symbols):
            slot = state & 0xffff

            symbol = self.slot_to_symbol[slot]
            symbols.append(symbol)

            freq, cumul = self.params.get(symbol)

            state = (state >> 16) * freq + slot - cumul

            if state < 1 << 16:
                state <<= 32
                state += self.encoded[-self.idx]
                self.idx += 1

        return list(reversed(symbols))


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 streaming_rans.py INPUT_FILE")
        return

    with open(sys.argv[1], "rb") as f:
        symbols = [b for b in f.read()]

    params = rANSParams(symbols)
    encoder = rANSEncoder(params)

    start = time.perf_counter()
    encoded = encoder.encode(symbols)
    encoding_duration = round(time.perf_counter() - start, 3)
    encoding_speed = round(len(symbols) / 1024 / 1024 / encoding_duration, 3)

    print(f"Encoding:\t{encoding_duration}s\t{encoding_speed} MB/s")

    decoder = rANSDecoder(params, encoded, len(symbols))

    start = time.perf_counter()
    decoded_symbols = decoder.decode()
    decoding_duration = round(time.perf_counter() - start, 3)
    decoding_speed = round(len(symbols) / 1024 / 1024 / decoding_duration, 3)

    print(f"Decoding:\t{decoding_duration}s\t{decoding_speed} MB/s")

    assert symbols == decoded_symbols

    compression_rate = round(len(symbols) / len(encoded), 3)

    print()
    print(f"{len(symbols)} -> {len(encoded)}\t{compression_rate}x")


if __name__ == "__main__":
    main()
