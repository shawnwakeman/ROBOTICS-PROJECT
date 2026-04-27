#!/usr/bin/env python3
"""
Debug script — capture one frame from the overhead camera,
save the raw image and color masks to /tmp for inspection.
Also print HSV values at various points.

Usage: python3 debug_perception.py
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class DebugPerception(Node):
    def __init__(self):
        super().__init__('debug_perception')
        self.bridge = CvBridge()
        self.got_image = False
        self.create_subscription(
            Image, '/overhead_camera/image', self.callback, 10)
        self.get_logger().info('Waiting for camera image...')

    def callback(self, msg):
        if self.got_image:
            return
        self.got_image = True

        self.get_logger().info(
            f'Got image: {msg.width}x{msg.height}, encoding={msg.encoding}')

        # Convert to BGR
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Conversion failed: {e}')
            # Try without encoding
            cv_image = self.bridge.imgmsg_to_cv2(msg)
            self.get_logger().info(f'Raw image shape={cv_image.shape}, dtype={cv_image.dtype}')

        # Save raw image
        cv2.imwrite('/tmp/camera_raw.png', cv_image)
        self.get_logger().info('Saved /tmp/camera_raw.png')

        # Convert to HSV
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        # Print HSV values at grid points
        h, w = cv_image.shape[:2]
        self.get_logger().info(f'Image size: {w}x{h}')
        self.get_logger().info('--- HSV samples across image ---')
        for row_frac in [0.25, 0.5, 0.75]:
            for col_frac in [0.25, 0.5, 0.75]:
                r = int(row_frac * h)
                c = int(col_frac * w)
                bgr = cv_image[r, c]
                hsv_val = hsv[r, c]
                self.get_logger().info(
                    f'  pixel({c},{r}): BGR={bgr}, HSV={hsv_val}')

        # Find all non-gray pixels (potential cubes)
        # Gray/white pixels have low saturation
        sat = hsv[:, :, 1]
        colored_mask = sat > 50
        colored_pixels = np.where(colored_mask)

        if len(colored_pixels[0]) > 0:
            self.get_logger().info(
                f'Found {len(colored_pixels[0])} colored pixels (saturation > 50)')

            # Sample some colored pixels
            indices = np.random.choice(
                len(colored_pixels[0]),
                min(20, len(colored_pixels[0])),
                replace=False)
            for idx in indices:
                r = colored_pixels[0][idx]
                c = colored_pixels[1][idx]
                bgr = cv_image[r, c]
                hsv_val = hsv[r, c]
                self.get_logger().info(
                    f'  colored pixel({c},{r}): BGR={bgr}, HSV={hsv_val}')
        else:
            self.get_logger().warn('No colored pixels found! (all saturation < 50)')
            # Show saturation stats
            self.get_logger().info(
                f'Saturation stats: min={sat.min()}, max={sat.max()}, '
                f'mean={sat.mean():.1f}')

        # Generate masks for each color
        color_ranges = {
            'red': [
                (np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255])),
            ],
            'green': [
                (np.array([35, 100, 100]), np.array([85, 255, 255])),
            ],
            'blue': [
                (np.array([100, 100, 100]), np.array([140, 255, 255])),
            ],
        }

        for color_name, ranges in color_ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                mask |= cv2.inRange(hsv, lower, upper)
            pixel_count = cv2.countNonZero(mask)
            cv2.imwrite(f'/tmp/mask_{color_name}.png', mask)
            self.get_logger().info(
                f'{color_name} mask: {pixel_count} pixels, '
                f'saved /tmp/mask_{color_name}.png')

            # Find contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.get_logger().info(
                f'  {color_name} contours: {len(contours)}, '
                f'areas: {[int(cv2.contourArea(c)) for c in contours]}')

        # Save annotated image with all colored regions highlighted
        annotated = cv_image.copy()
        annotated[colored_mask] = [0, 255, 255]  # highlight in yellow
        cv2.imwrite('/tmp/camera_colored.png', annotated)
        self.get_logger().info('Saved /tmp/camera_colored.png')

        self.get_logger().info('=== Debug complete — check /tmp/ for images ===')
        rclpy.shutdown()


def main():
    rclpy.init()
    node = DebugPerception()
    rclpy.spin(node)


if __name__ == '__main__':
    main()