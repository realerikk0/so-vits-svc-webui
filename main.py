from inference.infer_tool import Svc
from vextract.vocal_extract import VEX
import gradio as gr
import os


class VitsGradio:
    def __init__(self):
        self.so = Svc()
        self.v = VEX()
        self.lspk = []
        self.modelPaths = []
        for root, dirs, files in os.walk("checkpoints"):
            for dir in dirs:
                self.modelPaths.append(dir)
        with gr.Blocks() as self.Vits:
            gr.Markdown(
                """
                # 歌声合成工具
                - 请先选择声音模型，然后点击"载入模型"
                - 输入音频需要是干净的人声哦
                """
            )
            with gr.Tab("人声提取", visible=self.testSpleeter()):
                with gr.Row():
                    with gr.Column():
                        sample_audio = gr.Audio(label="输入音频")
                        extractAudioBtn = gr.Button("提取人声")
                with gr.Row():
                    with gr.Column():
                        self.sample_vocal_output = gr.Audio()
                        self.sample_accompaniment_output = gr.Audio()
                extractAudioBtn.click(self.v.separate, inputs=[sample_audio], outputs=[self.sample_vocal_output, self.sample_accompaniment_output], show_progress=True)
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
                                        self.dsid = gr.Dropdown(label="目标角色", choices=self.lspk)
                                        self.tran = gr.Slider(label="升降调", maximum=60, minimum=-60, step=1, value=0)
                                        self.th = gr.Slider(label="切片阈值", maximum=32767, minimum=-32768, step=0.1,
                                                            value=-40)
                                        self.ns = gr.Slider(label="噪音级别", maximum=1.0, minimum=0.0, step=0.1,
                                                            value=0.4)
                        with gr.Row():
                            self.VCOutputs = gr.Audio()
                    self.btnVC.click(self.so.inference, inputs=[self.srcaudio, self.dsid, self.tran, self.th, self.ns], outputs=[self.VCOutputs], show_progress=True)

                with gr.Row():
                    with gr.Column():
                        modelstrs = gr.Dropdown(label="模型", choices=self.modelPaths, value=self.modelPaths[0], type="value")
                        devicestrs = gr.Dropdown(label="设备", choices=["cpu", "cuda"], value="cpu", type="value")
                        btnMod = gr.Button("载入模型")
                        btnMod.click(self.loadModel, inputs=[modelstrs, devicestrs], outputs=[self.dsid, self.VoiceConversion], show_progress=True)

    def loadModel(self, path, device):
        self.lspk = []
        print(f"path: {path}, device: {device}")
        self.so.set_device(device)
        self.so.load_checkpoint(path)
        for spk, sid in self.so.hps_ms.spk.items():
            self.lspk.append(spk)
        VChange = gr.update(visible=True)
        SDChange = gr.update(choices=self.lspk, value=self.lspk[0])
        return [SDChange, VChange]

    def testSpleeter(self):
        try:
            import spleeter
            return True
        except ImportError:
            return False


if __name__ == "__main__":
    grVits = VitsGradio()
    grVits.Vits.launch(server_port=7870)
