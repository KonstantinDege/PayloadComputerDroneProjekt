===========================
PayloadComputerDroneProjekt
===========================


    https://konstantindege.github.io/PayloadComputerDroneProjekt/


=====
Setup
=====

1. install following

   https://docs.px4.io/main/en/dev_setup/dev_env_windows_wsl.html


2. run simulation

    .. code-block:: bash 
        
        export PX4_HOME_LAT=48.7678933
        export PX4_HOME_LON=11.3365773
        export PX4_HOME_ALT=375


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


======
Helper
======

1. PowerToys Color Picker

    .. code-block::

        LAB(L = %Lc, A = %Ca, B = %Cb)


2. Cron Tab

    echo 'export PATH="$HOME/PayloadComputerDroneProjekt:$PATH"' >> ~/.bashrc

    crontab -e

    @reboot start_raspi_script.sh

3. Systemd


    mkdir -p ~/.config/systemd/user
    
    code ~/.config/systemd/user/start_droneos.service

    [Unit]
    Description=Start Drone Computer
    After=multi-user.target

    [Service]
    ExecStart=/usr/bin/bash /home/aviator/PayloadComputerDroneProjekt/start_raspi_script.sh
    Type=simple

    [Install]
    WantedBy=multi-user.target
    
    systemctl --user daemon-reload
    systemctl --user enable start_droneos.service
    systemctl --user start start_droneos.service

    
    systemctl --user status start_droneos.service

    
    journalctl -u start_droneos.service

==========
Build docs
==========

1. Install Sphinx and dependencies

    .. code-block:: bash

        pip install sphinx sphinx-autobuild pydata-sphinx-theme

    .. code-block:: bash

        sphinx-autobuild docs_src docs
