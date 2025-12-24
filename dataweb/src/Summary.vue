<template>
  <div class="summary-page-container" v-loading="loading" element-loading-text="正在加载数据并解析...">
    <div class="page-header">
      <h1 class="page-title">数据总计</h1>
      <div class="header-actions">
        <el-button type="primary" @click="loadAndCalculate" :loading="loading">
          刷新数据
        </el-button>
        <el-button type="success" @click="saveSummary" :loading="saving">
          保存总计
        </el-button>
        <el-button type="info" @click="goBack">
          返回列表
        </el-button>
      </div>
    </div>

    <!-- 新的总计数据 -->
    <div class="summary-section">
      <h2 class="section-title">
        📊 当前总计
        <span v-if="lastUpdateTime" class="update-time">
          （更新时间：{{ formatTime(lastUpdateTime) }}）
        </span>
      </h2>
      
      <div class="summary-content">
        <div class="summary-item">
          <span class="summary-label">余额总计:</span>
          <span class="summary-value">{{ currentSummary.totalBalance }}</span>
          <span v-if="savedSummary" class="change-value" :class="getChangeClass(calculateChange(currentSummary.totalBalance, savedSummary.totalBalance))">
            {{ formatChange(calculateChange(currentSummary.totalBalance, savedSummary.totalBalance)) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Portfolio总计:</span>
          <span class="summary-value">{{ currentSummary.totalPortfolio }}</span>
          <span v-if="savedSummary" class="change-value" :class="getChangeClass(calculateChange(currentSummary.totalPortfolio, savedSummary.totalPortfolio))">
            {{ formatChange(calculateChange(currentSummary.totalPortfolio, savedSummary.totalPortfolio)) }}
          </span>
        </div>
        <div class="summary-item summary-positions">
          <span class="summary-label">持有仓位总计:</span>
          <div class="summary-positions-list">
            <div v-if="currentSummary.positionSummary.length === 0" class="empty-summary">
              无持仓
            </div>
            <div 
              v-for="(pos, idx) in currentSummary.positionSummary" 
              :key="`current-${pos.title}-${idx}`" 
              class="summary-position-item"
            >
              <span class="position-title-summary">{{ pos.title }}</span>
              <div class="position-values">
                <el-tag 
                  :type="parseFloat(pos.amount) >= 0 ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ pos.amount }}
                </el-tag>
                <span 
                  v-if="savedSummary && getSavedPositionAmount(pos.title) !== null" 
                  class="change-value" 
                  :class="getChangeClass(calculateChange(parseFloat(pos.amount), getSavedPositionAmount(pos.title)))"
                >
                  {{ formatChange(calculateChange(parseFloat(pos.amount), getSavedPositionAmount(pos.title))) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 保存的总计数据 -->
    <div v-if="savedSummary" class="summary-section saved-section">
      <h2 class="section-title">
        💾 已保存总计
        <span class="save-time">
          （保存时间：{{ formatTime(savedSummary.saveTime) }}）
        </span>
      </h2>
      
      <div class="summary-content">
        <div class="summary-item">
          <span class="summary-label">余额总计:</span>
          <span class="summary-value">{{ savedSummary.totalBalance }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Portfolio总计:</span>
          <span class="summary-value">{{ savedSummary.totalPortfolio }}</span>
        </div>
        <div class="summary-item summary-positions">
          <span class="summary-label">持有仓位总计:</span>
          <div class="summary-positions-list">
            <div v-if="savedSummary.positionSummary.length === 0" class="empty-summary">
              无持仓
            </div>
            <div 
              v-for="(pos, idx) in savedSummary.positionSummary" 
              :key="`saved-${pos.title}-${idx}`" 
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
    </div>

    <!-- 如果没有保存的数据 -->
    <div v-else class="no-saved-data">
      <el-empty description="暂无保存的总计数据，点击保存按钮保存当前总计" />
    </div>

    <!-- 链上数据总计 -->
    <div class="summary-section chain-section">
      <h2 class="section-title">
        🔗 链上数据总计
        <span v-if="chainSummary.updateTime" class="update-time">
          （更新时间：{{ formatTime(chainSummary.updateTime) }}）
        </span>
        <el-button 
          type="primary" 
          size="small" 
          @click="loadChainStats" 
          :loading="loadingChainData"
          style="margin-left: 15px;"
        >
          刷新链上数据
        </el-button>
      </h2>
      
      <div class="summary-content">
        <div class="summary-item summary-positions">
          <span class="summary-label">链上持仓总计:</span>
          <div class="summary-positions-list">
            <div v-if="chainSummary.positionSummary.length === 0" class="empty-summary">
              <span v-if="loadingChainData">正在加载...</span>
              <span v-else>无链上持仓数据</span>
            </div>
            <div 
              v-for="(pos, idx) in chainSummary.positionSummary" 
              :key="`chain-${pos.title}-${idx}`" 
              class="summary-position-item"
            >
              <span class="position-title-summary">{{ pos.title }}</span>
              <div class="position-values">
                <el-tag 
                  :type="parseFloat(pos.amount) >= 0 ? 'success' : 'danger'" 
                  size="small"
                >
                  链上: {{ pos.amount }}
                </el-tag>
                <span v-if="getPositionDifference(pos.title) !== null" class="difference-value" :class="getDifferenceClass(getPositionDifference(pos.title))">
                  信息差: {{ formatDifference(getPositionDifference(pos.title)) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'
const CHAIN_STATS_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/markets/stats'

const loading = ref(false)
const saving = ref(false)
const lastUpdateTime = ref(null)
const currentSummary = ref({
  totalBalance: '0.00',
  totalPortfolio: '0.00',
  positionSummary: []
})
const savedSummary = ref(null)
const chainSummary = ref({
  positionSummary: [],
  updateTime: null,
  participantCount: 0
})
const loadingChainData = ref(false)

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
        
        // 特殊处理：First to 5k: Gold or ETH? 市场
        if (title.includes('First to 5k') && (option === 'ETH' || option === 'GOLD')) {
          const numAmount = parseFloat(amount)
          if (!isNaN(numAmount)) {
            amount = option === 'GOLD' 
              ? Math.abs(numAmount).toFixed(2)
              : (-Math.abs(numAmount)).toFixed(2)
          }
        }
        
        // 特殊处理：Monad vs MegaETH — who has the higher FDV one day after launch? 市场
        if (title.includes('Monad vs MegaETH') && (option === 'Monad' || option === 'MegaETH')) {
          const numAmount = parseFloat(amount)
          if (!isNaN(numAmount)) {
            amount = option === 'Monad'
              ? Math.abs(numAmount).toFixed(2)
              : (-Math.abs(numAmount)).toFixed(2)
          }
        }
        
        positions.push({
          title: title,
          option: option,
          amount: amount,
          avgPrice: avgPrice
        })
      } else if (partsLength >= 3 && !isNewFormat) {
        positions.push({
          title: parts[0].trim(),
          option: parts[1].trim(),
          amount: parts[2].trim(),
          avgPrice: ''
        })
      } else if (partsLength >= 2 && !isNewFormat) {
        positions.push({
          title: parts[0].trim(),
          option: '',
          amount: parts[1].trim(),
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
 * 加载数据并计算总计（分批解析，避免阻塞）
 */
const loadAndCalculate = async () => {
  loading.value = true
  
  try {
    console.log('[数据总计] 开始加载数据...')
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`)
    
    if (response.data && response.data.data) {
      const data = response.data.data
      console.log(`[数据总计] 获取到 ${data.length} 条数据，开始解析...`)
      
      let totalBalance = 0
      let totalPortfolio = 0
      const positionMap = new Map()
      
      // 分批解析，避免阻塞UI
      const batchSize = 10
      for (let i = 0; i < data.length; i += batchSize) {
        const batch = data.slice(i, Math.min(i + batchSize, data.length))
        
        // 处理这一批数据
        for (const row of batch) {
          // 计算余额总计
          totalBalance += parseFloat(row.balance) || 0
          
          // 计算Portfolio总计
          totalPortfolio += parseFloat(row.c) || 0
          
          // 解析并计算持有仓位总计
          if (row.a) {
            const positions = parsePositions(row.a)
            for (const pos of positions) {
              const title = pos.title
              const amount = parseFloat(pos.amount) || 0
              positionMap.set(title, (positionMap.get(title) || 0) + amount)
            }
          }
        }
        
        // 让出主线程，避免阻塞
        if (i + batchSize < data.length) {
          await new Promise(resolve => {
            if (typeof requestIdleCallback !== 'undefined') {
              requestIdleCallback(() => resolve(), { timeout: 50 })
            } else {
              setTimeout(resolve, 10)
            }
          })
        }
      }
      
      console.log('[数据总计] 解析完成，开始计算统计...')
      
      // 转换为数组并排序
      const positionSummary = []
      for (const [title, amount] of positionMap.entries()) {
        if (Math.abs(amount) > 0.01) {
          positionSummary.push({ title, amount: amount.toFixed(2) })
        }
      }
      
      positionSummary.sort((a, b) => Math.abs(parseFloat(b.amount)) - Math.abs(parseFloat(a.amount)))
      
      currentSummary.value = {
        totalBalance: totalBalance.toFixed(2),
        totalPortfolio: totalPortfolio.toFixed(2),
        positionSummary
      }
      
      lastUpdateTime.value = Date.now()
      console.log('[数据总计] 计算完成')
      ElMessage.success(`数据加载并计算完成，共处理 ${data.length} 条数据`)
    } else {
      ElMessage.warning('未获取到数据')
    }
  } catch (error) {
    console.error('[数据总计] 加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 保存总计数据到本地
 */
const saveSummary = () => {
  try {
    const summaryToSave = {
      ...currentSummary.value,
      saveTime: Date.now()
    }
    
    localStorage.setItem('savedSummary', JSON.stringify(summaryToSave))
    savedSummary.value = summaryToSave
    ElMessage.success('总计数据已保存')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

/**
 * 加载保存的总计数据
 */
const loadSavedSummary = () => {
  try {
    const saved = localStorage.getItem('savedSummary')
    if (saved) {
      savedSummary.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('加载保存的数据失败:', error)
  }
}

/**
 * 计算变化值
 */
const calculateChange = (current, saved) => {
  const currentNum = parseFloat(current) || 0
  const savedNum = parseFloat(saved) || 0
  return currentNum - savedNum
}

/**
 * 格式化变化值
 */
const formatChange = (change) => {
  if (change === 0) return '0.00'
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}`
}

/**
 * 获取变化值的样式类
 */
const getChangeClass = (change) => {
  if (change > 0) return 'change-positive'
  if (change < 0) return 'change-negative'
  return 'change-zero'
}

/**
 * 获取保存的仓位数量
 */
const getSavedPositionAmount = (title) => {
  if (!savedSummary.value || !savedSummary.value.positionSummary) {
    return null
  }
  
  const savedPos = savedSummary.value.positionSummary.find(p => p.title === title)
  return savedPos ? parseFloat(savedPos.amount) : null
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
 * 加载链上数据总计
 */
const loadChainStats = async () => {
  loadingChainData.value = true
  
  try {
    console.log('[链上数据总计] 开始加载链上数据...')
    const response = await axios.get(CHAIN_STATS_API_URL)
    
    if (response.data && response.data.items && Array.isArray(response.data.items)) {
      const positionMap = new Map()
      
      // 处理每个市场的数据
      // 如果有相同的基础title（去除###后的部分），则累加数据
      for (const item of response.data.items) {
        if (item.title) {
          const fullTitle = item.title.trim()
          const titleKey = fullTitle.split('###')[0].trim()  // 去除 ### 后面的部分作为key
          const yesTotal = parseFloat(item.yes_total || 0)
          const noTotal = parseFloat(item.no_total || 0)
          const amount = yesTotal - noTotal
          
          // 只记录数量不为0的市场
          if (Math.abs(amount) > 0.01) {
            // 检查是否已有相同的基础title（去除###后的部分）
            let found = false
            for (const [key, value] of positionMap.entries()) {
              const existingKey = key.split('###')[0].trim()
              if (existingKey === titleKey) {
                // 找到相同基础title的，累加数据
                positionMap.set(key, value + amount)
                found = true
                break
              }
            }
            
            if (!found) {
              // 新建条目，使用完整title作为key
              positionMap.set(fullTitle, amount)
            }
          }
        }
      }
      
      // 转换为数组并排序
      const positionSummary = []
      for (const [title, amount] of positionMap.entries()) {
        positionSummary.push({ title, amount: amount.toFixed(2) })
      }
      
      positionSummary.sort((a, b) => Math.abs(parseFloat(b.amount)) - Math.abs(parseFloat(a.amount)))
      
      chainSummary.value = {
        positionSummary,
        updateTime: Date.now()
      }
      
      console.log('[链上数据总计] 加载完成，共处理', positionSummary.length, '个市场')
      console.log('[链上数据总计] 链上数据示例:', positionSummary.slice(0, 3))
      ElMessage.success(`链上数据加载完成，共 ${positionSummary.length} 个市场`)
    } else {
      ElMessage.warning('未获取到链上数据')
    }
  } catch (error) {
    console.error('[链上数据总计] 加载失败:', error)
    ElMessage.error('加载链上数据失败: ' + (error.message || '网络错误'))
  } finally {
    loadingChainData.value = false
  }
}

/**
 * 获取持有仓位的数量
 */
const getHoldingPositionAmount = (title) => {
  if (!currentSummary.value || !currentSummary.value.positionSummary) {
    return null
  }
  
  // 尝试精确匹配
  const exactMatch = currentSummary.value.positionSummary.find(p => p.title === title)
  if (exactMatch) {
    return parseFloat(exactMatch.amount) || 0
  }
  
  // 尝试匹配基础title（去除###后的部分）
  const titleKey = title.split('###')[0].trim()
  for (const pos of currentSummary.value.positionSummary) {
    const posTitleKey = pos.title.split('###')[0].trim()
    if (posTitleKey === titleKey) {
      return parseFloat(pos.amount) || 0
    }
  }
  
  return null
}

/**
 * 计算信息差（持有仓位 - 链上仓位）
 */
const getPositionDifference = (chainTitle) => {
  const chainAmount = parseFloat(chainSummary.value.positionSummary.find(p => p.title === chainTitle)?.amount || 0)
  const holdingAmount = getHoldingPositionAmount(chainTitle)
  
  if (holdingAmount === null) {
    return null  // 没有持有仓位数据
  }
  
  return holdingAmount - chainAmount
}

/**
 * 格式化差异值
 */
const formatDifference = (diff) => {
  if (diff === null) return '--'
  const sign = diff > 0 ? '+' : ''
  return `${sign}${diff.toFixed(2)}`
}

/**
 * 获取差异值的样式类
 */
const getDifferenceClass = (diff) => {
  if (diff === null) return 'difference-zero'
  if (diff > 0) return 'difference-positive'
  if (diff < 0) return 'difference-negative'
  return 'difference-zero'
}

/**
 * 返回列表页面
 */
const goBack = () => {
  // 通过事件通知父组件切换页面
  window.dispatchEvent(new CustomEvent('navigate-to-list'))
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  console.log('[数据总计] 组件已挂载，开始加载数据')
  loadSavedSummary()
  // 延迟一下，确保页面渲染完成
  setTimeout(() => {
    loadAndCalculate()
    loadChainStats()  // 同时加载链上数据
  }, 100)
})
</script>

<style scoped>
.summary-page-container {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.page-title {
  font-size: 28px;
  color: #333;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.summary-section {
  margin-bottom: 30px;
  padding: 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.saved-section {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.chain-section {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 20px 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  gap: 15px;
}

.update-time,
.save-time {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: none;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 15px;
  background-color: rgba(255, 255, 255, 0.15);
  padding: 15px 20px;
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

.change-value {
  font-size: 16px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 4px;
  margin-left: 10px;
}

.change-positive {
  background-color: rgba(103, 194, 58, 0.3);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.5);
}

.change-negative {
  background-color: rgba(245, 108, 108, 0.3);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.5);
}

.change-zero {
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.summary-positions {
  flex-direction: column;
  align-items: flex-start;
}

.summary-positions-list {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 12px;
  margin-top: 15px;
}

.empty-summary {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-style: italic;
  padding: 20px;
  text-align: center;
}

.summary-position-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 12px 16px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition: all 0.3s;
}

.summary-position-item:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateX(5px);
}

.position-title-summary {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
  flex: 1;
  line-height: 1.4;
}

.position-values {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.difference-value {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  white-space: nowrap;
}

.difference-positive {
  background-color: rgba(103, 194, 58, 0.2);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.4);
}

.difference-negative {
  background-color: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.4);
}

.difference-zero {
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.no-saved-data {
  padding: 40px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}
</style>

