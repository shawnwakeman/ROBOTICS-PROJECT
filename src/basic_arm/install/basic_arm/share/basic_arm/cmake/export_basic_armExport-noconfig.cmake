#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "basic_arm::basic_arm" for configuration ""
set_property(TARGET basic_arm::basic_arm APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(basic_arm::basic_arm PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libbasic_arm.so"
  IMPORTED_SONAME_NOCONFIG "libbasic_arm.so"
  )

list(APPEND _cmake_import_check_targets basic_arm::basic_arm )
list(APPEND _cmake_import_check_files_for_basic_arm::basic_arm "${_IMPORT_PREFIX}/lib/libbasic_arm.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
