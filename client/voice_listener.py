import os
import sys
import pyaudio
import asyncio
from vosk import Model, KaldiRecognizer


class VoskListener:
    def __init__(
        self,
        wake_word: str,
        model_path: str,
        callback: callable,
        loop: asyncio.events.AbstractEventLoop,
    ):
        self.wake_word = wake_word
        self.loop = loop
        self.model_path = model_path
        self.callback = callback
        # Load the Vosk model
        if not os.path.exists(model_path):
            print("Model not found. Please download and extract it.")
            sys.exit(1)

    async def start(self):
        """
        Start the voice listening model
        """
        return await asyncio.to_thread(self._listen)

    def _listen(self):
        """
        Start listening. This function is blocking
        """
        model = Model(self.model_path)

        # Initialize the microphone
        mic = pyaudio.PyAudio()
        stream = mic.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=4800,
        )
        stream.start_stream()

        rec = KaldiRecognizer(model, 48000)

        print("Listening for wake word...")

        while True:
            data = stream.read(4800, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = rec.Result()
                if self.wake_word.lower() in result.lower():
                    future = asyncio.run_coroutine_threadsafe(self.callback(result), self.loop)
                    try:
                        future.result()
                    except Exception as ex:
                        print(f"Error occured: {ex}")
                    print("Wake word detected!")
