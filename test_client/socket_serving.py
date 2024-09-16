import socket
import sounddevice as sd
import os

# Open a socket to the server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.getenv("server_ip"), 6455))


# Callback to stream audio to the server
def audio_callback(indata, frames, time, status):
    sock.sendall(indata)


# Start capturing audio and streaming it
with sd.InputStream(
    samplerate=16000, channels=1, dtype="int16", callback=audio_callback
):
    print("Streaming audio to the server...")
    sd.sleep(100000)  # Keep the stream open
