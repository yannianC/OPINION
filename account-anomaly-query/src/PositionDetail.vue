<template>
  <div class="position-detail-page">
    <h1 class="page-title">持仓详情</h1>
    
    <div class="toolbar">
      <el-button type="primary" @click="loadData" :loading="loading">
        刷新数据
      </el-button>
      <el-button type="primary" @click="updateOrderbook" :loading="updatingOrderbook" style="margin-left: 10px;">
        更新订单薄
      </el-button>
    </div>

    <!-- 持仓详情表格 -->
    <el-table 
      :data="tableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 200px)"
    >
      <el-table-column type="index" label="序号" width="60" align="center" :index="indexMethod" fixed />
      
      <el-table-column prop="eventName" label="事件名" width="300" fixed>
        <template #default="scope">
          <div class="event-name-cell" v-if="scope.row.eventName">
            {{ scope.row.eventName }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="yes持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesPosition, b.yesPosition)">
        <template #default="scope">
          <span v-if="scope.row.yesPosition > 0">{{ formatNumber(scope.row.yesPosition) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="no持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noPosition, b.noPosition)">
        <template #default="scope">
          <span v-if="scope.row.noPosition > 0">{{ formatNumber(scope.row.noPosition) }}</span>
        </template>
      </el-table-column>

      <!-- YES持仓详情 -->
      <el-table-column label="yes持仓详情" align="center" min-width="510">
        <el-table-column prop="yesBrowserNumber" label="浏览器编号" width="120" align="center" sortable :sort-method="(a, b) => sortByString(a.yesBrowserNumber, b.yesBrowserNumber)" />
        <el-table-column prop="yesUpdateTime" label="更新时间" width="150" align="center" sortable :sort-method="(a, b) => sortByTime(a.yesUpdateTime, b.yesUpdateTime)">
          <template #default="scope">
            <span>{{ formatTimeAgo(scope.row.yesUpdateTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="yesAmount" label="数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesAmount, b.yesAmount)">
          <template #default="scope">
            <span>{{ formatNumber(scope.row.yesAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="yesPrice" label="价格" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesPrice, b.yesPrice)">
          <template #default="scope">
            <span>{{ formatNumber(scope.row.yesPrice) }}</span>
          </template>
        </el-table-column>
      </el-table-column>

      <!-- NO持仓详情 -->
      <el-table-column label="no持仓详情" align="center" min-width="510">
        <el-table-column prop="noPrice" label="价格" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noPrice, b.noPrice)">
          <template #default="scope">
            <span>{{ formatNumber(scope.row.noPrice) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="noAmount" label="数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noAmount, b.noAmount)">
          <template #default="scope">
            <span>{{ formatNumber(scope.row.noAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="noUpdateTime" label="更新时间" width="150" align="center" sortable :sort-method="(a, b) => sortByTime(a.noUpdateTime, b.noUpdateTime)">
          <template #default="scope">
            <span>{{ formatTimeAgo(scope.row.noUpdateTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="noBrowserNumber" label="浏览器编号" width="120" align="center" sortable :sort-method="(a, b) => sortByString(a.noBrowserNumber, b.noBrowserNumber)" />
      </el-table-column>

      <!-- YES深度 -->
      <el-table-column label="YES深度" width="300" align="center">
        <template #default="scope">
          <div v-if="scope.row.depthData && scope.row.depthData.length > 0" class="depth-container">
            <div v-for="(item, index) in scope.row.depthData" :key="index" class="depth-item">
              <span class="depth-bid">{{ formatNumber(item.bidDepth) }}, {{ formatNumber(item.bidPrice) }}</span>
              <span class="depth-separator"> | </span>
              <span class="depth-ask">{{ formatNumber(item.askPrice) }}, {{ formatNumber(item.askDepth) }}</span>
            </div>
          </div>
          <span v-else style="color: #909399;">-</span>
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
const ORDERBOOK_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/orderbooks'
const CHAIN_STATS_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/markets/stats'

const loading = ref(false)
const updatingOrderbook = ref(false)
const tableData = ref([])
const exchangeConfigList = ref([])
const idToTrendingMap = ref(new Map())
const opTopicIdMap = ref(new Map()) // eventName -> opTopicId 映射
const eventMapCache = ref(new Map()) // 缓存事件映射，用于更新订单薄

/**
 * 序号计算方法（从1开始）
 */
const indexMethod = (index) => {
  return index + 1
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
 * 格式化时间差（显示为几分钟前/几小时前/几天前）
 */
const formatTimeAgo = (timestamp) => {
  if (!timestamp || timestamp === 0) return '-'
  
  const now = Date.now()
  const diff = now - timestamp
  
  if (diff < 0) return '未来时间'
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
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
 * 时间排序方法
 */
const sortByTime = (a, b) => {
  const timeA = typeof a === 'string' ? parseInt(a) : (a || 0)
  const timeB = typeof b === 'string' ? parseInt(b) : (b || 0)
  return timeA - timeB
}

/**
 * 字符串排序方法
 */
const sortByString = (a, b) => {
  const strA = (a || '').toString()
  const strB = (b || '').toString()
  return strA.localeCompare(strB)
}

/**
 * 加载 exchangeConfig 配置
 */
const loadExchangeConfig = async () => {
  try {
    console.log('[持仓详情] 开始加载 exchangeConfig 配置...')
    const response = await axios.get(`${API_BASE_URL}/mission/exchangeConfig`)
    
    if (response.data && response.data.code === 0 && response.data.data && response.data.data.configList) {
      exchangeConfigList.value = response.data.data.configList
      
      // 创建 id -> trending 的映射
      const newIdToTrendingMap = new Map()
      const newOpTopicIdMap = new Map()
      for (const config of exchangeConfigList.value) {
        if (config.id && config.trending) {
          newIdToTrendingMap.set(String(config.id), config.trending.trim())
        }
        if (config.trending && config.opTopicId) {
          newOpTopicIdMap.set(config.trending.trim(), String(config.opTopicId))
        }
      }
      idToTrendingMap.value = newIdToTrendingMap
      opTopicIdMap.value = newOpTopicIdMap
      
      console.log(`[持仓详情] exchangeConfig 配置加载完成，共 ${exchangeConfigList.value.length} 个配置`)
      return exchangeConfigList.value
    } else {
      console.warn('[持仓详情] 未获取到 exchangeConfig 配置数据')
      return []
    }
  } catch (error) {
    console.error('[持仓详情] 加载 exchangeConfig 配置失败:', error)
    return []
  }
}

/**
 * 加载订单薄数据
 */
const loadAllOrderbooks = async () => {
  try {
    console.log('[持仓详情] 开始加载所有订单薄数据...')
    const response = await axios.get(ORDERBOOK_API_URL)
    
    if (response.data && response.data.orderbooks && Array.isArray(response.data.orderbooks)) {
      console.log(`[持仓详情] 获取到 ${response.data.orderbooks.length} 条订单薄数据`)
      return response.data.orderbooks
    }
    
    console.warn('[持仓详情] 订单薄数据格式错误')
    return []
  } catch (error) {
    console.error('[持仓详情] 加载所有订单薄数据失败:', error)
    return []
  }
}

/**
 * 加载数据并构建表格
 */
const loadData = async () => {
  loading.value = true
  
  try {
    console.log('[持仓详情] 开始加载数据...')
    
    // 先加载 exchangeConfig 配置
    await loadExchangeConfig()
    
    // 加载账户数据
    const accountResponse = await axios.get(`${API_BASE_URL}/boost/getAllPosSnap`)
    
    if (accountResponse.data && accountResponse.data.data && accountResponse.data.data.list) {
      const data = accountResponse.data.data.list
      console.log(`[持仓详情] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 过滤掉 amt < 1 的数据
      const filteredData = data.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt >= 1
      })
      console.log(`[持仓详情] 过滤后剩余 ${filteredData.length} 条数据（已过滤掉 ${data.length - filteredData.length} 条 amt < 1 的数据）`)
      
      // 使用 Map 存储每个事件的数据
      const eventMap = new Map()
      
      // 处理每条数据（使用过滤后的数据）
      for (const row of filteredData) {
        // 从 trendingKey 中提取 id（格式：id::方向）
        if (!row.trendingKey) {
          continue
        }
        
        const parts = row.trendingKey.split('::')
        if (parts.length < 2) {
          continue
        }
        
        const configId = parts[0].trim()
        const direction = parts[1].trim()
        
        // 通过 id 查找对应的 trending（事件名）
        const eventName = idToTrendingMap.value.get(configId)
        if (!eventName) {
          continue
        }
        
        // 初始化事件数据
        if (!eventMap.has(eventName)) {
          eventMap.set(eventName, {
            eventName: eventName,
            yesPosition: 0,
            noPosition: 0,
            yesDetails: [], // YES持仓详情列表
            noDetails: [], // NO持仓详情列表
            depthData: [] // YES深度数据
          })
        }
        
        const event = eventMap.get(eventName)
        const amount = Math.abs(parseFloat(row.amt) || 0)
        const avgPrice = parseFloat(row.avgPrice) || 0
        const utime = row.utime ? (typeof row.utime === 'string' ? parseInt(row.utime) : row.utime) : null
        const number = row.number ? String(row.number) : ''
        
        // 根据 outCome 判断方向（YES/NO）
        const outComeUpper = (row.outCome || direction).toUpperCase()
        if (outComeUpper === 'YES') {
          event.yesPosition += amount
          // 添加YES持仓详情
          event.yesDetails.push({
            browserNumber: number,
            updateTime: utime,
            amount: amount,
            price: avgPrice
          })
        } else if (outComeUpper === 'NO') {
          event.noPosition += amount
          // 添加NO持仓详情
          event.noDetails.push({
            price: avgPrice,
            amount: amount,
            updateTime: utime,
            browserNumber: number
          })
        }
      }
      
      // 转换为表格数据格式（展开持仓详情）
      const expandedTableData = []
      for (const event of eventMap.values()) {
        // YES持仓按价格从大到小排序
        event.yesDetails.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
        // NO持仓按价格从小到大排序
        event.noDetails.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
        
        // 计算最大行数（YES和NO详情中的较大者）
        const maxRows = Math.max(event.yesDetails.length, event.noDetails.length, 1)
        
        // 为每一行创建数据
        for (let i = 0; i < maxRows; i++) {
          const rowData = {
            eventName: i === 0 ? event.eventName : '', // 只在第一行显示事件名
            yesPosition: i === 0 ? event.yesPosition : 0, // 只在第一行显示总量
            noPosition: i === 0 ? event.noPosition : 0, // 只在第一行显示总量
            yesBrowserNumber: event.yesDetails[i]?.browserNumber || '',
            yesUpdateTime: event.yesDetails[i]?.updateTime || null,
            yesAmount: event.yesDetails[i]?.amount || 0,
            yesPrice: event.yesDetails[i]?.price || 0,
            noPrice: event.noDetails[i]?.price || 0,
            noAmount: event.noDetails[i]?.amount || 0,
            noUpdateTime: event.noDetails[i]?.updateTime || null,
            noBrowserNumber: event.noDetails[i]?.browserNumber || '',
            depthData: i === 0 ? event.depthData : [] // 只在第一行显示深度数据
          }
          expandedTableData.push(rowData)
        }
      }
      
      tableData.value = expandedTableData
      eventMapCache.value = eventMap // 缓存事件映射
      
      console.log('[持仓详情] 数据加载完成，开始加载订单薄数据...')
      ElMessage.success(`数据加载完成，共 ${eventMap.size} 个事件`)
      
      // 异步加载订单薄数据
      loadAllOrderbooks().then(orderbooks => {
        updateDepthData(eventMap, orderbooks)
        eventMapCache.value = eventMap // 更新缓存
        // 重新构建表格数据
        rebuildTableData(eventMap)
      }).catch(error => {
        console.error('[持仓详情] 加载订单薄数据失败:', error)
      })
    } else {
      ElMessage.warning('未获取到数据')
    }
  } catch (error) {
    console.error('[持仓详情] 加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 更新深度数据
 */
const updateDepthData = (eventMap, orderbooks) => {
  // 创建 market_id -> orderbook 的映射
  const orderbookMap = new Map()
  for (const orderbook of orderbooks) {
    if (orderbook.market_id) {
      orderbookMap.set(String(orderbook.market_id), orderbook)
    }
  }
  
  // 更新每个事件的深度数据
  for (const event of eventMap.values()) {
    const opTopicId = opTopicIdMap.value.get(event.eventName)
    if (!opTopicId) {
      continue
    }
    
    const orderbook = orderbookMap.get(opTopicId)
    if (!orderbook) {
      continue
    }
    
    try {
      // 解析bids_json和asks_json
      let bids = []
      let asks = []
      
      try {
        bids = JSON.parse(orderbook.bids_json || '[]')
        asks = JSON.parse(orderbook.asks_json || '[]')
      } catch (parseError) {
        console.warn(`[持仓详情] ${event.eventName} 解析订单薄JSON失败:`, parseError)
        if (orderbook.best_bid_price !== null && orderbook.best_bid_price !== undefined &&
            orderbook.best_ask_price !== null && orderbook.best_ask_price !== undefined) {
          bids = [{ price: orderbook.best_bid_price, size: orderbook.best_bid_size || 0 }]
          asks = [{ price: orderbook.best_ask_price, size: orderbook.best_ask_size || 0 }]
        } else {
          continue
        }
      }
      
      // 对 bids 和 asks 进行排序
      bids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
      asks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
      
      // 构建深度数据
      const depthData = []
      const maxDepth = Math.max(bids.length, asks.length)
      for (let i = 0; i < maxDepth; i++) {
        const bid = bids[i] || { price: 0, size: 0 }
        const ask = asks[i] || { price: 0, size: 0 }
        depthData.push({
          bidDepth: parseFloat(bid.size),
          bidPrice: parseFloat(bid.price) * 100, // 转换为百分比
          askPrice: parseFloat(ask.price) * 100, // 转换为百分比
          askDepth: parseFloat(ask.size)
        })
      }
      
      event.depthData = depthData
    } catch (error) {
      console.error(`[持仓详情] 更新 ${event.eventName} 深度数据失败:`, error)
    }
  }
}

/**
 * 重新构建表格数据
 */
const rebuildTableData = (eventMap) => {
  const expandedTableData = []
  for (const event of eventMap.values()) {
    // 计算最大行数
    const maxRows = Math.max(event.yesDetails.length, event.noDetails.length, 1)
    
    // 为每一行创建数据
    for (let i = 0; i < maxRows; i++) {
      const rowData = {
        eventName: i === 0 ? event.eventName : '',
        yesPosition: i === 0 ? event.yesPosition : 0,
        noPosition: i === 0 ? event.noPosition : 0,
        yesBrowserNumber: event.yesDetails[i]?.browserNumber || '',
        yesUpdateTime: event.yesDetails[i]?.updateTime || null,
        yesAmount: event.yesDetails[i]?.amount || 0,
        yesPrice: event.yesDetails[i]?.price || 0,
        noPrice: event.noDetails[i]?.price || 0,
        noAmount: event.noDetails[i]?.amount || 0,
        noUpdateTime: event.noDetails[i]?.updateTime || null,
        noBrowserNumber: event.noDetails[i]?.browserNumber || '',
        depthData: i === 0 ? event.depthData : []
      }
      expandedTableData.push(rowData)
    }
  }
  
  tableData.value = expandedTableData
  ElMessage.success('订单薄数据已更新')
}

/**
 * 更新订单薄数据
 */
const updateOrderbook = async () => {
  updatingOrderbook.value = true
  
  try {
    console.log('[持仓详情] 开始更新订单薄数据...')
    
    // 加载所有订单薄数据
    const orderbooks = await loadAllOrderbooks()
    
    if (orderbooks.length === 0) {
      ElMessage.warning('未获取到订单薄数据')
      return
    }
    
    // 使用缓存的事件映射
    const eventMap = eventMapCache.value
    if (eventMap.size === 0) {
      ElMessage.warning('请先刷新数据')
      return
    }
    
    // 更新深度数据
    updateDepthData(eventMap, orderbooks)
    eventMapCache.value = eventMap // 更新缓存
    
    // 重新构建表格数据
    rebuildTableData(eventMap)
    
    ElMessage.success('订单薄数据更新完成')
  } catch (error) {
    console.error('[持仓详情] 更新订单薄失败:', error)
    ElMessage.error('更新订单薄失败: ' + (error.message || '未知错误'))
  } finally {
    updatingOrderbook.value = false
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
.position-detail-page {
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

.depth-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.depth-item {
  font-size: 12px;
  line-height: 1.5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.depth-bid {
  color: #67c23a;
}

.depth-ask {
  color: #f56c6c;
}

.depth-separator {
  color: #909399;
  margin: 0 4px;
}
</style>

