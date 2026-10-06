cmake_minimum_required(VERSION 3.20)
project(tron_reconstruction VERSION 0.1.0 LANGUAGES CXX)

add_executable(reztool src/reztool.cpp)
target_compile_features(reztool PRIVATE cxx_std_20)
set_target_properties(reztool PROPERTIES CXX_EXTENSIONS OFF)
if(MSVC)
  target_compile_options(reztool PRIVATE /W4 /permissive-)
else()
  target_compile_options(reztool PRIVATE -Wall -Wextra -Wpedantic -Wconversion)
endif()

include(CTest)
if(BUILD_TESTING)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  add_test(NAME reztool-fixtures COMMAND "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_reztool.py" "$<TARGET_FILE:reztool>")
endif()
