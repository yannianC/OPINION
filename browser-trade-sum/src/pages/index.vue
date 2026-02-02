<script setup lang="ts">
import type { AccountConfigCacheItem, PointItem } from '~/types/account'
import type { TradeItem } from '~/types/trade'
import { Download, Filter, Refresh, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { getAccountConfigCache } from '~/api/account'
import { getBrowserTradeSum } from '~/api/trade'
import { exportToExcel } from '~/utils/export'
import { ElMessage } from 'element-plus'

// 扩展 TradeItem 类型以包含 UI 辅助字段
interface TableRow extends Partial<TradeItem> {
  isSummary?: boolean // 标记是否为合计行
  pointsTotal?: number // 积分汇总数值
  pointsDetails?: PointItem[] // 新增：积分详情列表
  feePerPoint?: number // 新增：手续费/积分
  [key: string]: any // 允许索引访问
}

const LOCAL_STORAGE_KEY = 'account_config_cache'
const IDB_DB_NAME = 'browser_trade_sum_db'
const IDB_STORE_NAME = 'account_cache'

// 状态管理
const tradeLoading = ref(false) // 交易数据加载状态
const accountLoading = ref(false) // 账户缓存更新状态
const tableData = ref<TableRow[]>([])
const rawList = ref<TableRow[]>([]) // 存储原始业务数据

// 记录当前的排序状态，以便在数据更新时保持排序
const currentSort = ref<{ prop: string, order: string }>({ prop: '', order: '' })

// 交易统计时间范围
const defaultEnd = dayjs()
const defaultStart = dayjs().subtract(7, 'day')
const tradeDateRange = ref<[Date, Date]>([
  defaultStart.toDate(),
  defaultEnd.toDate(),
])

// 积分筛选时间范围 (UI绑定值)
const pointsDateRange = ref<[Date, Date]>([
  dayjs().subtract(30, 'day').toDate(),
  dayjs().toDate(),
])

// 实际生效的积分筛选范围
const appliedPointsDateRange = ref<[Date, Date] | null>(null)

// 缓存账户信息 Map<fingerprintNo, AccountItem>
const accountMap = ref<Map<string, AccountConfigCacheItem>>(new Map())
const lastCacheTime = ref<string>('')

// 计算属性：是否有账户数据
const hasAccountData = computed(() => accountMap.value.size > 0)

// 计算属性：积分列的标题，根据筛选状态变化
const pointsLabel = computed(() => {
  if (appliedPointsDateRange.value && hasAccountData.value) {
    return '积分汇总 (已筛选)'
  }
  return '积分汇总'
})

// 初始化：从 IndexedDB 加载缓存
onMounted(async () => {
  await loadCacheFromIndexedDB()
  // 默认不筛选积分数据，需要手动点击筛选按钮
})

// IndexedDB 辅助函数
async function openIndexedDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(IDB_DB_NAME, 1)

    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      if (!db.objectStoreNames.contains(IDB_STORE_NAME)) {
        db.createObjectStore(IDB_STORE_NAME)
      }
    }
  })
}

async function saveCacheToIndexedDB(data: AccountConfigCacheItem[], timestamp: number) {
  try {
    const db = await openIndexedDB()
    return new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([IDB_STORE_NAME], 'readwrite')
      const store = transaction.objectStore(IDB_STORE_NAME)

      store.put({ data, timestamp }, 'cache')

      transaction.oncomplete = () => resolve()
      transaction.onerror = () => reject(transaction.error)
    })
  }
  catch (error) {
    console.error('Failed to save cache to IndexedDB:', error)
    throw error
  }
}

async function loadCacheFromIndexedDB() {
  try {
    const db = await openIndexedDB()
    return new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([IDB_STORE_NAME], 'readonly')
      const store = transaction.objectStore(IDB_STORE_NAME)
      const request = store.get('cache')

      request.onsuccess = () => {
        const cachedData = request.result
        if (cachedData && cachedData.data && Array.isArray(cachedData.data)) {
          updateAccountMap(cachedData.data)
          if (cachedData.timestamp) {
            lastCacheTime.value = dayjs(cachedData.timestamp).format('MM-DD HH:mm')
          }
          // 加载缓存后，如果已有交易数据，需要刷新表格以计算积分
          if (rawList.value.length > 0) {
            updateTableData()
          }
        }
        resolve()
      }

      request.onerror = () => reject(request.error)
    })
  }
  catch (error) {
    console.error('Failed to load cache from IndexedDB:', error)
    // 回退到 localStorage 兼容旧数据
    loadCacheFromStorage()
  }
}

function loadCacheFromStorage() {
  try {
    const cachedStr = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (cachedStr) {
      const { data, timestamp } = JSON.parse(cachedStr)
      if (Array.isArray(data)) {
        updateAccountMap(data)
        if (timestamp) {
          lastCacheTime.value = dayjs(timestamp).format('MM-DD HH:mm')
        }
        if (rawList.value.length > 0) {
          updateTableData()
        }
      }
    }
  }
  catch (e) {
    console.error('Failed to load cache from storage', e)
  }
}

// 更新 Map 辅助函数
function updateAccountMap(list: AccountConfigCacheItem[]) {
  const newMap = new Map<string, AccountConfigCacheItem>()
  list.forEach((item) => {
    // 确保 key 统一为字符串并去除空格
    if (item.fingerprintNo) {
      newMap.set(String(item.fingerprintNo).trim(), item)
    }
  })
  accountMap.value = newMap
}

// 手动更新账户缓存
async function handleUpdateCache() {
  accountLoading.value = true
  try {
    const list = await getAccountConfigCache()
    if (list && list.length > 0) {
      // 1. 更新内存 Map
      updateAccountMap(list)
      // 2. 更新最后时间
      const now = Date.now()
      lastCacheTime.value = dayjs(now).format('MM-DD HH:mm')
      // 3. 写入 IndexedDB
      await saveCacheToIndexedDB(list, now)

      // 4. 刷新表格数据的积分计算
      updateTableData()

      ElMessage.success('账户缓存已更新')
    }
  }
  catch (error) {
    ElMessage.error('保存缓存失败')
    console.error('Failed to update cache:', error)
  }
  finally {
    accountLoading.value = false
  }
}

function disabledDate(time: Date) {
  return time.getTime() > Date.now()
}

function formatNumber(row: TableRow, column: any, cellValue: number) {
  if (row.isSummary && column.property !== 'feeRate') {
    return cellValue ? cellValue.toFixed(4) : '-'
  }
  if (cellValue === null || cellValue === undefined)
    return '-'
  return cellValue.toFixed(4)
}

// 解析逻辑：支持 '2026-01-25' 格式
function parsePointString(str: string): PointItem | null {
  if (!str)
    return null
  const parts = str.split('|||')
  if (parts.length < 3)
    return null

  // 尝试解析日期字符串
  const dateStrRaw = parts[0] // e.g., "2026-01-25"
  const dateObj = dayjs(dateStrRaw)

  if (!dateObj.isValid())
    return null

  return {
    timestamp: dateObj.valueOf(),
    dateStr: dateObj.format('YYYY-MM-DD'),
    description: parts[1],
    value: parts[2], // e.g. "+3.518 PTS"
    raw: str,
  }
}

// 提取 value 字符串中的数字
function extractPointValue(valStr: string): number {
  if (!valStr)
    return 0
  // 使用 parseFloat 可以直接处理 "+3.518 PTS" 这种情况，它会读取开头的数字
  const val = Number.parseFloat(valStr)
  return Number.isNaN(val) ? 0 : val
}

// 获取浏览器积分数据（总分和明细）
function getBrowserPointsData(number: string): { total: number, list: PointItem[] } {
  const key = number ? String(number).trim() : ''
  const acc = accountMap.value.get(key)
  if (!acc || !acc.k)
    return { total: 0, list: [] }

  const rawPoints = acc.k.split(';')
  const parsed = rawPoints
    .map(p => parsePointString(p))
    .filter((p): p is PointItem => p !== null)

  let filtered = parsed
  // 如果有时间筛选，则过滤
  if (appliedPointsDateRange.value) {
    const [start, end] = appliedPointsDateRange.value
    const startTime = start.getTime()
    const endTime = end.getTime()
    filtered = parsed.filter(p => p.timestamp >= startTime && p.timestamp <= endTime)
  }

  // 排序：按时间倒序
  filtered.sort((a, b) => b.timestamp - a.timestamp)

  // 累加
  const total = filtered.reduce((sum, item) => {
    return sum + extractPointValue(item.value)
  }, 0)

  return { total, list: filtered }
}

// 合并原始数据和积分数据，生成最终 TableData
function updateTableData() {
  if (rawList.value.length === 0) {
    tableData.value = []
    return
  }

  // 1. 映射原始数据，计算每一行的积分和详情，以及新字段：手续费/积分
  const rows = rawList.value.map((item) => {
    const { total, list } = getBrowserPointsData(item.number || '')
    const feeAmt = item.feeAmt || 0
    // 计算 fee/point，处理分母为0的情况
    const feePerPoint = total > 0 ? feeAmt / total : 0

    return {
      ...item,
      pointsTotal: total,
      pointsDetails: list,
      feePerPoint,
    }
  })

  // 2. 计算合计行
  const summaryRow = calculateSummary(rows)

  // 3. 设置数据（此时是未排序的列表 + 合计行）
  const list = [summaryRow, ...rows]

  // 4. 如果当前有排序规则，应用排序
  if (currentSort.value.prop) {
    // 剔除合计行进行排序
    const dataRows = list.slice(1)
    const sorted = sortList(dataRows, currentSort.value.prop, currentSort.value.order)
    tableData.value = [list[0], ...sorted]
  }
  else {
    tableData.value = list
  }
}

// 提取出的排序逻辑
function sortList(list: TableRow[], prop: string, order: string) {
  return list.sort((a, b) => {
    const valA = Number(a[prop]) || 0
    const valB = Number(b[prop]) || 0
    return order === 'ascending' ? valA - valB : valB - valA
  })
}

function calculateSummary(list: TableRow[]): TableRow {
  let totalFeeAmt = 0
  let totalTotalAmt = 0
  let totalMakerAmt = 0
  let totalTakerAmt = 0
  let totalPoints = 0

  list.forEach((item) => {
    totalFeeAmt += (item.feeAmt || 0)
    totalTotalAmt += (item.totalAmt || 0)
    totalMakerAmt += (item.makerAmt || 0)
    totalTakerAmt += (item.takerAmt || 0)
    totalPoints += (item.pointsTotal || 0)
  })

  const avgFeeRate = totalTotalAmt > 0 ? totalFeeAmt / totalTotalAmt : 0
  // 合计行的 手续费/积分
  const summaryFeePerPoint = totalPoints > 0 ? totalFeeAmt / totalPoints : 0

  return {
    isSummary: true,
    number: '总计',
    totalAmt: totalTotalAmt,
    makerAmt: totalMakerAmt,
    takerAmt: totalTakerAmt,
    feeAmt: totalFeeAmt,
    feeRate: avgFeeRate,
    pointsTotal: totalPoints,
    feePerPoint: summaryFeePerPoint,
    // Summary 通常不聚合详情列表，保持为空即可
  }
}

// 查询交易数据
async function handleSearch() {
  if (!tradeDateRange.value || tradeDateRange.value.length !== 2)
    return

  tradeLoading.value = true
  try {
    const startTime = dayjs(tradeDateRange.value[0]).valueOf()
    const endTime = dayjs(tradeDateRange.value[1]).valueOf()

    const tradeList = await getBrowserTradeSum({ startTime, endTime })

    rawList.value = tradeList
    // 获取到新数据后，重新计算表格
    updateTableData()
  }
  finally {
    tradeLoading.value = false
  }
}

// 点击积分筛选
function handlePointsFilter() {
  appliedPointsDateRange.value = pointsDateRange.value
  updateTableData() // 重新计算积分列
}

// 取消积分筛选
function handlePointsFilterCancel() {
  appliedPointsDateRange.value = null
  updateTableData() // 重新计算积分列
}

function handleSortChange({ prop, order }: { prop: string, order: string }) {
  currentSort.value = { prop, order }

  if (tableData.value.length <= 1)
    return // 只有合计行或空

  const summaryRow = tableData.value[0]
  const dataRows = tableData.value.slice(1) // 排除合计行

  if (!order) {
    // 恢复默认顺序 (按 rawList 的顺序，但要带上最新的 pointsTotal)
    updateTableData()
    // 清除排序状态
    currentSort.value = { prop: '', order: '' }
  }
  else {
    const sorted = sortList([...dataRows], prop, order)
    tableData.value = [summaryRow, ...sorted]
  }
}

// 导出 Excel
function handleExport() {
  if (tableData.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  // 定义表头 (Key -> Excel Title)
  const headers = {
    index: '序号',
    number: '浏览器编号',
    totalAmt: '成交总量',
    makerAmt: '挂单量(Maker)',
    takerAmt: '吃单量(Taker)',
    feeAmt: '手续费',
    feeRate: '手续费率',
    pointsTotal: '积分汇总',
    feePerPoint: '手续费/积分',
  }

  // 格式化工具函数
  const fmt = (val: number | undefined, precision: number) =>
    (val !== undefined && val !== null) ? val.toFixed(precision) : '-'

  // 映射数据，使其与 UI 表现一致
  const formattedData = tableData.value.map((row, index) => {
    // 序号逻辑：合计行显示“总计”，其他行显示 index (注意 UI 上第一行是 Summary，index=0)
    const indexStr = row.isSummary ? '总计' : String(index)

    // 费率格式化：0.0012 -> 0.1200%
    const feeRateStr = row.feeRate ? `${(row.feeRate * 100).toFixed(4)}%` : '0.0000%'

    // 手续费/积分：分母为0时显示 '-'
    const feePerPointStr = (row.pointsTotal && row.pointsTotal !== 0)
      ? fmt(row.feePerPoint, 4)
      : '-'

    return {
      index: indexStr,
      number: row.number,
      totalAmt: fmt(row.totalAmt, 4),
      makerAmt: fmt(row.makerAmt, 4),
      takerAmt: fmt(row.takerAmt, 4),
      feeAmt: fmt(row.feeAmt, 4),
      feeRate: feeRateStr,
      pointsTotal: fmt(row.pointsTotal, 3),
      feePerPoint: feePerPointStr,
    }
  })

  const dateStr = dayjs().format('YYYYMMDD_HHmm')
  exportToExcel(headers, formattedData, `交易汇总_${dateStr}.xlsx`)
  ElMessage.success('导出成功')
}

function tableRowClassName({ row }: { row: TableRow }) {
  return row.isSummary ? 'summary-row' : ''
}
</script>

<template>
  <div class="trade-container p-4">
    <div class="mb-4 flex flex-wrap items-center gap-4 bg-white p-4 shadow-sm dark:bg-dark-800 rounded-lg">
      <!-- 左侧：交易查询 (主功能) -->
      <div class="flex items-center gap-2">
        <span class="text-sm font-bold text-gray-700 dark:text-gray-300">交易时间:</span>
        <el-date-picker
          v-model="tradeDateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm"
          :disabled-date="disabledDate"
          :clearable="false"
        />
      </div>

      <el-button type="primary" :icon="Search" :loading="tradeLoading" @click="handleSearch">
        查询交易
      </el-button>

      <!-- 导出按钮 -->
      <el-button type="success" :icon="Download" plain @click="handleExport">
        导出 Excel
      </el-button>

      <!-- 分隔线 -->
      <div class="mx-2 h-6 w-px bg-gray-300 dark:bg-gray-600" />

      <!-- 右侧：积分设置 (独立功能) -->
      <div class="flex items-center gap-2">
        <span class="text-sm font-bold text-orange-600 dark:text-orange-400">积分筛选:</span>
        <!-- 始终显示，但无数据时禁用 -->
        <el-date-picker
          v-model="pointsDateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="积分开始"
          end-placeholder="积分结束"
          format="YYYY-MM-DD"
          :clearable="false"
          :disabled="!hasAccountData"
        />
        <el-button
          type="warning"
          :icon="Filter"
          plain
          :disabled="!hasAccountData"
          @click="handlePointsFilter"
        >
          筛选
        </el-button>
        <el-button
          v-if="appliedPointsDateRange"
          type="info"
          plain
          :disabled="!hasAccountData"
          @click="handlePointsFilterCancel"
        >
          取消筛选
        </el-button>

        <!-- 同步缓存按钮 -->
        <el-tooltip content="点击从远程更新账户配置和积分数据" placement="top">
          <el-button
            :loading="accountLoading"
            :icon="Refresh"
            circle
            @click="handleUpdateCache"
          />
        </el-tooltip>
        <span v-if="lastCacheTime" class="text-xs text-gray-400">
          (更新于: {{ lastCacheTime }})
        </span>
      </div>
    </div>

    <!-- 表格 Loading 只受 tradeLoading 控制 -->
    <el-table
      v-loading="tradeLoading"
      :data="tableData"
      stripe
      border
      style="width: 100%"
      :row-class-name="tableRowClassName"
      @sort-change="handleSortChange"
    >
      <template #empty>
        <el-empty description="请点击查询按钮获取数据" />
      </template>

      <el-table-column label="序号" width="70" align="center" fixed>
        <template #default="scope">
          <span v-if="scope.row.isSummary" class="font-bold">总计</span>
          <span v-else>{{ scope.$index }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="number" label="浏览器编号" min-width="120" sortable="custom" fixed />

      <el-table-column
        prop="totalAmt"
        label="成交总量"
        min-width="140"
        align="right"
        sortable="custom"
        :formatter="formatNumber"
      >
        <template #default="scope">
          <span class="font-bold text-ep-color-primary">{{ scope.row.totalAmt?.toFixed(4) }}</span>
        </template>
      </el-table-column>

      <el-table-column
        prop="makerAmt"
        label="挂单量 (Maker)"
        min-width="140"
        align="right"
        sortable="custom"
        :formatter="formatNumber"
      />

      <el-table-column
        prop="takerAmt"
        label="吃单量 (Taker)"
        min-width="140"
        align="right"
        sortable="custom"
        :formatter="formatNumber"
      />

      <el-table-column
        prop="feeAmt"
        label="手续费"
        min-width="120"
        align="right"
        sortable="custom"
        :formatter="formatNumber"
      />

      <el-table-column
        prop="feeRate"
        label="手续费率"
        min-width="120"
        align="right"
        sortable="custom"
      >
        <template #default="scope">
          {{ (scope.row.feeRate * 100).toFixed(4) }}%
        </template>
      </el-table-column>

      <!-- 积分列 -->
      <el-table-column
        prop="pointsTotal"
        :label="pointsLabel"
        min-width="150"
        align="right"
        sortable="custom"
      >
        <template #default="scope">
          <!-- 情况1：无账户数据且非合计行 -->
          <span v-if="!hasAccountData && !scope.row.isSummary" class="text-xs text-gray-300">
            暂无数据
          </span>

          <!-- 情况2：合计行 (直接展示数值) -->
          <span v-else-if="scope.row.isSummary" class="font-bold text-orange-600">
            {{ scope.row.pointsTotal?.toFixed(3) }}
          </span>

          <!-- 情况3：有详情数据 (Tooltip 展示) -->
          <el-tooltip
            v-else-if="scope.row.pointsDetails && scope.row.pointsDetails.length > 0"
            placement="top"
            effect="light"
          >
            <template #content>
              <div class="max-h-60 max-w-sm overflow-y-auto pr-2">
                <div v-for="(p, i) in scope.row.pointsDetails" :key="i" class="flex items-center gap-2 border-b border-gray-100 py-1 text-xs last:border-0">
                  <span class="min-w-[80px] font-mono text-gray-500">{{ p.dateStr }}</span>
                  <span class="flex-1 truncate text-gray-700" :title="p.description">{{ p.description }}</span>
                  <span class="whitespace-nowrap font-bold text-orange-600">{{ p.value }}</span>
                </div>
              </div>
            </template>
            <!-- 去除了下划线样式，仅保留 cursor-help -->
            <span class="cursor-help font-bold text-orange-600">
              {{ scope.row.pointsTotal?.toFixed(3) }}
            </span>
          </el-tooltip>

          <!-- 情况4：有数据但无详情 (直接展示数值) -->
          <span v-else class="font-bold text-orange-600">
            {{ scope.row.pointsTotal?.toFixed(3) }}
          </span>
        </template>
      </el-table-column>

      <!-- 新增：手续费/积分 -->
      <el-table-column
        prop="feePerPoint"
        label="手续费/积分"
        min-width="140"
        align="right"
        sortable="custom"
        :formatter="formatNumber"
      >
        <template #default="scope">
          <!-- 如果积分为0，显示 - 或 Inf -->
          <span v-if="scope.row.pointsTotal === 0" class="text-gray-300">-</span>
          <span v-else class="font-semibold text-blue-600">{{ scope.row.feePerPoint?.toFixed(4) }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.trade-container {
  max-width: 100%;
  margin: 0 auto;
}

:deep(.el-table .summary-row) {
  background-color: var(--ep-fill-color-light) !important;
  font-weight: bold;
  color: var(--ep-text-color-primary);
}

:deep(.el-table .summary-row:hover > td) {
  background-color: var(--ep-fill-color-light) !important;
}
</style>
