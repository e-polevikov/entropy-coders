from math import floor


def estimate_freqs(symbols, freqs_target_sum):
    freqs = [0 for _ in range(256)]

    for symbol in symbols:
        freqs[symbol] += 1

    return normalize_freqs(freqs, target_sum=freqs_target_sum)


def calc_cumul(freqs):
    cumul = [0 for _ in range(256 + 1)]

    for i in range(256):
        cumul[i + 1] = cumul[i] + freqs[i]
    
    return cumul


def normalize_freqs(freqs, target_sum):
    N = len(freqs)

    normalized_freqs = [0 for _ in range(N)]

    freqs_sum = sum(freqs)
    normalized_freqs_sum = 0
    max_idx = 0

    for i in range(N):
        normalized = floor(target_sum * freqs[i] / freqs_sum)

        if normalized == 0 and freqs[i] != 0:
            normalized = 1

        normalized_freqs[i] = normalized
        normalized_freqs_sum += normalized

        if normalized > normalized_freqs[max_idx]:
            max_idx = i

    normalized_freqs[max_idx] += target_sum - sum(normalized_freqs)

    assert sum(normalized_freqs) == target_sum

    return normalized_freqs
