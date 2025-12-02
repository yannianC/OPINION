<template>
  <div class="app-container">
    <h1 class="app-title">PLOY/OP数据</h1>
    
    <!-- 顶部操作按钮 -->
    <div class="toolbar">
      <el-button type="primary" @click="addRows(1)">增加一行</el-button>
      <el-button type="primary" @click="addRows(10)">增加十行</el-button>
      <el-button type="success" @click="saveAll" :loading="saving">保存所有数据</el-button>
      <el-button type="info" @click="loadData" :loading="loading">刷新列表</el-button>
      
      <!-- 自动刷新控制 -->
      <div class="auto-refresh-control">
        <el-checkbox v-model="autoRefresh.enabled" @change="toggleAutoRefresh">
          自动刷新
        </el-checkbox>
        <el-input 
          v-model.number="autoRefresh.interval" 
          type="number"
          size="small"
          style="width: 80px"
          min="10"
          @blur="resetAutoRefresh"
        />
        <span>秒</span>
      </div>
      
      <el-button type="warning" @click="refreshAllPositions" :loading="refreshingAll">
        刷新全部仓位
      </el-button>
      <el-button type="danger" @click="refreshRedPositions" :loading="refreshingRed">
        刷新变红仓位
      </el-button>
    </div>
    
    <!-- 批量添加区域 -->
    <div class="batch-add-container">
      <div class="batch-add-row">
        <label>批量添加:</label>
        <el-input 
          v-model="batchAddInput" 
          placeholder="格式: 1,4001;2,4002;3,4003,4004,4005"
          clearable
          size="small"
          style="width: 500px"
        />
        <el-button type="primary" size="small" @click="batchAddAccounts">
          确认添加
        </el-button>
        <span class="batch-add-tip">（电脑组,浏览器ID;电脑组,浏览器ID...）</span>
      </div>
    </div>

    <!-- 仓位时间配置区域 -->
    <div class="position-time-config-container">
      <div class="config-row">
        <label>忽略仓位时间的浏览器:</label>
        <el-input 
          v-model="positionTimeConfig.ignoredBrowsers" 
          placeholder="浏览器编号，逗号分隔，如: 4001,4002,4003"
          clearable
          size="small"
          style="width: 700px"
        />
        <el-button type="primary" size="small" @click="saveIgnoredBrowsers">
          确定并保存
        </el-button>
      </div>
      <div class="config-row">
        <el-checkbox v-model="positionTimeConfig.autoUpdate" @change="toggleAutoUpdate">
          自动更新打开时间大于最近
        </el-checkbox>
        <el-input 
          v-model.number="positionTimeConfig.updateThresholdMinutes" 
          type="number"
          size="small"
          style="width: 80px"
          min="1"
        />
        <span>分钟的仓位</span>
      </div>
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
            <el-option label="Ploy" value="Ploy" />
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
        <el-button type="primary" size="small" @click="applyFilters">应用筛选</el-button>
        <el-button size="small" @click="clearFilters">清除筛选</el-button>
      </div>
    </div>

    <!-- 总计信息 -->
    <div class="summary-container" :class="{ 'collapsed': summaryCollapsed }">
      <div class="summary-header">
        <h3 class="summary-title">📊 数据总计</h3>
        <el-button 
          :icon="summaryCollapsed ? ArrowDown : ArrowUp" 
          circle 
          size="small"
          @click="summaryCollapsed = !summaryCollapsed"
          class="collapse-btn"
        >
        </el-button>
      </div>
      
      <transition name="summary-collapse">
        <div v-show="!summaryCollapsed" class="summary-content">
          <div class="summary-item">
            <span class="summary-label">余额总计:</span>
            <span class="summary-value">{{ summaryData.totalBalance }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Portfolio总计:</span>
            <span class="summary-value">{{ summaryData.totalPortfolio }}</span>
          </div>
          <div class="summary-item summary-positions">
            <span class="summary-label">持有仓位总计:</span>
            <div class="summary-positions-list">
              <div v-if="summaryData.positionSummary.length === 0" class="empty-summary">
                无持仓
              </div>
              <div 
                v-for="(pos, idx) in summaryData.positionSummary" 
                :key="idx" 
                class="summary-position-item"
              >
                <span class="position-title-summary">{{ pos.title }}</span>
                <el-tag 
                  :type="parseFloat(pos.amount) >= 0 ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ pos.amount }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="filteredTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      :row-class-name="getRowClassName"
    >
      <el-table-column prop="index" label="序号" width="80" align="center" fixed />
      
      <el-table-column label="电脑组" width="100" align="center" sortable :sort-method="(a, b) => sortByNumber(a.computeGroup, b.computeGroup)">
        <template #default="scope">
          <el-input 
            v-model="scope.row.computeGroup" 
            placeholder="电脑组"
            size="small"
            @blur="saveRowData(scope.row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="指纹浏览器编号" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.fingerprintNo, b.fingerprintNo)">
        <template #default="scope">
          <el-input 
            v-model="scope.row.fingerprintNo" 
            placeholder="浏览器编号"
            size="small"
            @blur="saveRowData(scope.row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="平台" width="120" align="center">
        <template #default="scope">
          <el-select 
            v-model="scope.row.platform" 
            placeholder="选择平台"
            size="small"
            @change="saveRowData(scope.row)"
          >
            <el-option label="OP" value="OP" />
            <el-option label="Ploy" value="Ploy" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="余额 (Balance)" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.balance, b.balance)">
        <template #default="scope">
          <span>{{ formatNumber(scope.row.balance) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="Portfolio" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.c, b.c)">
        <template #default="scope">
          <span>{{ formatNumber(scope.row.c) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="持有仓位 (a)" width="400">
        <template #default="scope">
          <div class="position-list" v-if="scope.row.a">
            <div 
              v-for="(pos, idx) in parsePositions(scope.row.a)" 
              :key="idx" 
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
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="挂单仓位 (b)" width="400">
        <template #default="scope">
          <div class="position-list" v-if="scope.row.b">
            <div 
              v-for="(order, idx) in parseOpenOrders(scope.row.b)" 
              :key="idx" 
              class="position-item"
            >
              <div class="position-title">{{ order.title }}</div>
              <div class="position-details">
                <span class="position-price">{{ order.price }}</span>
                <span class="position-amount">{{ order.progress }}</span>
              </div>
            </div>
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="仓位抓取时间(d)" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.d, b.d)">
        <template #default="scope">
          <div class="capture-time-cell">
            <el-icon><Clock /></el-icon>
            <span>{{ formatRelativeTime(scope.row.d) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="打开时间(f)" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.f, b.f)">
        <template #default="scope">
          <div class="capture-time-cell">
            <el-icon><Clock /></el-icon>
            <span>{{ formatRelativeTime(scope.row.f) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="450" align="center" fixed="right">
        <template #default="scope">
          <el-button 
            type="primary" 
            size="small"
            @click="refreshPosition(scope.row)"
            :loading="scope.row.refreshing"
          >
            刷新仓位
          </el-button>
          <el-button 
            type="info" 
            size="small"
            @click="showTransactions(scope.row)"
            :disabled="!scope.row.g"
          >
            交易记录
          </el-button>
          <el-button 
            type="success" 
            size="small"
            @click="showMissionLog()"
            :disabled="!latestMissionId"
          >
            日志
          </el-button>
          <el-button 
            type="danger" 
            size="small"
            @click="deleteAccount(scope.row)"
            :disabled="!scope.row.id"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 交易记录弹窗 -->
    <el-dialog 
      v-model="transactionDialogVisible" 
      title="交易记录" 
      width="90%"
      :close-on-click-modal="false"
    >
      <div v-if="currentTransactions.length === 0" class="empty-message">
        暂无交易记录
      </div>
      <el-table 
        v-else
        :data="currentTransactions" 
        border 
        style="width: 100%"
        :max-height="500"
      >
        <el-table-column prop="index" label="序号" width="70" align="center" />
        <el-table-column prop="title" label="主题" min-width="250" />
        <el-table-column prop="direction" label="方向" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.direction === 'Buy' ? 'success' : 'danger'" size="small">
              {{ scope.row.direction === 'Buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="option" label="选项" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.option === 'YES' ? 'success' : 'warning'" size="small">
              {{ scope.row.option }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="数量" width="120" align="center" />
        <el-table-column prop="value" label="金额" width="120" align="center" />
        <el-table-column prop="price" label="价格" width="120" align="center" />
        <el-table-column prop="time" label="时间" min-width="180" align="center" />
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="transactionDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务日志弹窗 -->
    <el-dialog 
      v-model="missionLogDialogVisible" 
      title="任务执行日志" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-loading="loadingMissionStatus" class="mission-log-content">
        <div class="log-item">
          <span class="log-label">任务ID:</span>
          <span class="log-value">{{ latestMissionId || '暂无' }}</span>
        </div>
        <div class="log-item">
          <span class="log-label">状态:</span>
          <el-tag 
            :type="getMissionStatusType(missionStatus.status)" 
            size="large"
          >
            {{ getMissionStatusText(missionStatus.status) }}
          </el-tag>
        </div>
        <div class="log-item" v-if="missionStatus.msg">
          <span class="log-label">消息:</span>
          <span class="log-value">{{ missionStatus.msg }}</span>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="missionLogDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="refreshMissionStatus" :loading="loadingMissionStatus">
            刷新状态
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import axios from 'axios'

/**
 * 基础配置
 */
const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'

/**
 * 响应式数据
 */
const tableData = ref([])
const loading = ref(false)
const saving = ref(false)
const refreshingAll = ref(false)
const refreshingRed = ref(false)  // 刷新变红仓位的加载状态
const summaryCollapsed = ref(false)  // 总计区域折叠状态
let nextId = 1

/**
 * 任务日志相关
 */
const latestMissionId = ref(null)  // 最新的任务ID
const missionLogDialogVisible = ref(false)  // 任务日志弹窗显示状态
const loadingMissionStatus = ref(false)  // 加载任务状态的loading
const missionStatus = ref({
  status: null,
  msg: ''
})

/**
 * 交易记录弹窗相关
 */
const transactionDialogVisible = ref(false)
const currentTransactions = ref([])

/**
 * 自动刷新相关
 */
const autoRefresh = ref({
  enabled: true,  // 默认开启
  interval: 60
})
let autoRefreshTimer = null

/**
 * 批量添加相关
 */
const batchAddInput = ref('')

/**
 * 本地新增的行（未保存到服务器的）
 */
const localNewRows = ref(new Set())

/**
 * 筛选条件
 */
const filters = ref({
  computeGroup: '',
  fingerprintNo: '',
  platform: '',
  positionSearch: ''  // 新增：仓位搜索
})

const activeFilters = ref({
  computeGroup: [],
  fingerprintNo: [],
  platform: '',
  positionSearch: ''  // 新增：仓位搜索
})

/**
 * 仓位时间配置
 */
const positionTimeConfig = ref({
  ignoredBrowsers: '',  // 忽略的浏览器编号
  autoUpdate: false,  // 是否自动更新
  updateThresholdMinutes: 30  // 更新阈值（分钟）
})
let autoUpdateTimer = null

/**
 * 解析输入值（支持单个、逗号分隔、区间）
 * 例如: "1" 或 "1,2,3" 或 "1-3"
 */
const parseInputValues = (input) => {
  if (!input || !input.trim()) return []
  
  const values = new Set()
  const parts = input.split(',').map(p => p.trim())
  
  for (const part of parts) {
    if (part.includes('-')) {
      // 区间: 1-3
      const [start, end] = part.split('-').map(v => parseInt(v.trim()))
      if (!isNaN(start) && !isNaN(end)) {
        for (let i = Math.min(start, end); i <= Math.max(start, end); i++) {
          values.add(i.toString())
        }
      }
    } else {
      // 单个值
      values.add(part)
    }
  }
  
  return Array.from(values)
}

/**
 * 应用筛选
 */
const applyFilters = () => {
  activeFilters.value = {
    computeGroup: parseInputValues(filters.value.computeGroup),
    fingerprintNo: parseInputValues(filters.value.fingerprintNo),
    platform: filters.value.platform,
    positionSearch: filters.value.positionSearch.trim()
  }
  ElMessage.success('筛选已应用')
}

/**
 * 清除筛选
 */
const clearFilters = () => {
  filters.value = {
    computeGroup: '',
    fingerprintNo: '',
    platform: '',
    positionSearch: ''
  }
  activeFilters.value = {
    computeGroup: [],
    fingerprintNo: [],
    platform: '',
    positionSearch: ''
  }
  ElMessage.info('筛选已清除')
}

/**
 * 过滤后的表格数据
 */
const filteredTableData = computed(() => {
  let result = tableData.value
  
  // 电脑组筛选
  if (activeFilters.value.computeGroup.length > 0) {
    result = result.filter(row => 
      activeFilters.value.computeGroup.includes(String(row.computeGroup))
    )
  }
  
  // 浏览器编号筛选
  if (activeFilters.value.fingerprintNo.length > 0) {
    result = result.filter(row => 
      activeFilters.value.fingerprintNo.includes(String(row.fingerprintNo))
    )
  }
  
  // 平台筛选
  if (activeFilters.value.platform) {
    result = result.filter(row => row.platform === activeFilters.value.platform)
  }
  
  // 仓位搜索筛选
  if (activeFilters.value.positionSearch) {
    const searchTerm = activeFilters.value.positionSearch.toLowerCase()
    result = result.filter(row => {
      // 检查持有仓位 (a)
      if (row.a && row.a.toLowerCase().includes(searchTerm)) {
        return true
      }
      // 检查挂单仓位 (b)
      if (row.b && row.b.toLowerCase().includes(searchTerm)) {
        return true
      }
      return false
    })
  }
  
  // 排序：打开时间>仓位时间的置顶（排除忽略的浏览器）
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  result = result.sort((a, b) => {
    const aIgnored = ignoredBrowsersSet.has(String(a.fingerprintNo))
    const bIgnored = ignoredBrowsersSet.has(String(b.fingerprintNo))
    
    // 检查打开时间是否大于仓位时间
    const aOpenTimeGreater = !aIgnored && shouldHighlightRow(a)
    const bOpenTimeGreater = !bIgnored && shouldHighlightRow(b)
    
    // 打开时间>仓位时间的排在前面
    if (aOpenTimeGreater && !bOpenTimeGreater) return -1
    if (!aOpenTimeGreater && bOpenTimeGreater) return 1
    
    // 其他保持原顺序
    return 0
  })
  
  return result
})

/**
 * 计算总计数据
 */
const summaryData = computed(() => {
  const filtered = filteredTableData.value
  
  // 计算余额总计
  const totalBalance = filtered.reduce((sum, row) => {
    const balance = parseFloat(row.balance) || 0
    return sum + balance
  }, 0)
  
  // 计算Portfolio总计
  const totalPortfolio = filtered.reduce((sum, row) => {
    const portfolio = parseFloat(row.c) || 0
    return sum + portfolio
  }, 0)
  
  // 计算持有仓位总计（按标题分组）
  const positionMap = new Map()
  
  filtered.forEach(row => {
    if (!row.a) return
    
    const positions = parsePositions(row.a)
    positions.forEach(pos => {
      const title = pos.title
      const amount = parseFloat(pos.amount) || 0
      
      if (positionMap.has(title)) {
        positionMap.set(title, positionMap.get(title) + amount)
      } else {
        positionMap.set(title, amount)
      }
    })
  })
  
  // 过滤掉数量为0的，转换为数组并排序
  const positionSummary = Array.from(positionMap.entries())
    .filter(([title, amount]) => Math.abs(amount) > 0.01) // 过滤接近0的数量
    .map(([title, amount]) => ({ title, amount: amount.toFixed(2) }))
    .sort((a, b) => Math.abs(parseFloat(b.amount)) - Math.abs(parseFloat(a.amount))) // 按绝对值降序
  
  return {
    totalBalance: totalBalance.toFixed(2),
    totalPortfolio: totalPortfolio.toFixed(2),
    positionSummary
  }
})

/**
 * 数字排序方法
 */
const sortByNumber = (a, b) => {
  const numA = typeof a === 'string' ? parseFloat(a) : (a || 0)
  const numB = typeof b === 'string' ? parseFloat(b) : (b || 0)
  return numA - numB
}

/**
 * 格式化数字
 */
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '-'
  try {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return num.toFixed(2)
  } catch {
    return '-'
  }
}

/**
 * 格式化相对时间
 * 将时间戳转换为 "刚刚"、"几分钟前"、"几小时前"、"几天前"
 */
const formatRelativeTime = (timestamp) => {
  if (!timestamp) return '未采集'
  
  try {
    const ts = typeof timestamp === 'string' ? parseInt(timestamp) : timestamp
    const now = Date.now()
    const diff = now - ts
    
    if (diff < 0) return '刚刚'
    
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (seconds < 60) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 30) return `${days}天前`
    return '很久以前'
  } catch {
    return '未知'
  }
}

/**
 * 获取忽略的浏览器集合
 */
const getIgnoredBrowsersSet = () => {
  const input = positionTimeConfig.value.ignoredBrowsers.trim()
  if (!input) return new Set()
  
  const browsers = input.split(',').map(b => b.trim()).filter(b => b)
  return new Set(browsers)
}

/**
 * 判断行是否应该高亮（打开时间>仓位时间）
 */
const shouldHighlightRow = (row) => {
  if (!row.f || !row.d) return false
  
  const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
  const positionTime = typeof row.d === 'string' ? parseInt(row.d) : row.d
  
  return openTime > positionTime
}

/**
 * 获取行的CSS类名
 */
const getRowClassName = ({ row }) => {
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const isIgnored = ignoredBrowsersSet.has(String(row.fingerprintNo))
  
  if (!isIgnored && shouldHighlightRow(row)) {
    return 'highlight-row'
  }
  return ''
}

/**
 * 保存忽略的浏览器配置
 */
const saveIgnoredBrowsers = () => {
  try {
    localStorage.setItem('ignoredBrowsers', positionTimeConfig.value.ignoredBrowsers)
    ElMessage.success('已保存忽略浏览器配置')
  } catch (error) {
    ElMessage.error('保存配置失败')
    console.error('保存配置失败:', error)
  }
}

/**
 * 切换自动更新
 */
const toggleAutoUpdate = () => {
  if (positionTimeConfig.value.autoUpdate) {
    // 开启自动更新
    performAutoUpdate()  // 立即执行一次
    autoUpdateTimer = setInterval(performAutoUpdate, 20 * 60 * 1000)  // 每20分钟执行一次
    ElMessage.success('已开启自动更新仓位')
  } else {
    // 关闭自动更新
    if (autoUpdateTimer) {
      clearInterval(autoUpdateTimer)
      autoUpdateTimer = null
    }
    ElMessage.info('已关闭自动更新仓位')
  }
}

/**
 * 执行自动更新
 */
const performAutoUpdate = async () => {
  console.log('[自动更新] 开始检查需要更新的仓位...')
  
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const thresholdMinutes = positionTimeConfig.value.updateThresholdMinutes
  const now = Date.now()
  
  const browsersToUpdate = []
  
  for (const row of tableData.value) {
    // 跳过忽略的浏览器
    if (ignoredBrowsersSet.has(String(row.fingerprintNo))) {
      continue
    }
    
    // 检查打开时间是否大于仓位时间
    if (!shouldHighlightRow(row)) {
      continue
    }
    
    // 检查打开时间距离现在是否已经过去了阈值分钟数
    const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
    const elapsedMinutes = (now - openTime) / 1000 / 60
    
    if (elapsedMinutes >= thresholdMinutes) {
      browsersToUpdate.push(row)
    }
  }
  
  if (browsersToUpdate.length === 0) {
    console.log('[自动更新] 没有需要更新的仓位')
    return
  }
  
  console.log(`[自动更新] 发现 ${browsersToUpdate.length} 个需要更新的浏览器`)
  
  // 依次更新每个浏览器的仓位
  for (const row of browsersToUpdate) {
    try {
      console.log(`[自动更新] 正在更新浏览器 ${row.fingerprintNo}...`)
      await refreshPosition(row)
      await new Promise(resolve => setTimeout(resolve, 2000))  // 间隔2秒
    } catch (error) {
      console.error(`[自动更新] 更新浏览器 ${row.fingerprintNo} 失败:`, error)
    }
  }
  
  console.log('[自动更新] 完成')
  ElMessage.success(`已自动更新 ${browsersToUpdate.length} 个浏览器的仓位`)
}

/**
 * 解析持仓数据字符串
 * 格式: "标题1|||选项1|||数量1|||均价1;标题2|||选项2|||数量2|||均价2"
 * 兼容旧格式: "标题1,选项1,数量1,均价1;标题2,选项2,数量2,均价2"
 */
const parsePositions = (posStr) => {
  if (!posStr) return []
  try {
    const positions = []
    const items = posStr.split(';')
    for (const item of items) {
      // 优先尝试新格式（|||分隔符）
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 4) {
          let title = parts[0].trim()
          let option = parts[1].trim()
          let amount = parts[2].trim()
          let avgPrice = parts[3].trim()
          
          // 特殊处理：First to 5k: Gold or ETH? 市场
          if (title.includes('First to 5k') && (option === 'ETH' || option === 'GOLD')) {
            const numAmount = parseFloat(amount)
            if (!isNaN(numAmount)) {
              if (option === 'GOLD') {
                // GOLD改为正数
                amount = Math.abs(numAmount).toFixed(2)
              } else if (option === 'ETH') {
                // ETH改为负数
                amount = (-Math.abs(numAmount)).toFixed(2)
              }
            }
          }
          
          positions.push({
            title: title,
            option: option,
            amount: amount,
            avgPrice: avgPrice
          })
        }
      } else {
        // 兼容旧格式（逗号分隔符）
        const parts = item.split(',')
        if (parts.length >= 4) {
          let title = parts[0].trim()
          let option = parts[1].trim()
          let amount = parts[2].trim()
          let avgPrice = parts[3].trim()
          
          // 特殊处理：First to 5k: Gold or ETH? 市场
          if (title.includes('First to 5k') && (option === 'ETH' || option === 'GOLD')) {
            const numAmount = parseFloat(amount)
            if (!isNaN(numAmount)) {
              if (option === 'GOLD') {
                // GOLD改为正数
                amount = Math.abs(numAmount).toFixed(2)
              } else if (option === 'ETH') {
                // ETH改为负数
                amount = (-Math.abs(numAmount)).toFixed(2)
              }
            }
          }
          
          positions.push({
            title: title,
            option: option,
            amount: amount,
            avgPrice: avgPrice
          })
        } else if (parts.length >= 3) {
          positions.push({
            title: parts[0].trim(),
            option: parts[1].trim(),
            amount: parts[2].trim(),
            avgPrice: ''
          })
        } else if (parts.length >= 2) {
          positions.push({
            title: parts[0].trim(),
            option: '',
            amount: parts[1].trim(),
            avgPrice: ''
          })
        }
      }
    }
    return positions
  } catch {
    return []
  }
}

/**
 * 解析挂单数据字符串
 * 格式: "标题1|||价格1|||进度1;标题2|||价格2|||进度2"
 * 兼容旧格式: "标题1,价格1,进度1;标题2,价格2,进度2"
 */
const parseOpenOrders = (ordersStr) => {
  if (!ordersStr) return []
  try {
    const orders = []
    const items = ordersStr.split(';')
    for (const item of items) {
      // 优先尝试新格式（|||分隔符）
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 3) {
          orders.push({
            title: parts[0].trim(),
            price: parts[1].trim(),
            progress: parts[2].trim()
          })
        }
      } else {
        // 兼容旧格式（逗号分隔符）
        const parts = item.split(',')
        if (parts.length >= 3) {
          orders.push({
            title: parts[0].trim(),
            price: parts[1].trim(),
            progress: parts[2].trim()
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
 * 解析交易记录数据字符串
 * 格式: "标题1|||方向1|||选项1|||数量1|||金额1|||价格1|||时间1;标题2|||方向2|||选项2|||数量2|||金额2|||价格2|||时间2"
 */
const parseTransactions = (transStr) => {
  if (!transStr) return []
  try {
    const transactions = []
    const items = transStr.split(';')
    for (const item of items) {
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 7) {
          transactions.push({
            title: parts[0].trim(),
            direction: parts[1].trim(),
            option: parts[2].trim(),
            amount: parts[3].trim(),
            value: parts[4].trim(),
            price: parts[5].trim(),
            time: parts[6].trim()
          })
        }
      }
    }
    return transactions
  } catch {
    return []
  }
}

/**
 * 显示交易记录弹窗
 */
const showTransactions = (row) => {
  if (!row.g) {
    ElMessage.warning('该账户暂无交易记录')
    return
  }
  
  const transactions = parseTransactions(row.g)
  currentTransactions.value = transactions.map((trans, index) => ({
    index: index + 1,
    ...trans
  }))
  
  transactionDialogVisible.value = true
}


/**
 * 加载数据列表（支持静默刷新）
 */
const loadData = async (silent = false) => {
  if (!silent) {
    loading.value = true
  }
  
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`)
    
    if (response.data && response.data.data) {
      const serverData = response.data.data
      
      // 保存本地新增的行（没有 id 的）
      const localRows = tableData.value.filter(row => !row.id)
      
      // 创建一个 map 存储服务器数据，key 为 fingerprintNo
      const serverDataMap = new Map()
      serverData.forEach(item => {
        if (item.fingerprintNo) {
          serverDataMap.set(String(item.fingerprintNo), item)
        }
      })
      
      // 更新已存在的行
      const updatedData = []
      
      // 首先添加所有服务器数据
      serverData.forEach(item => {
        updatedData.push({
          ...item,
          platform: item.e || item.platform || 'OP',
          refreshing: false
        })
      })
      
      // 然后添加本地新增的行（如果服务器没有相同的 fingerprintNo）
      localRows.forEach(localRow => {
        if (!localRow.fingerprintNo || !serverDataMap.has(String(localRow.fingerprintNo))) {
          updatedData.push(localRow)
        }
      })
      
      // 重新计算序号
      updatedData.forEach((item, index) => {
        item.index = index + 1
      })
      
      tableData.value = updatedData
      nextId = Math.max(...tableData.value.map(item => item.id || 0)) + 1
      
      if (!silent) {
        ElMessage.success('数据加载成功')
      } else {
        console.log('数据静默刷新成功')
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    if (!silent) {
      ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
    }
  } finally {
    if (!silent) {
      loading.value = false
    }
  }
}

/**
 * 添加行
 */
const addRows = (count) => {
  for (let i = 0; i < count; i++) {
    const newRow = {
      index: tableData.value.length + 1,
      id: null, // 新行没有ID
      computeGroup: '1',  // 默认组号
      fingerprintNo: '',
      platform: 'OP',
      balance: 0,
      a: '',  // 持仓数据
      b: '',  // 挂单数据
      c: '0', // Portfolio
      d: '',  // 时间戳
      refreshing: false,
      // 其他必需字段
      no: null,
      addr: '',
      groupId: null,
      needDepositQty: 0,
      realSendBnbQty: null,
      sendBnbQty: null,
      receiveBnbQty: null,
      sendUsdtQty: null,
      receiveUsdtQty: null,
      searchUsdtQty: null,
      depositUsdtQty: null,
      currentUsdtQty: null,
      feeBackAddr: null,
      inviteCode: null,
      opUser: '',
      canOpenWorth: null,
      canOpenBtcQty: null,
      canOpenEthQty: null,
      useAster: null,
      totalBuyAster: null,
      remainingAster: 0,
      tradeIntegral: '0',
      positionIntegral: '0',
      btc: 0,
      eth: 0,
      useAccount: null,
      reason: null,
      groupNo: null,
      available: 0,
      catchTime: null,
      sol: 0,
      bnb: null,
      isTrans: false,
      positionMulti: '0',
      netPositionMulti: '0',
      positionWorth: null,
      weekVolume: 0,
      a: null,
      b: null,
      c: '0',
      d: '0',
      e: null,
      f: null,
      g: null,
      h: null,
      i: null,
      j: null,
      k: null,
      l: null,
      m: null,
      n: null,
      o: null,
      p: null,
      q: null,
      r: null,
      s: null,
      t: null,
      u: null,
      v: null,
      w: '',
      x: '0',
      y: null,
      z: '',
      predictBalance: null,
      predictPositionMulti: null,
      predictNetPositionMulti: null,
      proxyDelay: null,
      proxyIp: null,
      isWarn: 0
    }
    tableData.value.push(newRow)
  }
  
  // 重新计算序号
  tableData.value.forEach((row, index) => {
    row.index = index + 1
  })
  
  ElMessage.success(`已添加 ${count} 行`)
}

/**
 * 保存单行数据
 */
const saveRowData = async (row) => {
  try {
    // 准备要保存的数据
    const saveData = { ...row }
    // 平台值保存到 e 字段
    saveData.e = saveData.platform
    // 删除前端添加的字段
    delete saveData.index
    delete saveData.refreshing
    // 如果没有ID，删除ID字段（新增数据）
    if (!saveData.id) {
      delete saveData.id
    }
    
    // 将单个数据放在数组中
    const dataToSave = saveData
    
    const response = await axios.post(`${API_BASE_URL}/boost/addAccountConfig`, dataToSave)
    
    if (response.data) {
      console.log('行数据已自动保存')
      // 如果是新增数据，重新加载以获取服务器分配的ID
      if (!row.id) {
        await loadData()
      }
    }
  } catch (error) {
    console.error('保存行数据失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '网络错误'))
  }
}

/**
 * 保存所有数据
 */
const saveAll = async () => {
  saving.value = true
  try {
    // 准备要保存的数据
    const dataToSave = tableData.value.map(row => {
      const saveData = { ...row }
      // 删除前端添加的字段
      delete saveData.index
      delete saveData.refreshing
      // 如果没有ID，删除ID字段（新增数据）
      if (!saveData.id) {
        delete saveData.id
      }
      return saveData
    })
    
    const response = await axios.post(`${API_BASE_URL}/boost/addAccountConfig`, dataToSave)
    
    if (response.data) {
      ElMessage.success('保存成功')
      // 重新加载数据
      await loadData()
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '网络错误'))
  } finally {
    saving.value = false
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
  
  row.refreshing = true
  try {
    // 1. 发送 type=2 任务请求，让服务器采集最新数据
    ElMessage.info(`正在采集浏览器 ${row.fingerprintNo} 的最新仓位数据...`)
    
    const taskData = {
      groupNo: row.computeGroup,
      numberList: parseInt(row.fingerprintNo),
      type: 2,  // Type 2 任务
      exchangeName: row.platform === 'OP' ? 'OP' : 'Ploy'
    }
    
    // 发送任务请求
    const taskResponse = await axios.post(
      `${API_BASE_URL}/mission/add`,
      taskData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    // 服务器返回 {} 或 status 200 都视为成功
    if (taskResponse.status === 200) {
      ElMessage.success(`任务已提交，正在采集数据...`)
    } else {
      throw new Error('任务提交失败')
    }
    
    // 2. 等待一段时间让任务执行
    const waitTime = 60000  // 统一等待 60 秒
    ElMessage.info(`预计需要 ${waitTime / 1000} 秒，请稍候...`)
    
    await new Promise(resolve => setTimeout(resolve, waitTime))
    
    // 3. 获取更新后的数据
    const response = await axios.get(
      `${API_BASE_URL}/boost/findAccountConfigByNo?no=${row.fingerprintNo}`
    )
    
    if (response.data && response.data.data) {
      const newData = response.data.data
      
      // 更新字段
      row.balance = newData.balance || 0
      row.a = newData.a || ''  // 持仓
      row.b = newData.b || ''  // 挂单
      row.c = newData.c || '0' // Portfolio
      row.d = newData.d || ''  // 时间戳
      row.platform = newData.e || row.platform  // 平台
      
      ElMessage.success(`浏览器 ${row.fingerprintNo} 仓位数据已更新`)
    } else {
      ElMessage.warning('数据采集完成，但未获取到更新数据')
    }
  } catch (error) {
    console.error('刷新仓位失败:', error)
    const errorMsg = error.response?.data?.msg || error.message || '网络错误'
    ElMessage.error('刷新仓位失败: ' + errorMsg)
  } finally {
    row.refreshing = false
  }
}

/**
 * 删除账户配置
 */
const deleteAccount = async (row) => {
  if (!row.id) {
    ElMessage.warning('该行数据没有ID，无法删除')
    return
  }
  
  try {
    await axios.post(`${API_BASE_URL}/boost/deleteAccountConfig`, {
      id: row.id
    })
    
    ElMessage.success('删除成功')
    // 重新加载数据
    await loadData()
  } catch (error) {
    console.error('删除失败:', error)
    const errorMsg = error.response?.data?.msg || error.message || '网络错误'
    ElMessage.error('删除失败: ' + errorMsg)
  }
}

/**
 * 切换自动刷新
 */
const toggleAutoRefresh = () => {
  if (autoRefresh.value.enabled) {
    startAutoRefresh()
    ElMessage.success(`自动刷新已启动，间隔 ${autoRefresh.value.interval} 秒`)
  } else {
    stopAutoRefresh()
    ElMessage.info('自动刷新已关闭')
  }
}

/**
 * 启动自动刷新
 */
const startAutoRefresh = () => {
  stopAutoRefresh()  // 先清除旧的定时器
  
  if (autoRefresh.value.enabled && autoRefresh.value.interval > 0) {
    autoRefreshTimer = setInterval(() => {
      console.log('自动刷新数据...')
      loadData(true)  // 静默刷新
    }, autoRefresh.value.interval * 1000)
  }
}

/**
 * 停止自动刷新
 */
const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

/**
 * 重置自动刷新（间隔改变时）
 */
const resetAutoRefresh = () => {
  if (autoRefresh.value.enabled) {
    startAutoRefresh()
    ElMessage.success(`自动刷新间隔已更新为 ${autoRefresh.value.interval} 秒`)
  }
}

/**
 * 刷新全部仓位
 */
const refreshAllPositions = async () => {
  // 获取所有有浏览器编号和电脑组的行
  const validRows = tableData.value.filter(row => 
    row.fingerprintNo && row.computeGroup && row.platform
  )
  
  if (validRows.length === 0) {
    ElMessage.warning('没有可刷新的账户')
    return
  }
  
  refreshingAll.value = true
  ElMessage.info(`开始刷新 ${validRows.length} 个账户的仓位数据，请稍候...`)
  
  let successCount = 0
  let failCount = 0
  
  try {
    // 提交所有 type=2 任务
    const taskPromises = validRows.map(async (row) => {
      try {
        const taskData = {
          groupNo: row.computeGroup,
          numberList: parseInt(row.fingerprintNo),
          type: 2,
          exchangeName: row.platform === 'OP' ? 'OP' : 'Ploy'
        }
        
        await axios.post(
          `${API_BASE_URL}/mission/add`,
          taskData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
        
        console.log(`浏览器 ${row.fingerprintNo} 刷新任务已提交`)
        successCount++
      } catch (error) {
        console.error(`浏览器 ${row.fingerprintNo} 刷新任务提交失败:`, error)
        failCount++
      }
    })
    
    await Promise.all(taskPromises)
    
    ElMessage.success(`已提交 ${successCount} 个刷新任务${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 等待 70 秒后自动刷新列表
    ElMessage.info('任务已全部提交，70秒后自动刷新列表...')
    setTimeout(async () => {
      await loadData(true)  // 静默刷新
      ElMessage.success('数据已自动更新')
    }, 70000)
    
  } catch (error) {
    console.error('刷新全部仓位失败:', error)
    ElMessage.error('刷新全部仓位失败: ' + (error.message || '网络错误'))
  } finally {
    refreshingAll.value = false
  }
}

/**
 * 刷新变红仓位（打开时间>仓位时间的）
 */
const refreshRedPositions = async () => {
  // 获取所有背景标红的行（打开时间>仓位时间，且不在忽略列表中）
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const redRows = tableData.value.filter(row => 
    row.fingerprintNo && 
    row.computeGroup && 
    row.platform &&
    !ignoredBrowsersSet.has(String(row.fingerprintNo)) &&
    shouldHighlightRow(row)
  )
  
  if (redRows.length === 0) {
    ElMessage.warning('没有需要刷新的变红仓位')
    return
  }
  
  refreshingRed.value = true
  ElMessage.info(`开始刷新 ${redRows.length} 个变红仓位，请稍候...`)
  
  let successCount = 0
  let failCount = 0
  
  try {
    // 提交所有 type=2 任务
    const taskPromises = redRows.map(async (row) => {
      try {
        const taskData = {
          groupNo: row.computeGroup,
          numberList: parseInt(row.fingerprintNo),
          type: 2,
          exchangeName: row.platform === 'OP' ? 'OP' : 'Ploy'
        }
        
        const response = await axios.post(
          `${API_BASE_URL}/mission/add`,
          taskData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
        
        // 保存最新的任务ID（只保留最后一个）
        if (response.data && response.data.data && response.data.data.id) {
          latestMissionId.value = response.data.data.id
        }
        
        console.log(`浏览器 ${row.fingerprintNo} 刷新任务已提交`)
        successCount++
      } catch (error) {
        console.error(`浏览器 ${row.fingerprintNo} 刷新任务提交失败:`, error)
        failCount++
      }
    })
    
    await Promise.all(taskPromises)
    
    ElMessage.success(`已提交 ${successCount} 个刷新任务${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 等待 70 秒后自动刷新列表
    ElMessage.info('任务已全部提交，70秒后自动刷新列表...')
    setTimeout(async () => {
      await loadData(true)  // 静默刷新
      ElMessage.success('数据已自动更新')
    }, 70000)
    
  } catch (error) {
    console.error('刷新变红仓位失败:', error)
    ElMessage.error('刷新变红仓位失败: ' + (error.message || '网络错误'))
  } finally {
    refreshingRed.value = false
  }
}

/**
 * 获取任务状态文本
 */
const getMissionStatusText = (status) => {
  if (status === null || status === undefined) return '未知'
  switch (status) {
    case 0:
      return '尚未执行'
    case 2:
      return '成功'
    case 3:
      return '失败'
    case 9:
      return '进行中'
    default:
      return `状态${status}`
  }
}

/**
 * 获取任务状态类型（用于标签颜色）
 */
const getMissionStatusType = (status) => {
  if (status === null || status === undefined) return 'info'
  switch (status) {
    case 0:
      return 'info'
    case 2:
      return 'success'
    case 3:
      return 'danger'
    case 9:
      return 'warning'
    default:
      return 'info'
  }
}

/**
 * 显示任务日志弹窗
 */
const showMissionLog = async () => {
  if (!latestMissionId.value) {
    ElMessage.warning('暂无任务ID')
    return
  }
  
  missionLogDialogVisible.value = true
  await refreshMissionStatus()
}

/**
 * 刷新任务状态
 */
const refreshMissionStatus = async () => {
  if (!latestMissionId.value) {
    ElMessage.warning('暂无任务ID')
    return
  }
  
  loadingMissionStatus.value = true
  
  try {
    const response = await axios.get(
      `${API_BASE_URL}/mission/status`,
      {
        params: {
          id: latestMissionId.value
        }
      }
    )
    
    if (response.data && response.data.data && response.data.data.mission) {
      const mission = response.data.data.mission
      missionStatus.value = {
        status: mission.status,
        msg: mission.msg || ''
      }
    } else {
      ElMessage.warning('未获取到任务状态')
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
    ElMessage.error('获取任务状态失败: ' + (error.message || '网络错误'))
  } finally {
    loadingMissionStatus.value = false
  }
}

/**
 * 批量添加账户
 */
const batchAddAccounts = async () => {
  if (!batchAddInput.value || !batchAddInput.value.trim()) {
    ElMessage.warning('请输入要添加的数据')
    return
  }
  
  try {
    const input = batchAddInput.value.trim()
    const groups = input.split(';').map(g => g.trim()).filter(g => g)
    
    if (groups.length === 0) {
      ElMessage.warning('输入格式错误')
      return
    }
    
    const accountsToAdd = []
    
    for (const group of groups) {
      const parts = group.split(',').map(p => p.trim()).filter(p => p)
      
      if (parts.length < 2) {
        ElMessage.warning(`格式错误: ${group}，至少需要电脑组和一个浏览器ID`)
        continue
      }
      
      const computeGroup = parts[0]
      const browserIds = parts.slice(1)
      
      // 为每个浏览器ID创建账户配置
      for (const browserId of browserIds) {
        accountsToAdd.push({
          computeGroup: computeGroup,
          fingerprintNo: browserId,
          platform: 'OP',
          balance: 0,
          a: '',
          b: '',
          c: '0',
          d: '',
          e: 'OP',
          f: null,
          g: null,
          no: null,
          addr: '',
          groupId: null,
          needDepositQty: 0,
          realSendBnbQty: null,
          sendBnbQty: null,
          receiveBnbQty: null,
          sendUsdtQty: null,
          receiveUsdtQty: null,
          searchUsdtQty: null,
          depositUsdtQty: null,
          currentUsdtQty: null,
          feeBackAddr: null,
          inviteCode: null,
          opUser: '',
          canOpenWorth: null,
          canOpenBtcQty: null,
          canOpenEthQty: null,
          useAster: null,
          totalBuyAster: null,
          remainingAster: 0,
          tradeIntegral: '0',
          positionIntegral: '0',
          btc: 0,
          eth: 0,
          useAccount: null,
          reason: null,
          groupNo: null,
          available: 0,
          catchTime: null,
          sol: 0,
          bnb: null,
          isTrans: false,
          positionMulti: '0',
          netPositionMulti: '0',
          positionWorth: null,
          weekVolume: 0,
          h: null,
          i: null,
          j: null,
          k: null,
          l: null,
          m: null,
          n: null,
          o: null,
          p: null,
          q: null,
          r: null,
          s: null,
          t: null,
          u: null,
          v: null,
          w: '',
          x: '0',
          y: null,
          z: '',
          predictBalance: null,
          predictPositionMulti: null,
          predictNetPositionMulti: null,
          proxyDelay: null,
          proxyIp: null,
          isWarn: 0
        })
      }
    }
    
    if (accountsToAdd.length === 0) {
      ElMessage.warning('没有有效的账户数据')
      return
    }
    
    ElMessage.info(`开始添加 ${accountsToAdd.length} 个账户...`)
    
    // 逐个添加账户
    let successCount = 0
    let failCount = 0
    
    for (const account of accountsToAdd) {
      try {
        await axios.post(`${API_BASE_URL}/boost/addAccountConfig`, account)
        successCount++
        console.log(`账户 ${account.fingerprintNo} 添加成功`)
      } catch (error) {
        failCount++
        console.error(`账户 ${account.fingerprintNo} 添加失败:`, error)
      }
    }
    
    ElMessage.success(`成功添加 ${successCount} 个账户${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 清空输入框
    batchAddInput.value = ''
    
    // 重新加载数据
    await loadData()
    
  } catch (error) {
    console.error('批量添加失败:', error)
    ElMessage.error('批量添加失败: ' + (error.message || '网络错误'))
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadData()
  
  // 如果自动刷新已启用，启动定时器
  if (autoRefresh.value.enabled) {
    startAutoRefresh()
  }
  
  // 加载忽略浏览器配置
  try {
    const savedIgnoredBrowsers = localStorage.getItem('ignoredBrowsers')
    if (savedIgnoredBrowsers) {
      positionTimeConfig.value.ignoredBrowsers = savedIgnoredBrowsers
    }
  } catch (error) {
    console.error('加载忽略浏览器配置失败:', error)
  }
})

/**
 * 组件卸载时清理定时器
 */
onUnmounted(() => {
  stopAutoRefresh()
  
  // 清理自动更新定时器
  if (autoUpdateTimer) {
    clearInterval(autoUpdateTimer)
    autoUpdateTimer = null
  }
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.app-title {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
  font-size: 28px;
}

.toolbar {
  margin-bottom: 15px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.auto-refresh-control {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border-left: 2px solid #ddd;
  border-right: 2px solid #ddd;
}

.auto-refresh-control span {
  font-size: 14px;
  color: #606266;
}

.batch-add-container {
  margin-bottom: 15px;
  padding: 12px 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.batch-add-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-add-row label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.batch-add-tip {
  font-size: 12px;
  color: #999;
  font-style: italic;
}

.position-time-config-container {
  margin-bottom: 15px;
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.position-time-config-container .config-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.position-time-config-container .config-row:last-child {
  margin-bottom: 0;
}

.position-time-config-container label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.position-time-config-container span {
  font-size: 14px;
  color: #606266;
}

.filter-container {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
  font-weight: 500;
}

/* 总计信息容器 */
.summary-container {
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.3s ease;
}

.summary-container.collapsed {
  padding: 15px 20px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.summary-container.collapsed .summary-header {
  margin-bottom: 0;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.collapse-btn {
  background-color: rgba(255, 255, 255, 0.2) !important;
  border: none !important;
  color: #fff !important;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.3) !important;
  transform: scale(1.1);
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* 折叠过渡动画 */
.summary-collapse-enter-active,
.summary-collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.summary-collapse-enter-from,
.summary-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 15px;
  background-color: rgba(255, 255, 255, 0.15);
  padding: 12px 15px;
  border-radius: 6px;
  backdrop-filter: blur(10px);
}

.summary-label {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.summary-positions {
  flex-direction: column;
  align-items: flex-start;
}

.summary-positions-list {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.empty-summary {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-style: italic;
}

.summary-position-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  transition: all 0.3s;
}

.summary-position-item:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateX(5px);
}

.position-title-summary {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
  flex: 1;
  line-height: 1.4;
}

.position-list {
  max-height: 200px;
  overflow-y: auto;
}

.position-item {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.position-item:last-child {
  margin-bottom: 0;
}

.position-title {
  font-weight: bold;
  color: #333;
  margin-bottom: 6px;
  font-size: 14px;
  line-height: 1.4;
}

.position-details {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.position-amount,
.position-price {
  white-space: nowrap;
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
}

.empty-text {
  color: #999;
  font-size: 12px;
}

.capture-time-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.capture-time-cell .el-icon {
  color: #409eff;
  font-size: 14px;
}

/* 滚动条样式 */
.position-list::-webkit-scrollbar {
  width: 6px;
}

.position-list::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
}

.position-list::-webkit-scrollbar-thumb:hover {
  background-color: #bbb;
}

/* 弹窗内的空消息 */
.empty-message {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: center;
}

/* 高亮行（打开时间>仓位时间） */
:deep(.el-table__row.highlight-row) {
  background-color: #fee !important;
}

:deep(.el-table__row.highlight-row:hover > td) {
  background-color: #fdd !important;
}

/* 任务日志弹窗样式 */
.mission-log-content {
  padding: 20px;
  min-height: 150px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-label {
  font-size: 15px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
  min-width: 80px;
}

.log-value {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  word-break: break-all;
}
</style>

