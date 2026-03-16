#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import glob
import time

class KittiPublisher(Node):
    def __init__(self):
        super().__init__('kitti_publisher')
        self.publisher_ = self.create_publisher(Image, '/camera/image_raw', 10)
        
        self.declare_parameter('dataset_path', '/dataset/2011_09_26_drive_0014_sync/image_02/data')
        self.declare_parameter('fps', 10.0)
        
        self.dataset_path = self.get_parameter('dataset_path').get_parameter_value().string_value
        self.fps = self.get_parameter('fps').get_parameter_value().double_value
        
        self.bridge = CvBridge()
        
        self.image_files = sorted(glob.glob(os.path.join(self.dataset_path, '*.png')))
        if not self.image_files:
            self.get_logger().error(f"No images found in {self.dataset_path}")
            return
            
        self.current_idx = 0
        self.timer = self.create_timer(1.0 / self.fps, self.timer_callback)
        self.get_logger().info(f"Started publishing {len(self.image_files)} images at {self.fps} FPS")

    def timer_callback(self):
        if self.current_idx >= len(self.image_files):
            self.current_idx = 0 # Loop the dataset
            
        img_path = self.image_files[self.current_idx]
        cv_image = cv2.imread(img_path)
        
        if cv_image is not None:
            # KITTI images are often large, optionally resize or just publish
            # cv_image = cv2.resize(cv_image, (640, 480))
            msg = self.bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_frame'
            self.publisher_.publish(msg)
            
        self.current_idx += 1

def main(args=None):
    rclpy.init(args=args)
    kitti_publisher = KittiPublisher()
    
    try:
        rclpy.spin(kitti_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        kitti_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
