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

# Joint names used by the ros2_controller (trajectory publishing & JointState)
JOINTS = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']

# Link names as ikpy sees them — child link of each revolute joint above
LINK_NAMES = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5', 'link_6']

# Arm base in world frame (from URDF base_joint origin)
BASE_X = 0.0
BASE_Y = -0.8
BASE_Z = 0.75




FINGER_CENTER_DEPTH = 0.05  
FINGER_TIP_DEPTH    = 0.10  


GRASP_OFFSET    = 0.24   
                     
                        

APPROACH_OFFSET = 0.40   
GRASP_FLOOR     = -0.05            


# Bins in world: x=1.05, y={-0.4, 0.0, 0.4}, z origin at 0.75 + 0.30 wall = rim at 1.05
# Drop 5 cm above rim → z = 1.10 - 0.75 = 0.35 in base frame
BIN_POSITIONS = {
    'red':   (1.05 - BASE_X, -0.4 - BASE_Y, 1.10 - BASE_Z),
    'green': (1.05 - BASE_X,  0.0 - BASE_Y, 1.10 - BASE_Z),
    'blue':  (1.05 - BASE_X,  0.4 - BASE_Y, 1.10 - BASE_Z),
}


class PickAndPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_and_place')

        self.chain = None
        self.current_joints = [0.0] * 6
        self.is_moving = False
        self.processed_cubes = []

        self.arm_pub = self.create_publisher(
            JointTrajectory, '/r6bot_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(
            Float64MultiArray, '/gripper_controller/commands', 10)

        self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, 10)
        self.create_subscription(
            String, '/detected_cubes', self.detection_callback, 10)

        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(
            String, '/robot_description', self.urdf_callback, qos)

        self.get_logger().info('Pick-and-place node started — waiting for URDF & detections...')

    def joint_state_callback(self, msg):
        for i, name in enumerate(msg.name):
            if name in JOINTS:
                self.current_joints[JOINTS.index(name)] = msg.position[i]

    def urdf_callback(self, msg):
        if self.chain is not None:
            return

        self.get_logger().info('Received URDF — initializing ikpy chain...')

        # Strip gripper joints so the chain ends at tool0
        clean_urdf = re.sub(r'<joint name="gripper.*?</joint>', '', msg.data, flags=re.DOTALL)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write(clean_urdf)
            temp_path = f.name

        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')

                temp_chain = ikpy.chain.Chain.from_urdf_file(temp_path)

                # Active = any non-fixed joint (revolute/prismatic)
                active_mask = [lnk.joint_type != 'fixed' for lnk in temp_chain.links]

                self.chain = ikpy.chain.Chain.from_urdf_file(
                    temp_path, active_links_mask=active_mask)

            self.get_logger().info(
                f'ikpy ready — {len(self.chain.links)} links, {sum(active_mask)} active')
        except Exception as e:
            self.get_logger().error(f'Failed to init ikpy: {e}')
        finally:
            os.remove(temp_path)

    def detection_callback(self, msg):
        if self.is_moving or self.chain is None:
            return

        detections = json.loads(msg.data)
        if not detections:
            return

        new_cubes = [d for d in detections if not self._already_processed(d)]
        if not new_cubes:
            return

        self.get_logger().info(
            f'{len(new_cubes)} new cubes to pick '
            f'(filtered {len(detections) - len(new_cubes)} already done)')
        threading.Thread(target=self.process_cubes, args=(new_cubes,), daemon=True).start()

    def _already_processed(self, cube, threshold=0.05):
        return any(
            abs(cube['x'] - px) < threshold and abs(cube['y'] - py) < threshold
            for px, py in self.processed_cubes
        )

    def process_cubes(self, detections):
        self.is_moving = True

        for cube in detections:
            color = cube['color']

            # Convert world → arm-base frame
            rx = cube['x'] - BASE_X
            ry = cube['y'] - BASE_Y
            rz = cube['z'] - BASE_Z   # cube TOP surface in base frame

            grasp_z    = max(GRASP_FLOOR, rz + GRASP_OFFSET)
            approach_z = rz + APPROACH_OFFSET

            self.get_logger().info(
                f'Picking {color} cube | world({cube["x"]:.3f},{cube["y"]:.3f},{cube["z"]:.3f}) '
                f'base({rx:.3f},{ry:.3f},{rz:.3f}) '
                f'approach_z={approach_z:.3f} grasp_z={grasp_z:.3f}')

            # ── 1. Open gripper ──────────────────────────────────────────
            self.open_gripper()

            # ── 2. Move above cube ───────────────────────────────────────
            if not self.move_arm_to(rx, ry, approach_z):
                self.get_logger().warn(f'Cannot reach approach for {color}, skipping')
                continue

            # ── 3. Lower to grasp ────────────────────────────────────────
            if not self.move_arm_to(rx, ry, grasp_z):
                self.get_logger().warn(f'Cannot reach grasp for {color}, skipping')
                self.move_arm_to(rx, ry, approach_z)   # back up safely
                continue

            # ── 4. Close gripper ─────────────────────────────────────────
            self.close_gripper()

            # ── 5. Lift cube ──────────────────────────────────────────────
            self.move_arm_to(rx, ry, approach_z)

            # ── 6. Carry to bin ───────────────────────────────────────────
            bx, by, bz = BIN_POSITIONS.get(color, BIN_POSITIONS['red'])
            # Transit height: high enough to clear the cube and bin walls
            transit_z = max(approach_z, bz + 0.10)
            self.move_arm_to(bx, by, transit_z)

            # ── 7. Release ────────────────────────────────────────────────
            self.open_gripper()

            self.processed_cubes.append((cube['x'], cube['y']))
            self.get_logger().info(
                f'Placed {color} cube — {len(self.processed_cubes)} total processed')

            # ── 8. Return home ────────────────────────────────────────────
            self.move_to_home()
            break   # one cube per trigger; perception will re-detect the rest

        self.is_moving = False
        self.get_logger().info('Sequence complete — ready for next detection')

    # ── IK / motion helpers ───────────────────────────────────────────────────

    def move_arm_to(self, x, y, z):
        q_init = [0.0] * len(self.chain.links)
        for i, link in enumerate(self.chain.links):
            if link.name in JOINTS:                              # not LINK_NAMES
                q_init[i] = self.current_joints[JOINTS.index(link.name)]

        target = [x, y, z]

        ik_sol = self.chain.inverse_kinematics(
            target_position=target,
            target_orientation=np.array([0.0, 0.0, -1.0]),
            orientation_mode='Z',
            initial_position=q_init,
        )

        best_joints = [0.0] * 6
        for i, link in enumerate(self.chain.links):
            if link.name in JOINTS:                              # not LINK_NAMES
                best_joints[JOINTS.index(link.name)] = ik_sol[i]

        best_joints = [max(-3.14, min(3.14, j)) for j in best_joints]

            # FK sanity check
        fk_pos = self.chain.forward_kinematics(ik_sol)[:3, 3]
        err = np.linalg.norm(fk_pos - np.array(target))

        if err > 0.05:
            self.get_logger().warn(
                f'IK failed for ({x:.3f},{y:.3f},{z:.3f}) — err {err:.3f} m')
            return False

        self.get_logger().info(
            f'→ ({x:.3f},{y:.3f},{z:.3f})  FK err={err:.4f} m')
        self.send_trajectory(self.current_joints, best_joints, duration=2.5)
        return True

    def send_trajectory(self, start_joints, end_joints, duration, n_pts=50):
        """Publish a smooth cosine-profile trajectory with velocities."""
        traj = JointTrajectory()
        traj.joint_names = JOINTS

        for i in range(n_pts):
            t = i / (n_pts - 1) * duration
            alpha     = (1.0 - math.cos(math.pi * t / duration)) / 2.0
            alpha_dot = math.pi / (2.0 * duration) * math.sin(math.pi * t / duration)

            pt = JointTrajectoryPoint()
            pt.positions  = [start_joints[j] + alpha     * (end_joints[j] - start_joints[j]) for j in range(6)]
            pt.velocities = [                  alpha_dot * (end_joints[j] - start_joints[j]) for j in range(6)]
            pt.time_from_start = Duration(sec=int(t), nanosec=int((t % 1) * 1e9))
            traj.points.append(pt)

        self.arm_pub.publish(traj)
        time.sleep(duration + 0.5)

    def set_gripper(self, left_val, right_val):
        msg = Float64MultiArray()
        msg.data = [left_val, right_val]
        self.gripper_pub.publish(msg)
        time.sleep(1.0)

    def close_gripper(self):
        self.get_logger().info('Closing gripper')
        self.set_gripper(-0.06, 0.06)   

    def open_gripper(self):
        self.get_logger().info('Opening gripper')
        self.set_gripper(0.0, 0.0)    

    def move_to_home(self):
        self.get_logger().info('Returning home')
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