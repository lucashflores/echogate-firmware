from websocket import create_connection
import face_recognition
import pickle
import numpy as np
import cv2
import base64
import json

def process_base64_image(base64_string):
    binary_data = base64.b64decode(base64_string)
    image_array = np.frombuffer(binary_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return image

def handle(ws, message):

    data = json.loads(message)

    knownEncodings = []
    knownNames = []

    for person_data in data:
        person_name = person_data["name"]
        images_base64 = person_data["images"]
        for image_base64 in images_base64:
            image = process_base64_image(image_base64)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(person_name)
         
    print("[INFO] serializing encodings...")
    data = {"encodings": knownEncodings, "names": knownNames}
    f = open("encodings.pickle", "wb")
    f.write(pickle.dumps(data))
    f.close()

ws = create_connection("ws://localhost:3000/websocket/face-recognition")
ws.on_message = handle

while True:
    result = ws.recv()
    print("After")