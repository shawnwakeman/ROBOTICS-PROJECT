#!/usr/bin/env python3
"""
Pick-and-place node scaffolding.
Subscribes to /detected_cubes, uses MoveIt to pick and place.
TODO: implement actual MoveIt planning and execution.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json


# Bin drop positions in world frame
BIN_POSITIONS = {
    'red':   {'x': 1.05, 'y': -0.4, 'z': 0.95},
    'green': {'x': 1.05, 'y':  0.0, 'z': 0.95},
    'blue':  {'x': 1.05, 'y':  0.4, 'z': 0.95},
}


class PickAndPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_and_place')

        self.moveit_ready = False

        # Subscribe to cube detections
        self.create_subscription(
            String, '/detected_cubes', self.detection_callback, 10)

        # Try to init MoveIt after a delay
        self.create_timer(5.0, self.init_moveit)

        self.get_logger().info('Pick-and-place node started — waiting for MoveIt')

    def init_moveit(self):
        """Initialize MoveIt planning interface."""
        if self.moveit_ready:
            return

        # TODO: initialize MoveIt
        # from moveit.planning import MoveItPy
        # self.moveit = MoveItPy(node_name='pick_and_place_moveit')
        # self.arm = self.moveit.get_planning_component('arm')
        # self.gripper = self.moveit.get_planning_component('gripper')

        self.get_logger().info(
            'MoveIt init placeholder — not yet implemented',
            throttle_duration_sec=10.0)

    def detection_callback(self, msg):
        """Receive detected cubes and trigger pick-and-place."""
        detections = json.loads(msg.data)

        if not detections:
            return

        self.get_logger().info(
            f'Received {len(detections)} cube detections',
            throttle_duration_sec=2.0)

        for cube in detections:
            self.get_logger().info(
                f'  {cube["color"]} cube at ({cube["x"]}, {cube["y"]}), '
                f'rot={cube["rotation_deg"]}°',
                throttle_duration_sec=2.0)

        # TODO: implement pick-and-place sequence
        # For each cube:
        #   1. move_arm_above(cube x, y)
        #   2. open_gripper()
        #   3. lower_to_grasp(cube x, y, z)
        #   4. close_gripper()
        #   5. lift_up()
        #   6. move_to_bin(cube color)
        #   7. open_gripper()
        #   8. return_home()

    def move_arm_to(self, x, y, z, rotation_deg):
        """Plan and execute arm motion to target pose."""
        # TODO: MoveIt planning
        self.get_logger().info(f'  [TODO] move to ({x}, {y}, {z})')

    def open_gripper(self):
        """Open gripper."""
        # TODO: command gripper_left_joint -> -0.03, gripper_right_joint -> 0.03
        self.get_logger().info('  [TODO] open gripper')

    def close_gripper(self):
        """Close gripper."""
        # TODO: command gripper_left_joint -> 0.0, gripper_right_joint -> 0.0
        self.get_logger().info('  [TODO] close gripper')

    def move_to_home(self):
        """Move arm to home position."""
        # TODO: plan to named state 'home'
        self.get_logger().info('  [TODO] move to home')


def main(args=None):
    rclpy.init(args=args)
    node = PickAndPlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()