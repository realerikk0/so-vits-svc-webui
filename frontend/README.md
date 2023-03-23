# SVS SYSTEM

## Features
- 支持SVC模式切换
- 支持批量/单个处理

## Todos
- 音频清洗（需要ffmpeg）
- VocalRemover
- DiffSinger support coming soon

## Install & Run
### 预先下载的模型文件
+ 需要装有Node以及npm
+ 在frontend文件夹下
```shell
npm i
```

### 配置
1. 修改/frontend/src/main.ts文件，将axios.defaults.baseURL修改为服务器运行的IP地址与端口号
2. 运行
```bash
npm run buid
```
执行构建


## Some npm helpers

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
npm run test:unit
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
