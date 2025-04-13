import cv2
import numpy as np

def is_image_blurry(image, threshold=200.0):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return variance < threshold, variance




# Beispielnutzung:
image = cv2.imread(r"C:\Users\reich\iCloudDrive\THI\6. Semester\Projekt Drohne\SW_selbst\Testing\Bilder\image_15.jpg")
blurry, sharpness = is_image_blurry(image, threshold=150.0)
denoised = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
denoised1 = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
denoised2 = cv2.medianBlur(image, 5)
denoised3 = cv2.GaussianBlur(image, (5, 5), 0)
sharpen_strength = 1

kernel = np.array([[0, -1, 0],
                    [-1, 5 + sharpen_strength, -1],
                    [0, -1, 0]], dtype=np.float32)
sharpened = cv2.filter2D(denoised, -1, kernel)

cv2.imshow("Denoised Image", sharpened)
cv2.imshow("Denoised Image1", denoised1)
cv2.imshow("Denoised Image2", denoised2)
cv2.imshow("Denoised Image3", denoised3)
cv2.imshow("Original Image", image)
cv2.waitKey(0)
print(f"Schärfewert (Varianz): {sharpness:.2f}")
print("Bild ist unscharf." if blurry else "Bild ist scharf.")
