import hashlib
import io
import json
import logging
import os
import time
from pathlib import Path
from inference import slicer

import librosa
import numpy as np
# import onnxruntime
import parselmouth
import soundfile
import torch
import torchaudio

import cluster
from hubert import hubert_model
import utils
from models import SynthesizerTrn

logging.getLogger('matplotlib').setLevel(logging.WARNING)


def read_temp(file_name):
    if not os.path.exists(file_name):
        with open(file_name, "w") as f:
            f.write(json.dumps({"info": "temp_dict"}))
        return {}
    else:
        try:
            with open(file_name, "r") as f:
                data = f.read()
            data_dict = json.loads(data)
            if os.path.getsize(file_name) > 50 * 1024 * 1024:
                f_name = file_name.replace("\\", "/").split("/")[-1]
                print(f"clean {f_name}")
                for wav_hash in list(data_dict.keys()):
                    if int(time.time()) - int(data_dict[wav_hash]["time"]) > 14 * 24 * 3600:
                        del data_dict[wav_hash]
        except Exception as e:
            print(e)
            print(f"{file_name} error,auto rebuild file")
            data_dict = {"info": "temp_dict"}
        return data_dict


def write_temp(file_name, data):
    with open(file_name, "w") as f:
        f.write(json.dumps(data))


def timeit(func):
    def run(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        print('executing \'%s\' costed %.3fs' % (func.__name__, time.time() - t))
        return res

    return run


def format_wav(audio_path):
    if Path(audio_path).suffix == '.wav':
        return
    raw_audio, raw_sample_rate = librosa.load(audio_path, mono=True, sr=None)
    soundfile.write(Path(audio_path).with_suffix(".wav"), raw_audio, raw_sample_rate)


def get_end_file(dir_path, end):
    file_lists = []
    for root, dirs, files in os.walk(dir_path):
        files = [f for f in files if f[0] != '.']
        dirs[:] = [d for d in dirs if d[0] != '.']
        for f_file in files:
            if f_file.endswith(end):
                file_lists.append(os.path.join(root, f_file).replace("\\", "/"))
    return file_lists


def get_md5(content):
    return hashlib.new("md5", content).hexdigest()


def fill_a_to_b(a, b):
    if len(a) < len(b):
        for _ in range(0, len(b) - len(a)):
            a.append(a[0])


def mkdir(paths: list):
    for path in paths:
        if not os.path.exists(path):
            os.mkdir(path)


class Svc(object):
    def __init__(self):

        self.wav_format = "flac"
        self.auto_predict_f0 = False
        self.cluster_infer_ratio = 0.5
        self.noice_scale = 0.6
        self.pad_seconds = 0.5

        self.net_g_path = None

        self.dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net_g_ms = None
        self.hps_ms = None
        self.target_sample = None
        self.hop_size = None
        self.spk2id = None

    def set_device(self, device):
        self.dev = torch.device(device)
        # self.hubert_model = utils.get_hubert_model().to(self.dev)
        # if self.net_g_ms != None:
        #     self.net_g_ms.to(device)

    def load_checkpoint(self, path):
        self.hps_ms = utils.get_hparams_from_file(f"checkpoints/{path}/config.json")
        self.target_sample = self.hps_ms.data.sampling_rate
        self.hop_size = self.hps_ms.data.hop_length
        self.spk2id = self.hps_ms.spk

        self.net_g_ms = SynthesizerTrn(
            self.hps_ms.data.filter_length // 2 + 1,
            self.hps_ms.train.segment_size // self.hps_ms.data.hop_length,
            **self.hps_ms.model
        )
        _ = utils.load_checkpoint(f"checkpoints/{path}/model.pth", self.net_g_ms, None)
        _ = self.net_g_ms.eval().to(self.dev)

        # 加载hubert
        self.hubert_model = utils.get_hubert_model().to(self.dev)
        # self.load_model()
        cluster_model_path = f"checkpoints/{path}/kmeans_10000.pt"
        if os.path.exists(cluster_model_path):
            self.cluster_model = cluster.get_cluster_model(cluster_model_path)
        else:
            self.cluster_model = None

    def load_model(self):
        # 获取模型配置
        self.net_g_ms = SynthesizerTrn(
            self.hps_ms.data.filter_length // 2 + 1,
            self.hps_ms.train.segment_size // self.hps_ms.data.hop_length,
            **self.hps_ms.model)
        _ = utils.load_checkpoint(self.net_g_path, self.net_g_ms, None)
        if "half" in self.net_g_path and torch.cuda.is_available():
            _ = self.net_g_ms.half().eval().to(self.dev)
        else:
            _ = self.net_g_ms.eval().to(self.dev)

    def get_unit_f0(self, in_path, tran, cluster_infer_ratio, speaker):

        wav, sr = librosa.load(in_path, sr=self.target_sample)

        f0 = utils.compute_f0_parselmouth(wav, sampling_rate=self.target_sample, hop_length=self.hop_size)
        f0, uv = utils.interpolate_f0(f0)
        f0 = torch.FloatTensor(f0)
        uv = torch.FloatTensor(uv)
        f0 = f0 * 2 ** (tran / 12)
        f0 = f0.unsqueeze(0).to(self.dev)
        uv = uv.unsqueeze(0).to(self.dev)

        wav16k = librosa.resample(wav, orig_sr=self.target_sample, target_sr=16000)
        wav16k = torch.from_numpy(wav16k).to(self.dev)
        c = utils.get_hubert_content(self.hubert_model, wav_16k_tensor=wav16k)
        c = utils.repeat_expand_2d(c.squeeze(0), f0.shape[1])

        if self.cluster_model is not None and cluster_infer_ratio != 0:
            cluster_c = cluster.get_cluster_center_result(self.cluster_model, c.cpu().numpy().T, speaker).T
            cluster_c = torch.FloatTensor(cluster_c).to(self.dev)
            c = cluster_infer_ratio * cluster_c + (1 - cluster_infer_ratio) * c

        c = c.unsqueeze(0)
        return c, f0, uv

    def infer(self, speaker, tran, raw_path,
              cluster_infer_ratio=0.0,
              auto_predict_f0=False,
              noice_scale=0.4):
        speaker_id = self.spk2id[speaker]
        sid = torch.LongTensor([int(speaker_id)]).to(self.dev).unsqueeze(0)
        c, f0, uv = self.get_unit_f0(raw_path, tran, cluster_infer_ratio, speaker)

        with torch.no_grad():
            start = time.time()
            audio = self.net_g_ms.infer(c, f0=f0, g=sid, uv=uv, predict_f0=auto_predict_f0, noice_scale=noice_scale)[
                0, 0].data.float()
            use_time = time.time() - start
            print("vits use time:{}".format(use_time))
        return audio, audio.shape[-1]

    def slice_inference(self, raw_audio_path, spk, tran, slice_db, cluster_infer_ratio, auto_predict_f0, noice_scale,
                        pad_seconds=0.5):
        wav_path = raw_audio_path
        chunks = slicer.cut(wav_path, db_thresh=slice_db)
        audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)

        audio = []
        for (slice_tag, data) in audio_data:
            print(f'#=====segment start, {round(len(data) / audio_sr, 3)}s======')
            # padd
            pad_len = int(audio_sr * pad_seconds)
            data = np.concatenate([np.zeros([pad_len]), data, np.zeros([pad_len])])
            length = int(np.ceil(len(data) / audio_sr * self.target_sample))
            raw_path = io.BytesIO()
            soundfile.write(raw_path, data, audio_sr, format="wav")
            raw_path.seek(0)
            if slice_tag:
                print('jump empty segment')
                _audio = np.zeros(length)
            else:
                out_audio, out_sr = self.infer(spk, tran, raw_path,
                                               cluster_infer_ratio=cluster_infer_ratio,
                                               auto_predict_f0=auto_predict_f0,
                                               noice_scale=noice_scale
                                               )
                _audio = out_audio.cpu().numpy()

            pad_len = int(self.target_sample * pad_seconds)
            _audio = _audio[pad_len:-pad_len]
            audio.extend(list(_audio))
        return np.array(audio)

    def inference(self, srcaudio, chara, tran, slice_db, ns):
        self.noice_scale = ns
        sampling_rate, audio = srcaudio
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        if sampling_rate != 16000:
            audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=16000)
        soundfile.write("tmpwav.wav", audio, 16000, format="wav")

        chunks = slicer.cut("tmpwav.wav", db_thresh=slice_db)
        audio_data, audio_sr = slicer.chunks2audio("tmpwav.wav", chunks)
        audio = []
        for (slice_tag, data) in audio_data:
            print(f'#=====segment start, {round(len(data) / audio_sr, 3)}s======')
            # padd
            pad_len = int(audio_sr * self.pad_seconds)
            data = np.concatenate([np.zeros([pad_len]), data, np.zeros([pad_len])])
            length = int(np.ceil(len(data) / audio_sr * self.target_sample))
            raw_path = io.BytesIO()
            soundfile.write(raw_path, data, audio_sr, format="wav")
            raw_path.seek(0)
            if slice_tag:
                print('jump empty segment')
                _audio = np.zeros(length)
            else:
                out_audio, out_sr = self.infer(chara, tran, raw_path,
                                               cluster_infer_ratio=self.cluster_infer_ratio,
                                               auto_predict_f0=self.auto_predict_f0,
                                               noice_scale=self.noice_scale
                                               )
                _audio = out_audio.cpu().numpy()

            pad_len = int(self.target_sample * self.pad_seconds)
            _audio = _audio[pad_len:-pad_len]
            audio.extend(list(_audio))
        audio = (np.array(audio) * 32768).astype('int16')
        return (self.hps_ms.data.sampling_rate, audio)
