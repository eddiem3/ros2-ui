# ROS 2 Semantic Segmentation Dashboard

This project provides a modern, interactive web dashboard to visualize ROS 2 data streams from a custom computer vision pipeline running Semantic Segmentation on a KITTI dataset. It bridges a ROS 2 system with a web frontend using Flask and Socket.IO.

## Features

- **Draggable & Resizable Panes**: Customize your layout seamlessly.
- **Real-time Video Streaming**: View both the original and segment-overlay feeds simultaneously with minimal latency via MJPEG.
- **Active ROS Telemetry**: Socket.IO automatically bridges internal ROS node/topic polling directly to frontend display tables updating in real time.
- **Dynamic Data Introspection**: Click on any running topic listed in the "Active Topics" table to open a live modal streaming the raw data messages in real time.
- **Persistent State**: Toggle switches lock viewable feeds or data telemetry panes on and off without crashing layout.

## Tech Stack

- **Backend**: ROS 2 (Humble), Python, Flask, Flask-SocketIO, rclpy
- **Computer Vision**: OpenCV, PyTorch, Torchvision (DeepLabV3 ResNet50)
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript, GridStack.js, Socket.IO Client
- **Deployment**: Docker & Docker Compose

## Installation

This application is fully containerized using Docker, so you do not need to install ROS 2 locally on your system. 

### Prerequisites
- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- A local copy of the KITTI dataset frames inside an accessible directory (configured in `docker-compose.yml` and `kitti_publisher.py`).

### Setup
1. Clone the repository and navigate into the root directory.
2. Ensure you have the KITTI dataset placed appropriately. The default configuration expects frames located at: `./2011_09_26/2011_09_26_drive_0014_sync/image_02/data` relative to the workspace mount. You can modify the `dataset_path` parameter in `src/ros2_flask_ui/ros2_flask_ui/kitti_publisher.py` or the docker volume mount if yours is elsewhere.
3. Build the Docker container:
   ```bash
   docker compose build
   ```

## Running the Application

1. Start the containerized ROS 2 environment in the background:
   ```bash
   docker compose up -d
   ```
2. The initial startup may take a few seconds as the PyTorch node downloads the pre-trained DeepLabV3 weights. You can monitor the logs with:
   ```bash
   docker compose logs -f
   ```
3. Once the logs indicate that the Flask development server is running and the model is loaded, open your web browser and navigate to:
   ```
   http://localhost:5000
   ```
4. **Usage:**
   - Drag the headers of panes to move them.
   - Resize panes using the handles on their edges.
   - Use the toggles on the left sidebar to hide or show specific feeds or telemetry tables.
   - **Click on any topic row** in the "Active Topics" table to open a live data introspection modal.

5. To shut down the container, run:
   ```bash
   docker compose down
   ```

## Tips for Development

- **Rebuilding after changes**: The `docker-compose.yml` mounts the current directory as `/ros2_ws` within the container. If you modify Python scripts (`.py`), you generally need to restart the container or rebuild the ROS 2 space for the changes to take effect:
  ```bash
  # Option A: Restart container to trigger entrypoint colcon build
  docker compose restart ros_app
  
  # Option B: Rebuild inside the running container manually
  docker compose exec ros_app bash -c "colcon build --packages-select ros2_flask_ui && source install/setup.bash"
  ```
- **Frontend Changes**: Edits to files inside `static/` or `templates/` usually reflect immediately or upon a hard browser refresh, since they are served directly by Flask.
- **Node Configuration**:
  - The `kitti_publisher` node publishes images at a default of `10.0` FPS. 
  - The `segmentation_node` runs inference on the CPU by default unless `torch.cuda.is_available()` evaluates to true in the container environment. If you want GPU acceleration, ensure you configure Docker to use the NVIDIA Container Toolkit and modify `docker-compose.yml` with the appropriate `deploy: resources: reservations: devices` block.
- **Logs**: If the UI isn't displaying video frames, check the logs. ROS 2 nodes often die silently if there's a Python Exception (e.g., missing dependencies or filepath errors). `docker compose logs` is your best friend.
