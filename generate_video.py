import cv2
import numpy as np
import os

os.makedirs('media/sample', exist_ok=True)
out = cv2.VideoWriter('media/sample/test.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))

for i in range(150): # 5 seconds
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, f'Frame {i}', (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    out.write(frame)

out.release()
print("Test video created.")
