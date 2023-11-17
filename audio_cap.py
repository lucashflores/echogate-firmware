import pyaudio
import wave

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True, frames_per_buffer=1024)

frames = []

try:
    while True:
        data = stream.read(1024)
        frames.append(data)

except KeyboardInterrupt:
    pass

stream.stop_stream()
stream.close()
p.terminate()

sound_file = wave.open("audio.wav", "wb")
sound_file.setnchannels(1)
sound_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
sound_file.setframerate(48000)
sound_file.writeframes(b''.join(frames))
sound_file.close()