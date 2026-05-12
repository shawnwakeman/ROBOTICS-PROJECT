

import math
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

JOINTS = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
TARGET_RAD = math.pi / 2.0   # 90 degrees
SWEEP_SECS = 3.0              # seconds per leg
N_PTS = 50                    # waypoints per leg (100 total, like send_trajectory uses 200)
REPEAT_PERIOD = SWEEP_SECS * 2 + 2.0  # pause between sweeps


def _build_leg(start_rad, end_rad, duration, n_pts, t_offset):

    points = []
    n = len(JOINTS)
    for i in range(n_pts):
        t = i / (n_pts - 1) * duration
        # Smooth step: alpha goes 0→1 with zero vel at endpoints
        alpha = (1.0 - math.cos(math.pi * t / duration)) / 2.0
        pos = start_rad + alpha * (end_rad - start_rad)
        # Analytical derivative of alpha w.r.t. t
        vel = (end_rad - start_rad) * math.pi / (2.0 * duration) * math.sin(math.pi * t / duration)

        t_abs = t_offset + t
        pt = JointTrajectoryPoint()
        pt.positions = [pos] * n
        pt.velocities = [vel] * n
        pt.time_from_start = Duration(sec=int(t_abs), nanosec=int((t_abs % 1) * 1e9))
        points.append(pt)
    return points


class JointSweepDemo(Node):
    def __init__(self):
        super().__init__('joint_sweep_demo')

        self._pub = self.create_publisher(
            JointTrajectory, '/r6bot_controller/joint_trajectory', 10)

        self._sweep_count = 0
        # Wait 2s for controller to be fully active, then send; repeat every REPEAT_PERIOD
        self._timer = self.create_timer(2.0, self._first_sweep)
        self.get_logger().info(
            f'Joint sweep demo ready — first sweep in 2s '
            f'(repeating every {REPEAT_PERIOD:.0f}s, {N_PTS * 2 - 1} waypoints)')

    def _first_sweep(self):
        self._timer.cancel()
        self._send_sweep()
        self._timer = self.create_timer(REPEAT_PERIOD, self._send_sweep)

    def _send_sweep(self):
        # Leg 1: 0° → 90°  (t = 0 … SWEEP_SECS)
        leg_out = _build_leg(0.0, TARGET_RAD, SWEEP_SECS, N_PTS, t_offset=0.0)
        # Leg 2: 90° → 0°  (t = SWEEP_SECS … 2*SWEEP_SECS), skip duplicate boundary point
        leg_back = _build_leg(TARGET_RAD, 0.0, SWEEP_SECS, N_PTS, t_offset=SWEEP_SECS)

        traj = JointTrajectory()
        traj.joint_names = JOINTS
        traj.points = leg_out + leg_back[1:]

        self._pub.publish(traj)
        self._sweep_count += 1
        self.get_logger().info(
            f'Sweep #{self._sweep_count}: all joints 0 → 90° → 0 '
            f'({SWEEP_SECS:.0f}s each leg, sinusoidal profile)')


def main(args=None):
    rclpy.init(args=args)
    node = JointSweepDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
