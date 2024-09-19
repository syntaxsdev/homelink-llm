from shared.mixins import ResponseMixin

from pygame import mixer
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
        mixer.init()

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
            raise FileNotFoundError("Could not play audio file.")

        if self.is_playing and not overplay:
            while self.is_playing:
                asyncio.timeout(delay=0.2)  # wait until sound is done
        try:
            await self._play_sound(file)

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

    @property
    def is_playing(self) -> bool:
        return mixer.music.get_busy()
    
    async def _play_sound(self, file: str):
        """
        """

        await asyncio.to_thread(mixer.music.load, file)
        await asyncio.to_thread(mixer.music.play)
        
        asyncio.create_task(self.wait_for_playback())

    async def wait_for_playback(self):
        """Background task that monitors if the music is still playing"""
        while mixer.music.get_busy():
            await asyncio.sleep(0.1)  # Wait a bit before checking again
        print("Music finished")
        
    def stop_sound(self):
        """Stop playing sound"""
        if self.is_playing:
            mixer.music.stop()
