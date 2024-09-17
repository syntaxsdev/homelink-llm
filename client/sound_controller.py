from shared.mixins import ResponseMixin

from pydub import AudioSegment
from pydub.playback import play
from dataclasses import dataclass

from concurrent.futures import ThreadPoolExecutor

import os
import asyncio


@dataclass
class SoundControllerResponse(ResponseMixin):
    retry_count: int = 0
    ...


class SoundController:
    """The SoundController class"""

    def __init__(self):
        self.is_playing: bool = False
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def play_sound(
        self,
        file: str,
        overplay: bool = False,
        scr: SoundControllerResponse | None = None,
    ):
        """
        Play sound through the SoundController

        Args:
            file: the sound file
            overplay: whether or not to cut the other sound of
            scr: previous SoundControllerResponse in case of retry
        """
        if not os.path.exists(file):
            return FileNotFoundError("Could not play audio file.")

        if self.is_playing and not overplay:
            while self.is_playing:
                asyncio.timeout(delay=1)  # wait until sound is done
        try:
            await asyncio.to_thread(self.__play_sound_async, file)

        except Exception as ex:
            if scr:
                return SoundControllerResponse(
                    response="Could not play audio segment",
                    completed=False,
                    retry=False,
                )
            return SoundControllerResponse(
                response="Could not play audio segment",
                retry=True,
                retry_count=1,
                meta=ex,
            )
    
    def __play_sound_async(self, file: str):
        """Internal function that abstracts just playing the sound asynchronously

        Args:
            file: the sound file
        """
        try:
            sound = AudioSegment.from_wav(file)
        except Exception as ex:
            raise ex

        if self.is_playing:
            self.stop_sound()
        self.sound = sound
        play(sound)

    def stop_sound(self):
        """Hacky method to stop sound"""
        if self.is_playing and self.sound:
            audio_muted = self.sound.apply_gain(-120.0)
            self.executor.submit(play, audio_muted)