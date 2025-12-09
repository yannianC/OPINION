<template>
  <div class="event-anomaly-page">
    <h1 class="page-title">事件异常</h1>
    
    <div class="toolbar">
      <el-button type="primary" @click="loadAndCalculate" :loading="loading">
        刷新数据
      </el-button>
    </div>

    <!-- 事件统计表格 -->
    <el-table 
      :data="eventTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 300px)"
    >
      <el-table-column prop="eventName" label="事件名" width="400" fixed>
        <template #default="scope">
          <div class="event-name-cell">{{ scope.row.eventName }}</div>
        </template>
      </el-table-column>

      <el-table-column label="yes持仓数量" width="120" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.yesPosition) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.yesPosition) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="no持仓数量" width="120" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.noPosition) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.noPosition) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="实际差额" width="120" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.actualDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.actualDiff) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="挂单yes数量" width="130" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.orderYes) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.orderYes) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="挂单no数量" width="130" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.orderNo) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.orderNo) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="挂单差额" width="120" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.orderDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.orderDiff) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="成交后差额" width="130" align="center">
        <template #default="scope">
          <span :class="parseFloat(scope.row.finalDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.finalDiff) }}
          </span>
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
const eventTableData = ref([])

/**
 * 格式化数字
 */
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '0.00'
  const num = parseFloat(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

/**
 * 解析持仓数据字符串（a字段）
 * 格式: "事件唯一名|||方向|||数量|||价格;..."
 */
const parsePositions = (posStr) => {
  if (!posStr) return []
  
  try {
    const positions = []
    const items = posStr.split(';')
    const isNewFormat = posStr.includes('|||')
    const separator = isNewFormat ? '|||' : ','
    
    for (const item of items) {
      if (!item || !item.trim()) continue
      
      const parts = item.split(separator)
      const partsLength = parts.length
      
      if (partsLength >= 4) {
        let title = parts[0].trim()
        let option = parts[1].trim()
        let amount = parts[2].trim()
        let avgPrice = parts[3].trim()
        
        // 特殊处理：First to 5k: Gold or ETH? 市场
        if (title.includes('First to 5k') && (option === 'ETH' || option === 'GOLD')) {
          const numAmount = parseFloat(amount)
          if (!isNaN(numAmount)) {
            amount = option === 'GOLD' 
              ? Math.abs(numAmount).toFixed(2)
              : (-Math.abs(numAmount)).toFixed(2)
          }
        }
        
        // 特殊处理：Monad vs MegaETH — who has the higher FDV one day after launch? 市场
        if (title.includes('Monad vs MegaETH') && (option === 'Monad' || option === 'MegaETH')) {
          const numAmount = parseFloat(amount)
          if (!isNaN(numAmount)) {
            amount = option === 'Monad'
              ? Math.abs(numAmount).toFixed(2)
              : (-Math.abs(numAmount)).toFixed(2)
          }
        }
        
        positions.push({
          title: title,
          option: option,
          amount: parseFloat(amount) || 0,
          avgPrice: avgPrice
        })
      } else if (partsLength >= 3 && !isNewFormat) {
        positions.push({
          title: parts[0].trim(),
          option: parts[1].trim(),
          amount: parseFloat(parts[2].trim()) || 0,
          avgPrice: ''
        })
      } else if (partsLength >= 2 && !isNewFormat) {
        positions.push({
          title: parts[0].trim(),
          option: '',
          amount: parseFloat(parts[1].trim()) || 0,
          avgPrice: ''
        })
      }
    }
    
    return positions
  } catch {
    return []
  }
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
 * 解析挂单数据字符串（b字段）
 * 支持多种格式：
 * 1. 新格式（5个字段）："事件唯一名|||买卖方向|||方向|||价格|||进度"
 * 2. 旧格式（3个字段）："标题|||价格|||进度"
 * 3. 更旧格式（逗号分隔）："标题,价格,进度"
 * 进度格式支持：
 * - 数量格式：60.55/554.74shares 或 239.13/1,369.55shares
 * - 金额格式：$0/$462.2 或 $0/$1,462.2
 */
const parseOrders = (ordersStr) => {
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
          const title = parts[0].trim()
          const buySellDirection = parts[1].trim() // "Buy" 或 "Sell"
          const option = parts[2].trim() // "YES" 或 "NO"
          const price = parts[3].trim()
          const progress = parts[4].trim()
          
          // 解析价格：83.8 ¢ -> 提取数字部分
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pending = 0
          let filled = 0
          let total = 0
          
          // 判断进度格式：$0/$462.2（金额格式）或 60.55/554.74shares 或 239.13/1,369.55shares（数量格式）
          if (progress.includes('$')) {
            // 金额格式：$0/$462.2 或 $0/$1,462.2 -> 未成交金额 = 总金额 - 已成交金额
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              const pendingAmount = totalAmount - filledAmount
              // 未成交数量 = 未成交金额 * 100 / 价格
              if (priceNum > 0) {
                pending = (pendingAmount * 100) / priceNum
              }
              filled = filledAmount
              total = totalAmount
            }
          } else {
            // 数量格式：60.55/554.74shares 或 239.13/1,369.55shares -> 未成交数量 = 总数量 - 已成交数量
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              filled = parseNumberWithComma(progressMatch[1])
              total = parseNumberWithComma(progressMatch[2])
              pending = total - filled
            }
          }
          
          orders.push({
            title: title,
            buySellDirection: buySellDirection,
            option: option,
            price: price,
            filled: filled,
            total: total,
            pending: pending
          })
        } else if (parts.length >= 3) {
          // 兼容旧格式（3个字段：标题|||价格|||进度）
          const title = parts[0].trim()
          const price = parts[1].trim()
          const progress = parts[2].trim()
          
          // 解析价格
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pending = 0
          let filled = 0
          let total = 0
          
          // 判断进度格式
          if (progress.includes('$')) {
            // 金额格式
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              const pendingAmount = totalAmount - filledAmount
              if (priceNum > 0) {
                pending = (pendingAmount * 100) / priceNum
              }
              filled = filledAmount
              total = totalAmount
            }
          } else {
            // 数量格式
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              filled = parseNumberWithComma(progressMatch[1])
              total = parseNumberWithComma(progressMatch[2])
              pending = total - filled
            }
          }
          
          orders.push({
            title: title,
            price: price,
            filled: filled,
            total: total,
            pending: pending
          })
        }
      } else {
        // 兼容更旧格式（逗号分隔符）
        const parts = item.split(',')
        if (parts.length >= 3) {
          const title = parts[0].trim()
          const price = parts[1].trim()
          const progress = parts[2].trim()
          
          // 解析价格
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pending = 0
          let filled = 0
          let total = 0
          
          // 判断进度格式
          if (progress.includes('$')) {
            // 金额格式
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              const pendingAmount = totalAmount - filledAmount
              if (priceNum > 0) {
                pending = (pendingAmount * 100) / priceNum
              }
              filled = filledAmount
              total = totalAmount
            }
          } else {
            // 数量格式
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              filled = parseNumberWithComma(progressMatch[1])
              total = parseNumberWithComma(progressMatch[2])
              pending = total - filled
            }
          }
          
          orders.push({
            title: title,
            price: price,
            filled: filled,
            total: total,
            pending: pending
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
 * 加载数据并计算事件统计
 */
const loadAndCalculate = async () => {
  loading.value = true
  
  try {
    console.log('[事件异常] 开始加载数据...')
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`)
    
    if (response.data && response.data.data) {
      const data = response.data.data
      console.log(`[事件异常] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 使用 Map 存储每个事件的统计数据
      const eventMap = new Map()
      
      // 处理每条数据
      for (const row of data) {
        // 解析持仓数据（a字段）
        if (row.a) {
          const positions = parsePositions(row.a)
          for (const pos of positions) {
            const eventName = pos.title
            if (!eventMap.has(eventName)) {
              eventMap.set(eventName, {
                eventName: eventName,
                yesPosition: 0,
                noPosition: 0,
                actualDiff: 0,
                orderYes: 0,
                orderNo: 0,
                orderDiff: 0,
                finalDiff: 0
              })
            }
            
            const event = eventMap.get(eventName)
            const amount = Math.abs(pos.amount)
            
            // 特殊处理：First to 5k: Gold or ETH? 市场
            // GOLD为yes，ETH为no
            let isYes = false
            let isNo = false
            
            if (eventName.includes('First to 5k')) {
              if (pos.option === 'GOLD') {
                isYes = true
              } else if (pos.option === 'ETH') {
                isNo = true
              }
            }
            // 特殊处理：Monad vs MegaETH — who has the higher FDV one day after launch? 市场
            // Monad为yes，MegaETH为no
            else if (eventName.includes('Monad vs MegaETH')) {
              if (pos.option === 'Monad') {
                isYes = true
              } else if (pos.option === 'MegaETH') {
                isNo = true
              }
            }
            // 普通事件
            else {
              if (pos.option === 'YES' || (pos.amount >= 0 && !pos.option)) {
                isYes = true
              } else if (pos.option === 'NO' || pos.amount < 0) {
                isNo = true
              }
            }
            
            // 根据方向累加持仓数量（使用绝对值）
            if (isYes) {
              event.yesPosition += amount
            } else if (isNo) {
              event.noPosition += amount
            }
          }
        }
        
        // 解析挂单数据（b字段）
        if (row.b) {
          const orders = parseOrders(row.b)
          for (const order of orders) {
            const eventName = order.title
            if (!eventMap.has(eventName)) {
              eventMap.set(eventName, {
                eventName: eventName,
                yesPosition: 0,
                noPosition: 0,
                actualDiff: 0,
                orderYes: 0,
                orderNo: 0,
                orderDiff: 0,
                finalDiff: 0
              })
            }
            
            const event = eventMap.get(eventName)
            const pending = order.pending
            const sign = order.buySellDirection === 'Buy' ? 1 : -1
            
            // 特殊处理：First to 5k: Gold or ETH? 市场
            // GOLD为yes，ETH为no
            let isYes = false
            let isNo = false
            
            if (eventName.includes('First to 5k')) {
              if (order.option === 'GOLD') {
                isYes = true
              } else if (order.option === 'ETH') {
                isNo = true
              }
            }
            // 特殊处理：Monad vs MegaETH — who has the higher FDV one day after launch? 市场
            // Monad为yes，MegaETH为no
            else if (eventName.includes('Monad vs MegaETH')) {
              if (order.option === 'Monad') {
                isYes = true
              } else if (order.option === 'MegaETH') {
                isNo = true
              }
            }
            // 普通事件
            else {
              if (order.option === 'YES') {
                isYes = true
              } else if (order.option === 'NO') {
                isNo = true
              }
            }
            
            // 根据方向累加挂单数量
            if (isYes) {
              event.orderYes += sign * pending
            } else if (isNo) {
              event.orderNo += sign * pending
            }
          }
        }
      }
      
      // 计算差额
      for (const event of eventMap.values()) {
        // 实际差额：yes持仓数量 - no持仓数量（将no置为负数后相加）
        event.actualDiff = event.yesPosition - event.noPosition
        
        // 挂单差额：挂单yes数量 + (-挂单no数量) = 挂单yes数量 - 挂单no数量
        event.orderDiff = event.orderYes - event.orderNo
        
        // 成交后差额：实际差额 + 挂单差额
        event.finalDiff = event.actualDiff + event.orderDiff
      }
      
      // 转换为数组并排序（按成交后差额绝对值降序）
      eventTableData.value = Array.from(eventMap.values()).sort((a, b) => {
        return Math.abs(b.finalDiff) - Math.abs(a.finalDiff)
      })
      
      console.log('[事件异常] 计算完成')
      ElMessage.success(`数据加载并计算完成，共 ${eventTableData.value.length} 个事件`)
    } else {
      ElMessage.warning('未获取到数据')
    }
  } catch (error) {
    console.error('[事件异常] 加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadAndCalculate()
})
</script>

<style scoped>
.event-anomaly-page {
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

.event-name-cell {
  font-size: 13px;
  line-height: 1.4;
  word-break: break-word;
}

.positive {
  color: #67c23a;
  font-weight: 600;
}

.negative {
  color: #f56c6c;
  font-weight: 600;
}
</style>

