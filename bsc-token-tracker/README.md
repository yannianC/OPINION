# BSC Token Transfers 查询工具

查询 BSC 链上 Token 转账记录的工具，提供两种版本：

## 版本选择

### 🐍 Python 脚本版 - 链上直接查询

直接在命令行运行，通过 Web3 连接 BSC 节点查询。

**特点：**
- ✅ 无需 API Key
- ❌ 需要分批查询（公共节点限制）
- ❌ 查询速度较慢

**快速开始：**
```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python bsc_query.py <地址>
```

详细说明：[使用说明.md](使用说明.md)

### 🚀 Python 脚本版 - BscScan API（推荐）

使用 BscScan API，无需分批查询，更快速直接。

**特点：**
- ✅ 无需分批查询，一次获取所有数据
- ✅ 查询速度快
- ✅ 支持查询全部历史数据
- ⚠️ 需要免费 API Key（在 https://bscscan.com/apis 注册）

**快速开始：**
```bash
# 安装依赖
pip install requests

# 1. 获取 BscScan API Key（免费）
#    访问 https://bscscan.com/apis 注册并获取

# 2. 修改 bsc_query_bscscan.py 中的 BSCSCAN_API_KEY

# 3. 运行脚本
python bsc_query_bscscan.py <地址>
```

### 🌐 纯前端 HTML 版

在浏览器中直接运行，无需安装依赖。

**快速开始：**
1. 双击打开 `index.html` 文件
2. 输入 BSC 地址即可查询

详细说明：[使用说明-纯前端版.md](使用说明-纯前端版.md)

## 功能特性

- ✅ **Token 转账查询**：查询 ERC20 Token 转账记录
- ✅ **BNB 转账查询**：查询 BNB 转账记录
- ✅ **实时数据**：直接从链上获取最新数据
- ✅ **详细信息**：显示时间、类型、方向、数量、交易哈希等
- ✅ **保存功能**：可保存查询结果到 JSON 文件（Python 版）

## 项目结构

```
bsc-token-tracker/
├── bsc_query.py           # Python 脚本版本（推荐）
├── index.html             # 纯前端 HTML 版本
├── requirements.txt       # Python 依赖
├── 使用说明.md           # Python 版本使用说明
├── 使用说明-纯前端版.md   # HTML 版本使用说明
└── README.md             # 本文件
```

## 推荐使用

- **Python 脚本版**：更稳定，功能更完整，推荐日常使用
- **HTML 前端版**：适合快速查看，但可能遇到浏览器兼容性问题

## 注意事项

1. **BNB 转账查询**：默认只查询最近 10000 个区块（约 3-4 天）
2. **网络连接**：确保能够访问 BSC RPC 节点
3. **查询速度**：Token 转账查询较快，BNB 转账需要遍历区块，可能较慢

