import librosa
import numpy as np
import soundfile
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter


class VEX(object):
    def __init__(self):
        pass

    def separate(self, srcaudio):
        sampling_rate, audio = srcaudio
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        if sampling_rate != 44100:
            audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=44100)
        soundfile.write("samtmpwav.wav", audio, 44100, format="wav")

        separator = Separator('spleeter:2stems')

        audio_loader = AudioAdapter.default()
        waveform, _ = audio_loader.load("samtmpwav.wav", sample_rate=44100)

        prediction = separator.separate(waveform)

        return [(44100, prediction['vocals']), (44100,prediction['accompaniment'])]

