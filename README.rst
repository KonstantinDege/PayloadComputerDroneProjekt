===========================
PayloadComputerDroneProjekt
===========================


    Add a short description here!


A longer description of your project goes here...


=====
Setup
=====

1. install following

   https://docs.px4.io/main/en/dev_setup/dev_env_windows_wsl.html


2. run simulation

    .. code-block:: bash 

        cd && cd PX4-Autopilot/ && HEADLESS=1 make px4_sitl gz_x500_mono_cam_down

        ip addr | grep eth0

3. clone this repo and install this package inside of your wsl instance

    * start wsl in the folder
    * clone repo to folder inside wsl
    * python3 -m venv myenv
    * source myenv/bin/activate
    * ``pip install -e .``
    * gointo myenv foldern and open the conf file and change use global packages to true 

4. move models to simulation

    clone this repo also in the same folder as the PX4-Autopilot

    .. code-block:: bash

        cd ~/PX4-ROS2-Gazebo-Drone-Simulation-Template
        cp -r ./PX4-Autopilot_PATCH/* ~/PX4-Autopilot/

5. https://www.geeksforgeeks.org/using-github-with-ssh-secure-shell/


====
Helper
====

1. PowerToys Color Picker

    .. code-block::

        LAB(L = %Lc, A = %Ca, B = %Cb)


2. Cron Tab

    echo 'export PATH="$HOME/PayloadComputerDroneProjekt:$PATH"' >> ~/.bashrc

    crontab -e

    @reboot start_raspi_script.sh