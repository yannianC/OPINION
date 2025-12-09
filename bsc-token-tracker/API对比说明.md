# API 查询方式对比

## 当前实现方式

### 方式一：直接链上查询（bsc_query.py）

**使用的 API：** `eth_getLogs`（以太坊 JSON-RPC 标准）

**工作原理：**
- 通过 Web3 连接 BSC RPC 节点
- 调用 `eth_getLogs` API 查询事件日志
- 查询 Transfer 事件来获取 Token 转账记录

**为什么需要分批查询？**
- 公共 RPC 节点对查询范围有限制（`limit exceeded` 错误）
- 如果查询范围太大，会返回错误
- 所以需要分成小批次查询（每批 100-2000 个区块）

**优点：**
- ✅ 无需 API Key
- ✅ 完全去中心化
- ✅ 实时数据

**缺点：**
- ❌ 需要分批查询（慢）
- ❌ 公共节点限制严格
- ❌ 查询大量历史数据困难

---

### 方式二：BscScan API（bsc_query_bscscan.py）⭐ 推荐

**使用的 API：** BscScan 官方 API

**工作原理：**
- 直接调用 BscScan 的 REST API
- API 已经索引了所有交易数据
- 一次请求可以获取最多 10000 条记录

**为什么不需要分批查询？**
- BscScan API 已经处理好了数据索引
- 支持分页查询（page 和 offset 参数）
- 可以一次获取大量数据

**优点：**
- ✅ **无需分批查询**，一次获取所有数据
- ✅ 查询速度快
- ✅ 支持查询全部历史数据
- ✅ 免费 API Key（有速率限制，但足够使用）
- ✅ 更稳定可靠

**缺点：**
- ⚠️ 需要注册免费 API Key（在 https://bscscan.com/apis）
- ⚠️ 依赖第三方服务（BscScan）

---

## 对比总结

| 特性 | 链上直接查询 | BscScan API |
|------|------------|------------|
| 需要 API Key | ❌ 不需要 | ✅ 需要（免费） |
| 分批查询 | ❌ 需要 | ✅ 不需要 |
| 查询速度 | ⚠️ 较慢 | ✅ 快速 |
| 查询范围 | ⚠️ 受限（公共节点） | ✅ 全部历史 |
| 稳定性 | ⚠️ 受 RPC 节点影响 | ✅ 稳定 |
| 去中心化 | ✅ 完全去中心化 | ❌ 依赖 BscScan |

## 推荐使用

**如果只是查询 Token Transfers 记录，强烈推荐使用 BscScan API 版本：**

1. **更简单**：无需分批查询，一次获取所有数据
2. **更快速**：查询速度快，无需等待
3. **更稳定**：不受 RPC 节点限制影响
4. **免费**：BscScan 提供免费 API Key

**使用步骤：**

1. 访问 https://bscscan.com/apis
2. 注册账号并创建免费 API Key
3. 修改 `bsc_query_bscscan.py` 中的 `BSCSCAN_API_KEY`
4. 运行脚本即可

```bash
python bsc_query_bscscan.py <地址>
```

就这么简单！无需分批查询，一次获取所有数据。

