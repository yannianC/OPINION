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

    <!-- 筛选条件 -->
    <div class="filter-section">
      <el-card class="filter-card">
        <!-- 服务器端筛选（需要重新请求数据） -->
        <div class="filter-row search-row">
          <div class="filter-item">
            <span class="filter-label">事件名：</span>
            <el-input 
              v-model="filterEventName" 
              placeholder="输入事件名进行模糊匹配"
              style="width: 200px;"
              clearable
              @keyup.enter="searchData"
            />
          </div>
          
          <div class="filter-item">
            <span class="filter-label">方向：</span>
            <el-select v-model="filterOutCome" style="width: 120px;" clearable placeholder="全部" disabled>
              <el-option label="YES" value="YES" />
              <el-option label="NO" value="NO" />
            </el-select>
            <span style="margin-left: 5px; color: #909399; font-size: 12px;">(已按方向分表显示)</span>
          </div>
          
          <div class="filter-item">
            <span class="filter-label">电脑组：</span>
            <el-input 
              v-model="filterGroupFilter" 
              placeholder="多个用逗号分隔，如：4,5,907"
              style="width: 200px;"
              clearable
              @keyup.enter="searchData"
            />
          </div>
          
          <div class="filter-item">
            <span class="filter-label">浏览器编号：</span>
            <el-input 
              v-model="filterNumberFilter" 
              placeholder="多个用逗号分隔，如：2009,2981"
              style="width: 200px;"
              clearable
              @keyup.enter="searchData"
            />
          </div>
          
          <div class="filter-item">
            <el-button type="primary" @click="searchData" :loading="loading">搜索</el-button>
            <el-button @click="resetFilter" style="margin-left: 10px;">重置</el-button>
          </div>
        </div>
        
        <!-- 前端筛选（只对现有数据进行筛选） -->
        <div class="filter-row filter-row-local">
          <div class="filter-item">
            <span class="filter-label">数量：</span>
            <el-select v-model="filterAmountOperator" style="width: 100px;">
              <el-option label="大于" value="gt" />
              <el-option label="小于" value="lt" />
            </el-select>
            <el-input-number 
              v-model="filterAmountValue" 
              :min="0" 
              :precision="2"
              style="width: 150px; margin-left: 10px;"
              placeholder="请输入数量"
            />
          </div>
          
          <div class="filter-item">
            <span class="filter-label">更新时间：</span>
            <el-select v-model="filterTimeOperator" style="width: 100px;">
              <el-option label="大于" value="gt" />
              <el-option label="小于" value="lt" />
            </el-select>
            <el-input-number 
              v-model="filterTimeValue" 
              :min="0" 
              :precision="2"
              style="width: 150px; margin-left: 10px;"
              placeholder="小时数"
            />
            <span style="margin-left: 5px;">小时前</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- YES方向持仓表格 -->
    <div class="table-section">
      <h2 class="table-title yes-title">
        YES 方向持仓 ({{ yesTableData.length }} 条)
      </h2>
      <div v-loading="loading" class="loading-wrapper">
        <VirtualTable
          :data="yesTableData"
          :columns="yesColumns"
          :height="yesTableHeight"
          :row-height="40"
          :header-height="40"
          :buffer="10"
          :get-row-key="(row, index) => `yes-${index}`"
          @sort-change="handleYesSortChange"
        >
          <template #eventName="{ row }">
            <div class="event-name-cell">
              {{ row.eventName || '-' }}
            </div>
          </template>
          <template #amt="{ row }">
            <span>{{ formatNumber(row.amt) }}</span>
          </template>
          <template #avgPrice="{ row }">
            <span>{{ formatNumber(row.avgPrice) }}</span>
          </template>
          <template #ctime="{ row }">
            <span>{{ formatDateTime(row.ctime) }}</span>
          </template>
          <template #utime="{ row }">
            <span>{{ formatDateTime(row.utime) }}</span>
          </template>
          <template #catchTime="{ row }">
            <span>{{ formatDateTime(row.catchTime) }}</span>
          </template>
          <template #reason="{ row }">
            <span>{{ row.reason || '-' }}</span>
          </template>
        </VirtualTable>
      </div>
    </div>

    <!-- NO方向持仓表格 -->
    <div class="table-section">
      <h2 class="table-title no-title">
        NO 方向持仓 ({{ noTableData.length }} 条)
      </h2>
      <div v-loading="loading" class="loading-wrapper">
        <VirtualTable
          :data="noTableData"
          :columns="noColumns"
          :height="noTableHeight"
          :row-height="40"
          :header-height="40"
          :buffer="10"
          :get-row-key="(row, index) => `no-${index}`"
          @sort-change="handleNoSortChange"
        >
          <template #eventName="{ row }">
            <div class="event-name-cell">
              {{ row.eventName || '-' }}
            </div>
          </template>
          <template #amt="{ row }">
            <span>{{ formatNumber(row.amt) }}</span>
          </template>
          <template #avgPrice="{ row }">
            <span>{{ formatNumber(row.avgPrice) }}</span>
          </template>
          <template #ctime="{ row }">
            <span>{{ formatDateTime(row.ctime) }}</span>
          </template>
          <template #utime="{ row }">
            <span>{{ formatDateTime(row.utime) }}</span>
          </template>
          <template #catchTime="{ row }">
            <span>{{ formatDateTime(row.catchTime) }}</span>
          </template>
          <template #reason="{ row }">
            <span>{{ row.reason || '-' }}</span>
          </template>
        </VirtualTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import VirtualTable from './components/VirtualTable.vue'

const route = useRoute()

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'
const ORDERBOOK_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/orderbooks'
const CHAIN_STATS_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/markets/stats'

const loading = ref(false)
const updatingOrderbook = ref(false)
const tableData = ref([])
const filteredTableData = ref([]) // 筛选后的表格数据
const exchangeConfigList = ref([])
const idToTrendingMap = ref(new Map())
const opTopicIdMap = ref(new Map()) // eventName -> opTopicId 映射
const eventMapCache = ref(new Map()) // 缓存事件映射，用于更新订单薄
const reasonMap = ref(new Map()) // 原因映射：key为 "eventId_number_outCome"，value为原因数组

// 筛选条件
const filterAmountOperator = ref('gt') // 'gt' 或 'lt'
const filterAmountValue = ref(null)
const filterTimeOperator = ref('gt') // 'gt' 或 'lt'
const filterTimeValue = ref(null) // 小时数
const filterEventName = ref('') // 事件名模糊匹配（前端筛选）
const filterOutCome = ref('') // YES/NO筛选（服务器端筛选）
const filterGroupFilter = ref('') // 电脑组筛选（服务器端筛选），多个用逗号分隔
const filterNumberFilter = ref('') // 浏览器编号筛选（服务器端筛选），多个用逗号分隔
const filterTrending = ref('') // 主题名字筛选（服务器端筛选），从URL参数获取

// 深度显示状态
const depthFullShown = ref(new Set()) // 存储已展开完整深度的事件名

// 排序状态
const yesSortState = ref({ column: null, order: null })
const noSortState = ref({ column: null, order: null })

// YES表格列定义
const yesColumns = ref([
  { type: 'index', label: '序号', width: 60, fixed: 'left' },
  { prop: 'number', label: '浏览器编号', width: 120, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByString(a.number, b.number) },
  { prop: 'group', label: '电脑组', width: 100, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByNumber(a.group, b.group) },
  { prop: 'eventName', label: '事件名', width: 300, sortable: true, sortMethod: (a, b) => sortByString(a.eventName, b.eventName) },
  { prop: 'amt', label: '数量', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.amt, b.amt) },
  { prop: 'avgPrice', label: '价格', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.avgPrice, b.avgPrice) },
  { prop: 'ctime', label: '仓位创建时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.ctime, b.ctime) },
  { prop: 'utime', label: '仓位更新时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.utime, b.utime) },
  { prop: 'catchTime', label: '抓取时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.catchTime, b.catchTime) },
  { prop: 'reason', label: '原因', width: 300 }
])

// NO表格列定义
const noColumns = ref([
  { type: 'index', label: '序号', width: 60, fixed: 'left' },
  { prop: 'number', label: '浏览器编号', width: 120, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByString(a.number, b.number) },
  { prop: 'group', label: '电脑组', width: 100, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByNumber(a.group, b.group) },
  { prop: 'eventName', label: '事件名', width: 300, sortable: true, sortMethod: (a, b) => sortByString(a.eventName, b.eventName) },
  { prop: 'amt', label: '数量', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.amt, b.amt) },
  { prop: 'avgPrice', label: '价格', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.avgPrice, b.avgPrice) },
  { prop: 'ctime', label: '仓位创建时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.ctime, b.ctime) },
  { prop: 'utime', label: '仓位更新时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.utime, b.utime) },
  { prop: 'catchTime', label: '抓取时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.catchTime, b.catchTime) },
  { prop: 'reason', label: '原因', width: 300 }
])

/**
 * 序号计算方法（从1开始）
 */
const indexMethod = (index) => {
  return index + 1
}

/**
 * YES表格序号计算方法（从1开始）
 */
const indexMethodForYes = (index) => {
  return index + 1
}

/**
 * NO表格序号计算方法（从1开始）
 */
const indexMethodForNo = (index) => {
  return index + 1
}

/**
 * YES方向的数据（计算属性，支持排序）
 */
const yesTableData = computed(() => {
  let data = filteredTableData.value.filter(row => row.outCome === 'YES')
  
  // 应用排序
  if (yesSortState.value.column && yesSortState.value.order) {
    const column = yesColumns.value.find(col => (col.prop || col.type) === yesSortState.value.column)
    if (column && column.sortMethod) {
      const sorted = [...data].sort((a, b) => {
        // sortMethod 接收整行数据，内部提取需要的字段进行比较
        const result = column.sortMethod(a, b)
        return yesSortState.value.order === 'asc' ? result : -result
      })
      data = sorted
    }
  }
  
  return data
})

/**
 * NO方向的数据（计算属性，支持排序）
 */
const noTableData = computed(() => {
  let data = filteredTableData.value.filter(row => row.outCome === 'NO')
  
  // 应用排序
  if (noSortState.value.column && noSortState.value.order) {
    const column = noColumns.value.find(col => (col.prop || col.type) === noSortState.value.column)
    if (column && column.sortMethod) {
      const sorted = [...data].sort((a, b) => {
        // sortMethod 接收整行数据，内部提取需要的字段进行比较
        const result = column.sortMethod(a, b)
        return noSortState.value.order === 'asc' ? result : -result
      })
      data = sorted
    }
  }
  
  return data
})

/**
 * YES表格高度（动态计算）
 */
const yesTableHeight = computed(() => {
  if (typeof window === 'undefined') return 400
  const baseHeight = 350
  const tableCount = 2 // YES 和 NO 两个表格
  const titleHeight = 50 // 每个表格标题高度
  const availableHeight = window.innerHeight - baseHeight - (tableCount * titleHeight)
  return Math.max(200, availableHeight / 2)
})

/**
 * NO表格高度（动态计算）
 */
const noTableHeight = computed(() => {
  if (typeof window === 'undefined') return 400
  const baseHeight = 350
  const tableCount = 2 // YES 和 NO 两个表格
  const titleHeight = 50 // 每个表格标题高度
  const availableHeight = window.innerHeight - baseHeight - (tableCount * titleHeight)
  return Math.max(200, availableHeight / 2)
})

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
 * 格式化日期时间（显示完整时间）
 */
const formatDateTime = (timestamp) => {
  if (!timestamp || timestamp === 0) return '-'
  
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return '-'
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
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
      for (const config of exchangeConfigList.value) {
        if (config.id && config.trending) {
          newIdToTrendingMap.set(String(config.id), config.trending.trim())
        }
      }
      idToTrendingMap.value = newIdToTrendingMap
      
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
    
    // 构建服务器端筛选参数
    const serverFilterParams = {}
    
    // 电脑组筛选
    if (filterGroupFilter.value && filterGroupFilter.value.trim()) {
      serverFilterParams.groupFilter = filterGroupFilter.value.trim()
    }
    
    // 浏览器编号筛选
    if (filterNumberFilter.value && filterNumberFilter.value.trim()) {
      serverFilterParams.numberFilter = filterNumberFilter.value.trim()
    }
    
    // 主题名字筛选（从URL参数或筛选条件获取）
    if (filterTrending.value && filterTrending.value.trim()) {
      serverFilterParams.trending = filterTrending.value.trim()
    }
    
    // 注意：方向筛选已移除，因为现在按方向分表显示，不再需要服务器端方向筛选
    
    console.log('[持仓详情] 服务器端筛选参数:', serverFilterParams)
    
    // 加载账户数据（带服务器端筛选参数）
    const accountResponse = await axios.get(`${API_BASE_URL}/boost/getAllPosSnap`, {
      params: serverFilterParams
    })
    
    if (accountResponse.data && accountResponse.data.data && accountResponse.data.data.list) {
      const data = accountResponse.data.data.list
      console.log(`[持仓详情] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 过滤掉 amt < 1 的数据
      const filteredData = data.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt >= 1
      })
      console.log(`[持仓详情] 过滤后剩余 ${filteredData.length} 条数据（已过滤掉 ${data.length - filteredData.length} 条 amt < 1 的数据）`)
      
      // 处理每条数据，添加事件名
      const processedData = filteredData.map(row => {
        let eventName = ''
        
        // 从 trendingKey 中提取 id（格式：id::方向）
        if (row.trendingKey) {
          const parts = row.trendingKey.split('::')
          if (parts.length >= 2) {
            const configId = parts[0].trim()
            // 通过 id 查找对应的 trending（事件名）
            eventName = idToTrendingMap.value.get(configId) || ''
          }
        }
        
        // 处理时间字段，确保是数字类型
        const processedRow = {
          ...row,
          eventName: eventName,
          number: row.number ? String(row.number) : '',
          group: row.group ? (typeof row.group === 'string' ? parseInt(row.group) : row.group) : null,
          outCome: row.outCome || '',
          amt: parseFloat(row.amt) || 0,
          avgPrice: parseFloat(row.avgPrice) || 0,
          ctime: row.ctime ? (typeof row.ctime === 'string' ? parseInt(row.ctime) : row.ctime) : null,
          utime: row.utime ? (typeof row.utime === 'string' ? parseInt(row.utime) : row.utime) : null,
          catchTime: row.catchTime ? (typeof row.catchTime === 'string' ? parseInt(row.catchTime) : row.catchTime) : null
        }
        
        return processedRow
      })
      
      tableData.value = processedData
      
      // 如果有原因映射，更新原因
      if (reasonMap.value.size > 0) {
        updateTableDataReasons()
      } else {
        // 应用前端筛选
        applyClientFilter()
      }
      
      console.log('[持仓详情] 数据加载完成')
      ElMessage.success(`数据加载完成，共 ${processedData.length} 条记录`)
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
  // 转换为表格数据格式（只显示汇总信息）
  const summaryTableData = []
  for (const event of eventMap.values()) {
    const rowData = {
      eventName: event.eventName,
      yesPosition: event.yesPosition,
      noPosition: event.noPosition,
      depthData: event.depthData
    }
    summaryTableData.push(rowData)
  }
  
  tableData.value = summaryTableData
  // 应用筛选
  applyFilter()
  ElMessage.success('订单薄数据已更新')
}

/**
 * 获取YES持仓详情
 */
const getYesDetails = (eventName) => {
  const event = eventMapCache.value.get(eventName)
  return event ? event.yesDetails : []
}

/**
 * 获取NO持仓详情
 */
const getNoDetails = (eventName) => {
  const event = eventMapCache.value.get(eventName)
  return event ? event.noDetails : []
}

/**
 * 获取筛选后的YES持仓详情
 */
const getFilteredYesDetails = (eventName) => {
  const details = getYesDetails(eventName)
  if (!filterAmountValue.value) {
    return details
  }
  
  const amountValue = parseFloat(filterAmountValue.value) || 0
  if (filterAmountOperator.value === 'gt') {
    return details.filter(detail => {
      const amount = parseFloat(detail.amount) || 0
      return amount > amountValue
    })
  } else {
    return details.filter(detail => {
      const amount = parseFloat(detail.amount) || 0
      return amount < amountValue
    })
  }
}

/**
 * 获取筛选后的NO持仓详情
 */
const getFilteredNoDetails = (eventName) => {
  const details = getNoDetails(eventName)
  if (!filterAmountValue.value) {
    return details
  }
  
  const amountValue = parseFloat(filterAmountValue.value) || 0
  if (filterAmountOperator.value === 'gt') {
    return details.filter(detail => {
      const amount = parseFloat(detail.amount) || 0
      return amount > amountValue
    })
  } else {
    return details.filter(detail => {
      const amount = parseFloat(detail.amount) || 0
      return amount < amountValue
    })
  }
}

/**
 * 获取显示的深度数据（前5个买价和前5个卖价）
 */
const getDisplayDepthData = (eventName) => {
  const row = filteredTableData.value.find(r => r.eventName === eventName)
  if (!row || !row.depthData || row.depthData.length === 0) {
    return []
  }
  
  // 如果已展开完整深度，显示全部
  if (isDepthFullShown(eventName)) {
    return row.depthData
  }
  
  // 否则只显示前5个
  return row.depthData.slice(0, 5)
}

/**
 * 判断是否应该显示"查看更多"按钮
 */
const shouldShowMoreDepth = (eventName) => {
  const row = filteredTableData.value.find(r => r.eventName === eventName)
  if (!row || !row.depthData) {
    return false
  }
  return row.depthData.length > 5
}

/**
 * 判断深度是否已展开完整
 */
const isDepthFullShown = (eventName) => {
  return depthFullShown.value.has(eventName)
}

/**
 * 切换深度显示完整/收起
 */
const toggleDepthFull = (eventName) => {
  if (depthFullShown.value.has(eventName)) {
    depthFullShown.value.delete(eventName)
  } else {
    depthFullShown.value.add(eventName)
  }
}

/**
 * 处理展开/折叠事件
 */
const handleExpandChange = (row, expandedRows) => {
  // 可以在这里添加展开时的逻辑，比如加载更多数据
  console.log('[持仓详情] 展开事件:', row.eventName, '展开状态:', expandedRows.some(r => r.eventName === row.eventName))
}

/**
 * 处理YES表格排序变化
 */
const handleYesSortChange = ({ column, order, sortMethod }) => {
  yesSortState.value = { column, order }
}

/**
 * 处理NO表格排序变化
 */
const handleNoSortChange = ({ column, order, sortMethod }) => {
  noSortState.value = { column, order }
}

/**
 * 判断深度是否符合条件
 * 条件：卖一价减去买一价大于0.15，或者买一价或卖一价的深度小于100
 */
const isDepthQualified = (depthData) => {
  if (!depthData || depthData.length === 0) {
    return false
  }
  
  // 获取买一价和卖一价（第一个数据）
  const firstDepth = depthData[0]
  if (!firstDepth) {
    return false
  }
  
  const bidPrice = parseFloat(firstDepth.bidPrice) || 0
  const askPrice = parseFloat(firstDepth.askPrice) || 0
  const bidDepth = parseFloat(firstDepth.bidDepth) || 0
  const askDepth = parseFloat(firstDepth.askDepth) || 0
  
  // 卖一价减去买一价大于0.15
  const priceDiff = askPrice - bidPrice
  if (priceDiff > 0.15) {
    return true
  }
  
  // 买一价或卖一价的深度小于100
  if (bidDepth < 100 || askDepth < 100) {
    return true
  }
  
  return false
}

/**
 * 搜索数据（服务器端筛选，重新请求数据）
 * 服务器端筛选：电脑组、浏览器编号、主题名字
 */
const searchData = () => {
  // 重新加载数据（应用服务器端筛选）
  loadData()
}

/**
 * 应用前端筛选（在数据加载完成后调用）
 */
const applyClientFilter = () => {
  let filtered = [...tableData.value]
  
  // 始终过滤掉 amt < 1 的数据（必须保留的逻辑）
  filtered = filtered.filter(row => {
    const amt = parseFloat(row.amt) || 0
    return amt >= 1
  })
  
  // 数量筛选（前端筛选）
  if (filterAmountValue.value !== null && filterAmountValue.value !== undefined) {
    const amountValue = parseFloat(filterAmountValue.value) || 0
    if (filterAmountOperator.value === 'gt') {
      filtered = filtered.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt > amountValue
      })
    } else if (filterAmountOperator.value === 'lt') {
      filtered = filtered.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt < amountValue
      })
    }
  }
  
  // 更新时间筛选（前端筛选，筛选仓位更新时间）
  if (filterTimeValue.value !== null && filterTimeValue.value !== undefined) {
    const timeValue = parseFloat(filterTimeValue.value) || 0
    const timeThreshold = Date.now() - timeValue * 60 * 60 * 1000 // 转换为时间戳（小时转毫秒）
    
    filtered = filtered.filter(row => {
      if (!row.utime) return false
      const updateTime = typeof row.utime === 'string' ? parseInt(row.utime) : row.utime
      if (isNaN(updateTime)) return false
      
      if (filterTimeOperator.value === 'gt') {
        return updateTime > timeThreshold
      } else {
        return updateTime < timeThreshold
      }
    })
  }
  
  // 事件名模糊匹配筛选（前端筛选）
  if (filterEventName.value && filterEventName.value.trim()) {
    const searchText = filterEventName.value.trim().toLowerCase()
    filtered = filtered.filter(row => {
      const eventName = (row.eventName || '').toLowerCase()
      return eventName.includes(searchText)
    })
  }
  
  filteredTableData.value = filtered
  console.log(`[持仓详情] 前端筛选完成，共 ${filtered.length} 条数据`)
}

/**
 * 监听前端筛选条件变化，自动应用筛选
 */
watch(
  [filterAmountValue, filterAmountOperator, filterTimeValue, filterTimeOperator, filterEventName],
  () => {
    // 当数量、更新时间或事件名筛选条件变化时，自动应用前端筛选
    if (tableData.value.length > 0) {
      applyClientFilter()
    }
  },
  { deep: true }
)

/**
 * 重置筛选条件
 */
const resetFilter = () => {
  filterAmountOperator.value = 'gt'
  filterAmountValue.value = null
  filterTimeOperator.value = 'gt'
  filterTimeValue.value = null
  filterEventName.value = ''
  filterOutCome.value = ''
  filterGroupFilter.value = ''
  filterNumberFilter.value = ''
  filterTrending.value = ''
  // 重置后重新搜索数据
  searchData()
}

/**
 * 更新订单薄数据（已废弃，保留函数避免报错）
 */
const updateOrderbook = async () => {
  ElMessage.info('当前版本不再需要更新订单薄数据')
}

/**
 * 解析URL参数
 */
const parseUrlParams = () => {
  const hash = window.location.hash
  if (!hash || !hash.includes('?')) {
    return {}
  }
  
  const queryString = hash.split('?')[1]
  if (!queryString) {
    return {}
  }
  
  const params = {}
  const pairs = queryString.split('&')
  for (const pair of pairs) {
    const [key, value] = pair.split('=')
    if (key && value) {
      params[decodeURIComponent(key)] = decodeURIComponent(value)
    }
  }
  
  return params
}

/**
 * 加载测试缓存数据
 */
const loadTestCacheData = async (uid) => {
  try {
    console.log('[持仓详情] 开始加载测试缓存数据，uid:', uid)
    const response = await axios.get(`${API_BASE_URL}/hedge/calReadyToHedgeV4TestCache`, {
      params: { uid }
    })
    
    if (response.data && response.data.code === 0 && response.data.data) {
      const data = response.data.data
      console.log('[持仓详情] 获取到测试缓存数据:', data)
      
      // 构建原因映射
      // 注意：YES方向的持仓只匹配 closeYesPass 的原因，NO方向的持仓只匹配 closeNoPass 的原因
      const newReasonMap = new Map()
      
      // 处理 closeYesPass（只用于 YES 方向的持仓）
      if (data.closeYesPass && typeof data.closeYesPass === 'object') {
        for (const [reason, numbers] of Object.entries(data.closeYesPass)) {
          if (Array.isArray(numbers)) {
            for (const number of numbers) {
              const key = `YES_${number}` // YES方向的key
              if (!newReasonMap.has(key)) {
                newReasonMap.set(key, [])
              }
              newReasonMap.get(key).push(reason)
            }
          }
        }
      }
      
      // 处理 closeNoPass（只用于 NO 方向的持仓）
      if (data.closeNoPass && typeof data.closeNoPass === 'object') {
        for (const [reason, numbers] of Object.entries(data.closeNoPass)) {
          if (Array.isArray(numbers)) {
            for (const number of numbers) {
              const key = `NO_${number}` // NO方向的key
              if (!newReasonMap.has(key)) {
                newReasonMap.set(key, [])
              }
              newReasonMap.get(key).push(reason)
            }
          }
        }
      }
      
      reasonMap.value = newReasonMap
      console.log('[持仓详情] 原因映射构建完成，共', newReasonMap.size, '条记录')
      
      // 将测试缓存数据合并到列表中
      await mergeTestCacheDataToTable(data)
      
      // 更新表格数据中的原因字段（合并后更新）
      updateTableDataReasons()
      
      return data
    } else {
      console.warn('[持仓详情] 未获取到测试缓存数据')
      return null
    }
  } catch (error) {
    console.error('[持仓详情] 加载测试缓存数据失败:', error)
    return null
  }
}

/**
 * 将测试缓存数据合并到表格中
 */
const mergeTestCacheDataToTable = async (cacheData) => {
  try {
    console.log('[持仓详情] 开始合并测试缓存数据到表格...')
    
    // 先加载 exchangeConfig 配置（如果还没加载）
    if (idToTrendingMap.value.size === 0) {
      await loadExchangeConfig()
    }
    
    // 获取URL参数中的id（trendingId）
    const urlParams = parseUrlParams()
    const trendingId = urlParams.id ? String(urlParams.id) : null
    
    if (!trendingId) {
      console.warn('[持仓详情] 未找到trendingId参数，无法合并测试缓存数据')
      return
    }
    
    // 获取事件名
    const eventName = idToTrendingMap.value.get(trendingId) || ''
    if (!eventName) {
      console.warn('[持仓详情] 未找到对应的事件名，trendingId:', trendingId)
      return
    }
    
    // 合并到现有数据中（只更新已存在的数据，不添加新数据）
    // 以 getAllPosSnap 返回的数据为基准，只更新已存在的记录
    let updatedCount = 0
    let skippedCount = 0
    
    // 处理 closeYesPass（只匹配 YES 方向的持仓）
    if (cacheData.closeYesPass && typeof cacheData.closeYesPass === 'object') {
      for (const [reason, numbers] of Object.entries(cacheData.closeYesPass)) {
        if (Array.isArray(numbers)) {
          for (const number of numbers) {
            const numberStr = String(number)
            const trendingKey = `${trendingId}::YES`
            
            // 只查找 YES 方向的持仓
            const existingIndex = tableData.value.findIndex(item => 
              item.number === numberStr && 
              item.outCome === 'YES' &&
              item.trendingKey === trendingKey
            )
            
            if (existingIndex >= 0) {
              // 如果已存在（在 getAllPosSnap 返回的数据中），更新原因
              const existingReason = tableData.value[existingIndex].reason
              if (existingReason) {
                tableData.value[existingIndex].reason = `${existingReason}; ${reason}`
              } else {
                tableData.value[existingIndex].reason = reason
              }
              updatedCount++
            } else {
              // 如果不存在（不在 getAllPosSnap 返回的数据中），跳过，不添加
              skippedCount++
              console.log(`[持仓详情] 跳过测试缓存数据：number=${numberStr}, outCome=YES（不在 getAllPosSnap 返回的数据中）`)
            }
          }
        }
      }
    }
    
    // 处理 closeNoPass（只匹配 NO 方向的持仓）
    if (cacheData.closeNoPass && typeof cacheData.closeNoPass === 'object') {
      for (const [reason, numbers] of Object.entries(cacheData.closeNoPass)) {
        if (Array.isArray(numbers)) {
          for (const number of numbers) {
            const numberStr = String(number)
            const trendingKey = `${trendingId}::NO`
            
            // 只查找 NO 方向的持仓
            const existingIndex = tableData.value.findIndex(item => 
              item.number === numberStr && 
              item.outCome === 'NO' &&
              item.trendingKey === trendingKey
            )
            
            if (existingIndex >= 0) {
              // 如果已存在（在 getAllPosSnap 返回的数据中），更新原因
              const existingReason = tableData.value[existingIndex].reason
              if (existingReason) {
                tableData.value[existingIndex].reason = `${existingReason}; ${reason}`
              } else {
                tableData.value[existingIndex].reason = reason
              }
              updatedCount++
            } else {
              // 如果不存在（不在 getAllPosSnap 返回的数据中），跳过，不添加
              skippedCount++
              console.log(`[持仓详情] 跳过测试缓存数据：number=${numberStr}, outCome=NO（不在 getAllPosSnap 返回的数据中）`)
            }
          }
        }
      }
    }
    
    console.log(`[持仓详情] 测试缓存数据合并完成，更新 ${updatedCount} 条记录，跳过 ${skippedCount} 条记录（不在 getAllPosSnap 返回的数据中）`)
    
    // 应用前端筛选
    applyClientFilter()
  } catch (error) {
    console.error('[持仓详情] 合并测试缓存数据失败:', error)
  }
}

/**
 * 更新表格数据中的原因字段
 * 确保：YES方向的持仓只显示 closeYesPass 的原因，NO方向的持仓只显示 closeNoPass 的原因
 */
const updateTableDataReasons = () => {
  // 获取URL参数中的id（trendingId）
  const urlParams = parseUrlParams()
  const trendingId = urlParams.id ? String(urlParams.id) : null
  
  if (!trendingId) {
    console.warn('[持仓详情] 未找到trendingId参数，无法匹配原因')
    return
  }
  
  // 遍历表格数据，匹配原因
  for (const row of tableData.value) {
    // 检查事件ID是否匹配
    if (row.trendingKey) {
      const parts = row.trendingKey.split('::')
      if (parts.length >= 2) {
        const configId = parts[0].trim()
        if (configId === trendingId) {
          // 事件ID匹配，查找原因
          const number = String(row.number || '')
          const outCome = row.outCome || ''
          
          // 确保严格按照方向匹配：
          // YES方向只匹配 closeYesPass 的原因（key: YES_${number}）
          // NO方向只匹配 closeNoPass 的原因（key: NO_${number}）
          if (outCome === 'YES') {
            // YES方向，只查找 closeYesPass 的原因
            const key = `YES_${number}`
            const reasons = reasonMap.value.get(key)
            if (reasons && reasons.length > 0) {
              // 如果有多个原因，用分号连接
              row.reason = reasons.join('; ')
            } else {
              row.reason = null
            }
          } else if (outCome === 'NO') {
            // NO方向，只查找 closeNoPass 的原因
            const key = `NO_${number}`
            const reasons = reasonMap.value.get(key)
            if (reasons && reasons.length > 0) {
              // 如果有多个原因，用分号连接
              row.reason = reasons.join('; ')
            } else {
              row.reason = null
            }
          } else {
            // 其他方向，不显示原因
            row.reason = null
          }
        } else {
          row.reason = null
        }
      } else {
        row.reason = null
      }
    } else {
      row.reason = null
    }
  }
  
  // 重新应用前端筛选
  applyClientFilter()
}

/**
 * 初始化数据（根据URL参数决定是否自动加载）
 */
const initializeData = async () => {
  // 解析URL参数
  const urlParams = parseUrlParams()
  const uid = urlParams.uid
  const id = urlParams.id
  
  // 检查是否有任何URL参数
  const hasUrlParams = Object.keys(urlParams).length > 0
  
  // 只有当URL有参数时才自动请求数据
  if (hasUrlParams) {
    console.log('[持仓详情] 检测到URL参数，自动加载数据')
    
    // 如果URL参数中有id（trendingId），设置默认的主题名字筛选和事件名
    if (id) {
      console.log('[持仓详情] 检测到trendingId参数:', id)
      // 先加载配置，获取事件名
      await loadExchangeConfig()
      const eventName = idToTrendingMap.value.get(String(id))
      if (eventName) {
        filterTrending.value = eventName
        // 同时设置事件名到事件名输入框
        filterEventName.value = eventName
        console.log('[持仓详情] 设置默认主题名字筛选和事件名:', eventName)
      }
    }
    
    // 如果URL参数中有minUAmt，设置数量筛选的"大于"值
    const minUAmt = urlParams.minUAmt
    if (minUAmt) {
      const minUAmtValue = parseFloat(minUAmt)
      if (!isNaN(minUAmtValue)) {
        filterAmountValue.value = minUAmtValue
        filterAmountOperator.value = 'gt' // 设置为"大于"
        console.log('[持仓详情] 设置数量筛选条件: 大于', minUAmtValue)
      }
    }
    
    // 加载数据（会应用默认的主题名字筛选）
    await loadData()
    
    // 如果URL参数中有uid，加载测试缓存数据并合并到列表中
    if (uid) {
      console.log('[持仓详情] 检测到uid参数:', uid, 'trendingId:', id)
      // 加载测试缓存数据（会自动合并到列表中）
      await loadTestCacheData(uid)
    }
  } else {
    console.log('[持仓详情] 未检测到URL参数，不自动加载数据，请手动点击刷新或搜索')
  }
}

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  // 初始化筛选后的数据为空数组
  filteredTableData.value = []
  
  // 初始化数据（根据URL参数决定是否自动加载）
  await initializeData()
})

/**
 * 监听路由变化（处理组件复用的情况）
 */
watch(
  () => route.fullPath,
  async (newPath, oldPath) => {
    // 只有当路由确实发生变化时才重新初始化
    if (newPath !== oldPath && newPath.includes('/position-detail')) {
      console.log('[持仓详情] 检测到路由变化，重新初始化')
      // 清空当前数据
      filteredTableData.value = []
      tableData.value = []
      // 重新初始化数据
      await initializeData()
    }
  }
)
</script>

<style scoped>
.position-detail-page {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 200px);
  width: 100%;
  overflow-x: auto;
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
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  max-height: 2.8em;
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

.expand-content {
  padding: 20px;
  background-color: #fafafa;
  max-width: 100%;
  overflow-x: auto;
  box-sizing: border-box;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.detail-container {
  display: flex;
  gap: 20px;
  max-width: 100%;
  box-sizing: border-box;
}

.detail-left {
  flex: 1;
  min-width: 0;
  max-width: 50%;
}

.detail-right {
  flex: 1;
  min-width: 0;
  max-width: 50%;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-card {
  background-color: #fff;
}

.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.search-row {
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 15px;
}

.filter-row-local {
  padding-top: 5px;
}

.filter-item {
  display: flex;
  align-items: center;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  margin-right: 8px;
  white-space: nowrap;
}

.depth-qualified {
  background-color: #e6f4ff !important;
  padding: 8px;
  border-radius: 4px;
}

.yes-color {
  color: #67c23a;
  font-weight: 600;
}

.no-color {
  color: #f56c6c;
  font-weight: 600;
}

.table-section {
  margin-bottom: 30px;
}

.table-section:last-child {
  margin-bottom: 0;
}

.table-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
  padding: 10px 0;
}

.yes-title {
  color: #67c23a;
}

.no-title {
  color: #f56c6c;
}

.loading-wrapper {
  position: relative;
  min-width: 1800px;
}
</style>

