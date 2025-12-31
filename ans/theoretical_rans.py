import math
import sys


class rANSParams:
    def __init__(self, symbols):
        self.freqs = [0 for _ in range(256)]

        for symbol in symbols:
            self.freqs[symbol] += 1

        self.cumul = [0 for _ in range(256)]

        for i in range(1, 256):
            self.cumul[i] = self.cumul[i - 1] + self.freqs[i - 1]
        
        self.M = self.cumul[-1] + self.freqs[-1]
        self.cumul.append(self.M)
    
    def get(self, symbol):
        return self.freqs[symbol], self.cumul[symbol]


class rANSEncoder:
    def __init__(self, params):
        self.params = params

    def encode_symbol(self, state, symbol):
        freq, cumul = self.params.get(symbol)

        block_id = state // freq
        slot = cumul + state % freq

        next_state = block_id * self.params.M + slot

        return next_state

    def encode(self, symbols):
        state = 0

        for symbol in symbols:
            state = self.encode_symbol(state, symbol)

        return state


class rANSDecoder:
    def __init__(self, params):
        self.params = params
    
    def _decode_symbol(self, slot):
        symbol, cumul = 0, self.params.cumul

        while not cumul[symbol] <= slot < cumul[symbol + 1]:
            symbol += 1

        return symbol

    def decode_symbol(self, state):
        block_id = state // self.params.M
        slot = state % self.params.M

        symbol = self._decode_symbol(slot)
        freq, cumul = self.params.get(symbol)

        prev_state = block_id * freq + slot - cumul

        return prev_state, symbol

    def decode(self, state, num_symbols):
        symbols = []

        for _ in range(num_symbols):
            state, symbol = self.decode_symbol(state)
            symbols.append(symbol)

        return list(reversed(symbols))


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 theoretical_rans.py INPUT_FILE")
        return

    with open(sys.argv[1], "rb") as f:
        symbols = [b for b in f.read()]

    params = rANSParams(symbols)

    encoder = rANSEncoder(params)
    decoder = rANSDecoder(params)

    state = encoder.encode(symbols)
    decoded_symbols = decoder.decode(state, len(symbols))

    assert symbols == decoded_symbols

    state_bits_len = math.ceil(math.log2(state))
    state_bytes_len = math.ceil(state_bits_len / 8)
    compression_rate = round(len(symbols) / state_bytes_len, 3)

    print(f"{len(symbols)} -> {state_bytes_len}\t({compression_rate}x)")


if __name__ == "__main__":
    main()
