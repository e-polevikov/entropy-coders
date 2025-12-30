import sys
from collections import Counter
import math


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        input_bytes = f.read()

    bytes_by_counts = Counter(input_bytes).most_common()
    entropy = 0.0

    for b, count in bytes_by_counts: 
        entropy += -(count / len(input_bytes)) * math.log2(count / len(input_bytes))
    
    print(round(entropy, 3), round(8 / entropy, 3))
