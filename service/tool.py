import os
import subprocess
import tempfile
import logging
import wave

import numpy as np

logger = logging.getLogger(__name__)
FFMPEG_CMD = "ffmpeg"


async def audio_normalize(full_filename, file_data):
    try:
        file_name = os.path.splitext(full_filename)[0]
        file_extension = os.path.splitext(full_filename)[1].lower()

        logger.debug(f"normalizing {full_filename}")

        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file.write(file_data)
            temp_file.flush()
            temp_out_filename = f"norm_{file_name}.wav"

            subprocess.call(
                [FFMPEG_CMD,
                 '-i', temp_file.name,
                 '-ac', '1',
                 '-ar', '44100',
                 '-acodec', 'pcm_s16le',
                 '-f', 'wav',
                 temp_out_filename])

            if os.path.exists(temp_out_filename):
                return temp_out_filename
            else:
                raise FileNotFoundError("Unable to make the file")
    except Exception as e:
        logger.exception(e)
        return None


def read_wav_file_to_numpy_array(filename):
    with wave.open(filename, 'rb') as wav_file:
        sampling_rate = wav_file.getframerate()
        bytes_data = wav_file.readframes(wav_file.getnframes())
        sample_width = wav_file.getsampwidth()

    if sample_width == 1:
        data_type = np.uint8
    elif sample_width == 2:
        data_type = np.int16
    elif sample_width == 4:
        data_type = np.int32
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")

    numpy_data = np.frombuffer(bytes_data, dtype=data_type)

    return sampling_rate, numpy_data
