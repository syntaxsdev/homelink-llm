from fastapi import FastAPI, UploadFile, File
from .sound_controller import SoundController

from shared.mixins import ResponseMixin
from tempfile import TemporaryFile
from dataclasses import dataclass

import uvicorn
import asyncio

@dataclass
class ClientResponseMixin(ResponseMixin):
    ...

app = FastAPI(title="Client sided HomeLink server")
sound_controller = SoundController()

@app.get("/play")
async def play_audio(file: UploadFile = File(...)):
    with TemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(await file.read())
        temp_audio_file.flush()

        await sound_controller.play_sound(temp_audio_file.name)
        return ClientResponseMixin(response="Completed", completed=True)
    
async def entry():
    uvicorn.run(host="0.0.0.0", port=6454, reload=True)

asyncio.run(entry())