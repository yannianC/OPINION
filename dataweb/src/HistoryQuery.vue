<template>
  <div class="history-query-page">
    <h1 class="page-title">历史查询</h1>
    
    <!-- 查询工具栏 -->
    <div class="toolbar">
      <el-date-picker
        v-model="historyDate"
        type="date"
        placeholder="选择日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        size="default"
        style="width: 160px"
      />
      <el-button type="primary" @click="loadHistoryData" :loading="loading" :disabled="!historyDate">
        查询历史
      </el-button>
    </div>

    <!-- 数据总计表格（默认折叠） -->
    <div class="summary-section">
      <div class="summary-header">
        <h2 class="summary-title">数据总计</h2>
        <el-button 
          type="text" 
          @click="summaryExpanded = !summaryExpanded"
          class="collapse-btn"
        >
          {{ summaryExpanded ? '收起' : '展开' }}
        </el-button>
      </div>
      
      <el-collapse-transition>
        <div v-show="summaryExpanded">
          <!-- 总计信息 -->
          <div class="summary-totals">
            <div class="total-item">
              <span class="total-label">余额总计:</span>
              <span class="total-value">{{ formatNumber(summaryTotals.totalBalance) }}</span>
            </div>
            <div class="total-item">
              <span class="total-label">Portfolio总计:</span>
              <span class="total-value">{{ formatNumber(summaryTotals.totalPortfolio) }}</span>
            </div>
          </div>
          
          <el-table 
            :data="eventTableData" 
            border 
            style="width: 100%"
            v-loading="loading"
            max-height="500px"
          >
            <el-table-column prop="eventName" label="事件名" width="400" fixed>
              <template #default="scope">
                <div class="event-name-cell">{{ scope.row.eventName }}</div>
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

            <el-table-column label="实际差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.actualDiff, b.actualDiff)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.actualDiff) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.actualDiff) }}
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
          </el-table>
        </div>
      </el-collapse-transition>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-container">
      <div class="filter-row">
        <div class="filter-item">
          <label>电脑组:</label>
          <el-input 
            v-model="filters.computeGroup" 
            placeholder="如: 1 或 1,2,3 或 1-3"
            clearable
            size="small"
            style="width: 200px"
          />
        </div>
        <div class="filter-item">
          <label>浏览器编号:</label>
          <el-input 
            v-model="filters.fingerprintNo" 
            placeholder="如: 4001 或 4001,4002 或 4001-4010"
            clearable
            size="small"
            style="width: 250px"
          />
        </div>
        <div class="filter-item">
          <label>平台:</label>
          <el-select 
            v-model="filters.platform" 
            placeholder="全部"
            clearable
            size="small"
            style="width: 120px"
          >
            <el-option label="OP" value="OP" />
            <el-option label="监控" value="监控" />
          </el-select>
        </div>
        <div class="filter-item">
          <label>仓位搜索:</label>
          <el-input 
            v-model="filters.positionSearch" 
            placeholder="搜索持有仓位或挂单名称"
            clearable
            size="small"
            style="width: 250px"
          />
        </div>
        <div class="filter-item">
          <label>余额范围:</label>
          <el-input 
            v-model="filters.balanceMin" 
            placeholder="最小值"
            clearable
            size="small"
            style="width: 120px"
            type="number"
          />
          <span style="margin: 0 8px; color: #666;">-</span>
          <el-input 
            v-model="filters.balanceMax" 
            placeholder="最大值"
            clearable
            size="small"
            style="width: 120px"
            type="number"
          />
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showNoAddress" @change="applyFilters">
            显示无地址
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showDuplicateAddress" @change="applyFilters">
            显示地址重复
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showNoPoints" @change="applyFilters">
            显示无积分
          </el-checkbox>
        </div>
        <div class="filter-item">
          <label>打开时间大于:</label>
          <el-input 
            v-model.number="filters.openTimeGreaterThanHours" 
            placeholder="小时数"
            clearable
            size="small"
            style="width: 120px"
            type="number"
            min="0"
          />
          <span style="margin-left: 5px; color: #666;">小时</span>
        </div>
        <el-button type="primary" size="small" @click="applyFilters">应用筛选</el-button>
        <el-button size="small" @click="clearFilters">清除筛选</el-button>
        <el-button type="warning" size="small" @click="parseAllRows" :loading="parsingAll">
          全部解析
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="paginatedTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 600px)"
      :scrollbar-always-on="true"
    >
      <el-table-column prop="index" label="序号" width="80" align="center" fixed />
      
      <el-table-column label="电脑组" width="100" align="center" sortable :sort-method="(a, b) => sortByNumber(a.computeGroup, b.computeGroup)">
        <template #default="scope">
          {{ scope.row.computeGroup }}
        </template>
      </el-table-column>

      <el-table-column label="指纹浏览器编号" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.fingerprintNo, b.fingerprintNo)">
        <template #default="scope">
          {{ scope.row.fingerprintNo }}
        </template>
      </el-table-column>

      <el-table-column label="余额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.balance, b.balance)">
        <template #default="scope">
          {{ formatNumber(scope.row.balance) }}
        </template>
      </el-table-column>

      <el-table-column label="Portfolio" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.c, b.c)">
        <template #default="scope">
          {{ scope.row.c || '0' }}
        </template>
      </el-table-column>

      <el-table-column label="持有仓位" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && scope.row.a" class="position-list">
            <div 
              v-for="(pos, idx) in getCachedPositions(scope.row.a)" 
              :key="`${scope.row.index}-pos-${idx}`" 
              class="position-item"
            >
              <div class="position-title">{{ pos.title }}</div>
              <div class="position-details">
                <el-tag :type="pos.amount >= 0 ? 'success' : 'danger'" size="small">
                  {{ pos.option || (pos.amount >= 0 ? 'YES' : 'NO') }}
                </el-tag>
                <span class="position-amount">数量: {{ pos.amount }}</span>
                <span v-if="pos.avgPrice" class="position-price">均价: {{ pos.avgPrice }}</span>
              </div>
            </div>
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div v-else-if="scope.row.a" class="raw-data-text">
            {{ scope.row.a }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="挂单仓位" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && scope.row.b" class="position-list">
            <div 
              v-for="(order, idx) in getCachedOrders(scope.row.b)" 
              :key="`${scope.row.index}-order-${idx}`" 
              class="position-item"
            >
              <div class="position-title">{{ order.title }}</div>
              <div class="position-details">
                <el-tag :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" size="small">
                  {{ order.option || order.buySellDirection }}
                </el-tag>
                <span class="position-amount">未成交: {{ formatNumber(order.pending) }}</span>
                <span class="position-price">价格: {{ order.price }}</span>
              </div>
            </div>
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div v-else-if="scope.row.b" class="raw-data-text">
            {{ scope.row.b }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="仓位抓取时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.d, b.d)">
        <template #default="scope">
          {{ formatTime(scope.row.d) }}
        </template>
      </el-table-column>

      <el-table-column label="打开时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.f, b.f)">
        <template #default="scope">
          {{ formatTime(scope.row.f) }}
        </template>
      </el-table-column>

      <el-table-column label="积分" width="400">
        <template #default="scope">
          <div v-if="scope.row.k" class="raw-data-text">
            {{ scope.row.k }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="scope">
          <el-button 
            type="warning" 
            size="small"
            @click="parseRow(scope.row)"
            :loading="scope.row.parsing"
            :disabled="isRowParsed(scope.row)"
          >
            {{ isRowParsed(scope.row) ? '已解析' : '解析' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页组件 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPageNum"
        :page-size="pageSize"
        :total="filteredTableData.length"
        layout="total, prev, pager, next, jumper"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'

const loading = ref(false)
const historyDate = ref(null)
const summaryExpanded = ref(false)
const parsingAll = ref(false)
const currentPageNum = ref(1)
const pageSize = 50

// 表格数据
const tableData = shallowRef([])
const parsedDataCache = new Map()
const parsedRowsSet = ref(new Set())

// 筛选
const filters = ref({
  computeGroup: '',
  fingerprintNo: '',
  platform: '',
  positionSearch: '',
  balanceMin: '',
  balanceMax: '',
  showNoAddress: false,
  showDuplicateAddress: false,
  showNoPoints: false,
  openTimeGreaterThanHours: null  // 打开时间大于X小时
})

// 事件统计数据
const eventTableData = ref([])

// 总计数据
const summaryTotals = ref({
  totalBalance: 0,
  totalPortfolio: 0
})

/**
 * 解析筛选条件的电脑组和浏览器编号
 */
const parseFilterValues = (value) => {
  if (!value) return []
  const result = new Set()
  const parts = value.split(/[,;，；]/)
  
  for (const part of parts) {
    const trimmed = part.trim()
    if (!trimmed) continue
    
    // 检查是否是范围格式（如：1-3 或 4001-4010）
    const rangeMatch = trimmed.match(/^(\d+)-(\d+)$/)
    if (rangeMatch) {
      const start = parseInt(rangeMatch[1])
      const end = parseInt(rangeMatch[2])
      if (start <= end) {
        for (let i = start; i <= end; i++) {
          result.add(String(i))
        }
      }
    } else {
      result.add(trimmed)
    }
  }
  
  return Array.from(result)
}

/**
 * 过滤后的表格数据
 */
const filteredTableData = computed(() => {
  const data = tableData.value
  const filterVals = filters.value
  
  // 计算地址重复情况
  const addressCountMap = new Map()
  if (filterVals.showDuplicateAddress) {
    for (const row of data) {
      if (row.h && row.h.trim()) {
        const address = row.h.trim()
        addressCountMap.set(address, (addressCountMap.get(address) || 0) + 1)
      }
    }
  }
  
  const computeGroups = parseFilterValues(filterVals.computeGroup)
  const fingerprintNos = parseFilterValues(filterVals.fingerprintNo)
  const computeGroupSet = new Set(computeGroups)
  const fingerprintNoSet = new Set(fingerprintNos)
  const searchTerm = filterVals.positionSearch ? filterVals.positionSearch.toLowerCase() : ''
  
  const hasFilters = computeGroups.length > 0 || 
                    fingerprintNos.length > 0 || 
                    filterVals.platform || 
                    filterVals.positionSearch ||
                    filterVals.balanceMin ||
                    filterVals.balanceMax ||
                    filterVals.showNoAddress ||
                    filterVals.showDuplicateAddress ||
                    filterVals.showNoPoints ||
                    (filterVals.openTimeGreaterThanHours !== null && filterVals.openTimeGreaterThanHours !== undefined && filterVals.openTimeGreaterThanHours !== '')
  
  if (!hasFilters) {
    return data
  }
  
  return data.filter(row => {
    // 电脑组筛选
    if (computeGroupSet.size > 0 && !computeGroupSet.has(String(row.computeGroup))) {
      return false
    }
    
    // 浏览器编号筛选
    if (fingerprintNoSet.size > 0 && !fingerprintNoSet.has(String(row.fingerprintNo))) {
      return false
    }
    
    // 平台筛选
    if (filterVals.platform && row.platform !== filterVals.platform) {
      return false
    }
    
    // 仓位搜索筛选
    if (searchTerm) {
      const hasMatch = (row.a && row.a.toLowerCase().includes(searchTerm)) ||
                      (row.b && row.b.toLowerCase().includes(searchTerm))
      if (!hasMatch) {
        return false
      }
    }
    
    // 余额范围筛选
    if (filterVals.balanceMin || filterVals.balanceMax) {
      const balance = parseFloat(row.balance) || 0
      if (filterVals.balanceMin && balance < parseFloat(filterVals.balanceMin)) {
        return false
      }
      if (filterVals.balanceMax && balance > parseFloat(filterVals.balanceMax)) {
        return false
      }
    }
    
    // 显示无地址筛选
    if (filterVals.showNoAddress) {
      if (row.h && row.h.trim()) {
        return false
      }
    }
    
    // 显示地址重复筛选
    if (filterVals.showDuplicateAddress) {
      if (!row.h || !row.h.trim()) {
        return false
      }
      const address = row.h.trim()
      const count = addressCountMap.get(address) || 0
      if (count <= 1) {
        return false
      }
    }
    
    // 显示无积分筛选
    if (filterVals.showNoPoints) {
      if (row.k && row.k.trim()) {
        return false
      }
    }
    
    // 打开时间大于X小时筛选
    if (filterVals.openTimeGreaterThanHours !== null && filterVals.openTimeGreaterThanHours !== undefined && filterVals.openTimeGreaterThanHours !== '') {
      if (!row.f) {
        return false  // 没有打开时间的数据不显示
      }
      const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
      const now = Date.now()
      const hoursAgo = parseFloat(filterVals.openTimeGreaterThanHours)
      const thresholdTime = now - (hoursAgo * 60 * 60 * 1000)  // 转换为毫秒
      
      // 如果打开时间大于阈值时间（即打开时间更早），则显示
      if (openTime > thresholdTime) {
        return false  // 打开时间不够早，不显示
      }
    }
    
    return true
  })
})

/**
 * 分页后的表格数据
 */
const paginatedTableData = computed(() => {
  const filtered = filteredTableData.value
  const start = (currentPageNum.value - 1) * pageSize
  const end = start + pageSize
  return filtered.slice(start, end)
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
 * 格式化时间
 */
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
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
 * 解析持仓数据字符串
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
 * 解析挂单数据字符串
 */
const parseOrders = (ordersStr) => {
  if (!ordersStr) return []
  
  try {
    const orders = []
    const items = ordersStr.split(';')
    
    for (const item of items) {
      if (!item.trim()) continue
      
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 5) {
          const title = parts[0].trim()
          const buySellDirection = parts[1].trim()
          const option = parts[2].trim()
          const price = parts[3].trim()
          const progress = parts[4].trim()
          
          let pending = 0
          const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
          if (progressMatch) {
            const filled = parseFloat(progressMatch[1].replace(/,/g, '')) || 0
            const total = parseFloat(progressMatch[2].replace(/,/g, '')) || 0
            pending = total - filled
          }
          
          orders.push({
            title: title,
            buySellDirection: buySellDirection,
            option: option,
            price: price,
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
 * 获取缓存的持仓数据
 */
const getCachedPositions = (posStr) => {
  if (!posStr) return []
  if (parsedDataCache.has(posStr)) {
    return parsedDataCache.get(posStr)
  }
  const parsed = parsePositions(posStr)
  parsedDataCache.set(posStr, parsed)
  return parsed
}

/**
 * 获取缓存的挂单数据
 */
const getCachedOrders = (ordersStr) => {
  if (!ordersStr) return []
  const cacheKey = `order_${ordersStr}`
  if (parsedDataCache.has(cacheKey)) {
    return parsedDataCache.get(cacheKey)
  }
  const parsed = parseOrders(ordersStr)
  parsedDataCache.set(cacheKey, parsed)
  return parsed
}

/**
 * 检查行是否已解析
 */
const isRowParsed = (row) => {
  return parsedRowsSet.value.has(row.index)
}

/**
 * 解析单行数据
 */
const parseRow = async (row) => {
  row.parsing = true
  try {
    // 预解析持仓和挂单数据
    if (row.a) {
      getCachedPositions(row.a)
    }
    if (row.b) {
      getCachedOrders(row.b)
    }
    parsedRowsSet.value.add(row.index)
  } catch (error) {
    console.error('解析失败:', error)
    ElMessage.error('解析失败')
  } finally {
    row.parsing = false
  }
}

/**
 * 解析所有行
 */
const parseAllRows = async () => {
  parsingAll.value = true
  try {
    const data = filteredTableData.value
    for (const row of data) {
      if (!isRowParsed(row)) {
        await parseRow(row)
      }
    }
    ElMessage.success('全部解析完成')
  } catch (error) {
    console.error('批量解析失败:', error)
    ElMessage.error('批量解析失败')
  } finally {
    parsingAll.value = false
  }
}

/**
 * 应用筛选
 */
const applyFilters = () => {
  currentPageNum.value = 1
}

/**
 * 清除筛选
 */
const clearFilters = () => {
  filters.value = {
    computeGroup: '',
    fingerprintNo: '',
    platform: '',
    positionSearch: '',
    balanceMin: '',
    balanceMax: '',
    showNoAddress: false,
    showDuplicateAddress: false,
    showNoPoints: false,
    openTimeGreaterThanHours: null
  }
  currentPageNum.value = 1
}

/**
 * 分页改变
 */
const handlePageChange = (page) => {
  currentPageNum.value = page
}

/**
 * 计算事件统计数据
 */
const calculateEventStats = (data) => {
  const eventMap = new Map()
  
  for (const row of data) {
    // 解析持仓数据
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
        
        let isYes = false
        let isNo = false
        
        if (eventName.includes('First to 5k')) {
          if (pos.option === 'GOLD') {
            isYes = true
          } else if (pos.option === 'ETH') {
            isNo = true
          }
        } else if (eventName.includes('Monad vs MegaETH')) {
          if (pos.option === 'Monad') {
            isYes = true
          } else if (pos.option === 'MegaETH') {
            isNo = true
          }
        } else {
          if (pos.option === 'YES' || (pos.amount >= 0 && !pos.option)) {
            isYes = true
          } else if (pos.option === 'NO' || pos.amount < 0) {
            isNo = true
          }
        }
        
        if (isYes) {
          event.yesPosition += amount
        } else if (isNo) {
          event.noPosition += amount
        }
      }
    }
    
    // 解析挂单数据
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
        
        let isYes = false
        let isNo = false
        
        if (eventName.includes('First to 5k')) {
          if (order.option === 'GOLD') {
            isYes = true
          } else if (order.option === 'ETH') {
            isNo = true
          }
        } else if (eventName.includes('Monad vs MegaETH')) {
          if (order.option === 'Monad') {
            isYes = true
          } else if (order.option === 'MegaETH') {
            isNo = true
          }
        } else {
          if (order.option === 'YES') {
            isYes = true
          } else if (order.option === 'NO') {
            isNo = true
          }
        }
        
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
    event.actualDiff = event.yesPosition - event.noPosition
    event.orderDiff = event.orderYes - event.orderNo
    event.finalDiff = event.actualDiff + event.orderDiff
  }
  
  // 转换为数组并排序
  return Array.from(eventMap.values()).sort((a, b) => {
    return Math.abs(b.finalDiff) - Math.abs(a.finalDiff)
  })
}

/**
 * 计算总计数据（余额总计和Portfolio总计）
 */
const calculateSummaryTotals = (data) => {
  let totalBalance = 0
  let totalPortfolio = 0
  
  for (const row of data) {
    totalBalance += parseFloat(row.balance) || 0
    totalPortfolio += parseFloat(row.c) || 0
  }
  
  summaryTotals.value = {
    totalBalance: totalBalance,
    totalPortfolio: totalPortfolio
  }
}

/**
 * 加载历史数据
 */
const loadHistoryData = async () => {
  if (!historyDate.value) {
    ElMessage.warning('请先选择日期')
    return
  }
  
  loading.value = true
  
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigHist?dateStr=${historyDate.value}`)
    
    if (response.data && response.data.data) {
      const serverData = response.data.data
      
      // 格式化数据
      const formattedData = serverData.map((item, index) => ({
        ...item,
        index: index + 1,
        platform: item.e || item.platform || 'OP',
        parsing: false
      }))
      
      tableData.value = formattedData
      parsedDataCache.clear()
      parsedRowsSet.value = new Set()
      currentPageNum.value = 1
      
      // 计算事件统计数据
      eventTableData.value = calculateEventStats(serverData)
      
      // 计算总计数据
      calculateSummaryTotals(serverData)
      
      ElMessage.success(`已加载 ${historyDate.value} 的历史数据，共 ${serverData.length} 条`)
    } else {
      ElMessage.warning('未获取到历史数据')
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
    ElMessage.error('加载历史数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.history-query-page {
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
  gap: 10px;
  align-items: center;
}

.summary-section {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.summary-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.collapse-btn {
  padding: 0;
  font-size: 14px;
}

.filter-container {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.position-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.position-item {
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.position-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  word-break: break-word;
}

.position-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.position-amount {
  font-size: 12px;
  color: #666;
}

.position-price {
  font-size: 12px;
  color: #999;
}

.raw-data-text {
  font-size: 12px;
  color: #666;
  word-break: break-word;
  white-space: pre-wrap;
}

.empty-text {
  color: #999;
  font-style: italic;
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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.summary-totals {
  display: flex;
  gap: 30px;
  padding: 15px 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 15px;
  border: 1px solid #e4e7ed;
}

.total-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.total-label {
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.total-value {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}
</style>

