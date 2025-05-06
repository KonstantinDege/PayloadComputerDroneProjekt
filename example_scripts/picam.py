import time
import sys
from picamera2 import Picamera2

picam2 = Picamera2()
preview_config = picam2.create_still_configuration()
picam2.configure(preview_config)

picam2.start()
time.sleep(2)

picam2.capture_file(
    "/home/aviator/PayloadComputerDroneProjekt/tests"
    f"/image_analysis/pixel_imgs/{sys.argv[1]}.png")
