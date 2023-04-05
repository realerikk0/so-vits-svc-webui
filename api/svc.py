# -*- coding: utf-8 -*-
import logging
import tempfile

from inference.infer_tool import Svc
from typing import *
import api.base
import os
import io
import wave
import numpy as np
from service.tool import audio_normalize, read_wav_file_to_numpy_array
from utils import get_hparams_from_file

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
            audio_filename = audiofile['filename']
            audio_filebody = audiofile['body']
            audio_fileext = os.path.splitext(audio_filename)[-1].lower()

            with tempfile.NamedTemporaryFile(suffix=audio_fileext, delete=False) as temp_file:
                temp_file.write(audio_filebody)
                temp_file.close()

                converted_file = await audio_normalize(full_filename=audio_filename, file_data=audio_filebody)
                # if audio_fileext != ".wav":
                #     logger.debug(f"file format is {audio_fileext}, not wav\n"
                #                  f"converting to standard wav data...")
                #     converted_file = await audio_normalize(full_filename=audio_filename, file_data=audio_filebody)
                #     logger.debug(f"wav conversion completed.")
                # else:
                #     converted_file = temp_file.name

                sampling_rate, audio_array = read_wav_file_to_numpy_array(converted_file)
                os.remove(converted_file)

            scraudio = (sampling_rate, audio_array)

            logger.debug(f"read file {audio_filename}\n"
                         f"sampling rate: {sampling_rate}")

            tran = float(tran)
            th = float(th)
            ns = float(ns)

            hparams = get_hparams_from_file(f"checkpoints/{dsid}/config.json")
            spk = hparams.spk
            real_dsid = ""
            for k, v in spk.items():
                if v == 0:
                    real_dsid = k
            logger.debug(f"read dsid is: {real_dsid}")

            output_audio_sr, output_audio_array = _svc.inference(srcaudio=scraudio,
                                                                 chara=real_dsid,
                                                                 tran=tran,
                                                                 slice_db=th,
                                                                 ns=ns)

            logger.debug(f"svc for {audio_filename} succeed. \n"
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
            logger.debug(f"response completed.")
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

            logger.debug(len(self.request.files))

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

            hparams = get_hparams_from_file(f"checkpoints/{dsid}/config.json")
            spk = hparams.spk
            real_dsid = ""
            for k, v in spk.items():
                if v == 0:
                    real_dsid = k
            logger.debug(f"read dsid is: {real_dsid}")

            for idx, file in enumerate(audiofile_dict):
                audio_filename = file["filename"]
                audio_filebody = file["body"]
                filename = os.path.basename(audio_filename)
                audio_fileext = os.path.splitext(audio_filename)[-1].lower()

                with tempfile.NamedTemporaryFile(suffix=audio_fileext, delete=False) as temp_file:
                    temp_file.write(audio_filebody)
                    temp_file.close()

                    converted_file = await audio_normalize(full_filename=audio_filename, file_data=audio_filebody)

                    # if audio_fileext != ".wav":
                    #     logger.debug(f"file format is {audio_fileext}, not wav\n"
                    #                  f"converting to standard wav data...")
                    #     converted_file = await audio_normalize(full_filename=audio_filename, file_data=audio_filebody)
                    #     logger.debug(f"wav conversion completed.")
                    # else:
                    #     converted_file = temp_file.name

                    sampling_rate, audio_array = read_wav_file_to_numpy_array(converted_file)
                    os.remove(converted_file)

                scraudio = (sampling_rate, audio_array)

                print(f"{idx}, {len(audio_filebody)}, {filename}")

                output_sampling_rate, output_audio = _svc.inference(scraudio, chara=real_dsid, tran=tran,
                                                                    slice_db=th, ns=ns)
                new_filepath = f"{tmp_workdir_name}/{filename}"
                wavfile.write(filename=new_filepath, rate=output_sampling_rate, data=output_audio)
                output_files.append(new_filepath)

            zipfilename = f"{tmp_workdir_name}/output.zip"
            with ZipFile(zipfilename, "w") as zip_obj:
                for idx, filepath in enumerate(output_files):
                    zip_obj.write(filepath, os.path.basename(filepath))

            # todo: remove data

            logger.debug(f"start output data.")
            # set response header and body
            self.set_header("Content-Type", "application/zip")
            self.set_header("Content-Disposition", "attachment; filename=output.zip")
            with open(zipfilename, "rb") as file:
                self.write(file.read())
            await self.flush()
            logger.debug(f"response completed.")
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
