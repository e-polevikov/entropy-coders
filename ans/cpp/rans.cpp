#include "rans.h"

namespace rANS
{

void compress(uint8_t* src, uint64_t src_size, uint8_t* dst) {
    uint64_t freq[256] = {};

    for (uint64_t i = 0; i < src_size; i++) { freq[src[i]]++; }

    uint64_t max_i = 0;
    uint64_t sum = 0;

    for (uint64_t i = 0; i < 256; i++) {
        uint64_t f = static_cast<float>(freq[i]) / src_size * (1 << 16);

        if (f == 0 && freq[i] > 0) { f = 1; }
        if (f > freq[max_i]) { max_i = i; }

        freq[i] = f;
        sum += f;
    }

    freq[max_i] += static_cast<int64_t>(1 << 16) - sum;

    uint64_t cumul[1 + 256] = {};
    for (uint64_t i = 0; i < 256; i++) {
        cumul[i + 1] = cumul[i] + freq[i];
    }

    uint32_t* block = reinterpret_cast<uint32_t*>(dst);
    uint64_t  state = 1 << 16;

    for (uint64_t i = 0; i < src_size; i++) {
        uint8_t symbol = src[i];

        if (state >= freq[symbol] << 32) {
            *block = state & 0xffffffff;
            state >>= 32;
            block++;
        }

        state = cumul[symbol] + state % freq[symbol] + ((state / freq[symbol]) << 16);
    }
}

void decompress(uint8_t* src, uint8_t* dst) {
    std::cout << "decompress" << std::endl;
}

}
