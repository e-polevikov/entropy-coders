import sys
import time

from utils import estimate_freqs, calc_cumul
from bitarray import bitarray
from bitarray.util import int2ba, ba2int

class tANSParams:
    def __init__(self, symbols):
        self.LOG2_L = 12
        self.L = 1 << self.LOG2_L
        self.b = 4

        self.freqs = estimate_freqs(symbols, freqs_target_sum=self.L)
        self.cumul = calc_cumul(self.freqs)

    def get(self, symbol):
        return self.freqs[symbol], self.cumul[symbol]


class tANSEncoder:
    def __init__(self, params):
        self.params = params
        self._init_tables()

    def _init_tables(self):
        b = self.params.b
        LOG2_L = self.params.LOG2_L

        next_state_table = dict()

        for symbol in range(256):
            freq, cumul = self.params.get(symbol)

            for state in range(freq, freq << b):
                next_state_table[(symbol, state)] = cumul + state % freq + ((state // freq) << LOG2_L)

        self.next_state_table = next_state_table

    def encode(self, symbols):
        LOG2_L = self.params.LOG2_L
        L = self.params.L
        b = self.params.b

        state = L
        encoded = bitarray()

        for symbol in symbols:
            freq = self.params.freqs[symbol]

            while state >= freq << b:
                bits = int2ba(state & ((1 << b) - 1), length=b)
                encoded.extend(bits)
                state >>= b

            state = self.next_state_table[(symbol, state)]

        encoded.extend(int2ba(state, length=b + LOG2_L))

        return encoded


class tANSDecoder:
    def __init__(self, params, encoded, num_symbols):
        self.params = params
        self.num_symbols = num_symbols
        self.encoded = encoded

        self.idx = self.params.b + self.params.LOG2_L
        self.last_state = ba2int(encoded[-self.idx:])
        self.idx += self.params.b

        slot_to_symbol = [0 for _ in range(self.params.L)]

        for symbol in range(256):
            for slot in range(self.params.cumul[symbol], self.params.cumul[symbol + 1]):
                slot_to_symbol[slot] = symbol

        self.slot_to_symbol = slot_to_symbol

    def decode(self):
        symbols = []

        LOG2_L = self.params.LOG2_L
        L = self.params.L
        b = self.params.b

        state = self.last_state

        for _ in range(self.num_symbols):
            slot = state & (L - 1)

            symbol = self.slot_to_symbol[slot]
            symbols.append(symbol)

            freq, cumul = self.params.get(symbol)

            state = (state >> LOG2_L) * freq + slot - cumul

            while state < 1 << LOG2_L:
                state <<= b
                state += ba2int(self.encoded[-self.idx:-self.idx + b])
                self.idx += b

        return list(reversed(symbols))


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 tans.py INPUT_FILE")
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

    compression_rate = round(8 * len(symbols) / len(encoded), 3)

    print()
    print(f"{len(symbols)} -> {len(encoded) // 8}\t{compression_rate}x")


if __name__ == "__main__":
    main()
