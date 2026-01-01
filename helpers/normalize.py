from math import floor

def normalize_freqs(freqs, target_sum):
    normalized_freqs = [0 for _ in range(len(freqs))]

    freqs_sum = sum(freqs)
    normalized_freqs_sum = 0
    max_idx = 0

    for i in range(len(freqs)):
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


def main():
    freqs = [1, 1, 1, 2, 2, 3, 4, 500, 800]
    target_sum = 1 << 10

    normalized_freqs = normalize_freqs(freqs, target_sum)

    print(normalized_freqs)


if __name__ == "__main__":
    main()
