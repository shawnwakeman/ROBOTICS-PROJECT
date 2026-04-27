from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Get URDF via xacro with sim:=true
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("ros2_control_demo_example_7"),
                    "urdf",
                    "r6bot.urdf.xacro",
                ]
            ),
            " sim:=true",
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("ros2_control_demo_example_7"),
            "config",
            "r6bot_controller.yaml",
        ]
    )

    # Start Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                ]
            )
        ),
        launch_arguments={
            "gz_args": [
                "-r ",
                PathJoinSubstitution(
                    [
                        FindPackageShare("ros2_control_demo_example_7"),
                        "worlds",
                        "empty.sdf",
                    ]
                ),
            ]
        }.items(),
    )

    # Spawn the robot into Gazebo
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "/robot_description",
            "-name", "r6bot",
            "-allow_renaming", "true",
        ],
        output="screen",
    )
    gz_clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    camera_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/overhead_camera/image@sensor_msgs/msg/Image[gz.msgs.Image",
            "/overhead_camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image",
            "/overhead_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/overhead_camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
        ],
        output="screen",
    )

    # Publish robot description to /robot_description
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": True}],
    )
    

    # Spawn joint_state_broadcaster
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--param-file", robot_controllers],
    )

    # Spawn robot controller after joint_state_broadcaster
    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["r6bot_controller", "--param-file", robot_controllers],
    )

    delay_robot_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[robot_controller_spawner],
        )
    )

    return LaunchDescription(
        [
            gazebo,
            gz_clock_bridge,
            robot_state_pub_node,
            gz_spawn_entity,
            camera_bridge,
            joint_state_broadcaster_spawner,
            delay_robot_controller,
        ]
    )