import io
import logging
import os
import tempfile
import wave
import uuid
import zipfile
from zipfile import ZipFile

import numpy as np
from scipy.io import wavfile

import api.base
from service.tool import audio_normalize, read_wav_file_to_numpy_array
from vextract.vocal_extract import VEX

logger = logging.getLogger(__name__)


# noinspection PyAbstractClass
class VocalRemoverHandler(api.base.ApiHandler):
    async def post(self):
        try:
            uploaded_file = self.request.files['srcaudio'][0]
            audio_filebody = uploaded_file['body']
            audio_filename = uploaded_file['filename']
            audio_fileext = os.path.splitext(audio_filename)[-1].lower()

            if audio_fileext != ".wav":
                logger.debug(f"file format is {audio_fileext}, not wav\n"
                             f"converting to standard wav data...")
                converted_file = await audio_normalize(full_filename=audio_filename, file_data=audio_filebody)
                with wave.open(converted_file, 'rb') as wav_file:
                    num_frames = wav_file.getnframes()
                    audiofile_body = wav_file.readframes(num_frames)
                    logger.debug(f"wav conversion completed.")
                    os.remove(converted_file)

            with tempfile.NamedTemporaryFile(suffix=audio_fileext, delete=False) as temp_wav:
                temp_wav.write(audiofile_body)
                temp_wav.close()

                converted_file = await audio_normalize(full_filename=audio_filename, file_data=audio_filebody)

                sampling_rate, audio_array = read_wav_file_to_numpy_array(converted_file)
                os.remove(converted_file)

            print(f"Input Audio Shape: {audio_array.shape}\n"
                  f"Input Audio Data Type: {audio_array.dtype}")

            v = VEX()
            [(vocal_sampling_rate, vocal_audio), (accompaniment_sampling_rate, accompaniment_audio)] = v.separate((sampling_rate, audio_array))

            output_dirname = f"{uuid.uuid4()}"
            output_dir = f"output/{output_dirname}"
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            wavfile.write(f"{output_dir}/vocals.wav", vocal_sampling_rate, vocal_audio)
            wavfile.write(f"{output_dir}/accompaniment.wav", accompaniment_sampling_rate, accompaniment_audio)

            zipfilename = f"{output_dir}/output.zip"
            with ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zip_obj:
                zip_obj.write(f"{output_dir}/vocals.wav")
                zip_obj.write(f"{output_dir}/accompaniment.wav")

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
        except Exception as e:
            logger.exception(e)
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": "system_error",
                "data": None
            })
