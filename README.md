# SO-VITS-SVC 4.0 WEBUI

## Features
- 支持so-vits-svc 4.0，添加4.0的一些参数；
- 支持批量转换，输出文件名暂定为原文件名，执行打包下载；
- 添加人声提取Tab，需要Spleeter；
- Python 3.8。



## Install & Run
### 预先下载的模型文件
+ contentvec ：[checkpoint_best_legacy_500.pt](https://ibm.box.com/s/z1wgl1stco8ffooyatzdwsqn2psd9lrr)
  + 放在`hubert`目录下
```shell
# 一键下载
# contentvec
http://obs.cstcloud.cn/share/obs/sankagenkeshi/checkpoint_best_legacy_500.pt
# 也可手动下载放在hubert目录
```

### 配置
0. 新建"checkpoints"文件夹，并在文件夹下面新建角色名字的子文件夹
1. 将模型文件命名为“model.pth”，并和kmeans_10000.pt与config.json一同拷贝到角色名的子文件夹中
2. 运行
```bash
pip install -r requirements.txt
```
安装依赖

3. 运行
```bash
python main.py
```
运行程序