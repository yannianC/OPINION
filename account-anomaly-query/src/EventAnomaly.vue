<template>
  <div class="event-anomaly-page">
    <h1 class="page-title">事件异常</h1>
    
    <div class="toolbar">
      <el-button type="primary" @click="loadAndCalculate" :loading="loading">
        刷新数据
      </el-button>
      <el-button type="success" @click="exportAndCopy" :disabled="selectedCount === 0" style="margin-left: 10px;">
        导出主题并复制 ({{ selectedCount }})
      </el-button>
      <el-button type="warning" @click="exportAllBrowsers" :disabled="selectedCount === 0" style="margin-left: 10px;">
        导出勾选主题相关的所有浏览器编号 ({{ selectedCount }})
      </el-button>
      <el-button type="danger" @click="exportRedBrowsers" :disabled="selectedCount === 0" style="margin-left: 10px;">
        导出勾选主题相关的变红浏览器编号 ({{ selectedCount }})
      </el-button>
      <el-select 
        v-model="selectedGroup" 
        @change="handleGroupChange"
        style="width: 120px; margin-left: 10px;"
        placeholder="选择分组"
      >
        <el-option label="全部" value="all" />
        <el-option label="分组1" value="1" />
        <el-option label="分组2" value="2" />
      </el-select>
    </div>

    <!-- 事件统计表格 -->
    <el-table 
      :data="eventTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 300px)"
    >
      <el-table-column type="index" label="序号" width="60" align="center" :index="indexMethod" fixed />
      <el-table-column prop="eventName" label="事件名" width="400" fixed>
        <template #default="scope">
          <div class="event-name-cell">
            <el-checkbox 
              v-model="scope.row.selected" 
              style="margin-right: 10px;"
              @change="() => handleSelectionChange(scope.row)"
            />
            {{ scope.row.eventName }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="yes持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesPosition, b.yesPosition)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.yesPosition) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.yesPosition) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="no持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noPosition, b.noPosition)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.noPosition) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.noPosition) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="链上yes持仓数量" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainYesPosition, b.chainYesPosition)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.chainYesPosition) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.chainYesPosition) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="链上no持仓数量" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainNoPosition, b.chainNoPosition)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.chainNoPosition) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.chainNoPosition) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="实际差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.actualDiff, b.actualDiff)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.actualDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.actualDiff) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="链上实际差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainActualDiff, b.chainActualDiff)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.chainActualDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.chainActualDiff) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="挂单yes数量" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderYes, b.orderYes)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.orderYes) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.orderYes) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="挂单no数量" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderNo, b.orderNo)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.orderNo) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.orderNo) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="挂单差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderDiff, b.orderDiff)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.orderDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.orderDiff) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="成交后差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.finalDiff, b.finalDiff)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.finalDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.finalDiff) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="链上成交后差额" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainFinalDiff, b.chainFinalDiff)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.chainFinalDiff) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.chainFinalDiff) }}
          </span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'
const CHAIN_STATS_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/markets/stats'

const loading = ref(false)
const eventTableData = ref([])
const selectedGroup = ref('all')
const groupConfigList = ref([]) // 存储当前分组的事件名列表
const accountDataCache = ref([]) // 存储原始账户数据，用于导出浏览器编号

/**
 * 计算选中的事件数量
 */
const selectedCount = computed(() => {
  return eventTableData.value.filter(item => item.selected).length
})

/**
 * 序号计算方法（从1开始）
 */
const indexMethod = (index) => {
  return index + 1
}

/**
 * 保存勾选状态到本地存储
 */
const saveSelectionState = () => {
  try {
    const selectedEvents = eventTableData.value
      .filter(item => item.selected)
      .map(item => item.eventName)
    
    localStorage.setItem('eventAnomaly_selectedEvents', JSON.stringify(selectedEvents))
    console.log('[事件异常] 勾选状态已保存到本地，共', selectedEvents.length, '个')
  } catch (error) {
    console.error('[事件异常] 保存勾选状态失败:', error)
  }
}

/**
 * 从本地存储加载勾选状态
 */
const loadSelectionState = () => {
  try {
    const saved = localStorage.getItem('eventAnomaly_selectedEvents')
    if (saved) {
      const selectedEvents = JSON.parse(saved)
      const selectedSet = new Set(selectedEvents)
      
      // 恢复勾选状态
      eventTableData.value.forEach(event => {
        event.selected = selectedSet.has(event.eventName)
      })
      
      console.log('[事件异常] 从本地存储恢复勾选状态，共', selectedEvents.length, '个')
    }
  } catch (error) {
    console.error('[事件异常] 加载勾选状态失败:', error)
  }
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (row) => {
  // 选择变化时保存到本地存储
  saveSelectionState()
}

/**
 * 格式化数字
 */
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '0.00'
  const num = parseFloat(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
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
 * 匹配事件名称和链上数据的title
 * 支持完全匹配和部分匹配（去除特殊字符后匹配）
 */
const matchEventName = (eventName, chainTitle) => {
  if (!eventName || !chainTitle) return false
  
  // 去除首尾空格后完全匹配
  const trimmedEvent = eventName.trim()
  const trimmedChain = chainTitle.trim()
  if (trimmedEvent === trimmedChain) return true
  
  // 去除###后面的部分后匹配
  const eventBase = trimmedEvent.split('###')[0].trim()
  const chainBase = trimmedChain.split('###')[0].trim()
  if (eventBase === chainBase && eventBase.length > 0) return true
  
  // 去除特殊字符后匹配（去除问号等）
  const normalize = (str) => {
    return str
      .split('###')[0]  // 去除 ### 后面的部分
      .replace(/[?()]/g, '')  // 去除问号、括号
      .replace(/\s+/g, ' ')  // 多个空格合并为一个
      .trim()
      .toLowerCase()
  }
  
  const normalizedEvent = normalize(eventName)
  const normalizedChain = normalize(chainTitle)
  
  // 部分匹配：检查是否包含主要关键词
  if (normalizedEvent && normalizedChain) {
    // 如果去除特殊字符后相同，则匹配
    if (normalizedEvent === normalizedChain) return true
    
    // 如果事件名称包含在链上title中，或链上title包含在事件名称中，也认为匹配
    if (normalizedEvent.includes(normalizedChain) || normalizedChain.includes(normalizedEvent)) {
      return true
    }
  }
  
  return false
}

/**
 * 加载分组配置数据
 */
const loadGroupConfig = async (groupNo) => {
  try {
    console.log(`[事件异常] 开始加载分组${groupNo}配置...`)
    const response = await axios.get(`${API_BASE_URL}/mission/exchangeConfigByGroupNo?groupNo=${groupNo}`)
    
    if (response.data && response.data.code === 0 && response.data.data && response.data.data.configList) {
      // 提取所有trending字段作为事件名列表
      const eventNames = response.data.data.configList
        .map(config => config.trending)
        .filter(trending => trending) // 过滤掉null或undefined
      
      console.log(`[事件异常] 分组${groupNo}配置加载完成，共 ${eventNames.length} 个事件`)
      return eventNames
    } else {
      console.warn(`[事件异常] 未获取到分组${groupNo}配置数据`)
      return []
    }
  } catch (error) {
    console.error(`[事件异常] 加载分组${groupNo}配置失败:`, error)
    return []
  }
}

/**
 * 加载链上数据
 */
const loadChainStats = async () => {
  try {
    console.log('[事件异常] 开始加载链上数据...')
    const response = await axios.get(CHAIN_STATS_API_URL)
    
    if (response.data && response.data.markets && Array.isArray(response.data.markets)) {
      const chainDataMap = new Map()
      
      // 处理每个市场的数据，按完整title存储（包括###后面的部分）
      // 如果同一个完整title出现多次，则累加数据
      for (const item of response.data.markets) {
        if (item.title) {
          const fullTitle = item.title.trim()
          const yesTotal = parseFloat(item.yes_total || 0)
          const noTotal = parseFloat(item.no_total || 0)
          
          // 如果同一个完整title已经存在，累加数据
          if (chainDataMap.has(fullTitle)) {
            const existing = chainDataMap.get(fullTitle)
            existing.yesTotal += yesTotal
            existing.noTotal += noTotal
          } else {
            // 新建条目，使用完整title作为key
            chainDataMap.set(fullTitle, {
              title: fullTitle.split('###')[0].trim(),  // 基础title（去除###后的部分）
              fullTitle: fullTitle,  // 完整title
              yesTotal: yesTotal,  // 直接使用，可能是负数
              noTotal: noTotal  // 直接使用，可能是负数
            })
          }
        }
      }
      
      console.log(`[事件异常] 链上数据加载完成，共 ${chainDataMap.size} 个市场`)
      console.log('[事件异常] 链上数据示例:', Array.from(chainDataMap.entries()).slice(0, 5))
      return chainDataMap
    } else {
      console.warn('[事件异常] 未获取到链上数据')
      return new Map()
    }
  } catch (error) {
    console.error('[事件异常] 加载链上数据失败:', error)
    return new Map()
  }
}

/**
 * 加载数据并计算事件统计
 */
const loadAndCalculate = async () => {
  loading.value = true
  
  try {
    console.log('[事件异常] 开始加载数据...')
    
    // 如果选择了分组且分组配置列表为空，先加载分组配置
    if (selectedGroup.value !== 'all' && groupConfigList.value.length === 0) {
      const eventNames = await loadGroupConfig(selectedGroup.value)
      groupConfigList.value = eventNames
    }
    
    // 并行加载账户数据和链上数据
    const [accountResponse, chainDataMap] = await Promise.all([
      axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`),
      loadChainStats()
    ])
    
    if (accountResponse.data && accountResponse.data.data) {
      const data = accountResponse.data.data
      console.log(`[事件异常] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 保存原始账户数据，用于导出浏览器编号
      accountDataCache.value = data
      
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
                finalDiff: 0,
                chainYesPosition: 0,
                chainNoPosition: 0,
                chainActualDiff: 0,
                chainFinalDiff: 0
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
                finalDiff: 0,
                chainYesPosition: 0,
                chainNoPosition: 0,
                chainActualDiff: 0,
                chainFinalDiff: 0
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
      
      // 匹配链上数据（必须完全匹配，包括###后面的部分）
      console.log('[事件异常] 开始匹配链上数据，事件数量:', eventMap.size, '链上数据数量:', chainDataMap.size)
      for (const [eventName, event] of eventMap.entries()) {
        // 只使用完全匹配（去除首尾空格后比较）
        const trimmedEventName = eventName.trim()
        let matched = false
        
        // 尝试完全匹配
        if (chainDataMap.has(trimmedEventName)) {
          const chainData = chainDataMap.get(trimmedEventName)
          event.chainYesPosition = chainData.yesTotal
          event.chainNoPosition = chainData.noTotal
          matched = true
          console.log('[事件异常] 完全匹配成功:', trimmedEventName, '-> yes:', chainData.yesTotal, 'no:', chainData.noTotal)
        } else {
          // 遍历链上数据，尝试完全匹配（去除首尾空格）
          for (const [chainTitle, chainData] of chainDataMap.entries()) {
            if (trimmedEventName === chainData.fullTitle.trim() || trimmedEventName === chainTitle.trim()) {
              event.chainYesPosition = chainData.yesTotal
              event.chainNoPosition = chainData.noTotal
              matched = true
              console.log('[事件异常] 完全匹配成功（去除空格）:', trimmedEventName, '->', chainData.fullTitle, 'yes:', chainData.yesTotal, 'no:', chainData.noTotal)
              break
            }
          }
        }
        
        if (!matched) {
          console.log('[事件异常] 未匹配到链上数据（需要完全匹配）:', trimmedEventName)
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
        
        // 链上实际差额：链上yes持仓数量 - 链上no持仓数量
        event.chainActualDiff = event.chainYesPosition - event.chainNoPosition
        
        // 链上成交后差额：链上实际差额 + 挂单差额（使用原有的挂单差额）
        event.chainFinalDiff = event.chainActualDiff + event.orderDiff
      }
      
      // 转换为数组并排序（按成交后差额绝对值降序）
      let allEvents = Array.from(eventMap.values()).sort((a, b) => {
        return Math.abs(b.finalDiff) - Math.abs(a.finalDiff)
      })
      
      // 初始化选中状态（先设为false，后面会从本地存储恢复）
      allEvents.forEach(event => {
        event.selected = false
      })
      
      // 根据选择的分组进行过滤
      if (selectedGroup.value !== 'all' && groupConfigList.value.length > 0) {
        // 创建事件名集合用于快速查找（支持完全匹配和去除空格后的匹配）
        const eventNameSet = new Set(groupConfigList.value.map(name => name.trim()))
        const normalizedEventNameSet = new Set(
          groupConfigList.value.map(name => {
            // 去除首尾空格，去除###后面的部分
            return name.trim().split('###')[0].trim()
          })
        )
        
        allEvents = allEvents.filter(event => {
          const eventName = event.eventName.trim()
          const eventNameBase = eventName.split('###')[0].trim()
          
          // 完全匹配
          if (eventNameSet.has(eventName)) return true
          
          // 基础名称匹配（去除###后的部分）
          if (normalizedEventNameSet.has(eventNameBase)) return true
          
          // 检查是否包含在配置列表中（部分匹配）
          for (const configName of groupConfigList.value) {
            const configNameTrimmed = configName.trim()
            const configNameBase = configNameTrimmed.split('###')[0].trim()
            
            if (eventName === configNameTrimmed || eventNameBase === configNameBase) {
              return true
            }
            
            // 如果事件名包含配置名或配置名包含事件名，也认为匹配
            if (eventName.includes(configNameTrimmed) || configNameTrimmed.includes(eventName)) {
              return true
            }
            if (eventNameBase && configNameBase && 
                (eventNameBase.includes(configNameBase) || configNameBase.includes(eventNameBase))) {
              return true
            }
          }
          
          return false
        })
        
        console.log(`[事件异常] 分组${selectedGroup.value}过滤后，共 ${allEvents.length} 个事件`)
      }
      
      eventTableData.value = allEvents
      
      // 从本地存储恢复勾选状态
      loadSelectionState()
      
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
 * 处理分组变化
 */
const handleGroupChange = async (value) => {
  console.log('[事件异常] 分组选择变化:', value)
  
  if (value === 'all') {
    // 选择"全部"时，清空分组配置列表
    groupConfigList.value = []
    // 重新加载数据（会显示所有事件）
    await loadAndCalculate()
  } else {
    // 选择分组1或分组2时，加载对应的配置
    const eventNames = await loadGroupConfig(value)
    groupConfigList.value = eventNames
    
    if (eventNames.length === 0) {
      ElMessage.warning(`分组${value}配置为空，将显示所有事件`)
    } else {
      console.log(`[事件异常] 分组${value}包含的事件:`, eventNames)
      // 重新加载数据（会根据分组配置过滤）
      await loadAndCalculate()
    }
  }
}

/**
 * 导出并复制选中的事件名
 */
const exportAndCopy = async () => {
  const selectedEvents = eventTableData.value
    .filter(item => item.selected)
    .map(item => item.eventName)
  
  if (selectedEvents.length === 0) {
    ElMessage.warning('请至少选择一个事件')
    return
  }
  
  // 按分号拼接
  const result = selectedEvents.join(';')
  
  try {
    // 复制到剪切板
    await navigator.clipboard.writeText(result)
    ElMessage.success(`已复制 ${selectedEvents.length} 个事件名到剪切板`)
    console.log('[事件异常] 导出的内容:', result)
  } catch (error) {
    // 如果 clipboard API 不可用，使用备用方法
    const textArea = document.createElement('textarea')
    textArea.value = result
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success(`已复制 ${selectedEvents.length} 个事件名到剪切板`)
      console.log('[事件异常] 导出的内容:', result)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('[事件异常] 复制失败:', err)
    }
    document.body.removeChild(textArea)
  }
}

/**
 * 导出所有浏览器编号（包含选中主题的）
 */
const exportAllBrowsers = async () => {
  const selectedEvents = eventTableData.value
    .filter(item => item.selected)
    .map(item => item.eventName)
  
  if (selectedEvents.length === 0) {
    ElMessage.warning('请至少选择一个事件')
    return
  }
  
  if (accountDataCache.value.length === 0) {
    ElMessage.warning('请先刷新数据')
    return
  }
  
  // 创建选中主题的集合（支持完全匹配）
  const selectedEventSet = new Set(selectedEvents.map(e => e.trim()))
  
  // 收集包含选中主题的浏览器编号
  const browserSet = new Set()
  
  for (const row of accountDataCache.value) {
    let hasSelectedEvent = false
        
    // 检查持仓（a字段）
    if (row.a) {
      const positions = parsePositions(row.a)
      for (const pos of positions) {
        if (selectedEventSet.has(pos.title.trim())) {
          hasSelectedEvent = true
          break
        }
      }
    }
    
    // 检查挂单（b字段）
    if (!hasSelectedEvent && row.b) {
      const orders = parseOrders(row.b)
      for (const order of orders) {
        if (selectedEventSet.has(order.title.trim())) {
          hasSelectedEvent = true
          break
        }
      }
    }
    
    // 检查链上持仓（需要从链上数据中获取，这里暂时不处理，因为链上数据是单独加载的）
    // 如果需要链上持仓，需要额外处理
    
    if (hasSelectedEvent && row.fingerprintNo) {
      browserSet.add(String(row.fingerprintNo))
    }
  }
  
  if (browserSet.size === 0) {
    ElMessage.warning('未找到包含选中主题的浏览器')
    return
  }
  
  // 按逗号拼接
  const result = Array.from(browserSet).sort((a, b) => parseInt(a) - parseInt(b)).join(',')
  
  try {
    // 复制到剪切板
    await navigator.clipboard.writeText(result)
    ElMessage.success(`已复制 ${browserSet.size} 个浏览器编号到剪切板`)
    console.log('[事件异常] 导出的浏览器编号:', result)
  } catch (error) {
    // 如果 clipboard API 不可用，使用备用方法
    const textArea = document.createElement('textarea')
    textArea.value = result
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success(`已复制 ${browserSet.size} 个浏览器编号到剪切板`)
      console.log('[事件异常] 导出的浏览器编号:', result)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('[事件异常] 复制失败:', err)
    }
    document.body.removeChild(textArea)
  }
}

/**
 * 导出变红浏览器编号（包含选中主题的，且 d < f）
 */
const exportRedBrowsers = async () => {
  const selectedEvents = eventTableData.value
    .filter(item => item.selected)
    .map(item => item.eventName)
  
  if (selectedEvents.length === 0) {
    ElMessage.warning('请至少选择一个事件')
    return
  }
  
  if (accountDataCache.value.length === 0) {
    ElMessage.warning('请先刷新数据')
    return
  }
  
  // 创建选中主题的集合（支持完全匹配）
  const selectedEventSet = new Set(selectedEvents.map(e => e.trim()))
  
  // 收集包含选中主题且变红的浏览器编号
  const browserSet = new Set()
  
  for (const row of accountDataCache.value) {
    // 判断是否变红：d < f（仓位抓取时间 < 打开时间）
    // 监控类型不需要检测
    if (row.e === '监控' || row.platform === '监控') {
      continue
    }
    
    if (!row.d || !row.f) {
      continue
    }
    
    const positionTime = typeof row.d === 'string' ? parseInt(row.d) : row.d
    const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
    
    if (isNaN(positionTime) || isNaN(openTime)) {
      continue
    }
    
    // 判断是否变红：打开时间 > 仓位抓取时间，即 d < f
    if (openTime <= positionTime) {
      continue
    }
    
    // 检查是否包含选中的主题
    let hasSelectedEvent = false
        
    // 检查持仓（a字段）
    if (row.a) {
      const positions = parsePositions(row.a)
      for (const pos of positions) {
        if (selectedEventSet.has(pos.title.trim())) {
          hasSelectedEvent = true
          break
        }
      }
    }
    
    // 检查挂单（b字段）
    if (!hasSelectedEvent && row.b) {
      const orders = parseOrders(row.b)
      for (const order of orders) {
        if (selectedEventSet.has(order.title.trim())) {
          hasSelectedEvent = true
          break
        }
      }
    }
    
    if (hasSelectedEvent && row.fingerprintNo) {
      browserSet.add(String(row.fingerprintNo))
    }
  }
  
  if (browserSet.size === 0) {
    ElMessage.warning('未找到包含选中主题的变红浏览器')
    return
  }
  
  // 按逗号拼接
  const result = Array.from(browserSet).sort((a, b) => parseInt(a) - parseInt(b)).join(',')
  
  try {
    // 复制到剪切板
    await navigator.clipboard.writeText(result)
    ElMessage.success(`已复制 ${browserSet.size} 个变红浏览器编号到剪切板`)
    console.log('[事件异常] 导出的变红浏览器编号:', result)
  } catch (error) {
    // 如果 clipboard API 不可用，使用备用方法
    const textArea = document.createElement('textarea')
    textArea.value = result
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success(`已复制 ${browserSet.size} 个变红浏览器编号到剪切板`)
      console.log('[事件异常] 导出的变红浏览器编号:', result)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('[事件异常] 复制失败:', err)
    }
    document.body.removeChild(textArea)
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

