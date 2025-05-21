from simple_pid import PID


pid_x = PID(Kd=0.1, Kp=0.1, Ki=0.05)
pid_y = PID(Kd=0.1, Kp=0.1, Ki=0.05)
pid_z = PID(Kd=0.1, Kp=0.1, Ki=0.05)


def smooth(x, y, z):
    """
    smoothes the input values
    """
    return [pid_x(x), pid_y(y), pid_z(z)]
