<template>
  <div class="event-task-info-page">
    <h1 class="page-title">事件任务信息</h1>
    
    <div class="toolbar">
      <div class="time-range-selector">
        <label>时间范围（小时）：</label>
        <div class="time-inputs">
          <div class="time-input-item">
            <label>区间1：</label>
            <el-input-number 
              v-model="timeRange1" 
              :min="1" 
              :max="10000" 
              :precision="0"
              controls-position="right"
              style="width: 120px;"
            />
            <span class="time-unit">小时前</span>
          </div>
          <div class="time-input-item">
            <label>区间2：</label>
            <el-input-number 
              v-model="timeRange2" 
              :min="1" 
              :max="10000" 
              :precision="0"
              controls-position="right"
              style="width: 120px;"
            />
            <span class="time-unit">小时前</span>
          </div>
          <div class="time-input-item">
            <label>区间3：</label>
            <el-input-number 
              v-model="timeRange3" 
              :min="1" 
              :max="10000" 
              :precision="0"
              controls-position="right"
              style="width: 120px;"
            />
            <span class="time-unit">小时前</span>
          </div>
        </div>
      </div>
      <el-button type="primary" @click="loadData" :loading="loading" style="margin-left: 20px;">
        刷新数据
      </el-button>
      <div class="filter-section" style="margin-left: 20px;">
        <div class="filter-item">
          <label>事件名筛选：</label>
          <el-input 
            v-model="filterEventName" 
            placeholder="输入事件名进行模糊匹配"
            style="width: 250px;"
            clearable
          />
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-wrapper">
      <el-table 
        :data="filteredTableData" 
        border 
        style="width: 100%"
        v-loading="loading"
        height="calc(100vh - 300px)"
        stripe
      >
        <el-table-column type="index" label="序号" width="80" align="center" fixed :index="indexMethod" />
        
        <el-table-column prop="trending" label="事件名" width="300" align="center" fixed sortable />

        <!-- 第一个区间数据 -->
        <el-table-column :label="range1Label" align="center" width="720">
          <el-table-column prop="openAmt1" label="开仓数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.openAmt1) }}
            </template>
          </el-table-column>
          <el-table-column prop="closeAmt1" label="平仓数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.closeAmt1) }}
            </template>
          </el-table-column>
          <el-table-column prop="fullFillAmt1" label="完全成交数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.fullFillAmt1) }}
            </template>
          </el-table-column>
          <el-table-column prop="partFillAmt1" label="部分成交数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.partFillAmt1) }}
            </template>
          </el-table-column>
          <el-table-column prop="openCount1" label="开仓次数" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.openCount1) }}
            </template>
          </el-table-column>
          <el-table-column prop="closeCount1" label="平仓次数" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.closeCount1) }}
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 第二个区间数据 -->
        <el-table-column :label="range2Label" align="center" width="720">
          <el-table-column prop="openAmt2" label="开仓数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.openAmt2) }}
            </template>
          </el-table-column>
          <el-table-column prop="closeAmt2" label="平仓数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.closeAmt2) }}
            </template>
          </el-table-column>
          <el-table-column prop="fullFillAmt2" label="完全成交数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.fullFillAmt2) }}
            </template>
          </el-table-column>
          <el-table-column prop="partFillAmt2" label="部分成交数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.partFillAmt2) }}
            </template>
          </el-table-column>
          <el-table-column prop="openCount2" label="开仓次数" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.openCount2) }}
            </template>
          </el-table-column>
          <el-table-column prop="closeCount2" label="平仓次数" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.closeCount2) }}
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 第三个区间数据 -->
        <el-table-column :label="range3Label" align="center" width="720">
          <el-table-column prop="openAmt3" label="开仓数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.openAmt3) }}
            </template>
          </el-table-column>
          <el-table-column prop="closeAmt3" label="平仓数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.closeAmt3) }}
            </template>
          </el-table-column>
          <el-table-column prop="fullFillAmt3" label="完全成交数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.fullFillAmt3) }}
            </template>
          </el-table-column>
          <el-table-column prop="partFillAmt3" label="部分成交数量" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.partFillAmt3) }}
            </template>
          </el-table-column>
          <el-table-column prop="openCount3" label="开仓次数" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.openCount3) }}
            </template>
          </el-table-column>
          <el-table-column prop="closeCount3" label="平仓次数" width="120" align="center" sortable>
            <template #default="scope">
              {{ formatNumber(scope.row.closeCount3) }}
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'

const loading = ref(false)
const tableData = ref([])
const allTableData = ref([]) // 保存所有原始数据
const filterEventName = ref('') // 事件名筛选
const idToTrendingMap = ref(new Map()) // id -> trending 映射

// 从本地存储读取时间范围，如果没有则使用默认值
const loadTimeRangesFromStorage = () => {
  try {
    const saved = localStorage.getItem('eventTaskInfo_timeRanges')
    if (saved) {
      const ranges = JSON.parse(saved)
      return {
        timeRange1: ranges.timeRange1 || 24,
        timeRange2: ranges.timeRange2 || 72,
        timeRange3: ranges.timeRange3 || 168
      }
    }
  } catch (e) {
    console.error('读取本地存储失败:', e)
  }
  return {
    timeRange1: 24,
    timeRange2: 72,
    timeRange3: 168
  }
}

const savedRanges = loadTimeRangesFromStorage()
const timeRange1 = ref(savedRanges.timeRange1)
const timeRange2 = ref(savedRanges.timeRange2)
const timeRange3 = ref(savedRanges.timeRange3)

/**
 * 格式化时间范围标签
 */
const formatTimeLabel = (hours) => {
  if (hours < 24) {
    return `最近${hours}小时`
  } else {
    const days = hours / 24
    if (days === Math.floor(days)) {
      return `最近${days}天`
    } else {
      return `最近${days}天`
    }
  }
}

/**
 * 计算表格列标题
 */
const range1Label = computed(() => {
  return formatTimeLabel(timeRange1.value)
})

const range2Label = computed(() => {
  return formatTimeLabel(timeRange2.value)
})

const range3Label = computed(() => {
  return formatTimeLabel(timeRange3.value)
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
 * 序号计算方法
 */
const indexMethod = (index) => {
  return index + 1
}

/**
 * 过滤后的表格数据
 */
const filteredTableData = computed(() => {
  let data = allTableData.value
  
  // 事件名模糊匹配筛选
  if (filterEventName.value && filterEventName.value.trim()) {
    const searchText = filterEventName.value.trim().toLowerCase()
    data = data.filter(row => {
      const trending = (row.trending || '').toLowerCase()
      return trending.includes(searchText)
    })
  }
  
  return data
})

/**
 * 获取时间戳（毫秒）
 */
const getTimestamp = (hoursAgo) => {
  const now = Date.now()
  return now - (hoursAgo * 60 * 60 * 1000)
}

/**
 * 保存时间范围到本地存储
 */
const saveTimeRangesToStorage = () => {
  try {
    const ranges = {
      timeRange1: timeRange1.value,
      timeRange2: timeRange2.value,
      timeRange3: timeRange3.value
    }
    localStorage.setItem('eventTaskInfo_timeRanges', JSON.stringify(ranges))
  } catch (e) {
    console.error('保存本地存储失败:', e)
  }
}

/**
 * 加载 exchangeConfig 配置
 */
const loadExchangeConfig = async () => {
  try {
    console.log('[事件任务信息] 开始加载 exchangeConfig 配置...')
    const response = await axios.get(`${API_BASE_URL}/mission/exchangeConfig`)
    
    if (response.data && response.data.code === 0 && response.data.data && response.data.data.configList) {
      const configList = response.data.data.configList
      
      // 创建 id -> trending 的映射
      const newIdToTrendingMap = new Map()
      for (const config of configList) {
        if (config.id && config.trending) {
          newIdToTrendingMap.set(String(config.id), config.trending.trim())
        }
      }
      idToTrendingMap.value = newIdToTrendingMap
      
      console.log(`[事件任务信息] exchangeConfig 配置加载完成，共 ${configList.length} 个配置`)
      return configList
    } else {
      console.warn('[事件任务信息] 未获取到 exchangeConfig 配置数据')
      return []
    }
  } catch (error) {
    console.error('[事件任务信息] 加载 exchangeConfig 配置失败:', error)
    return []
  }
}

/**
 * 加载数据
 */
const loadData = async () => {
  // 保存时间范围到本地存储
  saveTimeRangesToStorage()
  
  loading.value = true
  
  try {
    // 先加载 exchangeConfig 配置
    await loadExchangeConfig()
    
    const now = Date.now()
    
    // 并行调用3次接口，根据输入的3个时间范围获取数据
    const [data1, data2, data3] = await Promise.all([
      axios.get(`${API_BASE_URL}/data/volumeSum`, {
        params: {
          startTime: getTimestamp(timeRange1.value),
          endTime: now
        }
      }),
      axios.get(`${API_BASE_URL}/data/volumeSum`, {
        params: {
          startTime: getTimestamp(timeRange2.value),
          endTime: now
        }
      }),
      axios.get(`${API_BASE_URL}/data/volumeSum`, {
        params: {
          startTime: getTimestamp(timeRange3.value),
          endTime: now
        }
      })
    ])
    
    // 处理数据
    const list1 = data1.data?.data?.list || []
    const list2 = data2.data?.data?.list || []
    const list3 = data3.data?.data?.list || []
    
    // 创建以 trendingId 为key的映射
    const dataMap = new Map()
    
    // 处理第一个区间的数据
    list1.forEach(item => {
      const trendingId = item.trendingId ? String(item.trendingId) : ''
      if (!dataMap.has(trendingId)) {
        dataMap.set(trendingId, {
          trendingId: trendingId,
          trending: idToTrendingMap.value.get(trendingId) || `ID:${trendingId}`,
          openAmt1: 0,
          closeAmt1: 0,
          fullFillAmt1: 0,
          partFillAmt1: 0,
          openCount1: 0,
          closeCount1: 0,
          openAmt2: 0,
          closeAmt2: 0,
          fullFillAmt2: 0,
          partFillAmt2: 0,
          openCount2: 0,
          closeCount2: 0,
          openAmt3: 0,
          closeAmt3: 0,
          fullFillAmt3: 0,
          partFillAmt3: 0,
          openCount3: 0,
          closeCount3: 0
        })
      }
      const row = dataMap.get(trendingId)
      row.openAmt1 = parseFloat(item.openAmt) || 0
      row.closeAmt1 = parseFloat(item.closeAmt) || 0
      row.fullFillAmt1 = parseFloat(item.fullFillAmt) || 0
      row.partFillAmt1 = parseFloat(item.partFillAmt) || 0
      row.openCount1 = parseFloat(item.openCount) || 0
      row.closeCount1 = parseFloat(item.closeCount) || 0
    })
    
    // 处理第二个区间的数据
    list2.forEach(item => {
      const trendingId = item.trendingId ? String(item.trendingId) : ''
      if (!dataMap.has(trendingId)) {
        dataMap.set(trendingId, {
          trendingId: trendingId,
          trending: idToTrendingMap.value.get(trendingId) || `ID:${trendingId}`,
          openAmt1: 0,
          closeAmt1: 0,
          fullFillAmt1: 0,
          partFillAmt1: 0,
          openCount1: 0,
          closeCount1: 0,
          openAmt2: 0,
          closeAmt2: 0,
          fullFillAmt2: 0,
          partFillAmt2: 0,
          openCount2: 0,
          closeCount2: 0,
          openAmt3: 0,
          closeAmt3: 0,
          fullFillAmt3: 0,
          partFillAmt3: 0,
          openCount3: 0,
          closeCount3: 0
        })
      }
      const row = dataMap.get(trendingId)
      row.openAmt2 = parseFloat(item.openAmt) || 0
      row.closeAmt2 = parseFloat(item.closeAmt) || 0
      row.fullFillAmt2 = parseFloat(item.fullFillAmt) || 0
      row.partFillAmt2 = parseFloat(item.partFillAmt) || 0
      row.openCount2 = parseFloat(item.openCount) || 0
      row.closeCount2 = parseFloat(item.closeCount) || 0
    })
    
    // 处理第三个区间的数据
    list3.forEach(item => {
      const trendingId = item.trendingId ? String(item.trendingId) : ''
      if (!dataMap.has(trendingId)) {
        dataMap.set(trendingId, {
          trendingId: trendingId,
          trending: idToTrendingMap.value.get(trendingId) || `ID:${trendingId}`,
          openAmt1: 0,
          closeAmt1: 0,
          fullFillAmt1: 0,
          partFillAmt1: 0,
          openCount1: 0,
          closeCount1: 0,
          openAmt2: 0,
          closeAmt2: 0,
          fullFillAmt2: 0,
          partFillAmt2: 0,
          openCount2: 0,
          closeCount2: 0,
          openAmt3: 0,
          closeAmt3: 0,
          fullFillAmt3: 0,
          partFillAmt3: 0,
          openCount3: 0,
          closeCount3: 0
        })
      }
      const row = dataMap.get(trendingId)
      row.openAmt3 = parseFloat(item.openAmt) || 0
      row.closeAmt3 = parseFloat(item.closeAmt) || 0
      row.fullFillAmt3 = parseFloat(item.fullFillAmt) || 0
      row.partFillAmt3 = parseFloat(item.partFillAmt) || 0
      row.openCount3 = parseFloat(item.openCount) || 0
      row.closeCount3 = parseFloat(item.closeCount) || 0
    })
    
    // 转换为数组并按事件名排序
    const processedData = Array.from(dataMap.values())
    processedData.sort((a, b) => {
      const trendingA = a.trending || ''
      const trendingB = b.trending || ''
      return trendingA.localeCompare(trendingB)
    })
    
    // 保存到原始数据
    allTableData.value = processedData
    tableData.value = processedData
    
    ElMessage.success(`数据加载成功，共 ${processedData.length} 条记录`)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
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
.event-task-info-page {
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
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.time-range-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.time-range-selector > label {
  font-weight: 500;
  color: #333;
}

.time-inputs {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.time-input-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.time-input-item label {
  font-weight: 500;
  color: #666;
  font-size: 14px;
}

.time-unit {
  color: #666;
  font-size: 14px;
}

.filter-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
  white-space: nowrap;
}

.table-wrapper {
  background: white;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>