from simple_pid import PID


class LowPassFilter:
    def __init__(self, alpha=0.2):
        self.alpha = alpha
        self.prev_output = 0

    def filter(self, input_value):
        self.prev_output = self.alpha * input_value \
            + (1 - self.alpha) * self.prev_output
        return self.prev_output


pid_x = PID(Kd=0.1, Kp=0.1, Ki=0.05)
pid_y = PID(Kd=0.1, Kp=0.1, Ki=0.05)
pid_z = PID(Kd=0.1, Kp=0.1, Ki=0.05)
f_x = LowPassFilter().filter
f_y = LowPassFilter().filter
f_z = LowPassFilter().filter


def smooth(x, y, z):
    """
    smoothes the input values
    """
    return [pid_x(f_x(x)), pid_y(f_y(y)), pid_z(f_z(z))]
