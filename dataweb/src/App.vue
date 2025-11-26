<template>
  <div class="app-container">
    <h1 class="app-title">PLOY/OP数据</h1>
    
    <!-- 顶部操作按钮 -->
    <div class="toolbar">
      <el-button type="primary" @click="addRows(1)">增加一行</el-button>
      <el-button type="primary" @click="addRows(10)">增加十行</el-button>
      <el-button type="success" @click="saveAll" :loading="saving">保存所有数据</el-button>
      <el-button type="info" @click="loadData" :loading="loading">刷新列表</el-button>
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
        <el-button type="primary" size="small" @click="applyFilters">应用筛选</el-button>
        <el-button size="small" @click="clearFilters">清除筛选</el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="filteredTableData" 
      border 
      style="width: 100%"
      :max-height="600"
      v-loading="loading"
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

      <el-table-column label="仓位抓取时间" width="150" align="center" fixed="right" sortable :sort-method="(a, b) => sortByNumber(a.d, b.d)">
        <template #default="scope">
          <div class="capture-time-cell">
            <el-icon><Clock /></el-icon>
            <span>{{ formatRelativeTime(scope.row.d) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="250" align="center" fixed="right">
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'
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
let nextId = 1

/**
 * 筛选条件
 */
const filters = ref({
  computeGroup: '',
  fingerprintNo: '',
  platform: ''
})

const activeFilters = ref({
  computeGroup: [],
  fingerprintNo: [],
  platform: ''
})

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
    platform: filters.value.platform
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
    platform: ''
  }
  activeFilters.value = {
    computeGroup: [],
    fingerprintNo: [],
    platform: ''
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
  
  return result
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
          positions.push({
            title: parts[0].trim(),
            option: parts[1].trim(),
            amount: parts[2].trim(),
            avgPrice: parts[3].trim()
          })
        }
      } else {
        // 兼容旧格式（逗号分隔符）
        const parts = item.split(',')
        if (parts.length >= 4) {
          positions.push({
            title: parts[0].trim(),
            option: parts[1].trim(),
            amount: parts[2].trim(),
            avgPrice: parts[3].trim()
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
 * 加载数据列表
 */
const loadData = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`)
    
    if (response.data && response.data.data) {
      tableData.value = response.data.data.map((item, index) => ({
        ...item,
        index: index + 1,
        platform: item.e || item.platform || 'OP',
        refreshing: false
      }))
      
      nextId = Math.max(...tableData.value.map(item => item.id || 0)) + 1
      ElMessage.success('数据加载成功')
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
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
    
    // 2. 等待一段时间让任务执行（根据平台不同，OP约20秒，Polymarket约30秒）
    const waitTime = row.platform === 'OP' ? 25000 : 35000
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
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadData()
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
</style>

