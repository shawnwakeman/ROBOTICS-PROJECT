import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
import xacro

def generate_launch_description():
    pkg_dir = get_package_share_directory('my_robot_arm')
    robot_description = {'robot_description': xacro.process_file(os.path.join(pkg_dir, 'description', 'arm.urdf.xacro')).toxml()}
    
    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher', parameters=[robot_description, {'use_sim_time': True}])
    gazebo = IncludeLaunchDescription(PythonLaunchDescriptionSource([os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]), launch_arguments={'gz_args': 'empty.sdf -r'}.items())
    spawn = Node(package='ros_gz_sim', executable='create', arguments=['-topic', 'robot_description', '-name', 'my_6dof_arm'])
    
    load_jsb = ExecuteProcess(cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'joint_state_broadcaster'])
    load_arm = ExecuteProcess(cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'arm_controller'])
    
    return LaunchDescription([rsp, gazebo, spawn, RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[load_jsb])), RegisterEventHandler(OnProcessExit(target_action=load_jsb, on_exit=[load_arm]))])


