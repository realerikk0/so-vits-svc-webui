import io
import logging
import os
import wave
import uuid
from zipfile import ZipFile

import numpy as np
from scipy.io import wavfile

import api.base
from vextract.vocal_extract import VEX

logger = logging.getLogger(__name__)


# noinspection PyAbstractClass
class VocalRemoverHandler(api.base.ApiHandler):
    async def post(self):
        try:
            uploaded_file = self.request.files['srcaudio'][0]
            audiofile_body = uploaded_file['body']
            # audiofile_name = uploaded_file['filename']

            with io.BytesIO(audiofile_body) as file_stream:
                with wave.open(file_stream, 'rb') as wave_file:
                    audio_data = wave_file.readframes(-1)
                    sampling_rate = wave_file.getframerate()
                    num_channels = wave_file.getnchannels()

            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_array = np.reshape(audio_array, (-1, num_channels))

            v = VEX()
            [(vocal_sampling_rate, vocal_audio), (accompaniment_sampling_rate, accompaniment_audio)] = v.separate((sampling_rate, audio_array))

            output_dirname = f"{uuid.uuid4()}"
            output_dir = f"output/{output_dirname}"
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            wavfile.write(f"{output_dir}/vocals.wav", vocal_sampling_rate, vocal_audio)
            wavfile.write(f"{output_dir}/accompaniment.wav", accompaniment_sampling_rate, accompaniment_audio)

            zipfilename = f"{output_dir}/output.zip"
            with ZipFile(zipfilename, 'w') as zip_obj:
                zip_obj.write(f"{output_dir}/vocals.wav", "vocals.wav")
                zip_obj.write(f"{output_dir}/accompaniment.wav", "accompaniment.wav")

            logger.debug(f"start output data.")
            # set response header and body
            self.set_header("Content-Type", "application/zip")
            self.set_header("Content-Disposition", "attachment; filename=output.zip")
            with open(zipfilename, "rb") as file:
                self.write(file.read())
            await self.flush()
            logger.debug(f"response completed.")

            os.remove(f"{output_dir}/vocals.wav")
            os.remove(f"{output_dir}/accompaniment.wav")
            os.remove(f"{output_dir}/output.zip")
            os.rmdir(output_dir)

            # self.set_header('Content-Type', 'audio/wav')
            # self.set_header('Content-Disposition', 'attachment; filename="vocals.wav"')
            # wavfile.write(self, vocal_sampling_rate, vocal_audio)
            # self.write('\n')
            # self.set_header('Content-Type', 'audio/wav')
            # self.set_header('Content-Disposition', 'attachment; filename="accompaniment.wav"')
            # wavfile.write(self, accompaniment_sampling_rate, accompaniment_audio)
            # await self.flush()
        except Exception as e:
            logger.exception(e)
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": "system_error",
                "data": None
            })
