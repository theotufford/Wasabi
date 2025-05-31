cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project( motCon C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
add_executable( motCon
  motCon.c
)
pico_enable_stdio_usb(motCon 0)
pico_enable_stdio_uart(motCon 1)
pico_add_extra_outputs(motCon)
target_link_libraries(motCon pico_stdlib)
