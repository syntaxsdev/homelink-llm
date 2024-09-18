from fastapi import FastAPI, WebSocket
from .homelink import HomeLink


import pvporcupine
import os
import asyncio

# app = FastAPI()

# @app.websocket("/audio/stream")
# async def audio_stream(websocket: WebSocket):
#     await websocket.accept()

#     porcupine: pvporcupine.Porcupine = pvporcupine.create(keywords=["hey"])
#     while True:
#         chunk = await websocket.receive_bytes()
#         if porcupine.process(chunk):
#             await websocket.send_text("Detected")



async def entry():
    dir = os.path.join(os.getcwd(), "config/")
    homelink = HomeLink(config_folder=dir)
    

asyncio.run(entry())