#pragma once
//  packet structure is strictly ordered by byte:
//  0: start byte
//  1: coms code
//  2: data type
//  3-4: data length
//  5 to n + 5: data
//  n+6 to n+10: checksum
#define COMS_START_BYTE 0xF8
#define HEADER_SIZE 5
#define CHECKSUM_SIZE_BYTES 4
#define CODE_INDEX 1
#define TYPE_INDEX 2
#define LENGTH_INDEX 3
// defs for checksum calculation
#define REVERSED_STD_POLY 0xEDB88320ul
#define CRC32_INIT 0xFFFFFFFF
#define MAX_PACKET_SIZE 1024
#define CRC_DISABLED true
#define TX_HISTORY_LEN 32
#define READ_TIMEOUT_US 3 * 1000 * 1000
