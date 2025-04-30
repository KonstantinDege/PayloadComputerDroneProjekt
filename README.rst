.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/PayloadComputerDroneProjekt.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/PayloadComputerDroneProjekt
    .. image:: https://readthedocs.org/projects/PayloadComputerDroneProjekt/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://PayloadComputerDroneProjekt.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/PayloadComputerDroneProjekt/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/PayloadComputerDroneProjekt

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