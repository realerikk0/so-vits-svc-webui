import io
import os
import subprocess
import wave

import librosa
import numpy as np
import soundfile
from scipy.io import wavfile
from scipy.io.wavfile import read


class VEX(object):
    def __init__(self):
        pass

    def load(self, audio_file):
        with wave.open(audio_file, 'rb') as wav_file:
            num_frames = wav_file.getnframes()
            audiofile_body = wav_file.readframes(num_frames)
        with io.BytesIO(audiofile_body) as file_stream:
            with wave.open(file_stream, 'rb') as wave_file:
                audio_data = wave_file.readframes(-1)
                sampling_rate = wave_file.getframerate()
                num_channels = wave_file.getnchannels()

        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_array = np.reshape(audio_array, (-1, num_channels))
        return sampling_rate, audio_array

    def separate(self, srcaudio=None):
        import uuid
        sampling_rate, audio = srcaudio

        temp_filename = f"splt_{uuid}.wav"
        wavfile.write(temp_filename, sampling_rate, audio)

        subprocess.run([
            'spleeter', 'separate',
            '-p', 'spleeter:2stems',
            '-o', 'output',
            temp_filename
        ])

        vocal_file = f"output/samtmpwav/vocals.wav"
        accompaniment_file = f"output/samtmpwav/accompaniment.wav"

        with wave.open(vocal_file, 'rb') as wav_file:
            num_frames = wav_file.getnframes()
            audiofile_body = wav_file.readframes(num_frames)
        with io.BytesIO(audiofile_body) as file_stream:
            with wave.open(file_stream, 'rb') as wave_file:
                audio_data = wave_file.readframes(-1)
                vocal_sampling_rate = wave_file.getframerate()
                num_channels = wave_file.getnchannels()

        vocal_audio = np.frombuffer(audio_data, dtype=np.int16)
        vocal_audio = np.reshape(vocal_audio, (-1, num_channels))

        with wave.open(accompaniment_file, 'rb') as wav_file:
            num_frames = wav_file.getnframes()
            audiofile_body = wav_file.readframes(num_frames)
        with io.BytesIO(audiofile_body) as file_stream:
            with wave.open(file_stream, 'rb') as wave_file:
                audio_data = wave_file.readframes(-1)
                accompaniment_sampling_rate = wave_file.getframerate()
                num_channels = wave_file.getnchannels()

        accompaniment_audio = np.frombuffer(audio_data, dtype=np.int16)
        accompaniment_audio = np.reshape(accompaniment_audio, (-1, num_channels))

        os.remove(temp_filename)
        os.remove(vocal_file)
        os.remove(accompaniment_file)

        return [(vocal_sampling_rate, vocal_audio), (accompaniment_sampling_rate, accompaniment_audio)]


if __name__ == "__main__":
    v = VEX()
    # srcaudio = v.load("")
    v.separate()

