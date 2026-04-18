cmake_minimum_required(VERSION 3.16)
project(basic_arm LANGUAGES CXX)

find_package(ros2_control_cmake REQUIRED)
set_compiler_options()
export_windows_symbols()

set(HW_IF_INCLUDE_DEPENDS
  pluginlib
  hardware_interface
)
set(REF_GEN_INCLUDE_DEPENDS
  kdl_parser
  rclcpp
  trajectory_msgs
)
set(CONTROLLER_INCLUDE_DEPENDS
  pluginlib
  controller_interface
  realtime_tools
  trajectory_msgs
)

find_package(controller_manager 4.0.0)
if(NOT controller_manager_FOUND)
  message(FATAL_ERROR "ros2_control 4.0.0+ required")
endif()

find_package(backward_ros REQUIRED)
find_package(ament_cmake REQUIRED)

foreach(Dependency IN ITEMS ${HW_IF_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

foreach(Dependency IN ITEMS ${REF_GEN_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

foreach(Dependency IN ITEMS ${CONTROLLER_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

add_executable(send_trajectory reference_generator/send_trajectory.cpp)

target_link_libraries(send_trajectory PUBLIC
  ${trajectory_msgs_TARGETS}
  kdl_parser::kdl_parser
  rclcpp::rclcpp
)

add_library(
  basic_arm
  SHARED
  hardware/r6bot_hardware.cpp
  controller/r6bot_controller.cpp
)

target_compile_features(basic_arm PUBLIC cxx_std_17)

target_include_directories(basic_arm PUBLIC
  $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/hardware/include>
  $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/controller/include>
  $<INSTALL_INTERFACE:include/basic_arm>
)

target_link_libraries(basic_arm PUBLIC
  ${trajectory_msgs_TARGETS}
  controller_interface::controller_interface
  hardware_interface::hardware_interface
  pluginlib::pluginlib
  realtime_tools::realtime_tools
)

pluginlib_export_plugin_description_file(hardware_interface basic_arm.xml)
pluginlib_export_plugin_description_file(controller_interface basic_arm.xml)

install(DIRECTORY hardware/include/
  DESTINATION include/basic_arm
)

install(DIRECTORY description/launch description/ros2_control description/urdf
  DESTINATION share/basic_arm
)

install(DIRECTORY bringup/launch bringup/config
  DESTINATION share/basic_arm
)

install(TARGETS send_trajectory
  RUNTIME DESTINATION lib/basic_arm
)

install(TARGETS basic_arm
  EXPORT export_basic_arm
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_export_targets(export_basic_arm HAS_LIBRARY_TARGET)
ament_export_dependencies(${HW_IF_INCLUDE_DEPENDS} ${REF_GEN_INCLUDE_DEPENDS} ${CONTROLLER_INCLUDE_DEPENDS})
ament_package()