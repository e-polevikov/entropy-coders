import sys
from dahuffman import HuffmanCodec


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 huffman.py INPUT_FILE")
        return

    with open(sys.argv[1], "rb") as f:
        data = f.read()

    codec = HuffmanCodec.from_data(data)
    encoded_data = codec.encode(data)

    compression_rate = round(len(data) / len(encoded_data), 3)

    print(f"{len(data)} -> {len(encoded_data)}\t({compression_rate}x)")


if __name__ == "__main__":
    main()
