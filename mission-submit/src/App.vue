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

          <!-- 浏览器ID批次选择和输入框 -->
          <div class="form-row" v-if="inputType === 'browser'">
            <div class="form-group">
              <label for="browserBatchType">电脑批次 *</label>
              <select
                id="browserBatchType"
                v-model="browserBatchType"
              >
                <option value="first">第一批电脑（1-27）</option>
                <option value="second">第二批电脑（901-927）</option>
              </select>
            </div>
          </div>
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
                已解析（共 {{ parsedBrowserIds.length }} 个）: {{ parsedBrowserIds.join(', ') }}
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

          <!-- 循环执行设置 -->
          <div class="form-row">
            <div class="form-group">
              <label>循环执行更新仓位</label>
              <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <label style="font-weight: normal; white-space: nowrap;">延迟</label>
                  <input
                    v-model.number="delayMinutes"
                    type="number"
                    min="0"
                    step="1"
                    placeholder="分钟"
                    style="width: 80px; padding: 6px; border: 1px solid #ddd; border-radius: 4px;"
                    :disabled="isLooping"
                  />
                  <span style="white-space: nowrap;">分钟后开始</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <label style="font-weight: normal; white-space: nowrap;">每间隔</label>
                  <input
                    v-model.number="intervalMinutes"
                    type="number"
                    min="1"
                    step="1"
                    placeholder="分钟"
                    style="width: 80px; padding: 6px; border: 1px solid #ddd; border-radius: 4px;"
                    :disabled="isLooping"
                  />
                  <span style="white-space: nowrap;">分钟执行一次</span>
                </div>
              </div>
              <div v-if="isLooping" style="margin-top: 8px; color: #28a745; font-size: 12px;">
                <div>循环执行中... {{ currentLoopingContent }}</div>
                <div style="margin-top: 4px;">下次执行时间: {{ nextExecuteTime }}</div>
              </div>
            </div>
          </div>

          <!-- 时间撤单设置 -->
          <div class="form-row">
            <div class="form-group">
              <label for="cancelHours">时间超过XX小时以上的撤单</label>
              <input
                id="cancelHours"
                v-model.number="cancelHours"
                type="number"
                min="0"
                step="0.1"
                placeholder="小时"
                style="width: 120px; padding: 6px; border: 1px solid #ddd; border-radius: 4px;"
              />
              <span style="margin-left: 8px; color: #666; font-size: 12px;">小时</span>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting || isUpdatingPosition || isLooping">
              <span v-if="isSubmitting">提交中...</span>
              <span v-else>撤单并更新</span>
            </button>
            <button type="button" class="btn btn-primary" @click="handleSubmitWithTime" :disabled="isSubmitting || isUpdatingPosition || isLooping || !cancelHours || cancelHours <= 0">
              <span v-if="isSubmitting">提交中...</span>
              <span v-else>按时间撤单并更新</span>
            </button>
            <button type="button" class="btn btn-primary" @click="handlePositionUpdate" :disabled="isSubmitting || isUpdatingPosition || isLooping">
              <span v-if="isUpdatingPosition">更新中...</span>
              <span v-else>更新仓位</span>
            </button>
            <button type="button" class="btn btn-success" @click="startLooping" :disabled="isLooping || isSubmitting || isUpdatingPosition || !delayMinutes || !intervalMinutes || delayMinutes < 0 || intervalMinutes < 1">
              开始循环更新仓位
            </button>
            <button type="button" class="btn btn-danger" @click="stopLooping" :disabled="!isLooping">
              停止循环更新仓位
            </button>
            <button type="button" class="btn btn-secondary" @click="resetForm">
              重置
            </button>
          </div>
        </form>
      </section>

      <!-- IP检测任务表单 -->
      <section class="section">
        <h2>检测IP任务</h2>
        <div class="task-form">
          <!-- 电脑批次选择 -->
          <div class="form-row">
            <div class="form-group">
              <label for="ipBatchSelect">电脑批次 *</label>
              <select
                id="ipBatchSelect"
                v-model="ipBatchType"
              >
                <option value="first">第一批电脑</option>
                <option value="second">第二批电脑</option>
              </select>
            </div>
          </div>

          <!-- 电脑组输入框 -->
          <div class="form-row">
            <div class="form-group">
              <label for="ipGroupNos">电脑组 *</label>
              <input
                id="ipGroupNos"
                v-model="ipGroupNosInput"
                type="text"
                placeholder="支持格式: 1 或 1,2,3 或 1-3"
              />
              <div v-if="parsedIpGroupNos.length > 0" style="margin-top: 8px; color: #666; font-size: 12px;">
                已解析: {{ parsedIpGroupNos.join(', ') }}
              </div>
              <div v-if="validIpGroupNos.length > 0" style="margin-top: 8px; color: #28a745; font-size: 12px;">
                有效电脑组: {{ validIpGroupNos.join(', ') }}
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="form-actions">
            <button type="button" class="btn btn-primary" @click="handleIpDetection" :disabled="isSubmittingIp || validIpGroupNos.length === 0">
              <span v-if="isSubmittingIp">运行中...</span>
              <span v-else>运行IP检测任务</span>
            </button>
            <button type="button" class="btn btn-secondary" @click="ipGroupNosInput = ''">
              清空
            </button>
          </div>
        </div>

        <!-- IP检测任务状态列表 -->
        <div v-if="ipTaskStatusList.length > 0" class="task-status-list" style="margin-top: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 12px; color: #333;">IP检测任务状态</h3>
          <div class="task-status-item" v-for="(item, index) in ipTaskStatusList" :key="index">
            <div class="task-status-header">
              <span class="task-group-no">电脑组: {{ item.groupNo }}</span>
              <span class="task-id">任务ID: {{ item.taskId || '获取中...' }}</span>
            </div>
            <div class="task-status-body">
              <span class="task-status" :class="getStatusClass(item.status)">
                状态: {{ getStatusText(item.status) }}
              </span>
              <span class="task-message" v-if="item.msg">消息: {{ item.msg }}</span>
            </div>
          </div>
          <div class="task-status-actions" style="margin-top: 12px;">
            <button class="btn btn-secondary btn-sm" @click="clearTaskStatusList">清除状态列表</button>
          </div>
        </div>

        <!-- IP检测失败列表 -->
        <div v-if="failedIpGroups.length > 0" class="failed-list" style="margin-top: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 12px; color: #333;">IP检测失败的电脑组</h3>
          <div class="failed-item" v-for="(item, index) in failedIpGroups" :key="index">
            <span class="failed-id">电脑组: {{ item.groupNo }}</span>
            <span class="failed-error" v-if="item.error">错误: {{ item.error }}</span>
          </div>
          <div class="failed-actions">
            <button class="btn btn-primary" @click="retryFailedIp" :disabled="isRetryingIp">
              {{ isRetryingIp ? '重试中...' : '重试失败的电脑组' }}
            </button>
            <button class="btn btn-secondary" @click="clearFailedIpList">清除列表</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
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
const browserBatchType = ref('second') // 浏览器ID批次选择：'first' 或 'second'，默认第二批
const groupNosInput = ref('')
const selectedTrending = ref('all') // 默认全部
const trendingSearchText = ref('全部') // 默认显示"全部"
const showTrendingDropdown = ref(false)
const isSubmitting = ref(false)
const isUpdatingPosition = ref(false)
const isRetrying = ref(false)
const failedBrowserIds = ref([]) // 存储失败的浏览器ID [{browserId, error, groupNo, tp1}]

// 循环执行相关
const delayMinutes = ref(0) // 延迟时间（分钟）
const intervalMinutes = ref(5) // 间隔时间（分钟）
const isLooping = ref(false) // 是否正在循环执行
const loopTimer = ref(null) // 循环定时器
const delayTimer = ref(null) // 延迟定时器
const nextExecuteTime = ref('') // 下次执行时间

// 时间撤单相关
const cancelHours = ref(null) // 时间超过XX小时以上的撤单

// 清除任务相关
const cleanGroupNosInput = ref('')
const isCleaning = ref(false)
const showConfirmDialog = ref(false)

// IP检测任务相关
const ipBatchType = ref('second') // 默认第二批电脑
const ipGroupNosInput = ref('')
const isSubmittingIp = ref(false)
const failedIpGroups = ref([]) // 存储失败的电脑组 [{groupNo, error}]
const isRetryingIp = ref(false)
const ipTaskStatusList = ref([]) // 存储任务状态 [{groupNo, taskId, status, msg}]
const statusPollingInterval = ref(null) // 状态轮询定时器

// 映射关系
const browserToGroupMap = ref({}) // 浏览器ID -> 电脑组
const groupToBrowserMap = ref({}) // 电脑组 -> 浏览器ID数组

// 第一批电脑组列表
const firstBatchGroups = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26, 27]

// 第二批电脑组列表（第一批+900）
const secondBatchGroups = firstBatchGroups.map(g => g + 900)

/**
 * 根据浏览器ID和批次获取对应的电脑组
 * @param {number|string} browserId - 浏览器ID
 * @param {string} batchType - 批次类型 'first' 或 'second'
 * @returns {number|null} 电脑组编号，如果找不到则返回null
 */
const getGroupNoByBrowserIdAndBatch = (browserId, batchType) => {
  // 从映射中获取浏览器ID对应的原始电脑组
  const originalGroupNo = browserToGroupMap.value[browserId] || browserToGroupMap.value[String(browserId)]
  
  if (!originalGroupNo) {
    return null
  }
  
  const groupNum = Number(originalGroupNo)
  if (isNaN(groupNum)) {
    return null
  }
  
  // 判断原始电脑组属于哪个批次
  const isFirstBatch = firstBatchGroups.includes(groupNum)
  const isSecondBatch = secondBatchGroups.includes(groupNum)
  
  if (batchType === 'first') {
    // 如果选择批次1
    if (isFirstBatch) {
      // 原始电脑组就是批次1的，直接返回
      return groupNum
    } else if (isSecondBatch) {
      // 原始电脑组是批次2的，减去900得到批次1的
      return groupNum - 900
    }
  } else if (batchType === 'second') {
    // 如果选择批次2
    if (isSecondBatch) {
      // 原始电脑组就是批次2的，直接返回
      return groupNum
    } else if (isFirstBatch) {
      // 原始电脑组是批次1的，加上900得到批次2的
      return groupNum + 900
    }
  }
  
  // 如果都不匹配，返回原始电脑组（兜底）
  return groupNum
}

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

// 当前循环执行的内容描述
const currentLoopingContent = computed(() => {
  if (!isLooping.value) return ''
  
  if (inputType.value === 'browser' && parsedBrowserIds.value.length > 0) {
    return `浏览器ID: ${parsedBrowserIds.value.join(', ')}`
  } else if (inputType.value === 'group' && parsedGroupNos.value.length > 0) {
    return `电脑组: ${parsedGroupNos.value.join(', ')}`
  }
  return ''
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

// 解析后的IP检测电脑组列表
const parsedIpGroupNos = computed(() => {
  return parseInput(ipGroupNosInput.value)
})

// 验证IP检测的电脑组是否在对应批次中
const validIpGroupNos = computed(() => {
  if (parsedIpGroupNos.value.length === 0) {
    return []
  }
  
  // 根据批次类型获取允许的电脑组列表
  const allowedGroups = ipBatchType.value === 'first' ? firstBatchGroups : secondBatchGroups
  
  // 过滤出在允许列表中的电脑组
  return parsedIpGroupNos.value.filter(groupNo => allowedGroups.includes(groupNo)).sort((a, b) => a - b)
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
  // 停止循环执行
  stopLooping()
  
  browserIdsInput.value = ''
  browserBatchType.value = 'second' // 重置为默认批次
  groupNosInput.value = ''
  selectedTrending.value = 'all'
  trendingSearchText.value = ''
  inputType.value = 'browser'
  delayMinutes.value = 0
  intervalMinutes.value = 5
  cancelHours.value = null
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
 * 提交单个浏览器ID的任务（带重试，带tp5参数）
 * @param {number} browserId - 浏览器ID
 * @param {number} groupNo - 电脑组
 * @param {string} tp1 - Trending值
 * @param {number} tp5 - 时间超过XX小时以上的撤单
 * @param {number} maxRetries - 最大重试次数
 * @returns {Promise<{success: boolean, error?: string}>}
 */
const submitSingleBrowserWithTime = async (browserId, groupNo, tp1, tp5, maxRetries = 3) => {
  const payload = {
    type: 4,
    groupNo: groupNo,
    numberList: String(browserId),
    exchangeName: 'OP',
    tp1: tp1,
    tp5: tp5
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
  // 建立浏览器ID到电脑组的映射（用于电脑组类型输入）
  const browserIdToGroupNoMap = {}
  
  if (inputType.value === 'browser') {
    // 直接使用解析的浏览器ID
    browserIdsToSubmit = parsedBrowserIds.value
  } else {
    // 从电脑组映射到浏览器ID，同时建立浏览器ID到用户输入电脑组的映射
    for (const groupNo of parsedGroupNos.value) {
      const browserIds = groupToBrowserMap.value[groupNo] || []
      browserIdsToSubmit.push(...browserIds)
      // 建立映射：浏览器ID -> 用户输入的电脑组号
      for (const browserId of browserIds) {
        browserIdToGroupNoMap[browserId] = groupNo
        browserIdToGroupNoMap[String(browserId)] = groupNo
      }
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
      // 获取对应的电脑组（根据输入类型和批次）
      let groupNo = null
      if (inputType.value === 'browser') {
        // 浏览器ID类型：根据批次获取电脑组
        groupNo = getGroupNoByBrowserIdAndBatch(browserId, browserBatchType.value)
      } else {
        // 电脑组类型：使用用户输入的电脑组号（而不是从映射中获取）
        groupNo = browserIdToGroupNoMap[browserId] || browserIdToGroupNoMap[String(browserId)]
      }
      
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
 * 按时间撤单并更新任务
 */
const handleSubmitWithTime = async () => {
  if (isSubmitting.value) return
  
  // 验证输入
  if (!cancelHours.value || cancelHours.value <= 0) {
    showMessage('请设置时间超过XX小时以上的撤单', 'error')
    return
  }
  
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
  // 建立浏览器ID到电脑组的映射（用于电脑组类型输入）
  const browserIdToGroupNoMap = {}
  
  if (inputType.value === 'browser') {
    // 直接使用解析的浏览器ID
    browserIdsToSubmit = parsedBrowserIds.value
  } else {
    // 从电脑组映射到浏览器ID，同时建立浏览器ID到用户输入电脑组的映射
    for (const groupNo of parsedGroupNos.value) {
      const browserIds = groupToBrowserMap.value[groupNo] || []
      browserIdsToSubmit.push(...browserIds)
      // 建立映射：浏览器ID -> 用户输入的电脑组号
      for (const browserId of browserIds) {
        browserIdToGroupNoMap[browserId] = groupNo
        browserIdToGroupNoMap[String(browserId)] = groupNo
      }
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
      // 获取对应的电脑组（根据输入类型和批次）
      let groupNo = null
      if (inputType.value === 'browser') {
        // 浏览器ID类型：根据批次获取电脑组
        groupNo = getGroupNoByBrowserIdAndBatch(browserId, browserBatchType.value)
      } else {
        // 电脑组类型：使用用户输入的电脑组号（而不是从映射中获取）
        groupNo = browserIdToGroupNoMap[browserId] || browserIdToGroupNoMap[String(browserId)]
      }
      
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
      
      const result = await submitSingleBrowserWithTime(browserId, groupNo, tp1, cancelHours.value, 3)
      
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
 * @param {boolean} skipReset - 是否跳过重置表单（用于循环执行）
 */
const handlePositionUpdate = async (skipReset = false) => {
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
  // 建立浏览器ID到电脑组的映射（用于电脑组类型输入）
  const browserIdToGroupNoMap = {}
  
  if (inputType.value === 'browser') {
    // 直接使用解析的浏览器ID
    browserIdsToSubmit = parsedBrowserIds.value
  } else {
    // 从电脑组映射到浏览器ID，同时建立浏览器ID到用户输入电脑组的映射
    for (const groupNo of parsedGroupNos.value) {
      const browserIds = groupToBrowserMap.value[groupNo] || []
      browserIdsToSubmit.push(...browserIds)
      // 建立映射：浏览器ID -> 用户输入的电脑组号
      for (const browserId of browserIds) {
        browserIdToGroupNoMap[browserId] = groupNo
        browserIdToGroupNoMap[String(browserId)] = groupNo
      }
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
      // 获取对应的电脑组（根据输入类型和批次）
      let groupNo = null
      if (inputType.value === 'browser') {
        // 浏览器ID类型：根据批次获取电脑组
        groupNo = getGroupNoByBrowserIdAndBatch(browserId, browserBatchType.value)
      } else {
        // 电脑组类型：使用用户输入的电脑组号（而不是从映射中获取）
        groupNo = browserIdToGroupNoMap[browserId] || browserIdToGroupNoMap[String(browserId)]
      }
      
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
    
    // 重置表单（循环执行时不重置）
    if (!skipReset) {
      resetForm()
    }
  } catch (error) {
    console.error('更新仓位失败:', error)
    showMessage('更新仓位失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isUpdatingPosition.value = false
  }
}

/**
 * 计算并更新下次执行时间
 * @param {number} additionalDelay - 额外的延迟时间（毫秒），用于延迟执行的情况。如果提供了此参数，则只使用延迟时间，不加间隔时间（用于第一次执行）
 * @param {boolean} isFirstExecution - 是否是第一次执行（有延迟时），如果是，则只显示延迟时间，不加间隔时间
 */
const updateNextExecuteTime = (additionalDelay = 0, isFirstExecution = false) => {
  if (!isLooping.value) {
    nextExecuteTime.value = ''
    return
  }
  
  const now = new Date()
  // 如果是第一次执行（有延迟），只使用延迟时间，不加间隔时间
  const timeToAdd = isFirstExecution ? additionalDelay : (additionalDelay + intervalMinutes.value * 60 * 1000)
  const nextTime = new Date(now.getTime() + timeToAdd)
  const hours = String(nextTime.getHours()).padStart(2, '0')
  const minutes = String(nextTime.getMinutes()).padStart(2, '0')
  const seconds = String(nextTime.getSeconds()).padStart(2, '0')
  nextExecuteTime.value = `${hours}:${minutes}:${seconds}`
}

/**
 * 执行一次更新仓位（用于循环执行）
 */
const executePositionUpdateOnce = async () => {
  if (!isLooping.value) return
  
  // 更新下次执行时间（在执行前更新，这样用户可以看到下次执行时间）
  updateNextExecuteTime()
  
  // 执行更新仓位（不重置表单）
  await handlePositionUpdate(true)
}

/**
 * 开始循环执行
 */
const startLooping = () => {
  if (isLooping.value) return
  
  // 验证输入类型和内容
  if (inputType.value === 'browser') {
    if (parsedBrowserIds.value.length === 0) {
      showMessage('请正确输入浏览器ID', 'error')
      return
    }
  } else if (inputType.value === 'group') {
    if (parsedGroupNos.value.length === 0) {
      showMessage('请正确输入电脑组', 'error')
      return
    }
  } else {
    showMessage('请选择输入类型（浏览器ID或电脑组）', 'error')
    return
  }
  
  if (!delayMinutes.value && delayMinutes.value !== 0) {
    showMessage('请输入延迟时间', 'error')
    return
  }
  
  if (!intervalMinutes.value || intervalMinutes.value < 1) {
    showMessage('请输入有效的间隔时间（至少1分钟）', 'error')
    return
  }
  
  // 显示当前选择的类型和内容
  const currentSelection = inputType.value === 'browser' 
    ? `浏览器ID: ${parsedBrowserIds.value.join(', ')}` 
    : `电脑组: ${parsedGroupNos.value.join(', ')}`
  
  isLooping.value = true
  
  // 延迟执行
  const delayMs = delayMinutes.value * 60 * 1000
  const intervalMs = intervalMinutes.value * 60 * 1000
  
  if (delayMs > 0) {
    // 有延迟，先等待延迟时间
    showMessage(`将在 ${delayMinutes.value} 分钟后开始循环更新仓位（${currentSelection}），每 ${intervalMinutes.value} 分钟执行一次`, 'info')
    updateNextExecuteTime(delayMs, true) // 计算延迟后的首次执行时间（只加延迟时间，不加间隔时间）
    
    delayTimer.value = setTimeout(() => {
      // 延迟时间到，立即执行一次
      showMessage(`延迟时间到，开始执行第一次更新仓位（${currentSelection}）`, 'info')
      executePositionUpdateOnce()
      
      // 然后设置循环定时器，每隔指定时间执行一次
      loopTimer.value = setInterval(() => {
        executePositionUpdateOnce()
      }, intervalMs)
    }, delayMs)
  } else {
    // 无延迟，立即执行一次
    showMessage(`开始循环更新仓位（${currentSelection}），每 ${intervalMinutes.value} 分钟执行一次`, 'info')
    executePositionUpdateOnce() // 执行第一次，内部会更新下次执行时间
    
    // 设置循环定时器
    loopTimer.value = setInterval(() => {
      executePositionUpdateOnce()
    }, intervalMs)
  }
}

/**
 * 停止循环执行
 */
const stopLooping = () => {
  if (!isLooping.value) return
  
  isLooping.value = false
  
  // 清除延迟定时器
  if (delayTimer.value) {
    clearTimeout(delayTimer.value)
    delayTimer.value = null
  }
  
  // 清除循环定时器
  if (loopTimer.value) {
    clearInterval(loopTimer.value)
    loopTimer.value = null
  }
  
  nextExecuteTime.value = ''
  showMessage('循环执行已停止', 'info')
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

// 监听IP批次类型变化，自动填充对应的电脑组
watch(ipBatchType, (newVal) => {
  if (newVal === 'first') {
    ipGroupNosInput.value = firstBatchGroups.join(',')
  } else if (newVal === 'second') {
    ipGroupNosInput.value = secondBatchGroups.join(',')
  }
}, { immediate: true })

/**
 * 获取任务状态
 * @param {number|string} taskId - 任务ID
 * @returns {Promise<object|null>} 返回mission对象或null
 */
const fetchMissionStatus = async (taskId) => {
  // 验证taskId是否有效
  if (taskId === undefined || taskId === null || taskId === '' || typeof taskId === 'object') {
    console.error(`获取任务状态失败: 无效的任务ID`, { taskId, type: typeof taskId })
    return null
  }
  
  // 确保taskId是数字或字符串
  const validTaskId = Number(taskId)
  if (isNaN(validTaskId)) {
    console.error(`获取任务状态失败: 任务ID不是有效数字`, { taskId, type: typeof taskId })
    return null
  }
  
  try {
    const url = `https://sg.bicoin.com.cn/99l/mission/status?id=${validTaskId}`
    console.log(`正在获取任务状态: ${url}`)
    const response = await axios.get(url)
    if (response.data && response.data.code === 0 && response.data.data) {
      // 返回 mission 对象，而不是整个 data
      return response.data.data.mission
    }
    return null
  } catch (error) {
    console.error(`获取任务 ${validTaskId} 状态失败:`, error)
    return null
  }
}

/**
 * 获取状态文本
 * @param {number} status - 状态码
 * @returns {string} 状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    0: '未启动',
    9: '进行中',
    2: '已成功发布任务',
    3: '失败'
  }
  return statusMap[status] || `未知状态(${status})`
}

/**
 * 获取状态样式类
 * @param {number} status - 状态码
 * @returns {string} 样式类名
 */
const getStatusClass = (status) => {
  const classMap = {
    0: 'status-pending',
    9: 'status-running',
    2: 'status-success',
    3: 'status-failed'
  }
  return classMap[status] || 'status-unknown'
}

/**
 * 提交单个IP检测任务（带重试）
 * @param {number} groupNo - 电脑组
 * @param {number} maxRetries - 最大重试次数
 * @returns {Promise<{success: boolean, taskId?: number, error?: string}>}
 */
const submitSingleIpDetection = async (groupNo, maxRetries = 3) => {
  const payload = {
    groupNo: String(groupNo),
    type: 11,
    exchangeName: 'OP'
  }
  
  let lastError = null
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        // 重试前等待5秒
        console.log(`电脑组 ${groupNo} IP检测第 ${attempt} 次重试，等待5秒...`)
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
      
      const response = await axios.post('https://sg.bicoin.com.cn/99l/mission/add', payload)
      
      if (response.data && response.data.code === 0) {
        console.log(`电脑组 ${groupNo} IP检测成功${attempt > 0 ? `（第${attempt}次重试成功）` : ''}`)
        // 获取任务ID
        const taskId = response.data.data?.id || response.data.data?.taskId || null
        return { success: true, taskId: taskId }
      } else {
        lastError = response.data?.msg || '未知错误'
        console.error(`电脑组 ${groupNo} IP检测失败${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
      }
    } catch (error) {
      lastError = error.message || '未知错误'
      console.error(`电脑组 ${groupNo} IP检测失败${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
    }
  }
  
  // 所有重试都失败
  return { success: false, error: lastError }
}

/**
 * 处理IP检测任务
 */
const handleIpDetection = async () => {
  if (isSubmittingIp.value || validIpGroupNos.value.length === 0) return
  
  // 验证输入
  if (parsedIpGroupNos.value.length === 0) {
    showMessage('请正确输入电脑组', 'error')
    return
  }
  
  if (validIpGroupNos.value.length === 0) {
    showMessage('输入的电脑组不在当前批次中', 'error')
    return
  }
  
  isSubmittingIp.value = true
  failedIpGroups.value = [] // 清空之前的失败列表
  
  try {
    let successCount = 0
    let failCount = 0
    
    // 清空之前的状态列表
    ipTaskStatusList.value = []
    
    // 为每个电脑组提交一个请求（带重试）
    for (const groupNo of validIpGroupNos.value) {
      const result = await submitSingleIpDetection(groupNo, 3)
      
      if (result.success) {
        successCount++
        // 存储任务信息到状态列表
        if (result.taskId) {
          ipTaskStatusList.value.push({
            groupNo: groupNo,
            taskId: result.taskId,
            status: 0, // 初始状态为未启动
            msg: ''
          })
        } else {
          // 如果没有任务ID，也添加到列表但标记为未知
          ipTaskStatusList.value.push({
            groupNo: groupNo,
            taskId: null,
            status: null,
            msg: '未获取到任务ID'
          })
        }
      } else {
        failCount++
        failedIpGroups.value.push({
          groupNo: groupNo,
          error: result.error || 'IP检测失败'
        })
      }
    }
    
    if (successCount > 0) {
      showMessage(`IP检测完成：成功 ${successCount} 个，失败 ${failCount} 个`, failCount > 0 ? 'info' : 'success')
      // 开始轮询任务状态
      startStatusPolling()
    } else {
      showMessage(`IP检测失败：所有请求都失败了`, 'error')
    }
    
    // 清空输入框
    ipGroupNosInput.value = ''
  } catch (error) {
    console.error('IP检测失败:', error)
    showMessage('IP检测失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isSubmittingIp.value = false
  }
}

/**
 * 重试失败的IP检测任务
 */
const retryFailedIp = async () => {
  if (isRetryingIp.value || failedIpGroups.value.length === 0) return
  
  isRetryingIp.value = true
  
  try {
    let successCount = 0
    let failCount = 0
    const newFailedList = []
    let hasNewTasks = false
    
    for (const item of failedIpGroups.value) {
      const result = await submitSingleIpDetection(item.groupNo, 3)
      
      if (result.success) {
        successCount++
        // 添加到状态列表
        if (result.taskId) {
          ipTaskStatusList.value.push({
            groupNo: item.groupNo,
            taskId: result.taskId,
            status: 0, // 初始状态为未启动
            msg: ''
          })
          hasNewTasks = true
        } else {
          ipTaskStatusList.value.push({
            groupNo: item.groupNo,
            taskId: null,
            status: null,
            msg: '未获取到任务ID'
          })
        }
      } else {
        failCount++
        newFailedList.push({
          ...item,
          error: result.error || 'IP检测失败'
        })
      }
    }
    
    failedIpGroups.value = newFailedList
    
    if (successCount > 0) {
      showMessage(`重试完成：成功 ${successCount} 个，失败 ${failCount} 个`, failCount > 0 ? 'info' : 'success')
      // 如果有新任务，开始轮询
      if (hasNewTasks) {
        startStatusPolling()
      }
    } else {
      showMessage(`重试失败：所有请求都失败了`, 'error')
    }
  } catch (error) {
    console.error('重试IP检测失败:', error)
    showMessage('重试IP检测失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isRetryingIp.value = false
  }
}

/**
 * 清除IP检测失败列表
 */
const clearFailedIpList = () => {
  failedIpGroups.value = []
  showMessage('失败列表已清除', 'info')
}

/**
 * 轮询任务状态
 */
const pollTaskStatus = async () => {
  // 检查是否有需要轮询的任务（状态不是2或3）
  const tasksToPoll = ipTaskStatusList.value.filter(task => {
    return task.taskId && task.status !== 2 && task.status !== 3
  })
  
  if (tasksToPoll.length === 0) {
    // 没有需要轮询的任务，停止轮询
    stopStatusPolling()
    return
  }
  
  // 并行获取所有任务的状态
  const statusPromises = tasksToPoll.map(async (task) => {
    try {
      const mission = await fetchMissionStatus(task.taskId)
      if (mission) {
        // 更新任务状态
        const taskIndex = ipTaskStatusList.value.findIndex(t => t.taskId === task.taskId)
        if (taskIndex !== -1) {
          ipTaskStatusList.value[taskIndex].status = mission.status || task.status
          ipTaskStatusList.value[taskIndex].msg = mission.msg || ''
        }
      }
    } catch (error) {
      console.error(`获取任务 ${task.taskId} 状态失败:`, error)
    }
  })
  
  await Promise.all(statusPromises)
}

/**
 * 开始轮询任务状态
 */
const startStatusPolling = () => {
  // 先立即执行一次
  pollTaskStatus()
  
  // 清除之前的定时器
  if (statusPollingInterval.value) {
    clearInterval(statusPollingInterval.value)
  }
  
  // 每隔10秒轮询一次
  statusPollingInterval.value = setInterval(() => {
    pollTaskStatus()
  }, 10000)
}

/**
 * 停止轮询任务状态
 */
const stopStatusPolling = () => {
  if (statusPollingInterval.value) {
    clearInterval(statusPollingInterval.value)
    statusPollingInterval.value = null
  }
}

/**
 * 清除任务状态列表
 */
const clearTaskStatusList = () => {
  stopStatusPolling()
  ipTaskStatusList.value = []
  showMessage('任务状态列表已清除', 'info')
}

// 页面加载时自动加载映射
onMounted(() => {
  loadMappings()
})

// 组件卸载时清除轮询定时器和循环定时器
onUnmounted(() => {
  stopStatusPolling()
  stopLooping()
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

/* 成功按钮样式 */
.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
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

/* 任务状态列表样式 */
.task-status-list {
  margin-top: 20px;
}

.task-status-item {
  padding: 12px;
  margin-bottom: 12px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.task-status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-group-no {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.task-id {
  font-size: 12px;
  color: #666;
}

.task-status-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-status {
  font-size: 14px;
  font-weight: 500;
}

.task-status.status-pending {
  color: #6c757d;
}

.task-status.status-running {
  color: #ffc107;
}

.task-status.status-success {
  color: #28a745;
}

.task-status.status-failed {
  color: #dc3545;
}

.task-status.status-unknown {
  color: #6c757d;
}

.task-message {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.task-status-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
</style>

