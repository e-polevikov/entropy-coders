from math import floor


def estimate_freqs(symbols, freqs_target_sum):
    freqs = [0 for _ in range(256)]

    for symbol in symbols:
        freqs[symbol] += 1

    normalize(freqs, freqs_target_sum)

    return freqs


def calc_cumul(freqs):
    cumul = [0 for _ in range(256 + 1)]

    for i in range(256):
        cumul[i + 1] = cumul[i] + freqs[i]
    
    return cumul


def normalize(freqs, target_sum):
    N = len(freqs)

    freqs_sum = sum(freqs)
    normalized_sum = 0
    max_idx = 0

    for i in range(N):
        f = floor(target_sum * freqs[i] / freqs_sum)

        if f == 0 and freqs[i] > 0:
            f = 1

        freqs[i] = f
        normalized_sum += f

        if f > freqs[max_idx]:
            max_idx = i

    freqs[max_idx] += target_sum - normalized_sum
