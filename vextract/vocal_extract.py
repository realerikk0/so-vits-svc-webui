import os

import librosa
import numpy as np
import soundfile
from scipy.io.wavfile import read


class VEX(object):
    def __init__(self):
        pass

    def separate(self, srcaudio):
        sampling_rate, audio = srcaudio
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        # if sampling_rate != 16000:
        #     audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=16000)

        sample_tmp_wav_filename = "samtmpwav.wav"
        soundfile.write(sample_tmp_wav_filename, audio, sampling_rate, format="wav")

        os.system(f"spleeter separate -p spleeter:2stems -o output {sample_tmp_wav_filename}")

        vocal_file = f"output/samtmpwav/vocals.wav"
        accompaniment_file = f"output/samtmpwav/accompaniment.wav"

        vocal_rate, vocal_audio = read(vocal_file)
        # vocal_audio = (vocal_audio / np.iinfo(audio.dtype).max).astype(np.float32)
        # vocal_audio = librosa.resample(vocal_audio, orig_sr=vocal_rate, target_sr=sampling_rate)
        # vocal_audio = (np.array(vocal_audio) * 32768).astype('int16')
        accompaniment_rate, accompaniment_audio = read(accompaniment_file)
        # accompaniment_audio = (accompaniment_audio / np.iinfo(audio.dtype).max).astype(np.float32)
        # accompaniment_audio = librosa.resample(accompaniment_audio, orig_sr=accompaniment_rate, target_sr=sampling_rate)
        # accompaniment_audio = (np.array(accompaniment_audio) * 32768).astype('int16')

        return [(sampling_rate, vocal_audio), (sampling_rate, accompaniment_audio)]

