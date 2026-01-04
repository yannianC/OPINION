# Opinion Trade 自动化控制台

一个基于 Vue 3 + Vite 的自动化任务监控控制台。

## 功能特性

- 📊 实时任务监控
- 📝 系统日志查看
- 🎨 现代化 UI 设计
- ⚡ 快速响应

## 快速开始

### 安装依赖

使用阿里镜像源安装依赖：

```bash
npm install --registry=https://registry.npmmirror.com
```

或者使用 cnpm：

```bash
cnpm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
web/
├── index.html          # HTML 入口
├── package.json        # 项目配置
├── vite.config.js      # Vite 配置
├── src/
│   ├── main.js         # 应用入口
│   ├── App.vue         # 根组件
│   └── style.css       # 全局样式
└── README.md           # 说明文档
```

## 技术栈

- Vue 3 - 渐进式 JavaScript 框架
- Vite - 下一代前端构建工具
- Axios - HTTP 客户端

## API 接口

控制台通过以下 API 与后端通信：

- `GET /api/99k/v2/mission/getOneMission` - 获取任务
- `POST /api/99k/v2/mission/saveResult` - 提交结果
- `POST /api/99k/v2/mission/addSucc` - 更新进度

## 开发说明

- 开发服务器运行在 `localhost:3000`
- API 请求会自动代理到 `https://sg.bicoin.com.cn`
- 支持热模块替换 (HMR)

## License

MIT

