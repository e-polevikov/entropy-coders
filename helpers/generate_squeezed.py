import random

def main():
    N = 20 * 10**6
    squeezed = []

    for _ in range(N):
        x = random.randint(1, 100)

        if 1 <= x < 80:
            squeezed.append(0)
        elif 80 <= x < 90:
            squeezed.append(1)
        else:
            squeezed.append(2)

    with open("squeezed.bin", "wb") as f:
        f.write(bytes(squeezed))

if __name__ == "__main__":
    main()
