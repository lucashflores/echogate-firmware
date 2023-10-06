import cv2
import os

output_folder = 'henrique'
dataset_folder = 'dataset'

output_folder = dataset_folder + '/' + output_folder

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

image_counter = 0

# Inicialize a webcam
cap = cv2.VideoCapture(0)

while True:
    # Capture um frame da webcam
    ret, frame = cap.read()

    # Exiba o frame em uma janela
    cv2.imshow('Webcam', frame)

    if cv2.waitKey(1) & 0xFF == ord(' '):
        image_name = os.path.join(output_folder, f'image_{image_counter}.jpg')
        cv2.imwrite(image_name, frame)
        print(f'Imagem salva como {image_name}')
        image_counter += 1

    # Verifique se a tecla 'q' foi pressionada para sair do loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libere a webcam e feche a janela
cap.release()
cv2.destroyAllWindows()