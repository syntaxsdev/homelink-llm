from shared.utils import get_time
from vosk import Model, KaldiRecognizer

import struct
import os
import sys
import pyaudio
import pvporcupine
import collections
import asyncio
import json
import numpy as np


class VoskListener:
    def __init__(
        self,
        wake_word: str,
        model_path: str,
        pico_keyword_files: str,
        pico_api_key: str,
        callback: callable,
        continous_listen_max: int,
        wake_word_active_max: int,
        loop: asyncio.events.AbstractEventLoop,
    ):
        self.wake_word = wake_word
        self.loop = loop
        self.model_path = model_path
        self.callback = callback
        self.continous_listen = False
        self.continous_listen_start: float = None
        self.continous_listen_max: int = continous_listen_max
        self.wake_word_waiting = wake_word_active_max

        if not pico_api_key:
            raise ValueError("Pico API Key not found")
        if not pico_keyword_files:
            raise ValueError("Pico keywords file not found.")

        if type(pico_keyword_files) is str:
            pico_keyword_files = [pico_keyword_files]

        self.porcupine = pvporcupine.create(
            access_key=pico_api_key,
            keyword_paths=pico_keyword_files,
            sensitivities=[0.7],
        )
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
            self.set_continous_listen_start: float = get_time()
            return
        self.continous_listen_start = None

    def continous_listen_check(self):
        """Control the continous listener"""
        if not self.continous_listen_start:
            return
        now = get_time()
        delta = now - self.continous_listen_start
        if delta.seconds >= self.continous_listen_max:
            self.set_continous_listen(False)

    def _listen(self):
        """
        Start listening. This function is blocking and will capture audio before and after the wake word.
        """
        model = Model(self.model_path)

        # Initialize the microphone (16kHz microphone)
        mic = pyaudio.PyAudio()
        stream = mic.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.porcupine.sample_rate,  # 16kHz microphone
            input=True,
            frames_per_buffer=self.porcupine.frame_length,  # Read 512 samples at a time
        )
        stream.start_stream()

        rec = KaldiRecognizer(model, 16000)

        wake_word_activity_start: float = None
        wake_word_activity_end: float = None
        print("Listening for wake word...")

        rolling_buffer = collections.deque(maxlen=60)
        try:
            while True:
                # Read exactly 512 samples (1024 bytes) from the microphone
                data = stream.read(
                    self.porcupine.frame_length, exception_on_overflow=False
                )

                # Unpack the raw byte data into 16-bit signed integers using struct
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, data)
                # audio_data = np.frombuffer(data, dtype=np.int16)

                # Store the audio in rolling buffer
                rolling_buffer.append(data)

                # Check if we need to process the wake word
                self.continous_listen_check()

                if self.continous_listen:
                    # Continuous listening mode
                    if rec.AcceptWaveform(data):
                        result = rec.Result()
                        self._process_phrase(result)
                else:
                    # Wake word detection mode
                    try:
                        # Pass the NumPy array directly to Porcupine
                        wake_word_detected = self.porcupine.process(pcm)
                        if wake_word_detected >= 0:
                            wake_word_activity_start = get_time()
                            print("Wake word detected!")
                            # self.set_continous_listen(mode=True)

                            recorded_audio = list(rolling_buffer)

                            # Immediately feed buffered audio to Kaldi
                            for buffered_data in recorded_audio:
                                if rec.AcceptWaveform(buffered_data):
                                    result = rec.Result()
                                    self._process_phrase(result)

                            while True:
                                wake_word_activity_end = get_time()

                                if (
                                    wake_word_activity_end - wake_word_activity_start
                                ) >= self.wake_word_waiting:
                                    print("Wake word activity window passd.")
                                    break

                                # Continue recording audio post-wake word
                                data = stream.read(
                                    self.porcupine.frame_length,
                                    exception_on_overflow=False,
                                )

                                if rec.AcceptWaveform(data):
                                    result = rec.Result()

                                    self._process_phrase(result)
                                    break

                            rolling_buffer.clear()
                    except Exception as e:
                        print(f"Error processing wake word: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            mic.terminate()
            self.porcupine.delete()

    def _process_full_audio(self, recorded_audio):
        """
        Process the full audio captured (both pre-wake and post-wake) after wake word detection.
        """
        # Convert the recorded_audio to a byte array for Kaldi processing
        full_audio = b"".join(recorded_audio)

        # Feed the full audio into Kaldi to process the entire phrase
        rec = KaldiRecognizer(self.model_path, 16000)

        if rec.AcceptWaveform(full_audio):
            result = rec.Result()
            phrase = result.lower()

            # Process the recognized phrase
            self._process_phrase(phrase, result)

    def _process_phrase(self, result: str):
        """
        Process the phrase detected by Kaldi recognizer.
        This method handles both continuous listen and wake word processing.
        """
        result = json.loads(result)
        text = result["text"]
        print(text)
        if text:
            self.set_continous_listen(False)
        return

        # Trigger the callback
        future = asyncio.run_coroutine_threadsafe(self.callback(result), self.loop)
        try:
            future.result()
        except Exception as ex:
            print(f"Error occurred: {ex}")
