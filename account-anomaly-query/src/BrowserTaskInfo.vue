<template>
  <div class="browser-task-info-page">
    <h1 class="page-title">浏览器任务信息</h1>
    
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
          <label>浏览器ID筛选：</label>
          <el-input 
            v-model="filterBrowserId" 
            placeholder="例如：906 或 901,902,903 或 901-903"
            style="width: 250px;"
            clearable
          />
        </div>
        <div class="filter-item" style="margin-left: 15px;">
          <label>电脑组筛选：</label>
          <el-input 
            v-model="filterGroupNo" 
            placeholder="例如：27 或 27,28,29 或 27-29"
            style="width: 250px;"
            clearable
          />
        </div>
      </div>
    </div>

    <!-- 总计表（默认折叠） -->
    <el-collapse v-model="summaryCollapseActive" class="summary-collapse">
      <el-collapse-item name="summary" title="总计表（按电脑组汇总）">
        <div class="summary-table-wrapper">
          <el-table 
            :data="summaryTableData" 
            border 
            style="width: 100%"
            stripe
          >
            <el-table-column type="index" label="序号" width="80" align="center" :index="summaryIndexMethod" />
            
            <el-table-column prop="groupNo" label="电脑组" width="120" align="center" sortable />

            <!-- 第一个区间汇总 -->
            <el-table-column :label="range1Label" align="center" width="400">
              <el-table-column prop="succ1" label="成功次数" width="100" align="center" sortable />
              <el-table-column prop="fail1" label="失败次数" width="100" align="center" sortable />
              <el-table-column prop="successRate1" label="成功率" width="100" align="center" sortable>
                <template #default="scope">
                  {{ formatPercentage(scope.row.successRate1) }}
                </template>
              </el-table-column>
              <el-table-column prop="ipFail1" label="IP失败次数" width="100" align="center" sortable />
            </el-table-column>

            <!-- 第二个区间汇总 -->
            <el-table-column :label="range2Label" align="center" width="400">
              <el-table-column prop="succ2" label="成功次数" width="100" align="center" sortable />
              <el-table-column prop="fail2" label="失败次数" width="100" align="center" sortable />
              <el-table-column prop="successRate2" label="成功率" width="100" align="center" sortable>
                <template #default="scope">
                  {{ formatPercentage(scope.row.successRate2) }}
                </template>
              </el-table-column>
              <el-table-column prop="ipFail2" label="IP失败次数" width="100" align="center" sortable />
            </el-table-column>

            <!-- 第三个区间汇总 -->
            <el-table-column :label="range3Label" align="center" width="400">
              <el-table-column prop="succ3" label="成功次数" width="100" align="center" sortable />
              <el-table-column prop="fail3" label="失败次数" width="100" align="center" sortable />
              <el-table-column prop="successRate3" label="成功率" width="100" align="center" sortable>
                <template #default="scope">
                  {{ formatPercentage(scope.row.successRate3) }}
                </template>
              </el-table-column>
              <el-table-column prop="ipFail3" label="IP失败次数" width="100" align="center" sortable />
            </el-table-column>
          </el-table>
        </div>
      </el-collapse-item>
    </el-collapse>

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
        
        <el-table-column prop="number" label="浏览器ID" width="120" align="center" fixed sortable />
        
        <el-table-column prop="groupNo" label="电脑组" width="100" align="center" sortable />

        <!-- 第一个区间数据 -->
        <el-table-column :label="range1Label" align="center" width="400">
          <el-table-column prop="succ1" label="成功次数" width="100" align="center" sortable />
          <el-table-column prop="fail1" label="失败次数" width="100" align="center" sortable />
          <el-table-column prop="successRate1" label="成功率" width="100" align="center" sortable>
            <template #default="scope">
              {{ formatPercentage(scope.row.successRate1) }}
            </template>
          </el-table-column>
          <el-table-column prop="ipFail1" label="IP失败次数" width="100" align="center" sortable />
        </el-table-column>

        <!-- 第二个区间数据 -->
        <el-table-column :label="range2Label" align="center" width="400">
          <el-table-column prop="succ2" label="成功次数" width="100" align="center" sortable />
          <el-table-column prop="fail2" label="失败次数" width="100" align="center" sortable />
          <el-table-column prop="successRate2" label="成功率" width="100" align="center" sortable>
            <template #default="scope">
              {{ formatPercentage(scope.row.successRate2) }}
            </template>
          </el-table-column>
          <el-table-column prop="ipFail2" label="IP失败次数" width="100" align="center" sortable />
        </el-table-column>

        <!-- 第三个区间数据 -->
        <el-table-column :label="range3Label" align="center" width="400">
          <el-table-column prop="succ3" label="成功次数" width="100" align="center" sortable />
          <el-table-column prop="fail3" label="失败次数" width="100" align="center" sortable />
          <el-table-column prop="successRate3" label="成功率" width="100" align="center" sortable>
            <template #default="scope">
              {{ formatPercentage(scope.row.successRate3) }}
            </template>
          </el-table-column>
          <el-table-column prop="ipFail3" label="IP失败次数" width="100" align="center" sortable />
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
const filterBrowserId = ref('')
const filterGroupNo = ref('')
const summaryCollapseActive = ref([]) // 默认折叠，空数组表示不展开

// 从本地存储读取时间范围，如果没有则使用默认值
const loadTimeRangesFromStorage = () => {
  try {
    const saved = localStorage.getItem('browserTaskInfo_timeRanges')
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
 * 格式化百分比
 */
const formatPercentage = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '0.00%'
  return (value * 100).toFixed(2) + '%'
}

/**
 * 序号计算方法
 */
const indexMethod = (index) => {
  return index + 1
}

/**
 * 解析筛选条件
 * 支持格式：单个值（906）、多个值（901,902,903）、范围（901-903）
 */
const parseFilter = (filterValue) => {
  if (!filterValue || !filterValue.trim()) {
    return null // 空值表示不过滤
  }
  
  const value = filterValue.trim()
  const result = new Set()
  
  // 处理逗号分隔的多个值
  if (value.includes(',')) {
    const parts = value.split(',')
    parts.forEach(part => {
      const trimmed = part.trim()
      if (trimmed.includes('-')) {
        // 处理范围
        const [start, end] = trimmed.split('-').map(s => s.trim())
        const startNum = parseInt(start)
        const endNum = parseInt(end)
        if (!isNaN(startNum) && !isNaN(endNum)) {
          for (let i = startNum; i <= endNum; i++) {
            result.add(i.toString())
          }
        }
      } else {
        // 单个值
        const num = parseInt(trimmed)
        if (!isNaN(num)) {
          result.add(num.toString())
        }
      }
    })
  } else if (value.includes('-')) {
    // 处理范围
    const [start, end] = value.split('-').map(s => s.trim())
    const startNum = parseInt(start)
    const endNum = parseInt(end)
    if (!isNaN(startNum) && !isNaN(endNum)) {
      for (let i = startNum; i <= endNum; i++) {
        result.add(i.toString())
      }
    }
  } else {
    // 单个值
    const num = parseInt(value)
    if (!isNaN(num)) {
      result.add(num.toString())
    }
  }
  
  return result.size > 0 ? result : null
}

/**
 * 过滤后的表格数据
 */
const filteredTableData = computed(() => {
  let data = allTableData.value
  
  // 浏览器ID筛选
  const browserFilter = parseFilter(filterBrowserId.value)
  if (browserFilter) {
    data = data.filter(row => {
      const browserId = row.number ? row.number.toString() : ''
      return browserFilter.has(browserId)
    })
  }
  
  // 电脑组筛选
  const groupFilter = parseFilter(filterGroupNo.value)
  if (groupFilter) {
    data = data.filter(row => {
      const groupNo = row.groupNo ? row.groupNo.toString() : ''
      return groupFilter.has(groupNo)
    })
  }
  
  return data
})

/**
 * 总计表数据（按电脑组汇总）
 */
const summaryTableData = computed(() => {
  const groupMap = new Map()
  
  // 遍历所有数据，按电脑组汇总
  allTableData.value.forEach(row => {
    const groupNo = row.groupNo || ''
    
    if (!groupMap.has(groupNo)) {
      groupMap.set(groupNo, {
        groupNo: groupNo,
        succ1: 0,
        fail1: 0,
        ipFail1: 0,
        succ2: 0,
        fail2: 0,
        ipFail2: 0,
        succ3: 0,
        fail3: 0,
        ipFail3: 0
      })
    }
    
    const summary = groupMap.get(groupNo)
    summary.succ1 += row.succ1 || 0
    summary.fail1 += row.fail1 || 0
    summary.ipFail1 += row.ipFail1 || 0
    summary.succ2 += row.succ2 || 0
    summary.fail2 += row.fail2 || 0
    summary.ipFail2 += row.ipFail2 || 0
    summary.succ3 += row.succ3 || 0
    summary.fail3 += row.fail3 || 0
    summary.ipFail3 += row.ipFail3 || 0
  })
  
  // 转换为数组并计算成功率
  const result = Array.from(groupMap.values()).map(summary => {
    // 计算第一个区间成功率
    const total1 = summary.succ1 + summary.fail1
    summary.successRate1 = total1 > 0 ? summary.succ1 / total1 : 0
    
    // 计算第二个区间成功率
    const total2 = summary.succ2 + summary.fail2
    summary.successRate2 = total2 > 0 ? summary.succ2 / total2 : 0
    
    // 计算第三个区间成功率
    const total3 = summary.succ3 + summary.fail3
    summary.successRate3 = total3 > 0 ? summary.succ3 / total3 : 0
    
    return summary
  })
  
  // 按电脑组排序
  result.sort((a, b) => {
    const numA = parseInt(a.groupNo) || 0
    const numB = parseInt(b.groupNo) || 0
    return numA - numB
  })
  
  return result
})

/**
 * 总计表序号计算方法
 */
const summaryIndexMethod = (index) => {
  return index + 1
}

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
    localStorage.setItem('browserTaskInfo_timeRanges', JSON.stringify(ranges))
  } catch (e) {
    console.error('保存本地存储失败:', e)
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
    const now = Date.now()
    
    // 并行调用3次接口，根据输入的3个时间范围获取数据
    const [data1, data2, data3] = await Promise.all([
      axios.get(`${API_BASE_URL}/data/browserCount`, {
        params: {
          startTime: getTimestamp(timeRange1.value),
          endTime: now
        }
      }),
      axios.get(`${API_BASE_URL}/data/browserCount`, {
        params: {
          startTime: getTimestamp(timeRange2.value),
          endTime: now
        }
      }),
      axios.get(`${API_BASE_URL}/data/browserCount`, {
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
    
    // 创建以浏览器ID和组号为key的映射
    const dataMap = new Map()
    
    // 处理第一个区间的数据
    list1.forEach(item => {
      const key = `${item.number}_${item.groupNo}`
      if (!dataMap.has(key)) {
        dataMap.set(key, {
          number: item.number,
          groupNo: item.groupNo,
          succ1: 0,
          fail1: 0,
          ipFail1: 0,
          succ2: 0,
          fail2: 0,
          ipFail2: 0,
          succ3: 0,
          fail3: 0,
          ipFail3: 0
        })
      }
      const row = dataMap.get(key)
      row.succ1 = item.succ || 0
      row.fail1 = item.fail || 0
      row.ipFail1 = item.ipFail || 0
    })
    
    // 处理第二个区间的数据
    list2.forEach(item => {
      const key = `${item.number}_${item.groupNo}`
      if (!dataMap.has(key)) {
        dataMap.set(key, {
          number: item.number,
          groupNo: item.groupNo,
          succ1: 0,
          fail1: 0,
          ipFail1: 0,
          succ2: 0,
          fail2: 0,
          ipFail2: 0,
          succ3: 0,
          fail3: 0,
          ipFail3: 0
        })
      }
      const row = dataMap.get(key)
      row.succ2 = item.succ || 0
      row.fail2 = item.fail || 0
      row.ipFail2 = item.ipFail || 0
    })
    
    // 处理第三个区间的数据
    list3.forEach(item => {
      const key = `${item.number}_${item.groupNo}`
      if (!dataMap.has(key)) {
        dataMap.set(key, {
          number: item.number,
          groupNo: item.groupNo,
          succ1: 0,
          fail1: 0,
          ipFail1: 0,
          succ2: 0,
          fail2: 0,
          ipFail2: 0,
          succ3: 0,
          fail3: 0,
          ipFail3: 0
        })
      }
      const row = dataMap.get(key)
      row.succ3 = item.succ || 0
      row.fail3 = item.fail || 0
      row.ipFail3 = item.ipFail || 0
    })
    
    // 转换为数组并计算成功率
    const processedData = Array.from(dataMap.values()).map(row => {
      // 计算第一个区间成功率
      const total1 = row.succ1 + row.fail1
      row.successRate1 = total1 > 0 ? row.succ1 / total1 : 0
      
      // 计算第二个区间成功率
      const total2 = row.succ2 + row.fail2
      row.successRate2 = total2 > 0 ? row.succ2 / total2 : 0
      
      // 计算第三个区间成功率
      const total3 = row.succ3 + row.fail3
      row.successRate3 = total3 > 0 ? row.succ3 / total3 : 0
      
      return row
    })
    
    // 按浏览器ID排序
    processedData.sort((a, b) => {
      const numA = parseInt(a.number) || 0
      const numB = parseInt(b.number) || 0
      return numA - numB
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
.browser-task-info-page {
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

.summary-collapse {
  margin-bottom: 20px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.summary-table-wrapper {
  padding: 10px;
}

.table-wrapper {
  background: white;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
