cmake_minimum_required(VERSION 3.13)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(machineController C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

pico_sdk_init()

include_directories(./)
add_executable(machineController dma_uart.cpp main.cpp)
target_link_libraries(machineController pico_stdlib hardware_gpio hardware_clocks
                      hardware_dma hardware_uart hardware_irq)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(machineController)
