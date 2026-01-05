#include <iostream>
#include <iomanip>
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

    auto start = std::chrono::steady_clock::now();
    uint64_t compressed_size = rANS::compress(buffer, filesize, dst);
    auto end = std::chrono::steady_clock::now();

    std::chrono::duration<double> duration = end - start;

    double compression_speed = static_cast<double>(filesize) / 1024 / 1024 / duration.count();   
    double compression_rate = static_cast<double>(filesize) / compressed_size;

    std::cout << std::fixed << std::setprecision(3) << filesize << " -> " << compressed_size << " (" << compression_rate << "x) ";
    std::cout << std::fixed << std::setprecision(1) << compression_speed << " MiB/s" << std::endl;

    //rANS::decompress(nullptr, nullptr);

    delete [] buffer;
    delete [] dst;

    return 0;
}
