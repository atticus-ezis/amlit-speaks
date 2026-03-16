from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings
from elevenlabs.play import play
from config import get_settings
import asyncio
from enums import stream_media_type, audio_formats, elevenlabs_voices
# from enums import elevenlabs_voices

settings = get_settings()


class GenerateVoices:
    def __init__(self):
        self.elevenlabs = AsyncElevenLabs(
            api_key=settings.elevenlabs_api_key,
        )

    async def test_async_http_streaming(
        self,
        text: str,
        model_id: str = "eleven_flash_v2",
    ):
        async for chunk in self.elevenlabs.text_to_speech.stream(
            voice_id=elevenlabs_voices["test"],
            model_id=model_id,
            text=text,
        ):
            yield chunk

    async def elevenlabs_http_streaming(
        self,
        text: str,
        voice_id: str = "test",
        model_id: str = "eleven_flash_v2",
    ):
        voice_id = elevenlabs_voices[voice_id]
        async for chunk in self.elevenlabs.text_to_speech.stream(
            voice_id=voice_id,
            model_id=model_id,
            text=text,
            output_format=audio_formats[stream_media_type],  # half storage space
            # ------------- voice_settings -------------
            # voice_settings=VoiceSettings(
            #     stability=0.5,
            #     similarity_boost=0.8,
            # ),
        ):
            yield chunk


if __name__ == "__main__":
    generate = GenerateVoices()

    async def main():
        async for chunk in generate.test_async_http_streaming(
            "The first move is what sets everything in motion."
        ):
            print(f"got chunk: {len(chunk)} bytes")

    asyncio.run(main())


# ------------- REFERENCE FOR WEBSOCKET STREAMING -------------

#  voice_id = elevenlabs_voices[voice_id]
#         uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model_id}"

#         async with websockets.connect(uri) as websocket:
#             # send config + text
#             await websocket.send(
#                 json.dumps(
#                     {
#                         "text": text,
#                         "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
#                         "xi_api_key": settings.elevenlabs_api_key,
#                     }
#                 )
#             )
#             await websocket.send(json.dumps({"text": text, "flush": True}))
#             await websocket.send(json.dumps({"text": ""}))  # close

#             # stream chunks as they arrive
#             while True:
#                 message = await websocket.recv()  # truly async await
#                 data = json.loads(message)
#                 if data.get("audio"):
#                     yield base64.b64decode(data["audio"])
#                 elif data.get("isFinal"):
#                     break
