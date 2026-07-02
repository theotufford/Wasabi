#pragma once
//  packet structure is strictly ordered by byte:
//  0: start byte
//  1: coms code
//  2: data length
//  3 to n + 3: data
//  n+4 to n+8: checksum
#define COMS_START_BYTE 0xF8
#define HEADER_SIZE 3
#define CHECKSUM_SIZE_BYTES 4
#define CODE_INDEX 1
#define LENGTH_INDEX 2
// defs for checksum calculation
#define REVERSED_STD_POLY 0xEDB88320ul
#define CRC32_INIT 0ul 
#define MAX_PACKET_SIZE 512
#define CRC_DISABLED true
