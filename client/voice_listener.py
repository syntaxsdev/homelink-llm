from shared.utils import get_datetime
from datetime import datetime
import os
import sys
import pyaudio
import asyncio
from vosk import Model, KaldiRecognizer
import numpy as np


class VoskListener:
    def __init__(
        self,
        wake_word: str,
        model_path: str,
        callback: callable,
        continous_listen_max: int,
        loop: asyncio.events.AbstractEventLoop,
    ):
        self.wake_word = wake_word
        self.loop = loop
        self.model_path = model_path
        self.callback = callback
        self.continous_listen = False
        self.continous_listen_start: datetime = None
        self.continous_listen_max: int = continous_listen_max
        # Load the Vosk model
        if not os.path.exists(model_path):
            print("Model not found. Please download and extract it.")
            sys.exit(1)

    async def start(self):
        """
        Start the voice listening model
        """
        return await asyncio.to_thread(self._listen)

    def set_continous_listen(self, mode: bool):
        """
        Set continous listening mode

        Args:
            mode: the mode setting
        """
        self.continous_listen = mode
        if mode:
            self.set_continous_listen_start = get_datetime()
            return
        self.continous_listen_start = None

    def continous_listen_check(self):
        """Control the continous listener"""
        if not self.continous_listen_start:
            return
        now = get_datetime()
        delta = now - self.continous_listen_start
        if delta.seconds >= self.continous_listen_max:
            self.set_continous_listen(False)

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

            # audio_data = np.frombuffer(data, dtype=np.int16)
            # mono_data = (audio_data[0::2] + audio_data[1::2]) // 2

            if rec.AcceptWaveform(data):
                result = rec.Result()
                phrase = result.lower()
                
                # Check open mic
                self.continous_listen_check()
                print(phrase)
                if (
                    any(word.lower() in phrase for word in self.wake_word)
                    or self.continous_listen
                ):
                    # disable the continous listen until told to reactivate
                    self.set_continous_listen(False)
                    future = asyncio.run_coroutine_threadsafe(
                        self.callback(result), self.loop
                    )
                    try:
                        future.result()
                    except Exception as ex:
                        print(f"Error occured: {ex}")
                    print("Wake word detected!")
