from websocket import create_connection
import json
import cv2
import numpy as np
import base64

started = False
cap=cv2.VideoCapture(0)
ws = create_connection("ws://localhost:3000/websocket/image-stream")
i = 0
while True:
        ret,frame=cap.read()
        ret, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        ws.send(json.dumps({"event": "stream", "data": str(jpg_as_text)}))
        i += 1