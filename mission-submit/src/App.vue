<template>
  <div class="app">
    <div class="container">
      <h1 style="margin-bottom: 24px; color: #333;">页面5-取消挂单</h1>

      <!-- 映射状态和加载按钮 -->
      <section class="section">
        <div class="mapping-status">
          <div class="mapping-status-item">
            <div 
              class="status-indicator" 
              :class="{
                'success': accountConfigLoaded && accountConfigData.length > 0,
                'error': accountConfigLoaded && accountConfigData.length === 0,
                'loading': isLoadingAccountConfig
              }"
            ></div>
            <span>账户配置映射: {{ accountConfigData.length > 0 ? `${accountConfigData.length} 条` : '未加载' }}</span>
          </div>
          <div class="mapping-status-item">
            <div 
              class="status-indicator" 
              :class="{
                'success': exchangeConfigLoaded && configList.length > 0,
                'error': exchangeConfigLoaded && configList.length === 0,
                'loading': isLoadingExchangeConfig
              }"
            ></div>
            <span>交易所配置: {{ configList.length > 0 ? `${configList.length} 条` : '未加载' }}</span>
          </div>
          <button 
            class="btn btn-info" 
            @click="loadMappings"
            :disabled="isLoadingAccountConfig || isLoadingExchangeConfig"
          >
            {{ (isLoadingAccountConfig || isLoadingExchangeConfig) ? '加载中...' : '加载映射' }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="message.text" class="message" :class="`message-${message.type}`">
        {{ message.text }}
      </div>

      <!-- 确认弹窗 -->
      <div v-if="showConfirmDialog" class="modal-overlay" @click="showConfirmDialog = false">
        <div class="modal-content" @click.stop>
          <h3>确认清除任务</h3>
          <p>您确定要清除以下电脑组的所有任务吗？</p>
          <div class="confirm-group-list">
            <span v-for="groupNo in validCleanGroupNos" :key="groupNo" class="group-tag">{{ groupNo }}</span>
          </div>
          <p style="color: #dc3545; font-size: 14px; margin-top: 12px;">此操作不可撤销，请谨慎操作！</p>
          <div class="modal-actions">
            <button class="btn btn-danger" @click="confirmCleanMission">确认清除</button>
            <button class="btn btn-secondary" @click="showConfirmDialog = false">取消</button>
          </div>
        </div>
      </div>

      <!-- 失败列表 -->
      <section v-if="failedBrowserIds.length > 0" class="section">
        <h2>提交失败的浏览器ID</h2>
        <div class="failed-list">
          <div class="failed-item" v-for="(item, index) in failedBrowserIds" :key="index">
            <span class="failed-id">浏览器ID: {{ item.browserId }}</span>
            <span class="failed-error" v-if="item.error">错误: {{ item.error }}</span>
          </div>
          <div class="failed-actions">
            <button class="btn btn-primary" @click="retryFailed" :disabled="isRetrying">
              {{ isRetrying ? '重试中...' : '重试失败的浏览器ID' }}
            </button>
            <button class="btn btn-secondary" @click="clearFailedList">清除列表</button>
          </div>
        </div>
      </section>

      <!-- 清除任务表单 -->
      <section class="section">
        <h2>清除任务</h2>
        <div class="task-form">
          <div class="form-row">
            <div class="form-group">
              <label for="cleanGroupNos">电脑组 *</label>
              <input
                id="cleanGroupNos"
                v-model="cleanGroupNosInput"
                type="text"
                placeholder="支持格式: 1 或 1,2,3 或 1-40"
              />
              <div v-if="parsedCleanGroupNos.length > 0" style="margin-top: 8px; color: #666; font-size: 12px;">
                已解析: {{ parsedCleanGroupNos.join(', ') }}
              </div>
              <div v-if="validCleanGroupNos.length > 0" style="margin-top: 8px; color: #28a745; font-size: 12px;">
                有效电脑组: {{ validCleanGroupNos.join(', ') }}
              </div>
              <div v-if="parsedCleanGroupNos.length > 0 && validCleanGroupNos.length === 0" style="margin-top: 8px; color: #dc3545; font-size: 12px;">
                警告: 输入的电脑组在配置中不存在
              </div>
            </div>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-danger" @click="handleCleanMission" :disabled="isCleaning || validCleanGroupNos.length === 0">
              <span v-if="isCleaning">清除中...</span>
              <span v-else>清除任务</span>
            </button>
            <button type="button" class="btn btn-secondary" @click="cleanGroupNosInput = ''">
              清空
            </button>
          </div>
        </div>
      </section>

      <!-- 任务提交表单 -->
      <section class="section">
        <h2>提交任务</h2>
        <form @submit.prevent="handleSubmit" class="task-form">
          <!-- 选择类型：浏览器id或电脑组 -->
          <div class="form-row">
            <div class="form-group">
              <label>选择类型 *</label>
              <div class="radio-group">
                <div class="radio-option">
                  <input 
                    type="radio" 
                    id="type-browser" 
                    value="browser" 
                    v-model="inputType"
                  />
                  <label for="type-browser">浏览器ID</label>
                </div>
                <div class="radio-option">
                  <input 
                    type="radio" 
                    id="type-group" 
                    value="group" 
                    v-model="inputType"
                  />
                  <label for="type-group">电脑组</label>
                </div>
              </div>
            </div>
          </div>

          <!-- 浏览器ID输入框 -->
          <div class="form-row" v-if="inputType === 'browser'">
            <div class="form-group">
              <label for="browserIds">浏览器ID *</label>
              <input
                id="browserIds"
                v-model="browserIdsInput"
                type="text"
                placeholder="支持格式: 201 或 201,202,203 或 201-203"
                required
              />
              <div v-if="parsedBrowserIds.length > 0" style="margin-top: 8px; color: #666; font-size: 12px;">
                已解析: {{ parsedBrowserIds.join(', ') }}
              </div>
            </div>
          </div>

          <!-- 电脑组输入框 -->
          <div class="form-row" v-if="inputType === 'group'">
            <div class="form-group">
              <label for="groupNos">电脑组 *</label>
              <input
                id="groupNos"
                v-model="groupNosInput"
                type="text"
                placeholder="支持格式: 1 或 1,2,3 或 1-3"
                required
              />
              <div v-if="parsedGroupNos.length > 0" style="margin-top: 8px; color: #666; font-size: 12px;">
                已解析: {{ parsedGroupNos.join(', ') }}
              </div>
            </div>
          </div>

          <!-- 事件选择 -->
          <div class="form-row">
            <div class="form-group">
              <label for="trendingId">事件 *</label>
              <div class="trending-autocomplete-wrapper">
                <input
                  id="trendingId"
                  v-model="trendingSearchText"
                  type="text"
                  placeholder="输入文字筛选或选择事件（默认：全部）"
                  @input="onTrendingSearchInput"
                  @focus="showTrendingDropdown = true"
                  @blur="handleTrendingBlur"
                  autocomplete="off"
                />
                <div 
                  v-if="showTrendingDropdown && (filteredTrendingList.length > 0 || trendingSearchText.trim() === '' || trendingSearchText.toLowerCase() === '全部' || trendingSearchText.toLowerCase() === 'all')" 
                  class="trending-dropdown"
                >
                  <!-- 全部选项 -->
                  <div
                    v-if="trendingSearchText.trim() === '' || trendingSearchText.toLowerCase() === '全部' || trendingSearchText.toLowerCase() === 'all'"
                    class="trending-dropdown-item"
                    @mousedown.prevent="selectTrendingAll"
                  >
                    全部
                  </div>
                  <!-- 其他选项 -->
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
              <div v-if="selectedTrending" style="margin-top: 8px; color: #666; font-size: 12px;">
                已选择: {{ selectedTrending === 'all' ? '全部' : selectedTrending }}
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting || isUpdatingPosition">
              <span v-if="isSubmitting">提交中...</span>
              <span v-else>撤单并更新</span>
            </button>
            <button type="button" class="btn btn-primary" @click="handlePositionUpdate" :disabled="isSubmitting || isUpdatingPosition">
              <span v-if="isUpdatingPosition">更新中...</span>
              <span v-else>更新仓位</span>
            </button>
            <button type="button" class="btn btn-secondary" @click="resetForm">
              重置
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

// 响应式数据
const accountConfigData = ref([])
const configList = ref([])
const accountConfigLoaded = ref(false)
const exchangeConfigLoaded = ref(false)
const isLoadingAccountConfig = ref(false)
const isLoadingExchangeConfig = ref(false)
const message = ref({ text: '', type: '' })

// 表单数据
const inputType = ref('browser') // 'browser' 或 'group'
const browserIdsInput = ref('')
const groupNosInput = ref('')
const selectedTrending = ref('all') // 默认全部
const trendingSearchText = ref('全部') // 默认显示"全部"
const showTrendingDropdown = ref(false)
const isSubmitting = ref(false)
const isUpdatingPosition = ref(false)
const isRetrying = ref(false)
const failedBrowserIds = ref([]) // 存储失败的浏览器ID [{browserId, error, groupNo, tp1}]

// 清除任务相关
const cleanGroupNosInput = ref('')
const isCleaning = ref(false)
const showConfirmDialog = ref(false)

// 映射关系
const browserToGroupMap = ref({}) // 浏览器ID -> 电脑组
const groupToBrowserMap = ref({}) // 电脑组 -> 浏览器ID数组

/**
 * 解析输入字符串（支持单个、逗号分隔、区间）
 * @param {string} input - 输入字符串
 * @returns {Array<number>} - 解析后的数字数组
 */
const parseInput = (input) => {
  if (!input || !input.trim()) {
    return []
  }

  const result = new Set()
  const parts = input.split(',').map(s => s.trim()).filter(s => s)

  for (const part of parts) {
    if (part.includes('-')) {
      // 区间格式：201-203
      const [start, end] = part.split('-').map(s => s.trim())
      const startNum = parseInt(start)
      const endNum = parseInt(end)
      
      if (!isNaN(startNum) && !isNaN(endNum) && startNum <= endNum) {
        for (let i = startNum; i <= endNum; i++) {
          result.add(i)
        }
      }
    } else {
      // 单个数字
      const num = parseInt(part)
      if (!isNaN(num)) {
        result.add(num)
      }
    }
  }

  return Array.from(result).sort((a, b) => a - b)
}

// 解析后的浏览器ID列表
const parsedBrowserIds = computed(() => {
  return parseInput(browserIdsInput.value)
})

// 解析后的电脑组列表
const parsedGroupNos = computed(() => {
  return parseInput(groupNosInput.value)
})

// 解析后的清除任务电脑组列表
const parsedCleanGroupNos = computed(() => {
  return parseInput(cleanGroupNosInput.value)
})

// 验证清除任务的电脑组是否存在（从配置中检查）
const validCleanGroupNos = computed(() => {
  if (parsedCleanGroupNos.value.length === 0) {
    return []
  }
  
  // 从groupToBrowserMap中获取所有存在的电脑组
  const existingGroups = Object.keys(groupToBrowserMap.value).map(Number)
  
  // 过滤出存在的电脑组
  return parsedCleanGroupNos.value.filter(groupNo => existingGroups.includes(groupNo)).sort((a, b) => a - b)
})

/**
 * 过滤后的Trending列表
 */
const filteredTrendingList = computed(() => {
  if (!trendingSearchText.value || trendingSearchText.value.trim() === '') {
    return configList.value
  }
  const searchLower = trendingSearchText.value.toLowerCase().trim()
  return configList.value.filter(config => {
    return config.trending.toLowerCase().includes(searchLower)
  })
})

/**
 * Trending搜索输入处理
 */
const onTrendingSearchInput = () => {
  showTrendingDropdown.value = true
  
  // 如果输入"全部"或"all"，自动选择全部
  const inputLower = trendingSearchText.value.toLowerCase().trim()
  if (inputLower === '全部' || inputLower === 'all' || inputLower === '') {
    selectedTrending.value = 'all'
    return
  }
  
  // 如果输入的内容完全匹配某个选项，自动选择
  const exactMatch = configList.value.find(config => {
    return config.trending === trendingSearchText.value
  })
  if (exactMatch) {
    selectedTrending.value = exactMatch.trending
  }
}

/**
 * 选择Trending
 */
const selectTrending = (config) => {
  selectedTrending.value = config.trending
  trendingSearchText.value = config.trending
  showTrendingDropdown.value = false
}

/**
 * 选择"全部"
 */
const selectTrendingAll = () => {
  selectedTrending.value = 'all'
  trendingSearchText.value = '全部'
  showTrendingDropdown.value = false
}

/**
 * Trending输入框失焦处理
 */
const handleTrendingBlur = () => {
  // 延迟隐藏，以便点击下拉项时能触发
  setTimeout(() => {
    showTrendingDropdown.value = false
  }, 200)
}

/**
 * 显示消息
 */
const showMessage = (text, type = 'info') => {
  message.value = { text, type }
  setTimeout(() => {
    message.value = { text: '', type: '' }
  }, 3000)
}

/**
 * 获取账户配置
 */
const fetchAccountConfig = async () => {
  isLoadingAccountConfig.value = true
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache')
    
    if (response.data && response.data.data) {
      accountConfigData.value = response.data.data
      
      // 建立浏览器编号到组号的映射（同时支持字符串和数字作为key）
      const browserToGroup = {}
      const groupToBrowser = {}
      
      response.data.data.forEach(item => {
        if (item.fingerprintNo && item.computeGroup) {
          const fingerprintNo = item.fingerprintNo
          const fingerprintNoStr = String(fingerprintNo)
          const fingerprintNoNum = Number(fingerprintNo)
          const computeGroup = item.computeGroup
          
          // 浏览器ID -> 电脑组
          browserToGroup[fingerprintNoStr] = computeGroup
          if (!isNaN(fingerprintNoNum)) {
            browserToGroup[fingerprintNoNum] = computeGroup
          }
          
          // 电脑组 -> 浏览器ID数组（反向映射）
          if (!groupToBrowser[computeGroup]) {
            groupToBrowser[computeGroup] = []
          }
          if (!groupToBrowser[computeGroup].includes(fingerprintNoNum)) {
            groupToBrowser[computeGroup].push(fingerprintNoNum)
          }
        }
      })
      
      browserToGroupMap.value = browserToGroup
      groupToBrowserMap.value = groupToBrowser
      
      accountConfigLoaded.value = true
      console.log(`账户配置加载成功，共 ${response.data.data.length} 条记录`)
      console.log('浏览器编号到组号映射:', browserToGroup)
      console.log('组号到浏览器编号映射:', groupToBrowser)
      
      return response.data.data.length > 0
    } else {
      console.warn('获取账户配置失败: 无数据')
      accountConfigLoaded.value = true
      return false
    }
  } catch (error) {
    console.error('获取账户配置失败:', error)
    accountConfigLoaded.value = true
    showMessage('获取账户配置失败: ' + (error.message || '未知错误'), 'error')
    return false
  } finally {
    isLoadingAccountConfig.value = false
  }
}

/**
 * 获取交易所配置
 */
const fetchExchangeConfig = async () => {
  isLoadingExchangeConfig.value = true
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/exchangeConfig')
    
    if (response.data && response.data.code === 0) {
      const data = response.data.data
      
      // 设置配置列表
      configList.value = data.configList || []
      
      exchangeConfigLoaded.value = true
      console.log(`配置加载成功：${configList.value.length} 个Trending`)
      
      return configList.value.length > 0
    } else {
      console.warn(`获取配置失败: ${response.data?.msg || '未知错误'}`)
      exchangeConfigLoaded.value = true
      return false
    }
  } catch (error) {
    console.error('获取配置失败:', error)
    exchangeConfigLoaded.value = true
    showMessage('获取交易所配置失败: ' + (error.message || '未知错误'), 'error')
    return false
  } finally {
    isLoadingExchangeConfig.value = false
  }
}

/**
 * 加载映射
 */
const loadMappings = async () => {
  showMessage('开始加载映射...', 'info')
  
  // 并行请求两个API
  const [accountResult, exchangeResult] = await Promise.all([
    fetchAccountConfig(),
    fetchExchangeConfig()
  ])
  
  // 如果某个请求没有数据，重新请求
  if (!accountResult) {
    showMessage('账户配置无数据，重新请求...', 'info')
    await fetchAccountConfig()
  }
  
  if (!exchangeResult) {
    showMessage('交易所配置无数据，重新请求...', 'info')
    await fetchExchangeConfig()
  }
  
  if (accountResult && exchangeResult) {
    showMessage('映射加载成功', 'success')
  } else {
    showMessage('映射加载完成，但部分数据可能缺失', 'info')
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  browserIdsInput.value = ''
  groupNosInput.value = ''
  selectedTrending.value = 'all'
  trendingSearchText.value = ''
  inputType.value = 'browser'
}

/**
 * 提交单个浏览器ID的任务（带重试）
 * @param {number} browserId - 浏览器ID
 * @param {number} groupNo - 电脑组
 * @param {string} tp1 - Trending值
 * @param {number} maxRetries - 最大重试次数
 * @returns {Promise<{success: boolean, error?: string}>}
 */
const submitSingleBrowser = async (browserId, groupNo, tp1, maxRetries = 3) => {
  const payload = {
    type: 4,
    groupNo: groupNo,
    numberList: String(browserId),
    exchangeName: 'OP',
    tp1: tp1
  }
  
  let lastError = null
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        // 重试前等待5秒
        console.log(`浏览器ID ${browserId} 第 ${attempt} 次重试，等待5秒...`)
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
      
      const response = await axios.post('https://sg.bicoin.com.cn/99l/mission/add', payload)
      
      if (response.data && response.data.code === 0) {
        console.log(`浏览器ID ${browserId} 提交成功${attempt > 0 ? `（第${attempt}次重试成功）` : ''}`)
        return { success: true }
      } else {
        lastError = response.data?.msg || '未知错误'
        console.error(`浏览器ID ${browserId} 提交失败${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
      }
    } catch (error) {
      lastError = error.message || '未知错误'
      console.error(`浏览器ID ${browserId} 提交失败${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
    }
  }
  
  // 所有重试都失败
  return { success: false, error: lastError }
}

/**
 * 提交单个浏览器ID的更新仓位任务（带重试，type=2，不传tp1）
 * @param {number} browserId - 浏览器ID
 * @param {number} groupNo - 电脑组
 * @param {number} maxRetries - 最大重试次数
 * @returns {Promise<{success: boolean, error?: string}>}
 */
const submitSinglePositionUpdate = async (browserId, groupNo, maxRetries = 3) => {
  const payload = {
    type: 2,
    groupNo: groupNo,
    numberList: String(browserId),
    exchangeName: 'OP'
  }
  
  let lastError = null
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        // 重试前等待5秒
        console.log(`浏览器ID ${browserId} 更新仓位第 ${attempt} 次重试，等待5秒...`)
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
      
      const response = await axios.post('https://sg.bicoin.com.cn/99l/mission/add', payload)
      
      if (response.data && response.data.code === 0) {
        console.log(`浏览器ID ${browserId} 更新仓位成功${attempt > 0 ? `（第${attempt}次重试成功）` : ''}`)
        return { success: true }
      } else {
        lastError = response.data?.msg || '未知错误'
        console.error(`浏览器ID ${browserId} 更新仓位失败${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
      }
    } catch (error) {
      lastError = error.message || '未知错误'
      console.error(`浏览器ID ${browserId} 更新仓位失败${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
    }
  }
  
  // 所有重试都失败
  return { success: false, error: lastError }
}

/**
 * 提交任务
 */
const handleSubmit = async () => {
  if (isSubmitting.value) return
  
  // 验证输入
  if (inputType.value === 'browser' && parsedBrowserIds.value.length === 0) {
    showMessage('请正确输入浏览器ID', 'error')
    return
  }
  
  if (inputType.value === 'group' && parsedGroupNos.value.length === 0) {
    showMessage('请正确输入电脑组', 'error')
    return
  }
  
  // 获取要提交的浏览器ID列表
  let browserIdsToSubmit = []
  
  if (inputType.value === 'browser') {
    // 直接使用解析的浏览器ID
    browserIdsToSubmit = parsedBrowserIds.value
  } else {
    // 从电脑组映射到浏览器ID
    for (const groupNo of parsedGroupNos.value) {
      const browserIds = groupToBrowserMap.value[groupNo] || []
      browserIdsToSubmit.push(...browserIds)
    }
    
    if (browserIdsToSubmit.length === 0) {
      showMessage('所选电脑组没有对应的浏览器ID', 'error')
      return
    }
  }
  
  // 去重并排序
  browserIdsToSubmit = [...new Set(browserIdsToSubmit)].sort((a, b) => a - b)
  
  // 获取tp1值
  const tp1 = selectedTrending.value === 'all' ? 'all' : selectedTrending.value
  
  isSubmitting.value = true
  failedBrowserIds.value = [] // 清空之前的失败列表
  
  try {
    let successCount = 0
    let failCount = 0
    
    // 为每个浏览器ID提交一个请求（带重试）
    for (const browserId of browserIdsToSubmit) {
      // 获取对应的电脑组
      const groupNo = browserToGroupMap.value[browserId] || browserToGroupMap.value[String(browserId)]
      
      if (!groupNo) {
        console.warn(`浏览器ID ${browserId} 没有对应的电脑组，跳过`)
        failCount++
        failedBrowserIds.value.push({
          browserId: browserId,
          error: '没有对应的电脑组',
          groupNo: null,
          tp1: tp1
        })
        continue
      }
      
      const result = await submitSingleBrowser(browserId, groupNo, tp1, 3)
      
      if (result.success) {
        successCount++
      } else {
        failCount++
        failedBrowserIds.value.push({
          browserId: browserId,
          error: result.error || '提交失败',
          groupNo: groupNo,
          tp1: tp1
        })
      }
    }
    
    if (successCount > 0) {
      showMessage(`提交完成：成功 ${successCount} 个，失败 ${failCount} 个`, failCount > 0 ? 'info' : 'success')
    } else {
      showMessage(`提交失败：所有请求都失败了`, 'error')
    }
    
    // 重置表单
    resetForm()
  } catch (error) {
    console.error('提交任务失败:', error)
    showMessage('提交任务失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 重试失败的浏览器ID
 */
const retryFailed = async () => {
  if (isRetrying.value || failedBrowserIds.value.length === 0) return
  
  isRetrying.value = true
  
  try {
    let successCount = 0
    let failCount = 0
    const newFailedList = []
    
    for (const item of failedBrowserIds.value) {
      if (!item.groupNo) {
        // 如果没有电脑组，直接加入失败列表
        newFailedList.push(item)
        failCount++
        continue
      }
      
      const result = await submitSingleBrowser(item.browserId, item.groupNo, item.tp1, 3)
      
      if (result.success) {
        successCount++
      } else {
        failCount++
        newFailedList.push({
          ...item,
          error: result.error || '提交失败'
        })
      }
    }
    
    failedBrowserIds.value = newFailedList
    
    if (successCount > 0) {
      showMessage(`重试完成：成功 ${successCount} 个，失败 ${failCount} 个`, failCount > 0 ? 'info' : 'success')
    } else {
      showMessage(`重试失败：所有请求都失败了`, 'error')
    }
  } catch (error) {
    console.error('重试失败:', error)
    showMessage('重试失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isRetrying.value = false
  }
}

/**
 * 清除失败列表
 */
const clearFailedList = () => {
  failedBrowserIds.value = []
  showMessage('失败列表已清除', 'info')
}

/**
 * 处理清除任务（显示确认弹窗）
 */
const handleCleanMission = () => {
  if (isCleaning.value || validCleanGroupNos.value.length === 0) return
  
  // 验证输入
  if (parsedCleanGroupNos.value.length === 0) {
    showMessage('请正确输入电脑组', 'error')
    return
  }
  
  if (validCleanGroupNos.value.length === 0) {
    showMessage('输入的电脑组在配置中不存在', 'error')
    return
  }
  
  // 显示确认弹窗
  showConfirmDialog.value = true
}

/**
 * 确认清除任务
 */
const confirmCleanMission = async () => {
  if (isCleaning.value || validCleanGroupNos.value.length === 0) return
  
  showConfirmDialog.value = false
  isCleaning.value = true
  
  try {
    const payload = {
      list: validCleanGroupNos.value
    }
    
    const response = await axios.post('https://sg.bicoin.com.cn/99l/mission/cleanAllMissionByGroup', payload)
    
    if (response.data && response.data.code === 0) {
      showMessage(`清除任务成功：已清除电脑组 ${validCleanGroupNos.value.join(', ')} 的所有任务`, 'success')
      cleanGroupNosInput.value = '' // 清空输入框
    } else {
      showMessage(`清除任务失败: ${response.data?.msg || '未知错误'}`, 'error')
    }
  } catch (error) {
    console.error('清除任务失败:', error)
    showMessage('清除任务失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isCleaning.value = false
  }
}

/**
 * 更新仓位
 */
const handlePositionUpdate = async () => {
  if (isUpdatingPosition.value) return
  
  // 验证输入
  if (inputType.value === 'browser' && parsedBrowserIds.value.length === 0) {
    showMessage('请正确输入浏览器ID', 'error')
    return
  }
  
  if (inputType.value === 'group' && parsedGroupNos.value.length === 0) {
    showMessage('请正确输入电脑组', 'error')
    return
  }
  
  // 获取要提交的浏览器ID列表
  let browserIdsToSubmit = []
  
  if (inputType.value === 'browser') {
    // 直接使用解析的浏览器ID
    browserIdsToSubmit = parsedBrowserIds.value
  } else {
    // 从电脑组映射到浏览器ID
    for (const groupNo of parsedGroupNos.value) {
      const browserIds = groupToBrowserMap.value[groupNo] || []
      browserIdsToSubmit.push(...browserIds)
    }
    
    if (browserIdsToSubmit.length === 0) {
      showMessage('所选电脑组没有对应的浏览器ID', 'error')
      return
    }
  }
  
  // 去重并排序
  browserIdsToSubmit = [...new Set(browserIdsToSubmit)].sort((a, b) => a - b)
  
  isUpdatingPosition.value = true
  failedBrowserIds.value = [] // 清空之前的失败列表
  
  try {
    let successCount = 0
    let failCount = 0
    
    // 为每个浏览器ID提交一个请求（带重试）
    for (const browserId of browserIdsToSubmit) {
      // 获取对应的电脑组
      const groupNo = browserToGroupMap.value[browserId] || browserToGroupMap.value[String(browserId)]
      
      if (!groupNo) {
        console.warn(`浏览器ID ${browserId} 没有对应的电脑组，跳过`)
        failCount++
        failedBrowserIds.value.push({
          browserId: browserId,
          error: '没有对应的电脑组',
          groupNo: null,
          tp1: null
        })
        continue
      }
      
      const result = await submitSinglePositionUpdate(browserId, groupNo, 3)
      
      if (result.success) {
        successCount++
      } else {
        failCount++
        failedBrowserIds.value.push({
          browserId: browserId,
          error: result.error || '更新仓位失败',
          groupNo: groupNo,
          tp1: null
        })
      }
    }
    
    if (successCount > 0) {
      showMessage(`更新仓位完成：成功 ${successCount} 个，失败 ${failCount} 个`, failCount > 0 ? 'info' : 'success')
    } else {
      showMessage(`更新仓位失败：所有请求都失败了`, 'error')
    }
    
    // 重置表单
    resetForm()
  } catch (error) {
    console.error('更新仓位失败:', error)
    showMessage('更新仓位失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isUpdatingPosition.value = false
  }
}

// 监听输入类型变化，清空另一个输入框
watch(inputType, () => {
  if (inputType.value === 'browser') {
    groupNosInput.value = ''
  } else {
    browserIdsInput.value = ''
  }
})

// 监听trendingSearchText变化，如果为空则设置为"全部"
watch(trendingSearchText, (newVal) => {
  if (!newVal || !newVal.trim()) {
    selectedTrending.value = 'all'
  } else {
    const inputLower = newVal.toLowerCase().trim()
    if (inputLower === '全部' || inputLower === 'all') {
      selectedTrending.value = 'all'
    }
  }
})

// 页面加载时自动加载映射
onMounted(() => {
  loadMappings()
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  padding: 20px 0;
}

.task-form {
  margin-top: 20px;
}

/* 危险按钮样式 */
.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

/* 确认弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.modal-content p {
  margin-bottom: 16px;
  color: #555;
  line-height: 1.5;
}

.confirm-group-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.group-tag {
  display: inline-block;
  padding: 4px 12px;
  background: #4a90e2;
  color: white;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>

