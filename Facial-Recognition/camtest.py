import cv2

cap = cv2.VideoCapture(1)

while True:
    success, img = cap.read()
    if success:
        cv2.imshow("video", img)
        cv2.waitKey(1)
        if 0xFF == ord('q') :
            break