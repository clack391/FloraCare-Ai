import cv2
import numpy as np

def enhance_image_for_ai(image_bytes):
    # 1. Decode Image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return image_bytes # Fallback if decoding fails

    # 2. Denoise (Fixes the "Background Noise" issue)
    # A 5x5 blur smooths out the "grain" in the dark room background
    img_blurred = cv2.GaussianBlur(img, (5, 5), 0)

    # 3. LAB Conversion & Mild Contrast
    lab = cv2.cvtColor(img_blurred, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Use a gentler CLAHE (Clip Limit 2.0 instead of 3.0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)

    # Merge back
    lab_merged = cv2.merge((l_enhanced, a, b))
    img_enhanced = cv2.cvtColor(lab_merged, cv2.COLOR_LAB2BGR)

    # 4. Create a "Focus Mask" (Vignette)
    # This slightly darkens the borders to tell AI: "Look at the center"
    rows, cols = img_enhanced.shape[:2]
    
    # Generate Gaussian kernel for vignette
    X_kernel = cv2.getGaussianKernel(cols, cols/2.5)
    Y_kernel = cv2.getGaussianKernel(rows, rows/2.5)
    kernel = Y_kernel * X_kernel.T
    mask = kernel / kernel.max()
    
    # Apply vignette (darken corners)
    img_focus = np.copy(img_enhanced)
    for i in range(3): # Apply to each channel (B, G, R)
        img_focus[:, :, i] = img_focus[:, :, i] * mask

    # 5. Encode back to Bytes
    _, encoded_img = cv2.imencode('.jpg', img_focus)
    return encoded_img.tobytes()
