import speech_recognition
import sounddevice

recognizer = speech_recognition.Recognizer()

for index, name in enumerate(speech_recognition.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

while True:

    try:
        with speech_recognition.Microphone(11) as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.2)
            audio = recognizer.listen(mic)
            text = recognizer.recognize_google(audio_data=audio, language="pt-BR")
            text = text.lower()
            print(f"Recognized: {text}")

    except:
        recognizer = speech_recognition.Recognizer()
        continue
