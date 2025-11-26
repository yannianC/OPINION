# 账户数据管理系统

## 功能说明

### 1. 主要功能
- 显示账户数据列表
- 添加新账户（单行或批量10行）
- 编辑账户信息（电脑组、浏览器编号、平台）
- 刷新单个账户的仓位数据
- 保存所有修改

### 2. 表格字段说明
- **序号**: 自动递增，不可编辑
- **电脑组**: 可编辑输入框
- **指纹浏览器编号**: 可编辑输入框
- **平台**: 下拉选择（OP/Ploy）
- **余额**: 只读，显示balance字段
- **Portfolio**: 只读，显示totalVolume字段
- **持有仓位**: 显示解析后的仓位信息
  - 标题
  - YES/NO标签
  - 仓位数量
  - 开仓价格
- **挂单仓位**: 显示解析后的挂单信息
  - 标题
  - YES/NO标签
  - 挂单数量
  - 挂单价格
- **操作**: "刷新仓位"按钮

### 3. 接口说明

#### 获取列表
```
GET https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache
返回: { msg: null, data: [...] }
```

#### 保存数据
```
POST https://sg.bicoin.com.cn/99l/boost/addAccountConfig
请求体: [账户对象数组]
```

#### 刷新仓位
```
GET https://sg.bicoin.com.cn/99l/boost/findAccountConfigByNo?no={浏览器编号}
返回: { data: {...} }
```

## 安装和运行

### 1. 安装依赖
```bash
cd dataweb
npm install
```

使用阿里镜像（如果npm慢）：
```bash
npm install --registry=https://registry.npmmirror.com
```

### 2. 运行开发服务器
```bash
npm run dev
```

服务器将在 http://localhost:3000 启动

### 3. 构建生产版本
```bash
npm run build
```

构建结果在 `dist` 目录

## 技术栈
- Vue 3 (Composition API)
- Element Plus (UI组件库)
- Vite (构建工具)
- Axios (HTTP请求)

## 数据解析逻辑

### OP平台数据解析
- **Position数据**: 每7项为一组
  - 索引0: 标题
  - 索引1: YES/NO
  - 索引2: 数量
  - 索引4: 价格

- **Open Orders数据**: 每11项为一组
  - 索引0: 标题
  - 索引2: YES/NO
  - 索引4: 价格
  - 索引6: 数量

### Polymarket平台数据解析
- 数据结构: tr数组 -> td数组 -> item对象数组
- 从item对象中提取h2(标题)和div(YES/NO)

## 注意事项

1. 新增行时ID字段为null，保存后服务器会分配ID
2. 更新已有数据时必须保留原有的ID
3. 所有未使用的字段也需要传递（null、空字符串或0）
4. 刷新仓位前需要先保存浏览器编号

