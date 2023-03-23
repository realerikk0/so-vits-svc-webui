# -*- coding: utf-8 -*-
import logging
from inference.infer_tool import Svc
from typing import *
import api.base
import os
import io
import wave
import numpy as np

logger = logging.getLogger(__name__)

_svc: Optional[Svc] = None
_model_paths: Optional[List] = None


def init():
    global _svc, _model_paths
    _svc = Svc()
    _model_paths = []

    # get the path to the parent directory
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.curdir))

    # construct the path to the "checkpoints" directory
    checkpoints_dir = os.path.join(parent_dir, "checkpoints")

    logger.debug(f"CkPoints Dir: {checkpoints_dir}")

    for root, dirs, files in os.walk(checkpoints_dir):
        for dir in dirs:
            _model_paths.append(dir)


# noinspection PyAbstractClass
class ModelListHandler(api.base.ApiHandler):
    async def get(self):
        self.write({
            "code": 200,
            "msg": "ok",
            "data": _model_paths
        })


# noinspection PyAbstractClass
class SwitchHandler(api.base.ApiHandler):
    async def post(self):
        model_name = self.get_argument("model", "")  # model name
        mode = self.get_argument("mode", "single")  # running mode: single or batch
        device = self.get_argument("device", "cuda")  # "cpu" or "cuda"

        if model_name == "":
            self.set_status(400)
            self.write({
                "code": 400,
                "msg": "未选择模型！",
                "data": None
            })
            return

        if mode not in ("single", "batch"):
            self.set_status(400)
            self.write({
                "code": 400,
                "msg": "运行模式选择错误！",
                "data": None
            })
            return

        if device not in ("cpu", "cuda"):
            self.set_status(400)
            self.write({
                "code": 400,
                "msg": "设备选择错误！",
                "data": None
            })
            return

        logger.debug(f"modelname: {model_name}\n"
                     f"mode: {mode}\n"
                     f"device: {device}\n")
        try:
            _svc.set_device(device=device)
            logger.debug(f"Device set.")
            _svc.load_checkpoint(path=model_name)
            logger.debug(f"Model set.")
        except Exception as e:
            logger.exception(e)
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": "system_error",
                "data": None
            })
            return

        self.write({
            "code": 200,
            "msg": "ok",
            "data": {
                "mode": mode
            }
        })


# noinspection PyAbstractClass
class SingleInferenceHandler(api.base.ApiHandler):
    async def post(self):
        try:
            from scipy.io import wavfile

            dsid = self.get_argument("dsid", "")
            tran = self.get_argument("tran", "0")
            th = self.get_argument("th", "-40.0")
            ns = self.get_argument("ns", "0.4")
            audiofile_dict = self.request.files.get("srcaudio", [])

            if not audiofile_dict:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": "未上传文件！",
                    "data": None
                })
                return

            if dsid == "":
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": "未选择模型！",
                    "data": None
                })
                return

            audiofile = audiofile_dict[0]
            audiofile_body = audiofile['body']
            audiofile_name = audiofile['filename']

            with io.BytesIO(audiofile_body) as file_stream:
                with wave.open(file_stream, 'rb') as wave_file:
                    # get the audio data as a byte string
                    audio_data = wave_file.readframes(-1)
                    # get the sampling rate
                    sampling_rate = wave_file.getframerate()
                    samp_width = wave_file.getsampwidth()
                    # get the number of channels and sample width
                    num_channels = wave_file.getnchannels()
                    # sample_width = wave_file.getsampwidth()

            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_array = np.reshape(audio_array, (-1, num_channels))

            scraudio = (sampling_rate, audio_array)

            logger.debug(f"read file {audiofile_name}\n"
                         f"sampling rate: {sampling_rate}")

            tran = float(tran)
            th = float(th)
            ns = float(ns)

            output_audio_sr, output_audio_array = _svc.inference(srcaudio=scraudio,
                                                                 chara=dsid,
                                                                 tran=tran,
                                                                 slice_db=th,
                                                                 ns=ns)

            logger.debug(f"svc for {audiofile_name} succeed. \n"
                         f"audio data type: {type(output_audio_array)}\n"
                         f"audio data sr: {output_audio_sr}")

            logger.debug(f"start output data.")

            # Convert the NumPy array to WAV format
            with io.BytesIO() as wav_file:
                wavfile.write(wav_file, sampling_rate, output_audio_array)
                wav_data = wav_file.getvalue()

            # set the response headers and body
            self.set_header('Content-Type', 'audio/wav')
            self.set_header('Content-Disposition', f'attachment; filename="svc_output.wav"')
            self.write(wav_data)
            await self.flush()
        except Exception as e:
            logger.exception(e)
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": "system_error",
                "data": None
            })
            return


# noinspection PyAbstractClass
class BatchInferenceHandler(api.base.ApiHandler):
    async def post(self):
        try:
            from zipfile import ZipFile
            from scipy.io import wavfile
            import uuid

            dsid = self.get_argument("dsid", "")
            tran = self.get_argument("tran", "0")
            th = self.get_argument("th", "-40.0")
            ns = self.get_argument("ns", "0.4")
            audiofile_dict = self.request.files.get("srcaudio", [])

            if not audiofile_dict:
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": "未上传文件！",
                    "data": None
                })
                return

            if dsid == "":
                self.set_status(400)
                self.write({
                    "code": 400,
                    "msg": "未选择模型！",
                    "data": None
                })
                return

            temp_dir_name = "temp"

            # get the path to the parent directory
            parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.curdir))

            # construct the path to the "temp" directory
            temp_dir = os.path.join(parent_dir, temp_dir_name)

            logger.debug(f"TempDir: {temp_dir}")

            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)

            tmp_workdir_name = f"{temp_dir}/batch_{uuid.uuid4()}"
            if not os.path.exists(tmp_workdir_name):
                os.mkdir(tmp_workdir_name)

            output_files = []

            tran = float(tran)
            th = float(th)
            ns = float(ns)

            for idx, file in enumerate(audiofile_dict):
                audio_filename = file["filename"]
                audio_filebody = file["body"]
                filename = os.path.basename(audio_filename)

                print(f"{idx}, {len(audio_filebody)}, {filename}")
                sampling_rate, audio = wavfile.read(io.BytesIO(audio_filebody))
                output_sampling_rate, output_audio = _svc.inference((sampling_rate, audio), chara=dsid, tran=tran,
                                                                    slice_db=th, ns=ns)
                new_filepath = f"{tmp_workdir_name}/{filename}"
                wavfile.write(filename=new_filepath, rate=output_sampling_rate, data=output_audio)
                output_files.append(new_filepath)

            zipfilename = f"{tmp_workdir_name}/output.zip"
            with ZipFile(zipfilename, "w") as zip_obj:
                for idx, filepath in enumerate(output_files):
                    zip_obj.write(filepath, os.path.basename(filepath))

            # todo: remove data

            # set response header and body
            self.set_header("Content-Type", "application/zip")
            self.set_header("Content-Disposition", "attachment; filename=output.zip")
            with open("output.zip", "rb") as file:
                self.write(file.read())
            await self.flush()
        except Exception as e:
            logger.exception(e)
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": "system_error",
                "data": None
            })
            return


if __name__ == "__main__":
    init()
    print(_model_paths)
