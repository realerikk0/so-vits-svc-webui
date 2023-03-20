from inference.infer_tool import Svc
from vextract.vocal_extract import VEX
import gradio as gr
import os


# os.environ['CUDA_VISIBLE_DEVICES'] = '1,2'


class VitsGradio:
    def __init__(self):
        self.so = Svc()
        self.v = VEX()
        self.lspk = []
        self.modelPaths = []
        for root, dirs, files in os.walk("checkpoints"):
            for dir in dirs:
                self.modelPaths.append(dir)
        with gr.Blocks(title="Sovits歌声合成工具") as self.Vits:
            gr.Markdown(
                """
                # 歌声合成工具
                - 请依次选择语音模型、设备以及运行模式，然后点击"载入模型"
                - 输入音频需要是干净的人声
                """
            )
            with gr.Tab("人声提取"):
                with gr.Row():
                    with gr.Column():
                        sample_audio = gr.Audio(label="输入音频")
                        extractAudioBtn = gr.Button("提取人声")
                with gr.Row():
                    with gr.Column():
                        self.sample_vocal_output = gr.Audio()
                        self.sample_accompaniment_output = gr.Audio()
                extractAudioBtn.click(self.v.separate, inputs=[sample_audio],
                                      outputs=[self.sample_vocal_output, self.sample_accompaniment_output],
                                      show_progress=True)
            with gr.Tab("歌声合成"):
                with gr.Row(visible=False) as self.VoiceConversion:
                    with gr.Column():
                        with gr.Row():
                            with gr.Column():
                                self.srcaudio = gr.Audio(label="输入音频")
                                self.btnVC = gr.Button("说话人转换")
                            with gr.Column():
                                with gr.Row():
                                    with gr.Column():
                                        self.dsid0 = gr.Dropdown(label="目标角色", choices=self.lspk)
                                        self.tran = gr.Slider(label="升降调", maximum=60, minimum=-60, step=1, value=0)
                                        self.th = gr.Slider(label="切片阈值", maximum=32767, minimum=-32768, step=0.1,
                                                            value=-40)
                                        self.ns = gr.Slider(label="噪音级别", maximum=1.0, minimum=0.0, step=0.1,
                                                            value=0.4)
                        with gr.Row():
                            self.VCOutputs = gr.Audio()
                    self.btnVC.click(self.so.inference, inputs=[self.srcaudio, self.dsid0, self.tran, self.th, self.ns],
                                     outputs=[self.VCOutputs], show_progress=True)

                with gr.Row(visible=False) as self.VoiceBatchConversion:
                    with gr.Column():
                        with gr.Row():
                            with gr.Column():
                                self.srcaudio = gr.Files(label="上传多个音频文件", file_types=['.wav'],
                                                         interactive=True)
                                self.btnVC = gr.Button("说话人转换")
                            with gr.Column():
                                with gr.Row():
                                    with gr.Column():
                                        self.dsid1 = gr.Dropdown(label="目标角色", choices=self.lspk)
                                        self.tran = gr.Slider(label="升降调", maximum=60, minimum=-60, step=1, value=0)
                                        self.th = gr.Slider(label="切片阈值", maximum=32767, minimum=-32768, step=0.1,
                                                            value=-40)
                                        self.ns = gr.Slider(label="噪音级别", maximum=1.0, minimum=0.0, step=0.1,
                                                            value=0.4)
                        with gr.Row():
                            self.VCOutputs = gr.File(label="Output Zip File", interactive=False)
                    self.btnVC.click(self.batch_inference, inputs=[self.srcaudio, self.dsid1, self.tran, self.th, self.ns],
                                     outputs=[self.VCOutputs], show_progress=True)

                with gr.Row():
                    with gr.Column():
                        modelstrs = gr.Dropdown(label="模型", choices=self.modelPaths, value=self.modelPaths[0],
                                                type="value")
                        devicestrs = gr.Dropdown(label="设备", choices=["cpu", "cuda"], value="cuda", type="value")
                        isbatchmod = gr.Radio(label="运行模式", choices=["single", "batch"], value="single",
                                              info="single: 单个文件处理. batch:批量处理支持上传多个文件")
                        btnMod = gr.Button("载入模型")
                        btnMod.click(self.loadModel, inputs=[modelstrs, devicestrs, isbatchmod],
                                     outputs=[self.dsid0, self.dsid1, self.VoiceConversion, self.VoiceBatchConversion],
                                     show_progress=True)

    def batch_inference(self, files, chara, tran, slice_db, ns, progress=gr.Progress()):
        from zipfile import ZipFile
        from scipy.io import wavfile
        import uuid

        temp_directory = "temp"
        if not os.path.exists(temp_directory):
            os.mkdir(temp_directory)

        progress(0.00, desc="初始化文件夹")
        tmp_workdir_name = f"{temp_directory}/batch_{uuid.uuid4()}"
        if not os.path.exists(tmp_workdir_name):
            os.mkdir(tmp_workdir_name)

        progress(0.10, desc="初始化文件夹")

        output_files = []

        for idx, file in enumerate(files):
            filename = os.path.basename(file.name)
            progress(0.10 + (0.70 / float(len(files))) * (idx + 1.00), desc=f"处理音频{(idx + 1)}/{len(files)}：{filename}")
            print(f"{idx}, {file}, {filename}")
            sampling_rate, audio = wavfile.read(file.name)
            output_sampling_rate, output_audio = self.so.inference((sampling_rate, audio), chara=chara, tran=tran,
                                                                   slice_db=slice_db, ns=ns)
            new_filepath = f"{tmp_workdir_name}/{filename}"
            wavfile.write(filename=new_filepath, rate=output_sampling_rate, data=output_audio)
            output_files.append(new_filepath)

        progress(0.70, desc="音频处理完毕")

        zipfilename = f"{tmp_workdir_name}/output.zip"
        with ZipFile(zipfilename, "w") as zip_obj:
            for idx, filepath in enumerate(output_files):
                zip_obj.write(filepath, os.path.basename(filepath))
        progress(0.80, desc="压缩完毕")
        # todo: remove data
        progress(1.00, desc="清理空间")
        return zipfilename

    def loadModel(self, path, device, process_mode):
        self.lspk = []
        print(f"path: {path}, device: {device}")
        self.so.set_device(device)
        print(f"device set.")
        self.so.load_checkpoint(path)
        print(f"checkpoint loaded")
        for spk, sid in self.so.hps_ms.spk.items():
            self.lspk.append(spk)
        print(f"LSPK: {self.lspk}")
        if process_mode == "single":
            VChange = gr.update(visible=True)
            VBChange = gr.update(visible=False)
        else:
            VChange = gr.update(visible=False)
            VBChange = gr.update(visible=True)
        SDChange = gr.update(choices=self.lspk, value=self.lspk[0])
        print("allset update display")
        return [SDChange, SDChange, VChange, VBChange]


if __name__ == "__main__":
    grVits = VitsGradio()
    grVits.Vits\
        .queue(concurrency_count=20, status_update_rate=5.0)\
        .launch(server_port=7870, share=True, show_api=True)
