import numpy as np

sample = np.round(
    np.random.normal(0, 256, size=1024 * 1024 * 20)
).astype(int).tolist()

sample = [min(abs(x), 255) for x in sample]

with open("sample.bin", "wb") as f:
    f.write(bytes(sample))
