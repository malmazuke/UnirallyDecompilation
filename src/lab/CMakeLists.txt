add_library(lab_state STATIC lab_state.cpp lab_state.hpp)
target_include_directories(lab_state PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(lab_state PUBLIC lab_options)

add_executable(lab_runner lab_runner.cpp)
target_link_libraries(lab_runner PRIVATE lab_state)
