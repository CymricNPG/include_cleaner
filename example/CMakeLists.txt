cmake_minimum_required (VERSION 2.6)

SET(ROOT_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${ROOT_SOURCE_DIR})

file(GLOB_RECURSE cppFiles RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} *.cpp)

add_library(test_lib SHARED ${cppFiles})

