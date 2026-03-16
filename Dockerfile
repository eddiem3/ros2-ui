FROM ros:humble-perception

# Install python and other dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavcodec-dev \
    libswresample-dev \
    libswscale-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Create a workspace
WORKDIR /ros2_ws
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc
