#ifndef RANS
#define RANS

#include <cstdint>

namespace rANS
{

const static  uint8_t LOG2_L = 16;
const static uint64_t      L = 1 << LOG2_L;
const static  uint8_t      b = 32;

inline static uint64_t compress(uint8_t* src, uint64_t src_size, uint8_t* dst) {
    uint64_t freq[256] = {};

    for (uint64_t i = 0; i < src_size; ++i) { ++freq[src[i]]; }

    uint64_t max_i = 0;
    uint64_t sum = 0;

    for (uint64_t i = 0; i < 256; ++i) {
        uint64_t f = static_cast<float>(freq[i]) / src_size * L;

        if (f == 0 && freq[i] > 0) { f = 1; }
        if (f > freq[max_i]) { max_i = i; }

        freq[i] = f;
        sum += f;
    }

    freq[max_i] += L - sum;

    uint64_t cumul[1 + 256] = {};
    for (uint64_t i = 0; i < 256; ++i) {
        cumul[i + 1] = cumul[i] + freq[i];
    }

    uint32_t* block = reinterpret_cast<uint32_t*>(dst + sizeof(uint64_t));
    uint64_t  state = L;

    for (uint64_t i = 0; i < src_size; ++i) {
        uint8_t symbol = src[i];

        if (state >= freq[symbol] << b) {
            *block++ = state & ((1ULL << b) - 1);
            state >>= b;
        }

        state = cumul[symbol] + state % freq[symbol] + ((state / freq[symbol]) << LOG2_L);
    }

    memcpy(block,     &state,    sizeof(uint64_t));
    memcpy(block + 2, &src_size, sizeof(uint64_t));

    uint16_t* freq_dst = reinterpret_cast<uint16_t*>(block + 4);
    for (uint64_t i = 0; i < 256; ++i) {
        freq_dst[i] = freq[i];
    }

    uint64_t compressed_size =
        sizeof(uint32_t) * (block - reinterpret_cast<uint32_t*>(dst))
        + 2 * sizeof(uint64_t)
        + 256 * sizeof(uint16_t);

    memcpy(dst, &compressed_size, sizeof(uint64_t));

    return compressed_size;
}

inline static void decompress(uint8_t* src, uint8_t* dst) {
    uint64_t  compressed_size = *reinterpret_cast<uint64_t*>(src);
    uint16_t* freq = reinterpret_cast<uint16_t*>(src + compressed_size - sizeof(uint16_t) * 256);

    uint64_t cumul[1 + 256] = {};
    for (uint64_t i = 0; i < 256; ++i) {
        cumul[i + 1] = cumul[i] + freq[i];
    }

    uint8_t slot_to_symbol[L];

    for (uint16_t symbol = 0; symbol < 256; ++symbol) {
        for (uint64_t slot = cumul[symbol]; slot < cumul[symbol + 1]; ++slot) {
            slot_to_symbol[slot] = symbol;
        }
    }

    uint64_t dst_size = 0;
    uint64_t state    = 0;

    memcpy(&dst_size, freq - 4, sizeof(uint64_t));
    memcpy(&state,    freq - 8, sizeof(uint64_t));

    uint32_t* block =  reinterpret_cast<uint32_t*>(freq - 10);
    dst += dst_size - 1;

    for (uint64_t i = 0; i < dst_size; ++i) {
        uint16_t slot = state & (L - 1);
        uint8_t  symbol = slot_to_symbol[slot];

        state = (state >> LOG2_L) * freq[symbol] + slot - cumul[symbol];
        *dst-- = symbol;

        if (state < L) { state = (state << b) + *block--; }
    }
}

}

#endif
