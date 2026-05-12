#!/usr/bin/env python3
"""
Pick-and-place node using ikpy for Inverse Kinematics.
Subscribes to /detected_cubes, solves IK, and publishes smooth trajectories.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from std_msgs.msg import String, Float64MultiArray
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

import json
import math
import time
import threading
import tempfile
import re
import os
import numpy as np

import ikpy.chain

# Joint names used by the ros2_controller (for trajectory publishing and JointState)
JOINTS = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']

# Link names as ikpy sees them in the URDF chain (child link of each revolute joint above)
LINK_NAMES = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5', 'link_6']

# Bin drop positions in world frame
BIN_POSITIONS = {
    'red':   {'x': 1.05, 'y': -0.4, 'z': 1.10},
    'green': {'x': 1.05, 'y':  0.0, 'z': 1.10},
    'blue':  {'x': 1.05, 'y':  0.4, 'z': 1.10},
}


class PickAndPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_and_place')

        self.chain = None
        self.current_joints = [0.0] * 6
        self.is_moving = False

        # Publishers
        self.arm_pub = self.create_publisher(
            JointTrajectory, '/r6bot_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(
            Float64MultiArray, '/gripper_controller/commands', 10)

        # Subscribers
        self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, 10)
        self.create_subscription(
            String, '/detected_cubes', self.detection_callback, 10)

        # Fetch URDF from robot_description to build IK chain dynamically
        qos_profile = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(
            String, '/robot_description', self.urdf_callback, qos_profile)

        self.get_logger().info('Pick-and-place node started — waiting for URDF & detections...')

    def joint_state_callback(self, msg):
        """Keep track of the current joint positions."""
        for i, name in enumerate(msg.name):
            if name in JOINTS:
                idx = JOINTS.index(name)
                self.current_joints[idx] = msg.position[i]

    def urdf_callback(self, msg):
        """Build the kinematic chain directly from the URDF string."""
        if self.chain is not None:
            return

        self.get_logger().info('Received URDF. Initializing ikpy solver...')

        # Strip gripper joints so the chain ends at tool0
        clean_urdf = re.sub(r'<joint name="gripper.*?</joint>', '', msg.data, flags=re.DOTALL)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write(clean_urdf)
            temp_path = f.name

        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                # Load once to inspect link names, then reload with the active mask
                temp_chain = ikpy.chain.Chain.from_urdf_file(temp_path)

                # Debug: see what ikpy calls each link
                for i, link in enumerate(temp_chain.links):
                    self.get_logger().info(f'  Link {i}: name={link.name}, joint_type={link.joint_type}')

                # ikpy link names are the URDF link names (link_1..link_6, not joint_1..joint_6)
                active_mask = [link.joint_type != 'fixed' for link in temp_chain.links]

                self.chain = ikpy.chain.Chain.from_urdf_file(
                    temp_path, active_links_mask=active_mask)

            self.get_logger().info(
                f'ikpy IK initialized. {len(self.chain.links)} links, '
                f'{sum(active_mask)} active joints.')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize ikpy: {e}')
        finally:
            os.remove(temp_path)

    def detection_callback(self, msg):
        """Receive detected cubes and trigger pick-and-place in a separate thread."""
        if self.is_moving or self.chain is None:
            return

        detections = json.loads(msg.data)
        if not detections:
            return

        self.get_logger().info(f'Received {len(detections)} cube detections. Starting sequence.')
        threading.Thread(target=self.process_cubes, args=(detections,)).start()

    def process_cubes(self, detections):
        self.is_moving = True

        for cube in detections:
            x, y = cube['x'], cube['y']
            color = cube['color']

            self.get_logger().info(f'Picking up {color} cube at ({x:.2f}, {y:.2f})')

            # 1. Move above the cube
            self.move_arm_to(x, y, 0.95)
            # 2. Open Gripper
            self.open_gripper()
            # 3. Lower to grasp (cube center ~0.78, grip slightly above)
            self.move_arm_to(x, y, 0.85)
            # 4. Close Gripper
            self.close_gripper()
            # 5. Lift up
            self.move_arm_to(x, y, 0.95)

            # 6. Move to bin
            bin_pos = BIN_POSITIONS.get(color, BIN_POSITIONS['red'])
            self.move_arm_to(bin_pos['x'], bin_pos['y'], bin_pos['z'])

            # 7. Release
            self.open_gripper()

            # 8. Return home
            self.move_to_home()
            break  # one cube per trigger; let perception redetect the rest

        self.is_moving = False
        self.get_logger().info('Sequence complete, ready for next detection.')

    def move_arm_to(self, x, y, z):
        q_init = [0.0] * len(self.chain.links)
        for i, link in enumerate(self.chain.links):
            if link.name in JOINTS:                  # was LINK_NAMES
                idx = JOINTS.index(link.name)        # was LINK_NAMES
                q_init[i] = self.current_joints[idx]

        target = [x, y, z]
        ik_sol = self.chain.inverse_kinematics(
            target_position=target, initial_position=q_init)

        best_joints = [0.0] * 6
        best_joints = [max(-3.14, min(3.14, j)) for j in best_joints]
        for i, link in enumerate(self.chain.links):
            if link.name in JOINTS:                  # was LINK_NAMES
                idx = JOINTS.index(link.name)        # was LINK_NAMES
                best_joints[idx] = ik_sol[i]
        # ... rest unchanged
        # Verify with FK
        fk_pos = self.chain.forward_kinematics(ik_sol)[:3, 3]
        err = np.linalg.norm(fk_pos - np.array(target))

        if err > 0.05:
            self.get_logger().warn(
                f'IK failed for ({x}, {y}, {z}) — out of reach? (err: {err:.3f}m)')
            return False

        # Add this right before send_trajectory in move_arm_to:
        self.get_logger().info(f'IK target: ({x}, {y}, {z})')
        self.get_logger().info(f'IK solution: {[f"{v:.3f}" for v in best_joints]}')
        self.get_logger().info(f'FK error: {err:.4f}m')
        self.send_trajectory(self.current_joints, best_joints, duration=2.5)
        return True

    def send_trajectory(self, start_joints, end_joints, duration, n_pts=50):
        """Publish a smooth cosine-profile trajectory with velocities."""
        traj = JointTrajectory()
        traj.joint_names = JOINTS

        for i in range(n_pts):
            t = i / (n_pts - 1) * duration
            alpha = (1.0 - math.cos(math.pi * t / duration)) / 2.0
            # Analytical derivative of the cosine profile
            alpha_dot = math.pi / (2.0 * duration) * math.sin(math.pi * t / duration)

            pt = JointTrajectoryPoint()
            pt.positions = [
                start_joints[j] + alpha * (end_joints[j] - start_joints[j])
                for j in range(6)
            ]
            pt.velocities = [
                alpha_dot * (end_joints[j] - start_joints[j])
                for j in range(6)
            ]
            pt.time_from_start = Duration(
                sec=int(t), nanosec=int((t % 1) * 1e9))
            traj.points.append(pt)

        self.arm_pub.publish(traj)
        time.sleep(duration + 0.5)

    def set_gripper(self, left_val, right_val):
        msg = Float64MultiArray()
        msg.data = [left_val, right_val]
        self.gripper_pub.publish(msg)
        time.sleep(1.0)

    def open_gripper(self):
        self.get_logger().info('Opening Gripper')
        self.set_gripper(-0.04, 0.04)

    def close_gripper(self):
        self.get_logger().info('Closing Gripper')
        self.set_gripper(0.0, 0.0)

    def move_to_home(self):
        self.get_logger().info('Moving to home position')
        self.send_trajectory(self.current_joints, [0.0] * 6, duration=2.5)


def main(args=None):
    rclpy.init(args=args)
    node = PickAndPlaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()