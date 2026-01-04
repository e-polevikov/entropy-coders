import sys
import time

from bisect import bisect
from utils import estimate_freqs, calc_cumul

class rANSParams:
    def __init__(self, symbols):
        self.LOG2_M = 16
        self.M = 1 << self.LOG2_M

        self.L = self.M
        self.b = 32

        self.freqs = estimate_freqs(symbols, freqs_target_sum=self.M)
        self.cumul = calc_cumul(self.freqs)

    def get(self, symbol):
        return self.freqs[symbol], self.cumul[symbol]


class rANSEncoder:
    def __init__(self, params):
        self.params = params
        self.encoded = []

    def encode(self, symbols):
        state = self.params.L

        for symbol in symbols:
            state = self._encode_symbol(state, symbol)

            assert self.params.L <= state < self.params.L << self.params.b

        return self._to_bytes(state)

    def _to_bytes(self, last_state):
        self.encoded = b''.join(list(map(
            lambda x: x.to_bytes(length=4, byteorder='little'),
            self.encoded
        )))

        self.encoded += last_state.to_bytes(length=8, byteorder='little')

        return self.encoded

    def _encode_symbol(self, state, symbol):
        state = self._normalize(state, symbol)

        next_state = self._next_state(state, symbol)

        return next_state

    def _normalize(self, state, symbol):
        while state >= self.params.freqs[symbol] << self.params.b:
            remainder = state & ((1 << self.params.b) - 1)
            self.encoded.append(remainder)
            state >>= self.params.b

        return state
    
    def _next_state(self, state, symbol):
        freq, cumul = self.params.get(symbol)

        block_id = state // freq
        slot = cumul + state % freq

        next_state = (block_id << self.params.LOG2_M) + slot

        return next_state


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

    def decode(self):
        symbols = []

        state = self.last_state

        for _ in range(self.num_symbols):
            state, symbol = self._decode_symbol(state)

            assert self.params.L <= state < self.params.L << self.params.b

            symbols.append(symbol)

        return list(reversed(symbols))
    
    def _decode_symbol(self, state):
        block_id = state >> self.params.LOG2_M
        slot = state & (self.params.M - 1)

        symbol = bisect(self.params.cumul, slot) - 1

        freq, cumul = self.params.get(symbol)

        prev_state = block_id * freq + slot - cumul
        prev_state = self._denormalize(prev_state)

        return prev_state, symbol

    def _denormalize(self, state):
        while state < self.params.L:
            state <<= self.params.b
            state += self.encoded[-self.idx]
            self.idx += 1

        return state


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
