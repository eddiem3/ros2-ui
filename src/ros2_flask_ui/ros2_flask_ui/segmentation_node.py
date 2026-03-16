#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import torch
from torchvision import models
from torchvision.models.segmentation import DeepLabV3_ResNet50_Weights
import numpy as np

# VOC color map
def decode_segmap(image, nc=21):
    label_colors = np.array([(0, 0, 0),  # 0=background
                             # 1=aeroplane, 2=bicycle, 3=bird, 4=boat, 5=bottle
                             (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128), (128, 0, 128),
                             # 6=bus, 7=car, 8=cat, 9=chair, 10=cow
                             (0, 128, 128), (128, 128, 128), (64, 0, 0), (192, 0, 0), (64, 128, 0),
                             # 11=dining table, 12=dog, 13=horse, 14=motorbike, 15=person
                             (192, 128, 0), (64, 0, 128), (192, 0, 128), (64, 128, 128), (192, 128, 128),
                             # 16=potted plant, 17=sheep, 18=sofa, 19=train, 20=tv/monitor
                             (0, 64, 0), (128, 64, 0), (0, 192, 0), (128, 192, 0), (0, 64, 128)])
    r = np.zeros_like(image).astype(np.uint8)
    g = np.zeros_like(image).astype(np.uint8)
    b = np.zeros_like(image).astype(np.uint8)
    for l in range(0, nc):
        idx = image == l
        r[idx] = label_colors[l, 0]
        g[idx] = label_colors[l, 1]
        b[idx] = label_colors[l, 2]
    rgb = np.stack([r, g, b], axis=2)
    return rgb

class SegmentationNode(Node):
    def __init__(self):
        super().__init__('segmentation_node')
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.listener_callback,
            1)
            
        self.publisher_ = self.create_publisher(Image, '/camera/segmentation', 1)
        self.bridge = CvBridge()
        
        self.get_logger().info('Loading DeepLabV3 model...')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Using pre-trained weights for quick deployment
        weights = DeepLabV3_ResNet50_Weights.DEFAULT
        self.model = models.segmentation.deeplabv3_resnet50(weights=weights).to(self.device)
        self.model.eval()
        self.transforms = weights.transforms()
        self.get_logger().info('Model loaded.')

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # Convert to tensor and run inference
        # To maintain aspect ratio and performance, resize first
        img_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        input_tensor = self.transforms(torch.from_numpy(img_rgb).permute(2, 0, 1)).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = self.model(input_tensor)['out'][0]
        
        output_predictions = output.argmax(0).byte().cpu().numpy()
        
        # Apply colormap
        seg_img = decode_segmap(output_predictions)
        
        # Resize back to original
        seg_img = cv2.resize(seg_img, (cv_image.shape[1], cv_image.shape[0]))
        
        # Overlay on original image with 0.5 alpha
        overlay = cv2.addWeighted(cv_image, 0.5, cv2.cvtColor(seg_img, cv2.COLOR_RGB2BGR), 0.5, 0)
        
        out_msg = self.bridge.cv2_to_imgmsg(overlay, encoding='bgr8')
        out_msg.header = msg.header
        self.publisher_.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SegmentationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
