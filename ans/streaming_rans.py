import sys
import time

from bitarray import bitarray
from bitarray.util import ba2int, int2ba
from bisect import bisect
from utils import estimate_freqs, calc_cumul


class rANSParams:
    def __init__(self, symbols):
        self.TOTAL_FREQ_LOG2 = 16
        self.TOTAL_FREQ = 1 << self.TOTAL_FREQ_LOG2

        self.L = self.TOTAL_FREQ
        self.b = 32

        self.freqs = estimate_freqs(symbols, self.TOTAL_FREQ)
        self.cumul = calc_cumul(self.freqs)

    def get(self, symbol):
        return self.freqs[symbol], self.cumul[symbol]


class rANSEncoder:
    def __init__(self, params):
        self.params = params

    def encode(self, symbols):
        state = self.params.L
        encoded = bitarray()

        for symbol in symbols:
            state, bits = self._encode_symbol(state, symbol)

            assert self.params.L <= state <= (self.params.L << self.params.b) - 1

            encoded = bits + encoded

        encoded = int2ba(state, length=64) + encoded

        return encoded.tobytes()

    def _encode_symbol(self, state, symbol):
        state, bits = self._normalize(state, symbol)

        next_state = self._next_state(state, symbol)

        return next_state, bits

    def _normalize(self, state, symbol):
        bits = bitarray()

        max_state = (self.params.freqs[symbol] << self.params.b) - 1

        while state > max_state:
            remainder = state & ((1 << self.params.b) - 1)
            bits = int2ba(remainder, length=self.params.b) + bits
            state >>= self.params.b

        return state, bits
    
    def _next_state(self, state, symbol):
        freq, cumul = self.params.get(symbol)

        block_id = state // freq
        slot = cumul + state % freq

        next_state = (block_id << self.params.TOTAL_FREQ_LOG2) + slot

        return next_state


class rANSDecoder:
    def __init__(self, params, encoded, num_symbols):
        self.params = params

        self.encoded = bitarray()
        self.encoded.frombytes(encoded)

        self.num_symbols = num_symbols
        self.bit_idx = 0

    def decode(self):
        symbols = []

        state = ba2int(self.encoded[:64])
        self.bit_idx += 64

        for _ in range(self.num_symbols):
            state, symbol = self._decode_symbol(state)

            assert self.params.L <= state <= (self.params.L << self.params.b) - 1

            symbols.append(symbol)

        return list(reversed(symbols))
    
    def _decode_symbol(self, state):
        block_id = state >> self.params.TOTAL_FREQ_LOG2
        slot = state & (self.params.TOTAL_FREQ - 1)

        symbol = bisect(self.params.cumul, slot) - 1

        freq, cumul = self.params.get(symbol)

        prev_state = block_id * freq + slot - cumul
        prev_state = self._denormalize(prev_state)

        return prev_state, symbol

    def _denormalize(self, state):
        while state < self.params.L:
            state <<= self.params.b
            state += ba2int(self.encoded[self.bit_idx:self.bit_idx + self.params.b])
            self.bit_idx += self.params.b

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
