<template>
  <div class="account-anomaly-page">
    <h1 class="page-title">账号异常查询</h1>
    
    <div class="toolbar">
      <el-button type="primary" @click="loadData" :loading="loading">
        刷新列表
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="tableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 300px)"
    >
      <el-table-column prop="index" label="序号" width="80" align="center" fixed />
      
      <el-table-column label="电脑组" width="100" align="center">
        <template #default="scope">
          {{ scope.row.computeGroup }}
        </template>
      </el-table-column>

      <el-table-column label="指纹浏览器编号" width="150" align="center">
        <template #default="scope">
          {{ scope.row.fingerprintNo }}
        </template>
      </el-table-column>

      <el-table-column label="平台" width="120" align="center">
        <template #default="scope">
          {{ scope.row.platform || 'OP' }}
        </template>
      </el-table-column>

      <el-table-column label="余额 (Balance)" width="120" align="center">
        <template #default="scope">
          {{ formatNumber(scope.row.balance) }}
        </template>
      </el-table-column>

      <el-table-column label="Portfolio" width="120" align="center">
        <template #default="scope">
          {{ formatNumber(scope.row.c) }}
        </template>
      </el-table-column>

      <el-table-column 
        label="未成交数量" 
        width="130" 
        align="center" 
        sortable 
        :sort-method="(a, b) => sortByNumber(a.pendingQuantity, b.pendingQuantity)"
      >
        <template #default="scope">
          {{ formatNumber(scope.row.pendingQuantity) }}
        </template>
      </el-table-column>

      <el-table-column 
        label="未成交金额" 
        width="130" 
        align="center" 
        sortable 
        :sort-method="(a, b) => sortByNumber(a.pendingAmount, b.pendingAmount)"
      >
        <template #default="scope">
          {{ formatNumber(scope.row.pendingAmount) }}
        </template>
      </el-table-column>

      <el-table-column label="挂单仓位 (b)" width="500">
        <template #default="scope">
          <div v-if="scope.row.b && parsedOrders[scope.row.index]" class="position-list">
            <div 
              v-for="(order, idx) in parsedOrders[scope.row.index]" 
              :key="idx" 
              class="position-item"
            >
              <div class="position-title">{{ order.title }}</div>
              <div class="position-details">
                <template v-if="order.buySellDirection !== undefined">
                  <el-tag 
                    :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" 
                    size="small"
                  >
                    {{ order.buySellDirection }}
                  </el-tag>
                  <el-tag 
                    :type="order.option === 'YES' ? 'success' : 'danger'" 
                    size="small"
                    style="margin-left: 4px;"
                  >
                    {{ order.option }}
                  </el-tag>
                  <span class="position-price" style="margin-left: 8px;">价格: {{ order.price }}</span>
                  <span class="position-amount" style="margin-left: 8px;">进度: {{ order.progress }}</span>
                </template>
                <template v-else>
                  <span class="position-price">{{ order.price }}</span>
                  <span class="position-amount">{{ order.progress }}</span>
                </template>
              </div>
            </div>
          </div>
          <span v-else-if="scope.row.b" class="raw-data-text">{{ scope.row.b }}</span>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="仓位抓取时间(d)" width="150" align="center">
        <template #default="scope">
          {{ formatTime(scope.row.d) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" align="center" fixed="right">
        <template #default="scope">
          <el-button 
            type="primary" 
            size="small"
            @click="refreshPosition(scope.row)"
            :loading="scope.row.refreshing"
          >
            刷新仓位
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'

const loading = ref(false)
const tableData = ref([])
const parsedOrders = ref({})

/**
 * 格式化数字
 */
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '0.00'
  const num = parseFloat(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

/**
 * 格式化时间
 */
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(parseInt(timestamp))
  return date.toLocaleString('zh-CN')
}

/**
 * 数字排序方法
 */
const sortByNumber = (a, b) => {
  const numA = parseFloat(a) || 0
  const numB = parseFloat(b) || 0
  return numA - numB
}

/**
 * 解析带逗号的数字字符串（如：1,369.55）
 */
const parseNumberWithComma = (str) => {
  if (!str) return 0
  // 移除逗号后解析
  const cleaned = str.replace(/,/g, '')
  return parseFloat(cleaned) || 0
}

/**
 * 解析挂单数据字符串
 */
const parseOpenOrders = (ordersStr) => {
  if (!ordersStr) return []
  
  try {
    const orders = []
    const items = ordersStr.split(';')
    
    for (const item of items) {
      if (!item.trim()) continue
      
      // 优先尝试新格式（5个字段：唯一标题|||买卖方向|||选项|||价格|||进度）
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 5) {
          // 新格式：唯一标题|||买卖方向|||选项|||价格|||进度
          const progress = parts[4].trim()
          const price = parts[3].trim()
          
          // 解析价格：83.8 ¢ -> 提取数字部分
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pendingQuantity = 0
          let pendingAmount = 0
          
          // 判断进度格式：$0/$462.2（金额格式）或 60.55/554.74shares 或 239.13/1,369.55shares（数量格式）
          if (progress.includes('$')) {
            // 金额格式：$0/$462.2 或 $0/$1,462.2 -> 未成交金额 = 总金额 - 已成交金额
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              pendingAmount = totalAmount - filledAmount
              // 未成交数量 = 未成交金额 * 100 / 价格
              if (priceNum > 0) {
                pendingQuantity = (pendingAmount * 100) / priceNum
              }
            }
          } else {
            // 数量格式：60.55/554.74shares 或 239.13/1,369.55shares -> 未成交数量 = 总数量 - 已成交数量
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              const filled = parseNumberWithComma(progressMatch[1])
              const total = parseNumberWithComma(progressMatch[2])
              pendingQuantity = total - filled
              // 计算未成交金额：价格 * 未成交数量 / 100
              pendingAmount = (priceNum * pendingQuantity) / 100
            }
          }
          
          orders.push({
            title: parts[0].trim(),
            buySellDirection: parts[1].trim(), // "Buy" 或 "Sell"
            option: parts[2].trim(), // "YES" 或 "NO"
            price: price,
            progress: progress,
            pendingQuantity: pendingQuantity,
            pendingAmount: pendingAmount
          })
        } else if (parts.length >= 3) {
          // 兼容旧格式（3个字段：标题|||价格|||进度）
          const progress = parts[2].trim()
          const price = parts[1].trim()
          
          // 解析价格
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pendingQuantity = 0
          let pendingAmount = 0
          
          // 判断进度格式：$0/$462.2（金额格式）或 60.55/554.74shares 或 239.13/1,369.55shares（数量格式）
          if (progress.includes('$')) {
            // 金额格式：$0/$462.2 或 $0/$1,462.2 -> 未成交金额 = 总金额 - 已成交金额
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              pendingAmount = totalAmount - filledAmount
              // 未成交数量 = 未成交金额 * 100 / 价格
              if (priceNum > 0) {
                pendingQuantity = (pendingAmount * 100) / priceNum
              }
            }
          } else {
            // 数量格式：60.55/554.74shares 或 239.13/1,369.55shares -> 未成交数量 = 总数量 - 已成交数量
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              const filled = parseNumberWithComma(progressMatch[1])
              const total = parseNumberWithComma(progressMatch[2])
              pendingQuantity = total - filled
              // 计算未成交金额：价格 * 未成交数量 / 100
              pendingAmount = (priceNum * pendingQuantity) / 100
            }
          }
          
          orders.push({
            title: parts[0].trim(),
            price: price,
            progress: progress,
            pendingQuantity: pendingQuantity,
            pendingAmount: pendingAmount
          })
        }
      } else {
        // 兼容更旧格式（逗号分隔符）
        const parts = item.split(',')
        if (parts.length >= 3) {
          const progress = parts[2].trim()
          const price = parts[1].trim()
          
          // 解析价格
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pendingQuantity = 0
          let pendingAmount = 0
          
          // 判断进度格式：$0/$462.2（金额格式）或 60.55/554.74shares 或 239.13/1,369.55shares（数量格式）
          if (progress.includes('$')) {
            // 金额格式：$0/$462.2 或 $0/$1,462.2 -> 未成交金额 = 总金额 - 已成交金额
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              pendingAmount = totalAmount - filledAmount
              // 未成交数量 = 未成交金额 * 100 / 价格
              if (priceNum > 0) {
                pendingQuantity = (pendingAmount * 100) / priceNum
              }
            }
          } else {
            // 数量格式：60.55/554.74shares 或 239.13/1,369.55shares -> 未成交数量 = 总数量 - 已成交数量
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              const filled = parseNumberWithComma(progressMatch[1])
              const total = parseNumberWithComma(progressMatch[2])
              pendingQuantity = total - filled
              // 计算未成交金额：价格 * 未成交数量 / 100
              pendingAmount = (priceNum * pendingQuantity) / 100
            }
          }
          
          orders.push({
            title: parts[0].trim(),
            price: price,
            progress: progress,
            pendingQuantity: pendingQuantity,
            pendingAmount: pendingAmount
          })
        }
      }
    }
    
    return orders
  } catch {
    return []
  }
}

/**
 * 加载数据列表
 */
const loadData = async () => {
  loading.value = true
  
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`)
    
    if (response.data && response.data.data) {
      const serverData = response.data.data
      
      // 只保留有挂单（b字段不为空）的数据
      const filteredData = serverData.filter(item => item.b && item.b.trim())
      
      // 处理数据
      const processedData = filteredData.map((item, index) => {
        const rowIndex = index + 1
        const orders = item.b ? parseOpenOrders(item.b) : []
        
        // 计算总的未成交数量和未成交金额
        let totalPendingQuantity = 0
        let totalPendingAmount = 0
        orders.forEach(order => {
          totalPendingQuantity += order.pendingQuantity || 0
          totalPendingAmount += order.pendingAmount || 0
        })
        
        return {
          index: rowIndex,
          id: item.id,
          computeGroup: item.computeGroup || '',
          fingerprintNo: item.fingerprintNo || '',
          platform: item.e || item.platform || 'OP',
          balance: item.balance || 0,
          c: item.c || '0',
          b: item.b || '',
          d: item.d || '',
          pendingQuantity: totalPendingQuantity,
          pendingAmount: totalPendingAmount,
          refreshing: false
        }
      })
      
      tableData.value = processedData
      
      // 解析所有挂单数据
      parsedOrders.value = {}
      processedData.forEach(row => {
        if (row.b) {
          parsedOrders.value[row.index] = parseOpenOrders(row.b)
        }
      })
      
      ElMessage.success(`数据加载成功，共 ${processedData.length} 条有挂单的数据`)
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 刷新单个账户的仓位数据
 */
const refreshPosition = async (row) => {
  if (!row.fingerprintNo) {
    ElMessage.warning('请先填写浏览器编号')
    return
  }
  
  if (!row.platform) {
    ElMessage.warning('请先选择平台')
    return
  }
  
  if (!row.computeGroup) {
    ElMessage.warning('请先填写电脑组')
    return
  }
  
  // 检查平台类型，仅支持 OP 平台
  if (row.platform !== 'OP') {
    ElMessage.warning('当前仅支持 OP 平台的仓位刷新')
    return
  }
  
  // 更新 refreshing 状态
  const currentData = [...tableData.value]
  const rowIndex = currentData.findIndex(r => r.index === row.index)
  if (rowIndex === -1) {
    ElMessage.warning('无法找到对应的数据行')
    return
  }
  
  currentData[rowIndex] = { ...currentData[rowIndex], refreshing: true }
  tableData.value = currentData
  
  try {
    // 1. 发送 type=2 任务请求
    ElMessage.info(`正在采集浏览器 ${row.fingerprintNo} 的最新仓位数据...`)
    const taskData = {
      groupNo: row.computeGroup,
      numberList: parseInt(row.fingerprintNo),
      type: 2,
      exchangeName: 'OP'
    }
    
    const taskResponse = await axios.post(
      `${API_BASE_URL}/mission/add`,
      taskData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (taskResponse.status === 200) {
      ElMessage.success('任务已提交，正在采集数据...')
    } else {
      throw new Error('任务提交失败')
    }
    
    // 2. 等待60秒
    const waitTime = 60000
    ElMessage.info(`预计需要 ${waitTime / 1000} 秒，请稍候...`)
    await new Promise(resolve => setTimeout(resolve, waitTime))
    
    // 3. 获取更新后的数据
    const response = await axios.get(
      `${API_BASE_URL}/boost/findAccountConfigByNo?no=${row.fingerprintNo}`
    )
    
    if (response.data && response.data.data) {
      const newData = response.data.data
      
      // 更新数据
      const updatedData = [...tableData.value]
      const idx = updatedData.findIndex(r => r.index === row.index)
      if (idx !== -1) {
        updatedData[idx] = {
          ...updatedData[idx],
          balance: newData.balance || 0,
          b: newData.b || '',
          c: newData.c || '0',
          d: newData.d || '',
          platform: newData.e || updatedData[idx].platform,
          refreshing: false
        }
        
        // 重新解析挂单数据并计算未成交数量和金额
        if (updatedData[idx].b) {
          const orders = parseOpenOrders(updatedData[idx].b)
          parsedOrders.value[updatedData[idx].index] = orders
          
          // 重新计算总的未成交数量和未成交金额
          let totalPendingQuantity = 0
          let totalPendingAmount = 0
          orders.forEach(order => {
            totalPendingQuantity += order.pendingQuantity || 0
            totalPendingAmount += order.pendingAmount || 0
          })
          
          updatedData[idx].pendingQuantity = totalPendingQuantity
          updatedData[idx].pendingAmount = totalPendingAmount
        }
        
        tableData.value = updatedData
      }
      
      ElMessage.success(`浏览器 ${row.fingerprintNo} 仓位数据已更新`)
    } else {
      ElMessage.warning('数据采集完成，但未获取到更新数据')
    }
  } catch (error) {
    console.error('刷新仓位失败:', error)
    ElMessage.error('刷新仓位失败: ' + (error.message || '网络错误'))
    
    // 重置 refreshing 状态
    const updatedData = [...tableData.value]
    const idx = updatedData.findIndex(r => r.index === row.index)
    if (idx !== -1) {
      updatedData[idx] = { ...updatedData[idx], refreshing: false }
      tableData.value = updatedData
    }
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.account-anomaly-page {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 200px);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.position-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.position-item {
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #667eea;
}

.position-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  font-size: 13px;
}

.position-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.position-price,
.position-amount {
  font-size: 12px;
  color: #666;
}

.raw-data-text {
  font-size: 12px;
  color: #999;
  word-break: break-all;
}

.empty-text {
  color: #ccc;
  font-style: italic;
}
</style>

