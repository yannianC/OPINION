# 获取钱包地址脚本使用说明

## 功能说明

这个脚本用于批量获取钱包地址（contractCreator）：
1. 从服务器加载数据列表
2. 对于 `n` 字段为空的记录：
   - 获取代理配置（通过浏览器编号）
   - 使用代理请求 contract-creator API
   - 更新 `n` 字段到服务器

## 安装依赖

```bash
pip install -r requirements.txt
```

或者单独安装：
```bash
pip install requests requests[socks]
```

## 使用方法

直接运行脚本：
```bash
python get_wallet_addresses.py
```

## 脚本逻辑

1. **加载数据**：从服务器 API `/boost/findAccountConfigCache` 获取数据列表
2. **筛选记录**：找出 `n` 字段为空的记录
3. **获取代理配置**：
   - 调用 `/bro/getIp` API 获取代理 IP
   - 根据 `isMain` 字段决定代理类型：
     - `isMain=1`：使用 HTTP 代理，端口和认证信息从服务器获取
     - `isMain!=1`：使用 SOCKS5 代理，端口固定为 `50100`，认证信息从服务器获取或使用默认值
4. **请求 contract-creator**：
   - 使用代理配置请求 `http://opinion.api.predictscan.dev:10001/api/user/contract-creator/{address}`
   - 获取 `contractCreator` 值
5. **更新数据**：将 `contractCreator` 保存到 `n` 字段，并上传到服务器

## 代理配置说明

- **HTTP 代理**：格式 `http://username:password@ip:port`
- **SOCKS5 代理**：格式 `socks5://username:password@ip:port`
- **端口**：SOCKS5 代理固定使用 `50100`
- **类型**：SOCKS5 代理固定使用 `SOCKS5` 类型

## 注意事项

1. 脚本会逐个处理记录，每个请求间隔 500ms，避免请求过快
2. 如果 `h` 字段为空，会跳过该记录
3. 如果缺少浏览器编号，会跳过该记录
4. 如果获取代理配置失败，会跳过该记录
5. 如果请求 contract-creator 失败，会跳过该记录
6. 脚本会显示详细的处理日志，包括成功、失败和跳过的记录数

## 输出示例

```
[2025-01-XX XX:XX:XX] ============================================================
[2025-01-XX XX:XX:XX] 开始获取钱包地址...
[2025-01-XX XX:XX:XX] ============================================================
[2025-01-XX XX:XX:XX] ✓ 成功加载 100 条数据
[2025-01-XX XX:XX:XX] 找到 50 条需要处理的记录

[1/50] 处理记录: fingerprintNo=4001, index=1
[4001] 调用获取新IP接口（超时: 15秒）...
[4001] ✓ 成功获取新代理配置 (isMain=0): IP=xxx.xxx.xxx.xxx, Port=50100, Type=SOCKS5
[代理请求] 地址: 0x88ca51cc60c0b0032efc63dd89581071276810e4, 代理: xxx.xxx.xxx.xxx:50100 (SOCKS5)
✓ 成功获取 contractCreator: 0x649ca7ffaf0dad3c392f0a72ab4be1d74fdbcf0b
✓ 数据保存成功: fingerprintNo=4001
✓ 成功处理并保存: contractCreator=0x649ca7ffaf0dad3c392f0a72ab4be1d74fdbcf0b

...

[2025-01-XX XX:XX:XX] ============================================================
[2025-01-XX XX:XX:XX] 处理完成！
[2025-01-XX XX:XX:XX] 成功: 45 个
[2025-01-XX XX:XX:XX] 失败: 3 个
[2025-01-XX XX:XX:XX] 跳过: 2 个
[2025-01-XX XX:XX:XX] ============================================================
```

