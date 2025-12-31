import sys
import time

from math import ceil, log2
from bitarray import bitarray


def calc_freqs_and_cumul(symbols):
    freqs = [0 for _ in range(256)]

    for symbol in symbols:
        freqs[symbol] += 1

    cumul = [0 for _ in range(256 + 1)]

    for i in range(256):
        cumul[i + 1] = cumul[i] + freqs[i]
    
    return freqs, cumul


def to_bitarray(value, num_bits):
    bits = bin(value)[2:]
    bits = "0" * (num_bits - len(bits)) + bits

    return bitarray(bits)


class rANSParams:
    def __init__(self, symbols):
        self.freqs, self.cumul = calc_freqs_and_cumul(symbols)

        self.M = self.cumul[-1]

        self.L = self.M * (1 << 16)
        self.H = 2 * self.L - 1

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

            assert self.params.L <= state <= self.params.H

            encoded = bits + encoded

        bits = to_bitarray(
            value=state, num_bits=ceil(log2(self.params.H))
        )

        encoded = bits + encoded

        return encoded.tobytes()

    def _encode_symbol(self, state, symbol):
        state, bits = self._renormalize(state, symbol)

        next_state = self._next_state(state, symbol)

        return next_state, bits

    def _renormalize(self, state, symbol):
        bits = bitarray()
        L, H = self.params.L, self.params.H

        while not L <= self._next_state(state, symbol) <= H:
            bits = bitarray([state % 2]) + bits
            state = state // 2

        return state, bits
    
    def _next_state(self, state, symbol):
        freq, cumul = self.params.get(symbol)

        block_id = state // freq
        slot = cumul + state % freq

        next_state = block_id * self.params.M + slot

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

        state = self._decode_final_state()

        for _ in range(self.num_symbols):
            state, symbol = self._decode_symbol(state)

            assert self.params.L <= state <= self.params.H

            symbols.append(symbol)

        return list(reversed(symbols))

    def _decode_final_state(self):
        final_state_bits = ceil(log2(self.params.H))

        state = int(self.encoded[:final_state_bits].to01(), 2)
        self.bit_idx += final_state_bits

        return state
    
    def _decode_symbol(self, state):
        block_id = state // self.params.M
        slot = state % self.params.M

        symbol = self._slot_to_symbol(slot)
        freq, cumul = self.params.get(symbol)

        prev_state = block_id * freq + slot - cumul
        prev_state = self._renormalize(prev_state)

        return prev_state, symbol

    def _slot_to_symbol(self, slot):
        symbol, cumul = 0, self.params.cumul

        while not cumul[symbol] <= slot < cumul[symbol + 1]:
            symbol += 1

        return symbol        

    def _renormalize(self, state):
        L, H = self.params.L, self.params.H

        while not L <= state <= H:
            state = state * 2 + self.encoded[self.bit_idx]
            self.bit_idx += 1

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
