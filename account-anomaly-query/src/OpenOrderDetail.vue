<template>
  <div class="open-order-detail-page">
    <h1 class="page-title">挂单详情</h1>
    
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
            <div class="trending-autocomplete-wrapper">
              <input
                v-model="trendingSearchText"
                type="text"
                placeholder="输入文字筛选或选择事件"
                :disabled="loading"
                @input="onTrendingSearchInput"
                @focus="showTrendingDropdown = true"
                @blur="handleTrendingBlur"
                @keyup.enter="searchData"
                autocomplete="off"
                class="trending-input"
              />
              <div 
                v-if="showTrendingDropdown && filteredTrendingList.length > 0" 
                class="trending-dropdown"
              >
                <div
                  v-for="config in filteredTrendingList"
                  :key="config.id"
                  class="trending-dropdown-item"
                  @mousedown.prevent="selectTrending(config)"
                >
                  {{ config.trending }}
                </div>
              </div>
            </div>
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

    <!-- YES方向挂单表格 -->
    <div class="table-section">
      <h2 class="table-title yes-title">
        YES 方向挂单 ({{ yesTableData.length }} 条)
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
          <template #restAmt="{ row }">
            <span>{{ formatNumber(row.restAmt) }}</span>
          </template>
          <template #price="{ row }">
            <span>{{ formatNumber(row.price) }}</span>
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
        </VirtualTable>
      </div>
    </div>

    <!-- NO方向挂单表格 -->
    <div class="table-section">
      <h2 class="table-title no-title">
        NO 方向挂单 ({{ noTableData.length }} 条)
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
          <template #restAmt="{ row }">
            <span>{{ formatNumber(row.restAmt) }}</span>
          </template>
          <template #price="{ row }">
            <span>{{ formatNumber(row.price) }}</span>
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

const loading = ref(false)
const updatingOrderbook = ref(false)
const tableData = ref([])
const filteredTableData = ref([]) // 筛选后的表格数据
const exchangeConfigList = ref([])
const idToTrendingMap = ref(new Map())

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

// 事件名自动完成相关
const trendingSearchText = ref('') // 事件名搜索文本
const showTrendingDropdown = ref(false) // 是否显示下拉列表
const selectedConfig = ref(null) // 选中的配置

// 排序状态
const yesSortState = ref({ column: null, order: null })
const noSortState = ref({ column: null, order: null })

// YES表格列定义（不包含"原因"列）
const yesColumns = ref([
  { type: 'index', label: '序号', width: 60, fixed: 'left' },
  { prop: 'number', label: '浏览器编号', width: 120, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByString(a.number, b.number) },
  { prop: 'group', label: '电脑组', width: 100, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByNumber(a.group, b.group) },
  { prop: 'eventName', label: '事件名', width: 300, sortable: true, sortMethod: (a, b) => sortByString(a.eventName, b.eventName) },
  { prop: 'side', label: '方向', width: 80, sortable: true, sortMethod: (a, b) => sortByNumber(a.side, b.side) },
  { prop: 'amt', label: '挂单数量', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.amt, b.amt) },
  { prop: 'restAmt', label: '剩余数量', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.restAmt, b.restAmt) },
  { prop: 'price', label: '价格', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.price, b.price) },
  { prop: 'ctime', label: '挂单创建时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.ctime, b.ctime) },
  { prop: 'utime', label: '挂单更新时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.utime, b.utime) },
  { prop: 'catchTime', label: '抓取时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.catchTime, b.catchTime) }
])

// NO表格列定义（不包含"原因"列）
const noColumns = ref([
  { type: 'index', label: '序号', width: 60, fixed: 'left' },
  { prop: 'number', label: '浏览器编号', width: 120, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByString(a.number, b.number) },
  { prop: 'group', label: '电脑组', width: 100, sortable: true, fixed: 'left', sortMethod: (a, b) => sortByNumber(a.group, b.group) },
  { prop: 'eventName', label: '事件名', width: 300, sortable: true, sortMethod: (a, b) => sortByString(a.eventName, b.eventName) },
  { prop: 'side', label: '方向', width: 80, sortable: true, sortMethod: (a, b) => sortByNumber(a.side, b.side) },
  { prop: 'amt', label: '挂单数量', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.amt, b.amt) },
  { prop: 'restAmt', label: '剩余数量', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.restAmt, b.restAmt) },
  { prop: 'price', label: '价格', width: 120, sortable: true, sortMethod: (a, b) => sortByNumber(a.price, b.price) },
  { prop: 'ctime', label: '挂单创建时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.ctime, b.ctime) },
  { prop: 'utime', label: '挂单更新时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.utime, b.utime) },
  { prop: 'catchTime', label: '抓取时间', width: 180, sortable: true, sortMethod: (a, b) => sortByTime(a.catchTime, b.catchTime) }
])

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
 * 过滤后的事件列表（用于自动完成下拉框）
 */
const filteredTrendingList = computed(() => {
  if (!trendingSearchText.value || trendingSearchText.value.trim() === '') {
    return exchangeConfigList.value
  }
  const searchLower = trendingSearchText.value.toLowerCase().trim()
  return exchangeConfigList.value.filter(config => {
    return config.trending && config.trending.toLowerCase().includes(searchLower)
  })
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
    console.log('[挂单详情] 开始加载 exchangeConfig 配置...')
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
      
      console.log(`[挂单详情] exchangeConfig 配置加载完成，共 ${exchangeConfigList.value.length} 个配置`)
      return exchangeConfigList.value
    } else {
      console.warn('[挂单详情] 未获取到 exchangeConfig 配置数据')
      return []
    }
  } catch (error) {
    console.error('[挂单详情] 加载 exchangeConfig 配置失败:', error)
    return []
  }
}

/**
 * 加载数据并构建表格
 */
const loadData = async () => {
  loading.value = true
  
  try {
    console.log('[挂单详情] 开始加载数据...')
    
    // 先加载 exchangeConfig 配置
    await loadExchangeConfig()
    
    // 优先使用选中的配置ID，否则使用URL参数中的trendingId
    let trendingId = null
    if (selectedConfig.value && selectedConfig.value.id) {
      trendingId = selectedConfig.value.id
      console.log('[挂单详情] 使用选中的配置ID:', trendingId)
    } else {
      const urlParams = parseUrlParams()
      trendingId = urlParams.id
      console.log('[挂单详情] 使用URL参数ID:', trendingId)
    }
    
    if (!trendingId) {
      ElMessage.warning('请选择一个事件或通过URL参数提供主题ID')
      loading.value = false
      return
    }
    
    console.log('[挂单详情] trendingId:', trendingId)
    
    // 加载挂单数据
    const response = await axios.get(`${API_BASE_URL}/boost/getOpenOrderSnapList`, {
      params: { trendingId }
    })
    
    if (response.data && response.data.code === 0 && response.data.data) {
      const data = response.data.data
      console.log(`[挂单详情] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 过滤掉 restAmt < 1 的数据
      const filteredData = data.filter(row => {
        const restAmt = parseFloat(row.restAmt) || 0
        return restAmt >= 1
      })
      console.log(`[挂单详情] 过滤后剩余 ${filteredData.length} 条数据（已过滤掉 ${data.length - filteredData.length} 条 restAmt < 1 的数据）`)
      
      // 获取事件名
      const eventName = idToTrendingMap.value.get(String(trendingId)) || ''
      
      // 处理每条数据
      const processedData = filteredData.map(row => {
        // 处理时间字段，确保是数字类型
        const processedRow = {
          ...row,
          eventName: eventName,
          number: row.number ? String(row.number) : '',
          group: row.group ? (typeof row.group === 'string' ? parseInt(row.group) : row.group) : null,
          outCome: row.outCome || '',
          amt: parseFloat(row.amt) || 0,
          restAmt: parseFloat(row.restAmt) || 0,
          price: parseFloat(row.price) || 0,
          side: row.side,
          ctime: row.ctime ? (typeof row.ctime === 'string' ? parseInt(row.ctime) : row.ctime) : null,
          utime: row.utime ? (typeof row.utime === 'string' ? parseInt(row.utime) : row.utime) : null,
          catchTime: row.catchTime ? (typeof row.catchTime === 'string' ? parseInt(row.catchTime) : row.catchTime) : null
        }
        
        return processedRow
      })
      
      tableData.value = processedData
      
      // 应用前端筛选
      applyClientFilter()
      
      console.log('[挂单详情] 数据加载完成')
      ElMessage.success(`数据加载完成，共 ${processedData.length} 条记录`)
    } else {
      ElMessage.warning('未获取到数据')
    }
  } catch (error) {
    console.error('[挂单详情] 加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
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
 * 事件名搜索输入处理
 */
const onTrendingSearchInput = () => {
  showTrendingDropdown.value = true
  // 如果输入的内容完全匹配某个选项，自动选择
  const exactMatch = exchangeConfigList.value.find(config => {
    return config.trending === trendingSearchText.value
  })
  if (exactMatch) {
    selectedConfig.value = exactMatch
  } else {
    selectedConfig.value = null
  }
}

/**
 * 选择事件
 */
const selectTrending = (config) => {
  selectedConfig.value = config
  trendingSearchText.value = config.trending
  showTrendingDropdown.value = false
}

/**
 * 事件名输入框失焦处理
 */
const handleTrendingBlur = () => {
  // 延迟隐藏，以便点击下拉项时能触发
  setTimeout(() => {
    showTrendingDropdown.value = false
  }, 200)
}

/**
 * 搜索数据（服务器端筛选，重新请求数据）
 */
const searchData = () => {
  loadData()
}

/**
 * 应用前端筛选（在数据加载完成后调用）
 */
const applyClientFilter = () => {
  let filtered = [...tableData.value]
  
  // 始终过滤掉 restAmt < 1 的数据
  filtered = filtered.filter(row => {
    const restAmt = parseFloat(row.restAmt) || 0
    return restAmt >= 1
  })
  
  // 数量筛选（前端筛选，针对 restAmt）
  if (filterAmountValue.value !== null && filterAmountValue.value !== undefined) {
    const amountValue = parseFloat(filterAmountValue.value) || 0
    if (filterAmountOperator.value === 'gt') {
      filtered = filtered.filter(row => {
        const restAmt = parseFloat(row.restAmt) || 0
        return restAmt > amountValue
      })
    } else if (filterAmountOperator.value === 'lt') {
      filtered = filtered.filter(row => {
        const restAmt = parseFloat(row.restAmt) || 0
        return restAmt < amountValue
      })
    }
  }
  
  // 更新时间筛选（前端筛选）
  if (filterTimeValue.value !== null && filterTimeValue.value !== undefined) {
    const timeValue = parseFloat(filterTimeValue.value) || 0
    const timeThreshold = Date.now() - timeValue * 60 * 60 * 1000
    
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
  
  // 电脑组筛选
  if (filterGroupFilter.value && filterGroupFilter.value.trim()) {
    const groups = filterGroupFilter.value.split(',').map(g => g.trim()).filter(g => g)
    if (groups.length > 0) {
      filtered = filtered.filter(row => {
        const group = String(row.group || '')
        return groups.includes(group)
      })
    }
  }
  
  // 浏览器编号筛选
  if (filterNumberFilter.value && filterNumberFilter.value.trim()) {
    const numbers = filterNumberFilter.value.split(',').map(n => n.trim()).filter(n => n)
    if (numbers.length > 0) {
      filtered = filtered.filter(row => {
        const number = String(row.number || '')
        return numbers.includes(number)
      })
    }
  }
  
  filteredTableData.value = filtered
  console.log(`[挂单详情] 前端筛选完成，共 ${filtered.length} 条数据`)
}

/**
 * 监听前端筛选条件变化，自动应用筛选
 */
watch(
  [filterAmountValue, filterAmountOperator, filterTimeValue, filterTimeOperator, filterEventName, filterGroupFilter, filterNumberFilter],
  () => {
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
  // 重置自动完成相关状态
  trendingSearchText.value = ''
  selectedConfig.value = null
  // 清空数据
  tableData.value = []
  filteredTableData.value = []
}

/**
 * 更新订单薄数据（占位函数）
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
 * 初始化数据（根据URL参数决定是否自动加载）
 */
const initializeData = async () => {
  // 先加载配置列表（用于自动完成下拉框）
  await loadExchangeConfig()
  
  const urlParams = parseUrlParams()
  const id = urlParams.id
  
  const hasUrlParams = Object.keys(urlParams).length > 0
  
  if (hasUrlParams) {
    console.log('[挂单详情] 检测到URL参数，自动加载数据')
    
    if (id) {
      console.log('[挂单详情] 检测到trendingId参数:', id)
      const eventName = idToTrendingMap.value.get(String(id))
      if (eventName) {
        // 设置自动完成输入框的值
        trendingSearchText.value = eventName
        // 找到对应的配置并设置为选中
        const config = exchangeConfigList.value.find(c => String(c.id) === String(id))
        if (config) {
          selectedConfig.value = config
        }
        filterTrending.value = eventName
        filterEventName.value = eventName
        console.log('[挂单详情] 设置默认主题名字筛选和事件名:', eventName)
      }
    }
    
    await loadData()
  } else {
    console.log('[挂单详情] 未检测到URL参数，请选择事件后点击搜索')
  }
}

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  filteredTableData.value = []
  await initializeData()
})

/**
 * 监听路由变化（处理组件复用的情况）
 */
watch(
  () => route.fullPath,
  async (newPath, oldPath) => {
    if (newPath !== oldPath && newPath.includes('/open-order-detail')) {
      console.log('[挂单详情] 检测到路由变化，重新初始化')
      filteredTableData.value = []
      tableData.value = []
      await initializeData()
    }
  }
)
</script>

<style scoped>
.open-order-detail-page {
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

/* 自动完成下拉框样式 */
.trending-autocomplete-wrapper {
  position: relative;
  display: inline-block;
  width: 300px;
}

.trending-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.trending-input:focus {
  border-color: #409eff;
}

.trending-input:disabled {
  background-color: #f5f7fa;
  cursor: not-allowed;
}

.trending-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 300px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 4px;
}

.trending-dropdown-item {
  padding: 10px 12px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trending-dropdown-item:hover {
  background-color: #f5f7fa;
}

.trending-dropdown-item:active {
  background-color: #ecf5ff;
  color: #409eff;
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
