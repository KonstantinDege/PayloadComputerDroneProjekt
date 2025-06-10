.. _sitl_installation:

SITL Installation Guide
=======================

This guide provides step-by-step instructions for installing and configuring
the Software-In-The-Loop (SITL) simulation environment.


Start with
----------

- `PX4 SITL Documentation <https://docs.px4.io/main/en/dev_setup/dev_env_windows_wsl.html>`_

Then just clone the repo into the same environment (WSL then also in WSL). Then
install the package with pip, you will probably need a virtual environment but
make sure that ``include-system-site-packages`` is set to true.

Then you can just run the script as usual. You only need to check which ip you
need to set where. If you are running in WSL you will probably just need to use
the WSL IP or when using VS Code the ports could also have been forwarded
automaticly. Then using localhost is sufficent. 