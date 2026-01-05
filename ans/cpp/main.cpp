#include <iostream>
#include <fstream>
#include <filesystem>

#include "rans.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        return 0;
    }

    std::uintmax_t filesize = std::filesystem::file_size(argv[1]);

    uint8_t *buffer = new uint8_t[filesize];
    uint8_t *dst = new uint8_t[filesize];

    std::ifstream file(argv[1], std::ios::binary);
    file.read((char*) buffer, filesize);

    rANS::compress(buffer, filesize, dst);
    //rANS::decompress(nullptr, nullptr);

    delete [] buffer;
    delete [] dst;

    return 0;
}
