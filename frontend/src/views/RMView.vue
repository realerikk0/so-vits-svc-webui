<template>
  <div class="svc-container">
    <div class="svc-wrapper">
      <div class="form-panel single-run">
        <h1 class="form-title">歌曲音声分离</h1>
        <h3 class="model-tips">上传歌曲，运行可下载人声（vocals.wav）与背景音乐（accompaniment.wav）</h3>
        <el-form class="svc-form single-run-form" :model="singleForm" label-width="150px">
          <el-upload
              ref="audioSingleUpload"
              class="audio-upload"
              action=""
              accept=".wav,.mp3"
              :http-request="handleSingleUpload"
          >
            <template #trigger>
              <el-button type="primary" v-loading="isRuningSingle">选择音频文件并开始转换！</el-button>
            </template>

            <template #tip>
              <div class="el-upload__tip">
                需要是wav或者mp3文件哦
              </div>
            </template>
          </el-upload>
        </el-form>
      </div>

    </div>

<!--    <GreetingAudio :title="audioTitle" :src="audioSrc" v-if="audioLoaded"></GreetingAudio>-->
  </div>
</template>

<script>
import axios from "axios";
import JSZip from "jszip";
import GreetingAudio from "@/components/GreetingAudio.vue";

export default {
  name: 'RMView',
  components: {GreetingAudio},
  data() {
    return {
      singleForm: {
        srcaudio: null,
      },
      isRuningSingle: false,
    }
  },
  mounted() {
  },
  methods: {
    async handleSingleUpload(file) {
      try {
        this.isRuningSingle = true
        console.log("HANDLE UPLOAD")
        console.log(file)
        let srcaudio = file.file
        if (srcaudio) {
          console.log(srcaudio)
          let runData = new FormData()
          runData.append("srcaudio", srcaudio)

          let resp = await axios.post('/api/vm/run', runData)
          if (resp.status === 200) {
            const zipBlob = new Blob([resp.data], { type: 'application/zip' });

            // Create a temporary link element to trigger the download
            const link = document.createElement('a');
            link.href = URL.createObjectURL(zipBlob);
            link.download = 'output.zip';

            // Trigger the download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.isRuningSingle = false
          } else {
            this.$message.error('Failed to load model: ' + resp.data.msg)
            this.isRuningSingle = false
          }
        } else {
          this.$message.error('Error unable to get audio files')
          this.isRuningSingle = false
        }
      } catch (e) {
        this.$message.error('Failed to run: ' + e)
      } finally {
        this.isRuningSingle = false
      }
    },
    getFileURL(file) {
      // Create a blob URL for the file
      const blob = new Blob([file], { type: 'audio/wav' })
      return URL.createObjectURL(blob)
    }
  }
}
</script>

<style scoped>
.svc-container {
  height: 100%;
  width: 100%;
}

.svc-wrapper {
  top: 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  /*background-color: #ccc;*/
}

.svc-form {
  max-width: 460px;
}

.svc-form el-alert {
  margin: 10px auto;
}

.svc-form el-form-item {
  margin-top: 10px;
}

.form-title {
  margin: 20px auto;
}
</style>
