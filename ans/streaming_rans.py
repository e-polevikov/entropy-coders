import sys
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

        self.L = self.M
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


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 streaming_rans.py INPUT_FILE")
        return

    with open(sys.argv[1], "rb") as f:
        symbols = [b for b in f.read()]

    params = rANSParams(symbols)

    encoder = rANSEncoder(params)
    encoded = encoder.encode(symbols)

    compression_rate = round(len(symbols) / len(encoded), 3)

    print(f"{len(symbols)} -> {len(encoded)}\t{compression_rate}x")


if __name__ == "__main__":
    main()
