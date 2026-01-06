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
        <div class="filter-row">
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
          
          <div class="filter-item">
            <span class="filter-label">事件名：</span>
            <el-input 
              v-model="filterEventName" 
              placeholder="输入事件名进行模糊匹配"
              style="width: 200px;"
              clearable
            />
          </div>
          
          <div class="filter-item">
            <el-checkbox v-model="filterDepthCondition">深度符合条件</el-checkbox>
          </div>
          
          <div class="filter-item">
            <el-button type="primary" @click="applyFilter">应用筛选</el-button>
            <el-button @click="resetFilter" style="margin-left: 10px;">重置</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 持仓详情表格 -->
    <el-table 
      :data="filteredTableData" 
      border 
      style="width: 100%; min-width: 1800px;"
      v-loading="loading"
      height="calc(100vh - 350px)"
      @expand-change="handleExpandChange"
    >
      <el-table-column type="expand" width="150">
        <template #header>
          <span>查看持仓详情</span>
        </template>
        <template #default="scope">
          <div class="expand-content">
            <div class="detail-container">
              <!-- YES持仓详情表格 - 左边 -->
              <div class="detail-section detail-left">
                <h3 class="detail-title">YES持仓详情</h3>
                  <el-table 
                  :data="getFilteredYesDetails(scope.row.eventName)" 
                  border 
                  size="small"
                  max-height="400"
                >
                  <el-table-column prop="browserNumber" label="浏览器编号" width="120" align="center" sortable />
                  <el-table-column prop="updateTime" label="更新时间" width="150" align="center" sortable>
                    <template #default="detailScope">
                      <span>{{ formatTimeAgo(detailScope.row.updateTime) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="amount" label="数量" width="120" align="center" sortable>
                    <template #default="detailScope">
                      <span>{{ formatNumber(detailScope.row.amount) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="price" label="价格" width="120" align="center" sortable>
                    <template #default="detailScope">
                      <span>{{ formatNumber(detailScope.row.price) }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              
              <!-- NO持仓详情表格 - 右边 -->
              <div class="detail-section detail-right">
                <h3 class="detail-title">NO持仓详情</h3>
                <el-table 
                  :data="getFilteredNoDetails(scope.row.eventName)" 
                  border 
                  size="small"
                  max-height="400"
                >
                  <el-table-column prop="price" label="价格" width="120" align="center" sortable>
                    <template #default="detailScope">
                      <span>{{ formatNumber(detailScope.row.price) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="amount" label="数量" width="120" align="center" sortable>
                    <template #default="detailScope">
                      <span>{{ formatNumber(detailScope.row.amount) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="updateTime" label="更新时间" width="150" align="center" sortable>
                    <template #default="detailScope">
                      <span>{{ formatTimeAgo(detailScope.row.updateTime) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="browserNumber" label="浏览器编号" width="120" align="center" sortable />
                </el-table>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column type="index" label="序号" width="60" align="center" :index="indexMethod" fixed />
      
      <el-table-column prop="eventName" label="事件名" width="300" fixed sortable>
        <template #default="scope">
          <div class="event-name-cell">
            {{ scope.row.eventName }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="yes持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesPosition, b.yesPosition)">
        <template #default="scope">
          <span>{{ formatNumber(scope.row.yesPosition) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="no持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noPosition, b.noPosition)">
        <template #default="scope">
          <span>{{ formatNumber(scope.row.noPosition) }}</span>
        </template>
      </el-table-column>

      <!-- YES深度 -->
      <el-table-column label="YES深度" width="300" align="center">
        <template #default="scope">
          <div 
            v-if="scope.row.depthData && scope.row.depthData.length > 0" 
            class="depth-container"
            :class="{ 'depth-qualified': isDepthQualified(scope.row.depthData) }"
          >
            <div v-for="(item, index) in getDisplayDepthData(scope.row.eventName)" :key="index" class="depth-item">
              <span class="depth-bid">{{ formatNumber(item.bidDepth) }}, {{ formatNumber(item.bidPrice) }}</span>
              <span class="depth-separator"> | </span>
              <span class="depth-ask">{{ formatNumber(item.askPrice) }}, {{ formatNumber(item.askDepth) }}</span>
            </div>
            <div v-if="shouldShowMoreDepth(scope.row.eventName)" class="depth-more">
              <el-button 
                type="text" 
                size="small" 
                @click="toggleDepthFull(scope.row.eventName)"
              >
                {{ isDepthFullShown(scope.row.eventName) ? '收起' : '查看更多' }}
              </el-button>
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
const filteredTableData = ref([]) // 筛选后的表格数据
const exchangeConfigList = ref([])
const idToTrendingMap = ref(new Map())
const opTopicIdMap = ref(new Map()) // eventName -> opTopicId 映射
const eventMapCache = ref(new Map()) // 缓存事件映射，用于更新订单薄

// 筛选条件
const filterAmountOperator = ref('gt') // 'gt' 或 'lt'
const filterAmountValue = ref(null)
const filterTimeOperator = ref('gt') // 'gt' 或 'lt'
const filterTimeValue = ref(null) // 小时数
const filterDepthCondition = ref(false) // 深度符合条件
const filterEventName = ref('') // 事件名模糊匹配

// 深度显示状态
const depthFullShown = ref(new Set()) // 存储已展开完整深度的事件名

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
      
      // 排序持仓详情
      for (const event of eventMap.values()) {
        // YES持仓按价格从大到小排序
        event.yesDetails.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
        // NO持仓按价格从小到大排序
        event.noDetails.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
      }
      
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
      eventMapCache.value = eventMap // 缓存事件映射
      
      // 应用筛选
      applyFilter()
      
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
 * 应用筛选条件
 */
const applyFilter = () => {
  let filtered = [...tableData.value]
  
  // 数量筛选
  if (filterAmountValue.value !== null && filterAmountValue.value !== undefined) {
    const amountValue = parseFloat(filterAmountValue.value) || 0
    if (filterAmountOperator.value === 'gt') {
      filtered = filtered.filter(row => {
        const yesAmount = parseFloat(row.yesPosition) || 0
        const noAmount = parseFloat(row.noPosition) || 0
        return yesAmount > amountValue || noAmount > amountValue
      })
    } else if (filterAmountOperator.value === 'lt') {
      filtered = filtered.filter(row => {
        const yesAmount = parseFloat(row.yesPosition) || 0
        const noAmount = parseFloat(row.noPosition) || 0
        return yesAmount < amountValue || noAmount < amountValue
      })
    }
  }
  
  // 更新时间筛选（筛选持仓详情中的更新时间）
  if (filterTimeValue.value !== null && filterTimeValue.value !== undefined) {
    const timeValue = parseFloat(filterTimeValue.value) || 0
    const timeThreshold = Date.now() - timeValue * 60 * 60 * 1000 // 转换为时间戳（小时转毫秒）
    
    filtered = filtered.filter(row => {
      const event = eventMapCache.value.get(row.eventName)
      if (!event) return false
      
      // 检查YES持仓详情
      const yesMatch = event.yesDetails.some(detail => {
        if (!detail.updateTime) return false
        const updateTime = typeof detail.updateTime === 'string' ? parseInt(detail.updateTime) : detail.updateTime
        if (filterTimeOperator.value === 'gt') {
          return updateTime > timeThreshold
        } else {
          return updateTime < timeThreshold
        }
      })
      
      // 检查NO持仓详情
      const noMatch = event.noDetails.some(detail => {
        if (!detail.updateTime) return false
        const updateTime = typeof detail.updateTime === 'string' ? parseInt(detail.updateTime) : detail.updateTime
        if (filterTimeOperator.value === 'gt') {
          return updateTime > timeThreshold
        } else {
          return updateTime < timeThreshold
        }
      })
      
      return yesMatch || noMatch
    })
  }
  
  // 深度条件筛选
  if (filterDepthCondition.value) {
    filtered = filtered.filter(row => {
      return isDepthQualified(row.depthData)
    })
  }
  
  // 事件名模糊匹配筛选
  if (filterEventName.value && filterEventName.value.trim()) {
    const searchText = filterEventName.value.trim().toLowerCase()
    filtered = filtered.filter(row => {
      return row.eventName.toLowerCase().includes(searchText)
    })
  }
  
  // 重新计算筛选后的yes持仓数量和no持仓数量
  filtered = filtered.map(row => {
    const filteredYesDetails = getFilteredYesDetails(row.eventName)
    const filteredNoDetails = getFilteredNoDetails(row.eventName)
    
    // 计算筛选后的YES持仓数量
    const filteredYesPosition = filteredYesDetails.reduce((sum, detail) => {
      return sum + (parseFloat(detail.amount) || 0)
    }, 0)
    
    // 计算筛选后的NO持仓数量
    const filteredNoPosition = filteredNoDetails.reduce((sum, detail) => {
      return sum + (parseFloat(detail.amount) || 0)
    }, 0)
    
    return {
      ...row,
      yesPosition: filteredYesPosition,
      noPosition: filteredNoPosition
    }
  })
  
  filteredTableData.value = filtered
  console.log(`[持仓详情] 筛选完成，共 ${filtered.length} 条数据`)
}

/**
 * 重置筛选条件
 */
const resetFilter = () => {
  filterAmountOperator.value = 'gt'
  filterAmountValue.value = null
  filterTimeOperator.value = 'gt'
  filterTimeValue.value = null
  filterDepthCondition.value = false
  filterEventName.value = ''
  applyFilter()
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
  // 初始化筛选后的数据为空数组，等数据加载完成后会自动应用筛选
  filteredTableData.value = []
})
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

.depth-more {
  text-align: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
}
</style>

