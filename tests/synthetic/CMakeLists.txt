# Synthetic checks that run without any game data.
add_executable(lab_state_tests lab_state_tests.cpp)
target_link_libraries(lab_state_tests PRIVATE lab_state)
# Reference hash of the probe after 1000 scripted steps, first observed on
# macOS 15.7 arm64 with Homebrew clang 19.1.7 at -O0, -O2, with ASan/UBSan
# and with Apple clang (Xcode 26.1). Linux must reproduce it.
target_compile_definitions(lab_state_tests PRIVATE LAB_KNOWN_HASH=0x0be347c529fadda9ull)

add_test(NAME lab_state_serialization_roundtrip COMMAND lab_state_tests roundtrip)
add_test(NAME lab_state_arithmetic_bounds COMMAND lab_state_tests bounds)
add_test(NAME lab_state_known_hash COMMAND lab_state_tests known_hash)
add_test(NAME lab_runner_smoke COMMAND lab_runner --steps 10)
add_test(NAME lab_runner_rejects_bad_argument COMMAND lab_runner --bogus)
set_tests_properties(lab_runner_rejects_bad_argument PROPERTIES WILL_FAIL TRUE)
set_tests_properties(
  lab_state_serialization_roundtrip lab_state_arithmetic_bounds lab_state_known_hash
  lab_runner_smoke lab_runner_rejects_bad_argument
  PROPERTIES TIMEOUT 30 LABELS synthetic)

if(LAB_PROBE_FAILURES)
  # These exist only to prove the tooling reports a failure and a timeout as
  # such. They are never part of an acceptance run.
  add_test(NAME lab_probe_expected_failure COMMAND lab_runner --bogus)
  add_test(NAME lab_probe_expected_timeout COMMAND lab_runner --sleep-ms 10000 --steps 1)
  set_tests_properties(lab_probe_expected_failure PROPERTIES TIMEOUT 30 LABELS probe)
  set_tests_properties(lab_probe_expected_timeout PROPERTIES TIMEOUT 1 LABELS probe)
endif()
