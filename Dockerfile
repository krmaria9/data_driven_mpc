FROM ros:melodic

ENV USERNAME krmaria
ENV HOME /home/$USERNAME

RUN useradd -m $USERNAME && \
    echo "$USERNAME:$USERNAME" | chpasswd && \
    usermod --shell /bin/bash $USERNAME && \
    usermod -aG sudo $USERNAME && \
    mkdir -p /etc/sudoers.d && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    usermod  --uid 1000 $USERNAME && \
    groupmod --gid 1000 $USERNAME

USER ${USERNAME}
WORKDIR ${HOME}

RUN sudo apt-get update

# GCC-9
RUN sudo apt-get install -y software-properties-common
RUN sudo add-apt-repository ppa:ubuntu-toolchain-r/test
RUN sudo apt-get update
RUN sudo apt-get install -y gcc-9 g++-9

# Set gcc-9 default GCC compiler
RUN sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 60 --slave /usr/bin/g++ g++ /usr/bin/g++-9

# Install miniconda
RUN sudo apt-get install wget
ENV CONDA_DIR ${HOME}/.conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
RUN sudo /bin/bash ~/miniconda.sh -b -p $CONDA_DIR
RUN sudo chown -R ${USERNAME}:${USERNAME} $CONDA_DIR

# create a new environment with Python 3.6
RUN $CONDA_DIR/bin/conda create -n myenv python=3.6
# initialize shell for conda
RUN echo ". ${CONDA_DIR}/etc/profile.d/conda.sh" >> ~/.bashrc

# activate the new environment
RUN echo "conda activate myenv" >> ~/.bashrc

SHELL ["/bin/bash", "--login", "-c"]

RUN sudo apt-get install -y \
    vim \
    git \
    python3-setuptools \
    python3 \
    python3-pip \
    python3-dev \
    libjpeg-dev

# Activate conda environment
RUN /bin/bash -c ". ${CONDA_DIR}/etc/profile.d/conda.sh && conda activate myenv"

# Then use pip
RUN pip3 install catkin-tools scipy rospkg catkin_pkg

# Create a catkin workspace
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash"
RUN mkdir -p catkin_ws/src
RUN cd catkin_ws && catkin config --init --mkdirs --extend /opt/ros/$ROS_DISTRO --merge-devel --cmake-args -DCMAKE_BUILD_TYPE=Release

CMD "sudo /etc/init.d/dbus start"

