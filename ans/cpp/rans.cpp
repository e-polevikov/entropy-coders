#include <iostream>
#include <iomanip>
#include <fstream>
#include <cstring>
#include <cassert>
#include <filesystem>

#include "rans.h"

const uint64_t MB = 1 << 20;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        return 0;
    }

    std::uintmax_t filesize = std::filesystem::file_size(argv[1]);

    uint8_t* buffer = new uint8_t[filesize];
    uint8_t* dst = new uint8_t[filesize];
    uint8_t* decompressed = new uint8_t[filesize]; 

    std::ifstream file(argv[1], std::ios::binary);
    file.read((char*) buffer, filesize);

    auto start = std::chrono::steady_clock::now();
    uint64_t compressed_size = rANS::compress(buffer, filesize, dst);
    auto end = std::chrono::steady_clock::now();

    std::chrono::duration<double> duration = end - start;

    double compression_speed = static_cast<double>(filesize) / MB / duration.count();
    double compression_rate = static_cast<double>(filesize) / compressed_size;

    std::cout << std::fixed << std::setprecision(3) << filesize << " -> " << compressed_size << " (" << compression_rate << "x)\t";
    std::cout << std::fixed << std::setprecision(1) << compression_speed << " MB/s\t";

    start = std::chrono::steady_clock::now();
    rANS::decompress(dst, decompressed);
    end = std::chrono::steady_clock::now();

    duration = end - start;

    double decompression_speed = static_cast<double>(filesize) / MB / duration.count();

    std::cout << std::fixed << std::setprecision(1) << decompression_speed << " MB/s" << std::endl;

    assert(memcmp(buffer, decompressed, filesize) == 0);

    delete [] buffer;
    delete [] dst;
    delete [] decompressed;

    return 0;
}
