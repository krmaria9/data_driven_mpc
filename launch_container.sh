#!/bin/sh
DATA_DRIVEN_DIR=${1:-"$HOME/git/data_driven_mpc"}
ACADOS_DIR=${2:-"$HOME/git/acados"}
USERNAME=krmaria
XSOCK=/tmp/.X11-unix
XAUTH=/tmp/.docker.xauth
touch $XAUTH
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -

# Check nVidia GPU docker support
# More info: http://wiki.ros.org/docker/Tutorials/Hardware%20Acceleration
NVIDIA_DOCKER_REQUIREMENT='nvidia-docker2'
GPU_OPTIONS=""
if dpkg --get-selections | grep -q "^$NVIDIA_DOCKER_REQUIREMENT[[:space:]]*install$" >/dev/null; then
  echo "Starting docker with nVidia support!"
  GPU_OPTIONS="--gpus all --runtime=nvidia"
fi

# Check if using tmux conf
TMUX_CONF_FILE=$HOME/.tmux.conf
TMUX_CONF=""
if test -f ${TMUX_CONF_FILE}; then
  echo "Loading tmux config: ${TMUX_CONF_FILE}"
  TMUX_CONF="--volume=$TMUX_CONF_FILE:/home/krmaria/.tmux.conf:ro"
fi

# # Download unity executable if not done already (takes ~60s, skip if not needed)
# if [ ! -f $RPG_FLIGHTMARE_DIR/flightrender/RPG_Flightmare.x86_64 ]; then
#    echo "Downloading RPG_Flightmare.x86_64"
#    wget -P $RPG_FLIGHTMARE_DIR/flightrender/ https://github.com/uzh-rpg/flightmare/releases/latest/download/RPG_Flightmare.tar.xz
#    tar -xf $RPG_FLIGHTMARE_DIR/flightrender/RPG_Flightmare.tar.xz
#    mv $RPG_FLIGHTMARE_DIR/flightrender/RPG_Flightmare/** $RPG_FLIGHTMARE_DIR/flightrender/
#    rm -rf $RPG_FLIGHTMARE_DIR/flightrender/RPG_Flightmare
# fi

docker run --privileged --rm -it \
	         --detach \
           --volume $DATA_DRIVEN_DIR:/home/$USERNAME/catkin_ws/src/data_driven_mpc/:rw \
           --volume $ACADOS_DIR:/home/$USERNAME/catkin_ws/src/data_driven_mpc/externals/acados-src/:rw \
           --volume=$XSOCK:$XSOCK:rw \
           --volume=$XAUTH:$XAUTH:rw \
           --volume=/dev:/dev:rw \
           --volume=/var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket \
           ${TMUX_CONF} \
           ${GPU_OPTIONS} \
           --shm-size=1gb \
           --env="XAUTHORITY=${XAUTH}" \
           --env="DISPLAY=${DISPLAY}" \
           --env=TERM=xterm-256color \
           --env=QT_X11_NO_MITSHM=1 \
           --net=host \
           -u "${USERNAME}"  \
           data_driven_mpc:latest \
           bash

  # Commands to build and run this (with GUI capabilities):
  # docker build --tag "data_driven_mpc:latest" .    # Run from dockerfile directory
  # ./launch_container.sh <your_data_driven_mpc_folder>   # launch the container with all GUI capabilities

