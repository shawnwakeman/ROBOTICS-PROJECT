#!/usr/bin/env python3
"""
Perception node — detects colored cubes from overhead camera.
Publishes list of (x, y, z, rotation_deg, color) for each detected cube.
Uses direct geometric conversion instead of TF.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import json


class CubePerceptionNode(Node):
    def __init__(self):
        super().__init__('cube_perception')

        self.bridge = CvBridge()

        # Camera data storage
        self.camera_info = None
        self.depth_image = None

        # Camera position in world frame (from URDF camera joint)
        # camera_joint: xyz="0.1 0.2 3.0" relative to table at world origin
        self.cam_x = 0.1
        self.cam_y = 0.2
        self.cam_z = 3.0

        # Subscribers
        self.create_subscription(
            Image, '/overhead_camera/image', self.image_callback, 10)
        self.create_subscription(
            Image, '/overhead_camera/depth_image', self.depth_callback, 10)
        self.create_subscription(
            CameraInfo, '/overhead_camera/camera_info', self.info_callback, 10)

        # Publisher — detected cubes as JSON
        self.detection_pub = self.create_publisher(String, '/detected_cubes', 10)

        # HSV color ranges matching cube colors from Gazebo
        self.color_ranges = {
            'red': [
                (np.array([0, 150, 50]), np.array([10, 255, 255])),
                (np.array([160, 150, 50]), np.array([180, 255, 255])),
            ],
            'green': [
                (np.array([35, 150, 50]), np.array([85, 255, 255])),
            ],
            'blue': [
                (np.array([100, 150, 50]), np.array([140, 255, 255])),
            ],
        }

        # Contour area range — cubes are ~30-300 pixels, bins are ~7000+
        self.min_contour_area = 15
        self.max_contour_area = 500

        self.get_logger().info('Cube perception node started')

    def info_callback(self, msg):
        if self.camera_info is None:
            self.get_logger().info(
                f'Camera info received: {msg.width}x{msg.height}, '
                f'fx={msg.k[0]:.1f}, fy={msg.k[4]:.1f}')
        self.camera_info = msg

    def depth_callback(self, msg):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(
                msg, desired_encoding='passthrough')
        except Exception as e:
            self.get_logger().warn(f'Depth conversion error: {e}',
                                   throttle_duration_sec=5.0)

    def image_callback(self, msg):
        if self.camera_info is None or self.depth_image is None:
            return

        # Convert ROS image to OpenCV BGR
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'Image conversion error: {e}',
                                   throttle_duration_sec=5.0)
            return

        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        detections = []

        for color_name, ranges in self.color_ranges.items():
            # Build combined mask for this color
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                mask |= cv2.inRange(hsv, lower, upper)

            # Light cleanup — only close to fill gaps, no open which erodes small blobs
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)

                # Filter: too small = noise, too big = bins
                if area < self.min_contour_area or area > self.max_contour_area:
                    continue

                # Get rotated bounding rectangle
                rect = cv2.minAreaRect(contour)
                center_px = rect[0]   # (cx, cy) in pixels
                size = rect[1]        # (width, height)
                angle = rect[2]       # degrees from OpenCV

                # Normalize angle for a square
                rotation = angle
                if size[0] < size[1]:
                    rotation = angle + 90.0

                # Convert pixel to world coordinates
                world_pos = self.pixel_to_world(
                    center_px[0], center_px[1])

                if world_pos is None:
                    continue

                detections.append({
                    'x': round(float(world_pos[0]), 4),
                    'y': round(float(world_pos[1]), 4),
                    'z': round(float(world_pos[2]), 4),
                    'rotation_deg': round(float(rotation), 1),
                    'color': color_name,
                    'pixel_u': round(float(center_px[0]), 1),
                    'pixel_v': round(float(center_px[1]), 1),
                    'area_px': round(float(area), 1),
                })

        # Publish detections
        det_msg = String()
        det_msg.data = json.dumps(detections)
        self.detection_pub.publish(det_msg)

        if detections:
            self.get_logger().info(
                f'Detected {len(detections)} cubes: ' +
                ', '.join(
                    f'{d["color"]}({d["x"]:.2f},{d["y"]:.2f},rot={d["rotation_deg"]}°)'
                    for d in detections),
                throttle_duration_sec=2.0)

    def pixel_to_world(self, u, v):
        """
        Convert pixel (u, v) to world (x, y, z) using depth + intrinsics.

        Camera is overhead looking straight down with rpy="0 pi/2 0".
        Gazebo camera convention: +X forward, +Y left, +Z up.
        With Ry(pi/2): camera +X -> world -Z, camera +Y -> world +Y, camera +Z -> world +X.

        Image mapping:
          u (column, right) -> camera -Y -> world -Y
          v (row, down)     -> camera -Z -> world -X
        """
        if self.depth_image is None or self.camera_info is None:
            return None

        # Clamp pixel coordinates
        v_int = int(np.clip(v, 0, self.depth_image.shape[0] - 1))
        u_int = int(np.clip(u, 0, self.depth_image.shape[1] - 1))

        # Sample depth — median of small region for noise reduction
        v_lo = max(0, v_int - 2)
        v_hi = min(self.depth_image.shape[0], v_int + 3)
        u_lo = max(0, u_int - 2)
        u_hi = min(self.depth_image.shape[1], u_int + 3)
        depth_region = self.depth_image[v_lo:v_hi, u_lo:u_hi]

        valid = depth_region[np.isfinite(depth_region) & (depth_region > 0)]
        if len(valid) == 0:
            return None
        depth = float(np.median(valid))

        # Camera intrinsics
        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        # 3D point in camera frame
        # x_cam = depth (along optical axis)
        # y_cam = -(u - cx) * depth / fx
        # z_cam = -(v - cy) * depth / fy

        # Transform to world using Ry(pi/2):
        # world_x = cam_x + z_cam = cam_x - (v - cy) * depth / fy
        # world_y = cam_y + y_cam = cam_y - (u - cx) * depth / fx
        # world_z = cam_z - x_cam = cam_z - depth

        world_x = self.cam_x - (v - cy) * depth / fy
        world_y = self.cam_y - (u - cx) * depth / fx
        world_z = self.cam_z - depth

        return (world_x, world_y, world_z)


def main(args=None):
    rclpy.init(args=args)
    node = CubePerceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()