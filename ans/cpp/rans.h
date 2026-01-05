#ifndef RANS
#define RANS

#include <cstdint>

namespace rANS
{

uint64_t compress(uint8_t* src, uint64_t src_size, uint8_t* dst);
void decompress(uint8_t* src, uint8_t* dst);

}

#endif
