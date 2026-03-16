#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
from flask import Flask, Response, render_template, jsonify
from flask_socketio import SocketIO
import base64
import time
import os
from ament_index_python.packages import get_package_share_directory
from rosidl_runtime_py.utilities import get_message

package_share_directory = get_package_share_directory('ros2_flask_ui')
template_dir = os.path.join(package_share_directory, 'templates')
static_dir = os.path.join(package_share_directory, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

class FlaskRosNode(Node):
    def __init__(self):
        super().__init__('flask_webapp')
        self.bridge = CvBridge()
        
        self.raw_subscription = self.create_subscription(
            Image, '/camera/image_raw', self.raw_callback, 10)
        self.seg_subscription = self.create_subscription(
            Image, '/camera/segmentation', self.seg_callback, 10)
            
        self.raw_frame = None
        self.seg_frame = None
        self.lock = threading.Lock()
        
        self.dynamic_subs = {}

        # Timer to publish ROS graph info
        self.create_timer(1.0, self.publish_graph)

    def raw_callback(self, msg):
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        _, buffer = cv2.imencode('.jpg', cv_img)
        with self.lock:
            self.raw_frame = buffer.tobytes()

    def seg_callback(self, msg):
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        _, buffer = cv2.imencode('.jpg', cv_img)
        with self.lock:
            self.seg_frame = buffer.tobytes()

    def publish_graph(self):
        # Introspect ROS2 graph
        topics = self.get_topic_names_and_types()
        services = self.get_service_names_and_types()
        
        # Format for UI
        topics_json = [{"name": t[0], "types": t[1]} for t in topics]
        services_json = [{"name": s[0], "types": s[1]} for s in services]
        
        socketio.emit('ros_data', {'topics': topics_json, 'services': services_json})

    def subscribe_dynamic_topic(self, topic_name, topic_type):
        if topic_name in self.dynamic_subs:
            return
            
        try:
            if isinstance(topic_type, list):
                topic_type = topic_type[0]
                
            msg_class = get_message(topic_type)
            
            def callback(msg):
                msg_str = repr(msg)
                if len(msg_str) > 2000:
                    msg_str = msg_str[:2000] + "\n... [truncated]"
                socketio.emit('topic_data', {'topic': topic_name, 'data': msg_str})
                
            sub = self.create_subscription(msg_class, topic_name, callback, 10)
            self.dynamic_subs[topic_name] = sub
            self.get_logger().info(f"Subscribed to {topic_name}")
        except Exception as e:
            self.get_logger().error(f"Failed to subscribe to {topic_name}: {e}")

    def unsubscribe_dynamic_topic(self, topic_name):
        if topic_name in self.dynamic_subs:
            self.destroy_subscription(self.dynamic_subs[topic_name])
            del self.dynamic_subs[topic_name]
            self.get_logger().info(f"Unsubscribed from {topic_name}")

ros_node = None

def generate_frames(stream_type):
    global ros_node
    while True:
        frame = None
        if ros_node:
            with ros_node.lock:
                if stream_type == 'raw':
                    frame = ros_node.raw_frame
                elif stream_type == 'seg':
                    frame = ros_node.seg_frame
                    
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream/raw')
def stream_raw():
    return Response(generate_frames('raw'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream/seg')
def stream_seg():
    return Response(generate_frames('seg'), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('subscribe_topic')
def handle_subscribe(data):
    topic_name = data.get('topic')
    topic_type = data.get('type')
    if ros_node and topic_name and topic_type:
        ros_node.subscribe_dynamic_topic(topic_name, topic_type)

@socketio.on('unsubscribe_topic')
def handle_unsubscribe(data):
    topic_name = data.get('topic')
    if ros_node and topic_name:
        ros_node.unsubscribe_dynamic_topic(topic_name)

def spin_ros():
    global ros_node
    rclpy.init()
    ros_node = FlaskRosNode()
    rclpy.spin(ros_node)
    ros_node.destroy_node()
    rclpy.shutdown()

def main():
    threading.Thread(target=spin_ros, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
