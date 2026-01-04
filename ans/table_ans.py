import sys
import time

from bitarray import bitarray
from bitarray.util import ba2int, int2ba
from bisect import bisect
from utils import estimate_freqs, calc_cumul


class tANSParams:
    def __init__(self, symbols):
        self.LOG2_M = 16
        self.M = 1 << self.LOG2_M

        self.L = self.M

        self.freqs = estimate_freqs(symbols, freqs_target_sum=self.M)
        self.cumul = calc_cumul(self.freqs)

    def get(self, symbol):
        return self.freqs[symbol], self.cumul[symbol]


class tANSEncoder:
    def __init__(self, params):
        self.params = params
        self.encoded = bitarray()

    def encode(self, symbols):
        state = self.params.L

        for symbol in symbols:
            state = self._encode_symbol(state, symbol)

            assert self.params.L <= state < 2 * self.params.L

        self.encoded += int2ba(state, length=32)
        self._add_padding()

        return self.encoded.tobytes()

    def _add_padding(self):
        padding_len = 0 if len(self.encoded) % 8 == 0 else 8 - len(self.encoded) % 8
        self.encoded += int2ba(0, length=padding_len)
        self.encoded += int2ba(padding_len, length=8)

    def _encode_symbol(self, state, symbol):
        state = self._normalize(state, symbol)

        next_state = self._next_state(state, symbol)

        return next_state

    def _normalize(self, state, symbol):
        while state >= 2 * self.params.freqs[symbol]:
            remainder = state % 2
            self.encoded += int2ba(remainder)
            state >>= 1

        return state
    
    def _next_state(self, state, symbol):
        freq, cumul = self.params.get(symbol)

        block_id = state // freq
        slot = cumul + state % freq

        next_state = (block_id << self.params.LOG2_M) + slot

        return next_state


class tANSDecoder:
    def __init__(self, params, encoded, num_symbols):
        self.params = params

        self.encoded = bitarray()
        self.encoded.frombytes(encoded)

        self.num_symbols = num_symbols
        self.bit_idx = 0

    def decode(self):
        symbols = []

        state = self._read_last_state()

        for _ in range(self.num_symbols):
            state, symbol = self._decode_symbol(state)

            assert self.params.L <= state < 2 * self.params.L

            symbols.append(symbol)

        return list(reversed(symbols))

    def _read_last_state(self):
        padding_len = ba2int(self.encoded[-8:])
        self.bit_idx += 8 + padding_len

        state = ba2int(self.encoded[-self.bit_idx - 32:-self.bit_idx])
        self.bit_idx += 32 + 1

        return state
    
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
            state <<= 1
            state += self.encoded[-self.bit_idx]
            self.bit_idx += 1

        return state


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 streaming_rans.py INPUT_FILE")
        return

    with open(sys.argv[1], "rb") as f:
        symbols = [b for b in f.read()]

    params = tANSParams(symbols)
    encoder = tANSEncoder(params)

    start = time.perf_counter()
    encoded = encoder.encode(symbols)
    encoding_duration = round(time.perf_counter() - start, 3)
    encoding_speed = round(len(symbols) / 1024 / 1024 / encoding_duration, 3)

    print(f"Encoding:\t{encoding_duration}s\t{encoding_speed} MB/s")

    decoder = tANSDecoder(params, encoded, len(symbols))

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
