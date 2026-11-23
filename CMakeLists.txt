cmake_minimum_required(VERSION 3.20)

file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" ASCII_SAVER_VERSION LIMIT_COUNT 1)
if(NOT ASCII_SAVER_VERSION)
  set(ASCII_SAVER_VERSION "0.1.0")
endif()

project(ascii-saver-watcher VERSION ${ASCII_SAVER_VERSION} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)

if(NOT DEFINED CMAKE_INSTALL_BINDIR)
  set(CMAKE_INSTALL_BINDIR bin)
endif()

find_package(Qt6 REQUIRED COMPONENTS Gui DBus)
find_package(KF6IdleTime REQUIRED)

add_executable(ascii-saver-watcher watcher.cpp)
target_link_libraries(ascii-saver-watcher PRIVATE Qt6::Gui Qt6::DBus KF6::IdleTime)
target_compile_definitions(ascii-saver-watcher PRIVATE ASCII_SAVER_VERSION=\"${ASCII_SAVER_VERSION}\")
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(ascii-saver-watcher PRIVATE -Wall -Wextra)
endif()

install(TARGETS ascii-saver-watcher RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
