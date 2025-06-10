.. _raspi_installation:

Raspberry Pi Installation Guide
===============================

This guide provides step-by-step instructions for setting up the Raspberry Pi for the Payload Computer Drone Project.


Introduction
------------

Follow the sections below to prepare your Raspberry Pi for use in the project.

Connect the Raspi as discribed in the PX4 dokumentation and make sure you use
the same bit rate as used in your start file.

Install the Picamera2 package. 

.. code-block:: bash

    sudo apt install python3-picamera2

Clone and install the repo into a virtual environment on the Raspi. Make sure
``include-system-site-packages`` is set to true, else it will not be able to
access the raspicam package.

Configure the config file as needed by your system and requierements.


Autostart
---------
Only do this when you want the script to start on every boot.

.. code-block:: bash

    mkdir -p ~/.config/systemd/user
    code ~/.config/systemd/user/start_droneos.service

Then add this to the file, make sure that you replace ``/home/aviator/`` to the
absolute path to your install directory of the package.

.. code-block:: service

    [Unit]
    Description=Start Drone Computer
    After=multi-user.target

    [Service]
    ExecStart=/usr/bin/bash /home/aviator/PayloadComputerDroneProjekt/start_raspi_script.sh
    Type=simple

    [Install]
    WantedBy=multi-user.target

.. code-block:: bash

    systemctl --user daemon-reload
    systemctl --user enable start_droneos.service
    systemctl --user start start_droneos.service

To check on it run 

.. code-block:: bash

    systemctl --user status start_droneos.service