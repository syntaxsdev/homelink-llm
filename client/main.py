from fastapi import FastAPI, UploadFile, File
from contextlib import asynccontextmanager

from .sound_controller import SoundController

from shared.mixins import ResponseMixin
from shared.utils import load_yaml
from tempfile import TemporaryFile
from dataclasses import dataclass
import httpx
import uvicorn
import asyncio
import os
import json

from .voice_listener import VoskListener


@dataclass
class ClientResponseMixin(ResponseMixin): ...


def on_startup() -> tuple[FastAPI, SoundController, VoskListener]:
    dir = os.path.abspath(__file__)
    client_file = os.path.abspath(os.path.join(dir, "..", "..", "config", "client.yml"))
    client_settings = load_yaml(client_file)
    if not client_settings:
        print("Quitting because there is no client file.")
        os.exit(1)

    server = client_settings.get("server_ip")
    server_ip = client_settings.get("server_port")

    sound_controller = SoundController()

    async def send_speech_phenomenon(input: str):
        input: dict = json.loads(input)
        payload = {"input": input["text"]}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{server}{(':' + str(server_ip)) if server_ip else ''}/awake",
                json=payload,
                headers={"Content-Type":"application/json"}
            )
    
    vosk_listener = VoskListener(
        wake_word=client_settings["wake_word"],
        model_path=f"{os.path.join(os.path.abspath(dir), "vosk-model-small-en-us-0.15")}",
        callback=send_speech_phenomenon,
        loop=asyncio.get_event_loop(),
    )

    @asynccontextmanager
    async def on_fastapi_lifecycle(app: FastAPI):
        # start vosk_listener
        task = asyncio.create_task(vosk_listener.start())

        try:
            yield
        finally:
            # tear down
            task.cancel()
            await task

    app = FastAPI(title="Client sided HomeLink server", lifespan=on_fastapi_lifecycle)

    return app, sound_controller, vosk_listener


app, sound_controller, vosk_listener = on_startup()


@app.get("/")
def get_root():
    return {"status": "active"}


@app.post("/play")
async def play_audio(file: UploadFile = File(...)):
    with TemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(await file.read())
        temp_audio_file.flush()

    await sound_controller.play_sound(temp_audio_file.name)
    return ClientResponseMixin(response="Completed", completed=True)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6454, reload=True)
