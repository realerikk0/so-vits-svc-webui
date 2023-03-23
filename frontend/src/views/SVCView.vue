<template>
  <div class="svc-container">
    <div class="svc-wrapper">
      <div class="form-panel">
        <h1 class="form-title">基本设置</h1>
        <el-form class="svc-form" :model="initForm" label-width="150px">
          <el-alert type="info" show-icon :closable="false">
            单个文件处理需要提供音频文件，输出会是单个音频文件； <br>
            批量处理支持上传多个音频文件，输出会是一个zip压缩包。
          </el-alert>
          <el-form-item label="运行模式" required>
            <el-select v-model="initForm.mode" placeholder="选择运行模式" default-first-option=default-first-option>
              <el-option label="单个处理" value="single"></el-option>
              <el-option label="批量处理" value="batch"></el-option>
            </el-select>
          </el-form-item>

          <el-alert type="info" show-icon :closable="false">
            运行设备，默认选择cuda，即GPU计算；如果没有支持的GPU设备可以选择cpu。
          </el-alert>
          <el-form-item label="计算设备" required>
            <el-select v-model="initForm.device" placeholder="选择计算设备" default-first-option="default-first-option">
              <el-option label="GPU(cuda)" value="cuda"></el-option>
              <el-option label="CPU" value="cpu"></el-option>
            </el-select>
          </el-form-item>

          <el-alert type="info" show-icon :closable="false">
            选择一个语音模型
          </el-alert>
          <el-form-item label="语音模型" required>
            <el-select v-model="initForm.model" placeholder="选择语音模型">
              <el-option
                  v-for="modelName in this.models"
                  :key="modelName"
                  :label="modelName"
                  :value="modelName"
              />
            </el-select>
          </el-form-item>

          <el-button type="primary" @click="loadModel" v-loading="isLoadingModel">加载模型</el-button>
        </el-form>
      </div>

      <el-divider v-if="displaySVCForm" />

      <div class="form-panel single-run" v-if="displaySingleSVCForm">
        <h1 class="form-title">制作一个歌曲。</h1>
        <h3 class="model-tips">你使用的语音模型是 {{initForm.model}}</h3>
        <el-form class="svc-form single-run-form" :model="singleForm" label-width="150px">
          <el-upload
              ref="audioSingleUpload"
              class="audio-upload"
              action=""
              accept=".wav"
              :auto-upload="false"
          >
            <template #trigger>
              <el-button type="primary">选择音频文件</el-button>
            </template>

            <el-button class="ml-3" type="success" @click="handleSingleUpload">
              开始制作！
            </el-button>

            <template #tip>
              <div class="el-upload__tip">
                需要是wav文件哦
              </div>
            </template>
          </el-upload>
        </el-form>
      </div>

      <div class="form-panel batch-run" v-if="displayBatchSVCForm">
        <h1 class="form-title">制作多个歌曲。</h1>
        <h3 class="model-tips">你使用的语音模型是 {{initForm.model}}</h3>
        <el-form class="svc-form batch-run-form" :model="batchForm" label-width="150px">
          <el-upload
              ref="audioBatchUpload"
              class="audio-upload"
              action=""
              accept=".wav"
              :auto-upload="false"
              multiple
          >
            <template #trigger>
              <el-button type="primary">选择音频文件</el-button>
            </template>

            <el-button class="ml-3" type="success" @click="handleBatchUpload">
              开始制作！
            </el-button>

            <template #tip>
              <div class="el-upload__tip">
                需要是wav文件哦
              </div>
            </template>
          </el-upload>
        </el-form>
      </div>

    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: 'SVCView',
  data() {
    return {
      models: [],
      initForm: {
        mode: '',
        model: '',
        device: '',
      },
      singleForm: {
        dsid: '',
        srcaudio: null,
      },
      batchForm: {
        dsid: '',
        srcaudio: [],
      },
      displaySVCForm: false,
      displaySingleSVCForm: false,
      displayBatchSVCForm: false,
      isLoadingModel: false,
      isRuningSingle: false,
      isRunningBatch: false
    }
  },
  mounted() {
    this.getModelLists()
  },
  methods: {
    axios,
    async getModelLists() {
      try {
        let resp = (await axios.get('/api/svc/model')).data
        if (resp.code === 200) {
          this.models = resp.data
          console.log(this.models)
        } else {
          this.$message.error('Failed to fetch model information: ' + resp.msg)
        }
      } catch (e) {
        this.$message.error('Failed to fetch model information: ' + e)
      }
    },
    async loadModel() {
      try {
        this.isLoadingModel = true
        let initFormData = new FormData()
        initFormData.append("mode", this.initForm.mode)
        initFormData.append("device", this.initForm.device)
        initFormData.append("model", this.initForm.model)
        let resp = (await axios.post('/api/svc/switch', initFormData)).data
        if (resp.code === 200) {
          this.displaySVCForm = true
          console.log(resp.data.mode)
          if (resp.data.mode === "single") {
            this.displaySingleSVCForm = true
          } else if (resp.data.mode === "batch") {
            this.displayBatchSVCForm = true
          }
        } else {
          this.$message.error('Failed to load model: ' + resp.msg)
        }
      } catch (e) {
        this.$message.error('Failed to load model: ' + e)
      } finally {
        this.isLoadingModel = false
      }
    },
    async handleSingleUpload() {
      try {
        let uploadComponent = this.$refs.audioSingleUpload
        let srcaudio = uploadComponent.uploadFiles[0]
        if (srcaudio) {
          let runData = new FormData()
          runData.append("srcaudio", srcaudio.raw)
          runData.append("dsid", this.initForm.model)

          let resp = await axios.post('/api/svc/run', runData)
          if (resp.status === 200) {
            // todo: 生成一个音频播放器
            // todo: resp.data audio/wav
          } else {
            this.$message.error('Failed to load model: ' + resp.data.msg)
          }
        } else {
          this.$message.error('Error unable to get audio file')
        }
      } catch (e) {
        this.$message.error('Failed to run: ' + e)
      }
    },
    async handleBatchUpload() {
      try {
        let uploadComponent = this.$refs.audioBatchUpload
        const audioFiles = uploadComponent.uploadFiles
        if (audioFiles.length > 0) {
          let runData = new FormData()
          for (let file in audioFiles) {
            runData.append('srcaudio[]', file.raw)
          }
          runData.append("dsid", this.initForm.model)

          let resp = await axios.post('/api/svc/batch', runData)
          if (resp.status === 200) {
            // todo: 生成一个下载
            // todo: resp.data application/zip
          } else {
            this.$message.error('Failed to load model: ' + resp.data.msg)
          }
        } else {
          this.$message.error('Error unable to get audio file')
        }
      } catch (e) {
        this.$message.error('Failed to run: ' + e)
      }
    },
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
