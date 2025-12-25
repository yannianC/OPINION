<template>
  <div class="app">
    <div class="container">
      <!-- 查询区域 -->
      <section class="query-section">
        <div class="query-form">
          <div class="form-group">
            <label>模式:</label>
            <div class="mode-switch">
              <button 
                :class="['mode-btn', queryMode === 1 ? 'active' : '']"
                @click="switchMode(1)"
              >
                模式1
              </button>
              <button 
                :class="['mode-btn', queryMode === 2 ? 'active' : '']"
                @click="switchMode(2)"
              >
                模式2
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>分组:</label>
            <select 
              v-model="selectedGroup" 
              class="group-select"
              @change="onGroupChange"
            >
              <option value="default">默认</option>
              <option value="1">分组1</option>
              <option value="2">分组2</option>
              <option value="3">分组3</option>
            </select>
          </div>
          <div class="form-group" v-if="queryMode === 1">
            <label>交易方向:</label>
            <select 
              v-model="sideFilter" 
              class="group-select"
            >
              <option value="all">全部</option>
              <option value="buy">买入</option>
              <option value="sell">卖出</option>
            </select>
          </div>
          <div class="form-group">
            <label>开始时间:</label>
            <input 
              v-model="query.startTime" 
              type="datetime-local" 
              class="datetime-input"
            />
          </div>
          <div class="form-group">
            <label>结束时间:</label>
            <input 
              v-model="query.endTime" 
              type="datetime-local" 
              class="datetime-input"
            />
          </div>
          <button 
            class="query-btn" 
            @click="queryAnomalies"
            :disabled="loading"
          >
            {{ loading ? '查询中...' : '查询' }}
          </button>
        </div>
        
        <div class="quick-query-form">
          <div class="form-group">
            <label>查询最近:</label>
            <input 
              v-model.number="recentHours" 
              type="number" 
              class="hours-input"
              placeholder="输入小时数"
              min="1"
              step="1"
            />
            <span class="hours-label">小时</span>
          </div>
          <button 
            class="quick-query-btn" 
            @click="queryRecentHours"
            :disabled="loading || !recentHours || recentHours <= 0"
          >
            {{ loading ? '查询中...' : '快速查询' }}
          </button>
        </div>
      </section>

      <!-- 结果区域 -->
      <section class="results-section" v-if="Object.keys(results).length > 0">
        <div class="results-header">
          <h2>查询结果 (共 {{ Object.keys(results).length }} 个任务组)</h2>
          
          <!-- 筛选区域 -->
          <div class="filter-section">
            <div class="filter-input-wrapper">
              <input 
                v-model="filterKeyword" 
                type="text" 
                class="filter-input"
                placeholder="输入失败原因关键词进行筛选"
                @keyup.enter="applyFilter"
              />
              <!-- 筛选历史 -->
              <div class="filter-history" v-if="filterHistory.length > 0">
                <span class="history-label">历史:</span>
                <span 
                  v-for="(history, index) in filterHistory" 
                  :key="index"
                  class="history-item"
                  @click="selectHistory(history)"
                  :title="history"
                >
                  {{ history }}
                </span>
              </div>
            </div>
            <button 
              class="filter-btn" 
              @click="applyFilter"
            >
              筛选
            </button>
            <button 
              v-if="filterKeyword" 
              class="clear-filter-btn" 
              @click="clearFilter"
            >
              清除
            </button>
          </div>
        </div>
        
        <div class="tasks-container">
          <!-- 模式1的显示 -->
          <div v-if="queryMode === 1" class="task-groups-list">
            <div 
              v-for="(item, itemIndex) in taskGroupsWithIndex" 
              :key="item.groupKey"
              :class="['task-group-card', `group-color-${item.colorIndex}`]"
            >
              <div class="tasks-list">
                <div 
                  v-for="(task, taskIndex) in item.group.tasks" 
                  :key="taskIndex"
                  class="task-item"
                >
                  <div class="task-line">
                    <span class="task-id">{{ task.id }}</span>
                    <span class="task-separator">|</span>
                    <span class="task-info">
                      <span class="field-label">电脑组:</span>{{ task.groupNo || '-' }}
                    </span>
                    <span class="task-separator">|</span>
                    <span class="task-info">
                      <span class="field-label">浏览器编号:</span>{{ task.browserId || '-' }}
                    </span>
                    <span class="task-separator">|</span>
                    <span class="task-info">{{ task.trending }}</span>
                    <span class="task-separator">|</span>
                    <span class="task-info">{{ formatDateTime(task.createTime) }}</span>
                    <span class="task-separator">|</span>
                    <span class="task-info">{{ formatDateTime(task.updateTime) }}</span>
                    <span class="task-separator">|</span>
                    <span :class="['task-info', task.side === 1 ? 'buy' : 'sell']">
                      {{ task.side === 1 ? '买入' : '卖出' }}
                    </span>
                    <span class="task-separator">|</span>
                    <span class="task-info">{{ task.amt }}</span>
                    <span class="task-separator">|</span>
                    <span class="task-info">{{ task.price }}</span>
                    <span class="task-separator">|</span>
                    <span :class="['task-info', task.psSide === 1 ? 'yes' : 'no']">
                      {{ task.psSide === 1 ? 'YES' : 'NO' }}
                    </span>
                    <span class="task-separator">|</span>
                    <span class="task-info">
                      <span class="field-label">链上余额:</span>
                      <span v-if="task.onChainBalance" :class="['balance-value', 
                        task.onChainBalance === '获取失败' ? 'error' : 'success']">
                        {{ task.onChainBalance }}
                      </span>
                      <button 
                        v-else
                        @click="loadTaskBalance(task)"
                        class="balance-btn"
                        :disabled="task.balanceLoading"
                      >
                        {{ task.balanceLoading ? '加载中...' : '获取' }}
                      </button>
                    </span>
                    <span class="task-separator">|</span>
                    <span class="task-info msg-value">{{ formatTaskMsg(task.msg) || '无' }}</span>
                    <span class="task-separator">|</span>
                    <a 
                      :href="task.opUrl" 
                      target="_blank" 
                      class="link-btn"
                    >
                      查看
                    </a>
                    <a 
                      :href="task.opUrl" 
                      target="_blank" 
                      class="link-btn"
                      style="margin-left: 8px;"
                    >
                      查看
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 模式2的显示 -->
          <div v-else class="task-groups-list">
            <div 
              v-for="(item, itemIndex) in mode2GroupsWithIndex" 
              :key="item.groupKey"
              :class="['task-group-card', `group-color-${item.colorIndex}`]"
            >
              <div class="mode2-group-header">
                <div class="mode2-trending">{{ item.group.trending }}</div>
                <div class="mode2-stats">
                  <span class="stat-item success">
                    成功: YES {{ item.group.successYesAmt || 0 }} | NO {{ item.group.successNoAmt || 0 }}
                  </span>
                  <span class="stat-item fail">
                    失败: YES {{ item.group.failYesAmt || 0 }} | NO {{ item.group.failNoAmt || 0 }}
                  </span>
                  <span class="stat-item fail-exclude-partial">
                    失败(除部分成交): YES {{ item.group.failYesAmtExcludePartial || 0 }} | NO {{ item.group.failNoAmtExcludePartial || 0 }}
                  </span>
                  <span v-if="item.group.needSupplement" class="stat-item supplement">
                    需补{{ item.group.needSupplement.type }}: {{ item.group.needSupplement.amount }}
                  </span>
                </div>
              </div>
              
              <!-- 成功YES -->
              <div v-if="item.group.successYesTasks && item.group.successYesTasks.length > 0" class="mode2-category">
                <div 
                  class="mode2-category-header"
                  @click="toggleExpand(item.group.trendingId, 'successYes')"
                >
                  <span class="expand-icon">{{ isExpanded(item.group.trendingId, 'successYes') ? '▼' : '▶' }}</span>
                  <span class="category-title success">成功 YES ({{ item.group.successYesTasks.length }})</span>
                </div>
                <div v-if="isExpanded(item.group.trendingId, 'successYes')" class="mode2-tasks-list">
                  <div 
                    v-for="(task, taskIndex) in item.group.successYesTasks" 
                    :key="taskIndex"
                    class="task-item"
                  >
                    <div class="task-line">
                      <span class="task-id">{{ task.id }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">电脑组:</span>{{ task.groupNo || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">浏览器编号:</span>{{ task.browserId || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.createTime) }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.updateTime) }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.side === 1 ? 'buy' : 'sell']">
                        {{ task.side === 1 ? '买入' : '卖出' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.amt }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.price }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.psSide === 1 ? 'yes' : 'no']">
                        {{ task.psSide === 1 ? 'YES' : 'NO' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">链上余额:</span>
                        <span v-if="task.onChainBalance" :class="['balance-value', 
                          task.onChainBalance === '获取失败' ? 'error' : 'success']">
                          {{ task.onChainBalance }}
                        </span>
                        <button 
                          v-else
                          @click="loadTaskBalance(task)"
                          class="balance-btn"
                          :disabled="task.balanceLoading"
                        >
                          {{ task.balanceLoading ? '加载中...' : '获取' }}
                        </button>
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info msg-value">{{ formatTaskMsg(task.msg) || '无' }}</span>
                      <span class="task-separator">|</span>
                      <a 
                        :href="task.opUrl" 
                        target="_blank" 
                        class="link-btn"
                      >
                        查看
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 成功NO -->
              <div v-if="item.group.successNoTasks && item.group.successNoTasks.length > 0" class="mode2-category">
                <div 
                  class="mode2-category-header"
                  @click="toggleExpand(item.group.trendingId, 'successNo')"
                >
                  <span class="expand-icon">{{ isExpanded(item.group.trendingId, 'successNo') ? '▼' : '▶' }}</span>
                  <span class="category-title success">成功 NO ({{ item.group.successNoTasks.length }})</span>
                </div>
                <div v-if="isExpanded(item.group.trendingId, 'successNo')" class="mode2-tasks-list">
                  <div 
                    v-for="(task, taskIndex) in item.group.successNoTasks" 
                    :key="taskIndex"
                    class="task-item"
                  >
                    <div class="task-line">
                      <span class="task-id">{{ task.id }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">电脑组:</span>{{ task.groupNo || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">浏览器编号:</span>{{ task.browserId || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.createTime) }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.updateTime) }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.side === 1 ? 'buy' : 'sell']">
                        {{ task.side === 1 ? '买入' : '卖出' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.amt }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.price }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.psSide === 1 ? 'yes' : 'no']">
                        {{ task.psSide === 1 ? 'YES' : 'NO' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">链上余额:</span>
                        <span v-if="task.onChainBalance" :class="['balance-value', 
                          task.onChainBalance === '获取失败' ? 'error' : 'success']">
                          {{ task.onChainBalance }}
                        </span>
                        <button 
                          v-else
                          @click="loadTaskBalance(task)"
                          class="balance-btn"
                          :disabled="task.balanceLoading"
                        >
                          {{ task.balanceLoading ? '加载中...' : '获取' }}
                        </button>
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info msg-value">{{ formatTaskMsg(task.msg) || '无' }}</span>
                      <span class="task-separator">|</span>
                      <a 
                        :href="task.opUrl" 
                        target="_blank" 
                        class="link-btn"
                      >
                        查看
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 失败YES -->
              <div v-if="item.group.failYesTasks && item.group.failYesTasks.length > 0" class="mode2-category">
                <div class="mode2-category-header">
                  <span class="expand-icon">▼</span>
                  <span class="category-title fail">失败 YES ({{ item.group.failYesTasks.length }})</span>
                </div>
                <div class="mode2-tasks-list">
                  <div 
                    v-for="(task, taskIndex) in item.group.failYesTasks" 
                    :key="taskIndex"
                    class="task-item"
                  >
                    <div class="task-line">
                      <span class="task-id">{{ task.id }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">电脑组:</span>{{ task.groupNo || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">浏览器编号:</span>{{ task.browserId || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.createTime) }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.updateTime) }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.side === 1 ? 'buy' : 'sell']">
                        {{ task.side === 1 ? '买入' : '卖出' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.amt }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.price }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.psSide === 1 ? 'yes' : 'no']">
                        {{ task.psSide === 1 ? 'YES' : 'NO' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">链上余额:</span>
                        <span v-if="task.onChainBalance" :class="['balance-value', 
                          task.onChainBalance === '获取失败' ? 'error' : 'success']">
                          {{ task.onChainBalance }}
                        </span>
                        <button 
                          v-else
                          @click="loadTaskBalance(task)"
                          class="balance-btn"
                          :disabled="task.balanceLoading"
                        >
                          {{ task.balanceLoading ? '加载中...' : '获取' }}
                        </button>
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info msg-value">{{ formatTaskMsg(task.msg) || '无' }}</span>
                      <span class="task-separator">|</span>
                      <a 
                        :href="task.opUrl" 
                        target="_blank" 
                        class="link-btn"
                      >
                        查看
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 失败NO -->
              <div v-if="item.group.failNoTasks && item.group.failNoTasks.length > 0" class="mode2-category">
                <div class="mode2-category-header">
                  <span class="expand-icon">▼</span>
                  <span class="category-title fail">失败 NO ({{ item.group.failNoTasks.length }})</span>
                </div>
                <div class="mode2-tasks-list">
                  <div 
                    v-for="(task, taskIndex) in item.group.failNoTasks" 
                    :key="taskIndex"
                    class="task-item"
                  >
                    <div class="task-line">
                      <span class="task-id">{{ task.id }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">电脑组:</span>{{ task.groupNo || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">浏览器编号:</span>{{ task.browserId || '-' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.createTime) }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ formatDateTime(task.updateTime) }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.side === 1 ? 'buy' : 'sell']">
                        {{ task.side === 1 ? '买入' : '卖出' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.amt }}</span>
                      <span class="task-separator">|</span>
                      <span class="task-info">{{ task.price }}</span>
                      <span class="task-separator">|</span>
                      <span :class="['task-info', task.psSide === 1 ? 'yes' : 'no']">
                        {{ task.psSide === 1 ? 'YES' : 'NO' }}
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info">
                        <span class="field-label">链上余额:</span>
                        <span v-if="task.onChainBalance" :class="['balance-value', 
                          task.onChainBalance === '获取失败' ? 'error' : 'success']">
                          {{ task.onChainBalance }}
                        </span>
                        <button 
                          v-else
                          @click="loadTaskBalance(task)"
                          class="balance-btn"
                          :disabled="task.balanceLoading"
                        >
                          {{ task.balanceLoading ? '加载中...' : '获取' }}
                        </button>
                      </span>
                      <span class="task-separator">|</span>
                      <span class="task-info msg-value">{{ formatTaskMsg(task.msg) || '无' }}</span>
                      <span class="task-separator">|</span>
                      <a 
                        :href="task.opUrl" 
                        target="_blank" 
                        class="link-btn"
                      >
                        查看
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 空状态 -->
      <section class="empty-section" v-if="!loading && Object.keys(results).length === 0 && hasQueried">
        <p>未找到异常账号</p>
      </section>
    </div>

    <!-- Toast 提示 -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      {{ toast.message }}
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TaskAnomaly',
  data() {
    return {
      queryMode: 1, // 默认模式1
      query: {
        startTime: '',
        endTime: ''
      },
      recentHours: 3, // 默认查询最近3小时
      loading: false,
      results: {},
      hasQueried: false,
      filterKeyword: '', // 筛选关键词
      filterHistory: [], // 筛选历史
      expandedGroups: {}, // 模式2中展开的分组 {trendingId: {successYes: true, successNo: true}}
      selectedGroup: 'default', // 当前选择的分组
      groupConfigList: [], // 分组配置列表
      sideFilter: 'all', // 模式1的交易方向筛选：'all'全部, 'buy'买入, 'sell'卖出
      toast: {
        show: false,
        message: '',
        type: 'info'
      }
    }
  },
  mounted() {
    // 从本地存储加载筛选历史
    this.loadFilterHistory()
    
    // 解析URL参数
    this.parseUrlParams()
    
    // 如果有分组参数，加载分组配置（不自动查询）
    if (this.selectedGroup !== 'default') {
      this.loadGroupConfig(this.selectedGroup)
    }
  },
  computed: {
    // 过滤后的结果
    filteredResults() {
      // 先应用关键词筛选
      let keywordFiltered = this.results
      if (this.filterKeyword && this.filterKeyword.trim() !== '') {
        const keyword = this.filterKeyword.trim().toLowerCase()
        keywordFiltered = {}
        
        if (this.queryMode === 1) {
          // 模式1：过滤每个任务组：如果组内任何一个任务匹配关键词，就显示整个组
          Object.keys(this.results).forEach(groupKey => {
            const group = this.results[groupKey]
            
            // 检查组内是否有任何任务匹配关键词
            const hasMatch = group.tasks.some(task => {
              // 检查失败原因是否包含关键词（同时检查原始和格式化后的文本）
              const originalMsg = (task.msg || '').toLowerCase()
              const formattedMsg = this.formatTaskMsg(task.msg).toLowerCase()
              return originalMsg.includes(keyword) || formattedMsg.includes(keyword)
            })
            
            // 如果有匹配，返回整个组（包含所有任务）
            if (hasMatch) {
              keywordFiltered[groupKey] = {
                ...group,
                tasks: group.tasks // 返回所有任务，而不是只返回匹配的任务
              }
            }
          })
        } else {
          // 模式2：检查所有分类的任务
          Object.keys(this.results).forEach(groupKey => {
            const group = this.results[groupKey]
            
            // 检查所有任务列表（成功YES、成功NO、失败YES、失败NO）
            const allTasks = [
              ...(group.successYesTasks || []),
              ...(group.successNoTasks || []),
              ...(group.failYesTasks || []),
              ...(group.failNoTasks || [])
            ]
            
            const hasMatch = allTasks.some(task => {
              const originalMsg = (task.msg || '').toLowerCase()
              const formattedMsg = this.formatTaskMsg(task.msg).toLowerCase()
              return originalMsg.includes(keyword) || formattedMsg.includes(keyword)
            })
            
            if (hasMatch) {
              keywordFiltered[groupKey] = { ...group }
            }
          })
        }
      }
      
      // 模式1时应用交易方向筛选
      if (this.queryMode === 1 && this.sideFilter !== 'all') {
        const sideFiltered = {}
        Object.keys(keywordFiltered).forEach(groupKey => {
          const group = keywordFiltered[groupKey]
          
          // 根据 sideFilter 筛选任务
          const filteredTasks = group.tasks.filter(task => {
            if (this.sideFilter === 'buy') {
              return task.side === 1 // 买入
            } else if (this.sideFilter === 'sell') {
              return task.side !== 1 // 卖出
            }
            return true
          })
          
          // 如果筛选后还有任务，则保留这个组
          if (filteredTasks.length > 0) {
            sideFiltered[groupKey] = {
              ...group,
              tasks: filteredTasks
            }
          }
        })
        return sideFiltered
      }
      
      return keywordFiltered
    },
    
    // 获取带索引的任务组列表，用于颜色循环（模式1）
    taskGroupsWithIndex() {
      if (this.queryMode !== 1) return []
      
      // 对组键进行排序，确保顺序稳定
      const sortedKeys = Object.keys(this.filteredResults).sort((a, b) => {
        // 先按groupId排序，确保同组任务颜色一致
        const groupA = this.filteredResults[a].groupId
        const groupB = this.filteredResults[b].groupId
        if (groupA < groupB) return -1
        if (groupA > groupB) return 1
        return 0
      })
      
      // 创建internalGroupId到colorIndex的映射，确保同组任务使用相同颜色
      const groupIdColorMap = new Map()
      sortedKeys.forEach((groupKey, index) => {
        const group = this.filteredResults[groupKey]
        const colorIndex = index % 4
        // 使用internalGroupId作为key，确保同组任务使用相同颜色
        const internalGroupId = group.internalGroupId || group.groupId
        groupIdColorMap.set(internalGroupId, colorIndex)
      })
      
      return sortedKeys.map((groupKey) => {
        const group = this.filteredResults[groupKey]
        const internalGroupId = group.internalGroupId || group.groupId
        return {
          groupKey,
          group: group,
          colorIndex: groupIdColorMap.get(internalGroupId) || 0
        }
      })
    },
    
    // 获取带索引的任务组列表，用于颜色循环（模式2）
    mode2GroupsWithIndex() {
      if (this.queryMode !== 2) return []
      
      const sortedKeys = Object.keys(this.filteredResults).sort((a, b) => {
        const groupA = this.filteredResults[a].trendingId
        const groupB = this.filteredResults[b].trendingId
        if (groupA < groupB) return -1
        if (groupA > groupB) return 1
        return 0
      })
      
      return sortedKeys.map((groupKey, index) => {
        const group = this.filteredResults[groupKey]
        return {
          groupKey,
          group: group,
          colorIndex: index % 4
        }
      })
    }
  },
  methods: {
    // 解析URL参数
    parseUrlParams() {
      const hash = window.location.hash
      const params = new URLSearchParams(hash.split('?')[1] || '')
      const groupParam = params.get('group')
      
      if (groupParam) {
        // 参数映射：分组1传2->收到2选分组2, 分组2传3->收到3选分组3, 分组3传1->收到1选分组3
        if (groupParam === '2') {
          this.selectedGroup = '2' // 收到2，对应分组2
        } else if (groupParam === '3') {
          this.selectedGroup = '3' // 收到3，对应分组3
        } else if (groupParam === '1') {
          this.selectedGroup = '3' // 收到1，对应分组3
        }
      }
    },
    
    // 加载分组配置
    async loadGroupConfig(groupNo) {
      try {
        const response = await axios.get(`https://sg.bicoin.com.cn/99l/mission/exchangeConfigByGroupNo?groupNo=${groupNo}`)
        
        if (response.data && response.data.code === 0) {
          this.groupConfigList = response.data.data.configList || []
          console.log(`分组${groupNo}配置加载成功，共 ${this.groupConfigList.length} 个主题`)
          return true
        } else {
          console.error('获取分组配置失败')
          this.showToast('获取分组配置失败', 'error')
          return false
        }
      } catch (error) {
        console.error('加载分组配置失败:', error)
        this.showToast('加载分组配置失败', 'error')
        return false
      }
    },
    
    // 分组变化处理
    async onGroupChange() {
      if (this.selectedGroup === 'default') {
        this.groupConfigList = []
      } else {
        await this.loadGroupConfig(this.selectedGroup)
      }
    },
    
    // 检查主题是否在分组配置中
    isTopicInGroupConfig(trending) {
      if (this.selectedGroup === 'default') {
        return true // 默认分组显示所有主题
      }
      return this.groupConfigList.some(config => config.trending === trending)
    },
    
    // 切换模式
    switchMode(mode) {
      if (this.queryMode !== mode) {
        this.queryMode = mode
        // 清空结果和展开状态
        this.results = {}
        this.expandedGroups = {}
        this.hasQueried = false
        this.filterKeyword = ''
        this.sideFilter = 'all' // 重置交易方向筛选
      }
    },
    
    // 获取链上余额
    async getOnChainBalance(fingerprintNo, title, psSide) {
      if (!fingerprintNo || !title) {
        return '获取失败'
      }
      
      try {
        const response = await axios.post('https://enstudyai.fatedreamer.com/t3/api/fingerprint/position', {
          fingerprintNo: String(fingerprintNo),
          title: title
        })
        
        // 检查是否有错误信息
        if (response.data && response.data.detail) {
          return '获取失败'
        }
        
        // 检查是否有position数据
        if (response.data && response.data.position) {
          const position = response.data.position
          // 根据购买的 YES/NO 返回对应的余额
          if (psSide === 1) {
            // YES
            return position.yes_amount !== undefined ? position.yes_amount.toFixed(8) : '获取失败'
          } else {
            // NO
            return position.no_amount !== undefined ? position.no_amount.toFixed(8) : '获取失败'
          }
        }
        
        return '获取失败'
      } catch (error) {
        console.error('获取链上余额失败:', error)
        return '获取失败'
      }
    },
    
    // 点击查看余额按钮时加载链上余额
    async loadTaskBalance(task) {
      if (!task.browserId || !task.trending) {
        this.showToast('缺少必要信息，无法获取余额', 'warning')
        return
      }
      
      // 如果正在加载中，直接返回
      if (task.balanceLoading) {
        return
      }
      
      // 设置加载状态
      task.balanceLoading = true
      
      try {
        const balance = await this.getOnChainBalance(task.browserId, task.trending, task.psSide)
        task.onChainBalance = balance
      } catch (error) {
        console.error('加载链上余额失败:', error)
        task.onChainBalance = '获取失败'
      } finally {
        task.balanceLoading = false
      }
    },
    
    // 为失败任务加载链上余额（只处理状态不为2的任务）
    async loadOnChainBalances(groups) {
      // 收集所有需要获取余额的任务（只收集失败的任务，status !== 2）
      const tasksToLoad = []
      Object.keys(groups).forEach(groupKey => {
        const group = groups[groupKey]
        // 检查是否有 tasks 属性（模式1）或其他任务数组（模式2）
        if (group.tasks && Array.isArray(group.tasks)) {
          group.tasks.forEach((task, taskIndex) => {
            // 只处理失败的任务（status !== 2）
            if (task.browserId && task.trending && task.status !== 2) {
              tasksToLoad.push({
                task: task,
                groupKey: groupKey,
                taskIndex: taskIndex,
                isMode1: true
              })
            }
          })
        }
      })
      
      // 为每个任务获取链上余额（使用 Promise.all 并发请求，但限制并发数）
      const batchSize = 10 // 每批处理10个任务
      for (let i = 0; i < tasksToLoad.length; i += batchSize) {
        const batch = tasksToLoad.slice(i, i + batchSize)
        await Promise.all(batch.map(async ({ task, groupKey, taskIndex, isMode1 }) => {
          const balance = await this.getOnChainBalance(task.browserId, task.trending, task.psSide)
          // 更新任务对象的链上余额（Vue 3 直接赋值即可）
          if (isMode1 && this.results[groupKey] && this.results[groupKey].tasks && this.results[groupKey].tasks[taskIndex]) {
            this.results[groupKey].tasks[taskIndex].onChainBalance = balance
          } else {
            // 直接更新任务对象（模式2的情况）
            task.onChainBalance = balance
          }
        }))
      }
    },
    
    // 格式化日期时间
    formatDateTime(dateTimeStr) {
      if (!dateTimeStr) return '-'
      try {
        const date = new Date(dateTimeStr)
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        const seconds = String(date.getSeconds()).padStart(2, '0')
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
      } catch (e) {
        return dateTimeStr
      }
    },
    
    // 格式化任务消息
    formatTaskMsg(msg) {
      if (!msg) return ''
      
      // 如果包含"执行异常"，直接返回"执行异常"
      if (msg.includes('执行异常')) {
        return '执行异常'
      }
      
      // 尝试解析JSON格式的Type 1 或 Type 5消息
      try {
        const data = JSON.parse(msg)
        
        if (data.type === 'TYPE1_SUCCESS' || data.type === 'TYPE5_SUCCESS') {
          // Type 1 或 Type 5 成功：全部成交
          let result = `✅ 全部成交`
          
          // 处理初始数量
          if (data.initial_filled_amount) {
            result += ` | 初始数量: ${data.initial_filled_amount}`
          }
          
          // 处理现有数量，如果是"<0.01"则显示为0
          let currentAmount = data.filled_amount
          if (typeof currentAmount === 'string' && currentAmount.includes('<')) {
            currentAmount = '0'
          }
          result += ` | 现有数量: ${currentAmount}`
          
          // 计算并显示交易额（现有数量 - 初始数量）
          if (data.initial_filled_amount && data.filled_amount) {
            // 去除千位分隔符（逗号）后再解析
            const initialAmountStr = String(data.initial_filled_amount).replace(/,/g, '')
            const initialAmount = parseFloat(initialAmountStr) || 0
            
            let filledAmount = 0
            if (typeof data.filled_amount === 'string' && data.filled_amount.includes('<')) {
              filledAmount = 0
            } else {
              const filledAmountStr = String(data.filled_amount).replace(/,/g, '')
              filledAmount = parseFloat(filledAmountStr) || 0
            }
            const tradeAmount = filledAmount - initialAmount
            result += ` | 交易额: ${tradeAmount.toFixed(2)}`
          }
          
          // 显示价格
          result += ` | 价格: ${data.filled_price}`
          
          // 显示交易费
          if (data.transaction_fee) {
            result += ` | 交易费: ${data.transaction_fee}`
          }
          
          return result
        } else if (data.type === 'TYPE1_PARTIAL' || data.type === 'TYPE5_PARTIAL') {
          // Type 1 或 Type 5 部分成交：有挂单
          let result = `⚠️ 部分成交`
          
          // 辅助函数：移除逗号并解析数字
          const parseNumber = (value) => {
            if (!value) return 0
            if (typeof value === 'string') {
              if (value.includes('<')) return 0
              // 移除逗号（千位分隔符）后再解析
              return parseFloat(value.replace(/,/g, '')) || 0
            }
            return parseFloat(value) || 0
          }
          
          // 处理初始数量
          if (data.initial_filled_amount) {
            result += ` | 初始数量: ${data.initial_filled_amount}`
          }
          
          // 处理现有数量
          let currentAmount = data.filled_amount
          if (typeof currentAmount === 'string' && currentAmount.includes('<')) {
            currentAmount = '0'
          }
          result += ` | 现有数量: ${currentAmount}`
          
          // 计算并显示交易额
          if (data.initial_filled_amount && data.filled_amount) {
            const initialAmount = parseNumber(data.initial_filled_amount)
            const filledAmount = parseNumber(data.filled_amount)
            const tradeAmount = filledAmount - initialAmount
            result += ` | 交易额: ${tradeAmount.toFixed(2)}`
          }
          
          result += ` | 成交价格: ${data.filled_price} | 挂单价格: ${data.pending_price} | 进度: ${data.progress}`
          
          if (data.transaction_fee) {
            result += ` | 交易费: ${data.transaction_fee}`
          }
          return result
        }
      } catch (e) {
        // 不是JSON格式，返回原始消息
      }
      
      // 返回原始消息
      return msg
    },
    
    showToast(message, type = 'info') {
      this.toast = {
        show: true,
        message,
        type
      }
      setTimeout(() => {
        this.toast.show = false
      }, 3000)
    },
    
    queryRecentHours() {
      if (!this.recentHours || this.recentHours <= 0) {
        this.showToast('请输入有效的小时数', 'warning')
        return
      }
      
      // 计算时间范围
      const now = new Date()
      const endTime = new Date(now)
      const startTime = new Date(now.getTime() - this.recentHours * 60 * 60 * 1000)
      
      // 转换为 datetime-local 格式 (YYYY-MM-DDTHH:mm)
      const formatDateTime = (date) => {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day}T${hours}:${minutes}`
      }
      
      // 设置查询时间
      this.query.startTime = formatDateTime(startTime)
      this.query.endTime = formatDateTime(endTime)
      
      // 执行查询
      this.queryAnomalies()
    },
    
    async queryAnomalies() {
      if (!this.query.startTime || !this.query.endTime) {
        this.showToast('请选择开始和结束时间', 'warning')
        return
      }
      
      try {
        // 将 datetime-local 格式转换为时间戳
        const startTimestamp = new Date(this.query.startTime).getTime()
        const endTimestamp = new Date(this.query.endTime).getTime()
        
        if (startTimestamp >= endTimestamp) {
          this.showToast('开始时间必须早于结束时间', 'warning')
          return
        }
        
        this.loading = true
        this.hasQueried = false
        
        // 调用接口，根据模式选择type
        const type = this.queryMode === 1 ? 5 : 1
        const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/listPart', {
          params: {
            type: type,
            startTime: startTimestamp,
            endTime: endTimestamp
          }
        })
        
        if (response.data && response.data.code === 0) {
          const missions = response.data.data.list || []
          
          // 根据模式处理数据
          if (this.queryMode === 1) {
            this.processMode1Data(missions)
          } else {
            this.processMode2Data(missions)
          }
        } else {
          this.showToast('查询失败', 'error')
        }
      } catch (error) {
        console.error('查询账号异常失败:', error)
        this.showToast('查询失败: ' + (error.message || '未知错误'), 'error')
      } finally {
        this.loading = false
      }
    },
    
    // 处理模式1的数据
    processMode1Data(missions) {
      // 处理数据：先收集所有任务，建立任务1和任务2的映射关系
          const allTasksMap = new Map() // id -> task (所有任务，包括成功的)
          const task2ToTask1Map = new Map() // task2Id -> task1Id (任务2的id -> 任务1的id)
          const task1ToTask2Map = new Map() // task1Id -> task2Id (任务1的id -> 任务2的id)
          const now = new Date().getTime()
          const twentyMinutes = 20 * 60 * 1000 // 20分钟的毫秒数
          
          // 第一步：收集所有任务，建立任务1和任务2的映射关系
          // 统一将id和tp1转换为字符串，避免类型不一致导致查找失败
          missions.forEach(item => {
            const mission = item.mission
            const exchangeConfig = item.exchangeConfig
            
            const browserId = mission.numberList
            const groupNo = mission.groupNo
            
            // 统一转换为字符串
            const taskId = String(mission.id)
            const tp1Id = mission.tp1 ? String(mission.tp1) : null
            
            const task = {
              id: taskId,
              tp1: tp1Id,
              msg: mission.msg,
              browserId: browserId,
              groupNo: groupNo,
              trending: exchangeConfig.trending,
              opUrl: exchangeConfig.opUrl,
              side: mission.side,
              amt: mission.amt,
              price: mission.price,
              psSide: mission.psSide,
              createTime: mission.createTime,
              updateTime: mission.updateTime,
              status: mission.status // 保存状态，用于判断是否失败
            }
            
            // 记录所有任务（使用字符串作为key）
            allTasksMap.set(taskId, task)
            
            // 建立任务2到任务1的映射（如果任务的tp1存在，说明它是任务2，tp1是任务1的id）
            if (tp1Id) {
              task2ToTask1Map.set(taskId, tp1Id)
              task1ToTask2Map.set(tp1Id, taskId)
            }
          })
          
          // 第二步：过滤出失败的任务
          // 过滤规则：
          // 1. status === 2：跳过（成功任务）
          // 2. status === 3：直接显示（失败任务）
          // 3. status !== 2 && status !== 3：检查 createTime，如果距离现在超过20分钟才显示
          // 4. 如果是分组模式，只显示分组配置中的主题
          const failedTasks = []
          allTasksMap.forEach((task, taskId) => {
            // 跳过状态为2（成功）的任务
            if (task.status === 2) {
              return
            }
            
            // 如果是分组模式，检查主题是否在分组配置中
            if (this.selectedGroup !== 'default' && !this.isTopicInGroupConfig(task.trending)) {
              return
            }
            
            // 如果 status !== 3，需要检查创建时间是否超过20分钟
            if (task.status !== 3) {
              if (task.createTime) {
                const createTime = new Date(task.createTime).getTime()
                const timeDiff = now - createTime
                
                // 如果创建时间距离现在不超过20分钟，跳过（可能是正在执行的任务）
                if (timeDiff <= twentyMinutes) {
                  return
                }
              } else {
                // 如果没有创建时间，也跳过
                return
              }
            }
            
            failedTasks.push(task)
          })
          
          // 第三步：对失败任务进行分组
          // 先建立任务组关系：每个任务组包含任务1和任务2
          const taskGroupMap = new Map() // taskId -> groupId
          const groupMap = new Map() // groupId -> { tasks: [], groupId: string, task1CreateTime: number }
          const processedGroups = new Set() // 已处理的组（用任务1的id标识）
          let groupCounter = 0
          
          // 辅助函数：获取任务的创建时间戳
          const getCreateTime = (task) => {
            if (!task.createTime) return 0
            return new Date(task.createTime).getTime()
          }
          
          // 遍历失败任务，为每个失败任务找到它的组
          failedTasks.forEach(failedTask => {
            // 确定这个失败任务属于哪个组（任务1的id）
            let task1Id = null
            
            // 如果失败任务有tp1，说明它是任务2，tp1就是任务1的id
            if (failedTask.tp1) {
              task1Id = failedTask.tp1
            } else {
              // 如果失败任务没有tp1，说明它是任务1
              task1Id = failedTask.id
            }
            
            // 如果这个组已经处理过，跳过
            if (processedGroups.has(task1Id)) {
              return
            }
            
            // 标记这个组已处理
            processedGroups.add(task1Id)
            
            // 获取任务1和任务2
            const task1 = allTasksMap.get(task1Id)
            if (!task1) {
              // 如果任务1不存在，跳过（不应该发生，但做保护性检查）
              return
            }
            
            const task2Id = task1ToTask2Map.get(task1Id)
            const task2 = task2Id ? allTasksMap.get(task2Id) : null
            
            // 创建新组
            const groupId = `group-${groupCounter++}`
            const group = {
              groupId: groupId,
              tasks: [],
              task1CreateTime: getCreateTime(task1)
            }
            groupMap.set(groupId, group)
            
            // 将任务1加入组（无论是否失败）
            group.tasks.push(task1)
            taskGroupMap.set(task1.id, groupId)
            
            // 将任务2加入组（如果存在，无论是否失败）
            if (task2) {
              group.tasks.push(task2)
              taskGroupMap.set(task2.id, groupId)
            }
          })
          
          // 第四步：为每个任务计算同组任务ID，并转换为对象格式用于显示
          // 先转换为数组，然后根据分组模式决定排序方式
          const groupsArray = []
          groupMap.forEach((group, internalGroupId) => {
            // 为组内每个任务计算同组任务ID
            const tasksWithGroupId = group.tasks.map(task => {
              let groupTaskId = null
              
              // 如果任务有tp1，说明它是任务2，同组任务ID就是tp1（任务1的id）
              if (task.tp1) {
                groupTaskId = task.tp1
              } else {
                // 如果任务没有tp1，说明它是任务1，查找任务2的id
                const task2Id = task1ToTask2Map.get(task.id)
                if (task2Id) {
                  groupTaskId = task2Id
                } else {
                  // 如果没有找到，说明这个任务没有同组任务，显示自己的ID
                  groupTaskId = task.id
                }
              }
              
              return {
                ...task,
                groupTaskId: groupTaskId
              }
            })
            
            // 确定任务1用于显示标识（任务1是没有tp1的那个）
            const task1 = tasksWithGroupId.find(t => !t.tp1)
            const displayKey = task1 ? task1.id : group.tasks[0].id
            
            // 获取主题（trending）用于分组排序
            const trending = task1 ? task1.trending : group.tasks[0].trending
            
            groupsArray.push({
              groupId: displayKey, // 用于显示
              internalGroupId: internalGroupId, // 用于颜色计算，确保同组任务使用相同颜色
              tasks: tasksWithGroupId,
              task1CreateTime: group.task1CreateTime,
              trending: trending // 添加trending用于分组排序
            })
          })
          
          // 排序：如果是分组模式，按事件（trending）分组；否则按时间排序
          if (this.selectedGroup !== 'default') {
            // 分组模式：按trending分组，相同trending的放在一起
            groupsArray.sort((a, b) => {
              // 先按trending排序
              if (a.trending < b.trending) return -1
              if (a.trending > b.trending) return 1
              // 相同trending的，按时间排序
              return a.task1CreateTime - b.task1CreateTime
            })
          } else {
            // 默认模式：按时间排序
            groupsArray.sort((a, b) => {
              return a.task1CreateTime - b.task1CreateTime
            })
          }
          
          // 转换为对象格式，使用排序后的顺序
          const sortedGroups = {}
          groupsArray.forEach((group, index) => {
            // 使用排序后的索引作为key，确保顺序稳定
            sortedGroups[`group-${index}`] = {
              groupId: group.groupId,
              internalGroupId: group.internalGroupId,
              tasks: group.tasks
            }
          })
          
      this.results = sortedGroups
      
      // 不再自动加载链上余额，改为点击按钮时加载
      
      const totalGroups = Object.keys(sortedGroups).length
      this.hasQueried = true
      this.showToast(`查询成功，共 ${totalGroups} 个任务组`, 'success')
    },
    
    // 处理模式2的数据
    processMode2Data(missions) {
      // 按trendingId分组
      const groupsByTrendingId = new Map()
      
      missions.forEach(item => {
        const mission = item.mission
        const exchangeConfig = item.exchangeConfig
        const trendingId = mission.trendingId
        
        if (!groupsByTrendingId.has(trendingId)) {
          groupsByTrendingId.set(trendingId, {
            trendingId: trendingId,
            trending: exchangeConfig.trending,
            tasks: []
          })
        }
        
        const group = groupsByTrendingId.get(trendingId)
        const task = {
          id: String(mission.id),
          browserId: mission.numberList,
          groupNo: mission.groupNo,
          trending: exchangeConfig.trending,
          opUrl: exchangeConfig.opUrl,
          side: mission.side,
          amt: mission.amt,
          price: mission.price,
          psSide: mission.psSide,
          createTime: mission.createTime,
          updateTime: mission.updateTime,
          status: mission.status,
          msg: mission.msg
        }
        
        group.tasks.push(task)
      })
      
      // 辅助函数：检查是否为 TYPE1_PARTIAL
      const isType1Partial = (msg) => {
        if (!msg) return false
        try {
          const data = JSON.parse(msg)
          return data.type === 'TYPE1_PARTIAL'
        } catch (e) {
          return false
        }
      }
      
      // 处理每个分组：统计成功/失败，分类任务
      const processedGroups = {}
      groupsByTrendingId.forEach((group, trendingId) => {
        // 如果是分组模式，只处理分组配置中的主题
        if (this.selectedGroup !== 'default' && !this.isTopicInGroupConfig(group.trending)) {
          return
        }
        let successYesAmt = 0
        let successNoAmt = 0
        let failYesAmt = 0
        let failNoAmt = 0
        let failYesAmtExcludePartial = 0  // 排除 PARTIAL 的失败 YES amt
        let failNoAmtExcludePartial = 0    // 排除 PARTIAL 的失败 NO amt
        
        const successYesTasks = []
        const successNoTasks = []
        const failYesTasks = []
        const failNoTasks = []
        
        group.tasks.forEach(task => {
          if (task.status === 2) {
            // 成功任务
            if (task.psSide === 1) {
              successYesAmt += parseFloat(task.amt) || 0
              successYesTasks.push(task)
            } else {
              successNoAmt += parseFloat(task.amt) || 0
              successNoTasks.push(task)
            }
          } else {
            // 失败任务
            const taskAmt = parseFloat(task.amt) || 0
            if (task.psSide === 1) {
              failYesAmt += taskAmt
              failYesTasks.push(task)
              // 排除 TYPE1_PARTIAL
              if (!isType1Partial(task.msg)) {
                failYesAmtExcludePartial += taskAmt
              }
            } else {
              failNoAmt += taskAmt
              failNoTasks.push(task)
              // 排除 TYPE1_PARTIAL
              if (!isType1Partial(task.msg)) {
                failNoAmtExcludePartial += taskAmt
              }
            }
          }
        })
        
        // 计算需补信息
        let needSupplement = null
        if (failYesAmtExcludePartial > failNoAmtExcludePartial) {
          needSupplement = {
            type: 'YES',
            amount: (failYesAmtExcludePartial - failNoAmtExcludePartial).toFixed(2)
          }
        } else if (failNoAmtExcludePartial > failYesAmtExcludePartial) {
          needSupplement = {
            type: 'NO',
            amount: (failNoAmtExcludePartial - failYesAmtExcludePartial).toFixed(2)
          }
        }
        
        processedGroups[`trending-${trendingId}`] = {
          trendingId: trendingId,
          trending: group.trending,
          successYesAmt: successYesAmt.toFixed(2),
          successNoAmt: successNoAmt.toFixed(2),
          failYesAmt: failYesAmt.toFixed(2),
          failNoAmt: failNoAmt.toFixed(2),
          failYesAmtExcludePartial: failYesAmtExcludePartial.toFixed(2),
          failNoAmtExcludePartial: failNoAmtExcludePartial.toFixed(2),
          needSupplement: needSupplement,
          successYesTasks: successYesTasks,
          successNoTasks: successNoTasks,
          failYesTasks: failYesTasks,
          failNoTasks: failNoTasks
        }
      })
      
      this.results = processedGroups
      
      // 不再自动加载链上余额，改为点击按钮时加载
      
      const totalGroups = Object.keys(processedGroups).length
      this.hasQueried = true
      this.showToast(`查询成功，共 ${totalGroups} 个任务组`, 'success')
    },
    
    // 应用筛选
    applyFilter() {
      if (!this.filterKeyword || this.filterKeyword.trim() === '') {
        this.showToast('请输入筛选关键词', 'warning')
        return
      }
      
      // 保存筛选历史
      this.saveFilterHistory(this.filterKeyword.trim())
      
      let filteredCount = 0
      if (this.queryMode === 1) {
        filteredCount = Object.values(this.filteredResults).reduce((sum, group) => sum + (group.tasks ? group.tasks.length : 0), 0)
      } else {
        filteredCount = Object.values(this.filteredResults).reduce((sum, group) => {
          return sum + 
            (group.successYesTasks ? group.successYesTasks.length : 0) +
            (group.successNoTasks ? group.successNoTasks.length : 0) +
            (group.failYesTasks ? group.failYesTasks.length : 0) +
            (group.failNoTasks ? group.failNoTasks.length : 0)
        }, 0)
      }
      
      if (filteredCount === 0) {
        this.showToast('未找到匹配的任务', 'warning')
      } else {
        this.showToast(`筛选完成，找到 ${filteredCount} 个匹配的任务`, 'success')
      }
    },
    
    // 清除筛选
    clearFilter() {
      this.filterKeyword = ''
      this.showToast('筛选已清除', 'info')
    },
    
    // 从本地存储加载筛选历史
    loadFilterHistory() {
      try {
        const history = localStorage.getItem('taskAnomaly_filterHistory')
        if (history) {
          this.filterHistory = JSON.parse(history)
        }
      } catch (e) {
        console.error('加载筛选历史失败:', e)
        this.filterHistory = []
      }
    },
    
    // 保存筛选历史到本地存储
    saveFilterHistory(keyword) {
      if (!keyword || keyword.trim() === '') {
        return
      }
      
      try {
        // 移除重复项
        let history = [...this.filterHistory]
        const index = history.indexOf(keyword)
        if (index > -1) {
          // 如果已存在，先移除
          history.splice(index, 1)
        }
        // 添加到最前面
        history.unshift(keyword)
        // 最多保存10条历史
        if (history.length > 10) {
          history = history.slice(0, 10)
        }
        
        this.filterHistory = history
        localStorage.setItem('taskAnomaly_filterHistory', JSON.stringify(history))
      } catch (e) {
        console.error('保存筛选历史失败:', e)
      }
    },
    
    // 选择历史记录
    selectHistory(keyword) {
      this.filterKeyword = keyword
      // 自动执行筛选
      this.applyFilter()
    },
    
    // 切换展开/折叠（模式2）
    toggleExpand(trendingId, category) {
      if (!this.expandedGroups[trendingId]) {
        this.expandedGroups[trendingId] = {}
      }
      
      const isExpanded = this.expandedGroups[trendingId][category] || false
      this.expandedGroups[trendingId][category] = !isExpanded
      
      // 不再自动加载链上余额，改为点击按钮时加载
    },
    
    // 检查是否展开（模式2）
    isExpanded(trendingId, category) {
      return this.expandedGroups[trendingId] && this.expandedGroups[trendingId][category]
    },
    
    // 加载模式2分类的链上余额（只处理失败任务，status !== 2）
    async loadMode2CategoryBalances(trendingId, category) {
      // 找到对应的分组
      const groupKey = Object.keys(this.results).find(key => {
        const group = this.results[key]
        return group.trendingId === trendingId
      })
      
      if (!groupKey) return
      
      const group = this.results[groupKey]
      let tasks = []
      
      if (category === 'successYes') {
        tasks = group.successYesTasks || []
      } else if (category === 'successNo') {
        tasks = group.successNoTasks || []
      }
      
      // 过滤出失败的任务（status !== 2）
      const failedTasks = tasks.filter(task => task.status !== 2)
      
      // 只为失败任务加载链上余额
      const batchSize = 10
      for (let i = 0; i < failedTasks.length; i += batchSize) {
        const batch = failedTasks.slice(i, i + batchSize)
        await Promise.all(batch.map(async (task) => {
          const balance = await this.getOnChainBalance(task.browserId, task.trending, task.psSide)
          // 更新任务对象的链上余额
          task.onChainBalance = balance
        }))
      }
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
}

.container {
  max-width: 2000px;
  margin: 0 auto;
}

/* 查询区域 */
.query-section {
  background: white;
  border-radius: 8px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.query-form {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.datetime-input {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 200px;
  transition: border-color 0.3s;
}

.datetime-input:focus {
  outline: none;
  border-color: #667eea;
}

.group-select {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 120px;
  transition: border-color 0.3s;
  background: white;
  cursor: pointer;
}

.group-select:focus {
  outline: none;
  border-color: #667eea;
}

/* 模式开关 */
.mode-switch {
  display: flex;
  gap: 8px;
}

.mode-btn {
  padding: 10px 20px;
  border: 2px solid #ddd;
  border-radius: 6px;
  background: white;
  color: #666;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 80px;
}

.mode-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.mode-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.query-btn {
  padding: 10px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 42px;
}

.query-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.query-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 快速查询区域 */
.quick-query-form {
  display: flex;
  gap: 15px;
  align-items: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.quick-query-form .form-group {
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.hours-input {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  width: 100px;
  transition: border-color 0.3s;
}

.hours-input:focus {
  outline: none;
  border-color: #667eea;
}

.hours-label {
  font-weight: 500;
  color: #555;
  font-size: 14px;
  white-space: nowrap;
}

.quick-query-btn {
  padding: 10px 25px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 42px;
  white-space: nowrap;
}

.quick-query-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
}

.quick-query-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 结果区域 */
.results-section {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.results-header {
  margin-bottom: 20px;
}

.results-section h2 {
  margin-bottom: 15px;
  color: #333;
  font-size: 20px;
}

/* 筛选区域 */
.filter-section {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.filter-input-wrapper {
  flex: 1;
  min-width: 250px;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-input {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  width: 100%;
  transition: border-color 0.3s;
}

.filter-input:focus {
  outline: none;
  border-color: #667eea;
}

/* 筛选历史 */
.filter-history {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
}

.history-label {
  color: #666;
  font-weight: 500;
}

.history-item {
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 4px;
  color: #667eea;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-item:hover {
  background: #667eea;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.filter-btn {
  padding: 10px 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  white-space: nowrap;
}

.filter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.clear-filter-btn {
  padding: 10px 20px;
  background: #95a5a6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  white-space: nowrap;
}

.clear-filter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(149, 165, 166, 0.4);
  background: #7f8c8d;
}

.tasks-container {
  padding: 0;
  background: transparent;
}

.task-groups-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 任务组卡片 */
.task-group-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.task-group-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 任务组背景颜色循环 */
.task-group-card.group-color-0 {
  border-left: 4px solid #667eea;
}

.task-group-card.group-color-1 {
  border-left: 4px solid #f093fb;
}

.task-group-card.group-color-2 {
  border-left: 4px solid #4facfe;
}

.task-group-card.group-color-3 {
  border-left: 4px solid #43e97b;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-label {
  font-size: 14px;
  opacity: 0.9;
}

.group-id {
  font-size: 16px;
  font-weight: 600;
}

.group-task-count {
  font-size: 14px;
  opacity: 0.9;
}

.tasks-list {
  display: flex;
  flex-direction: column;
}

.task-item {
  padding: 12px 20px;
  border-bottom: 1px solid #e0e0e0;
  transition: background-color 0.2s;
}

.task-item:last-child {
  border-bottom: none;
}

.task-item:hover {
  background-color: #f8f9fa;
}

.task-line {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 14px;
}

.task-id {
  font-weight: 600;
  color: #667eea;
  font-size: 15px;
}

.task-separator {
  color: #ccc;
  font-weight: 300;
}

.task-info {
  color: #333;
}

.field-label {
  color: #666;
  font-weight: 500;
  margin-right: 4px;
}

.balance-value {
  font-weight: 600;
}

.balance-value.success {
  color: #27ae60;
}

.balance-value.error {
  color: #e74c3c;
}

.balance-value.loading {
  color: #95a5a6;
  font-style: italic;
}

.task-info.msg-value {
  color: #e74c3c;
  font-weight: 500;
  max-width: 400px;
  word-break: break-word;
}

.buy {
  color: #27ae60;
  font-weight: 600;
}

.sell {
  color: #e74c3c;
  font-weight: 600;
}

.yes {
  color: #3498db;
  font-weight: 600;
}

.no {
  color: #e67e22;
  font-weight: 600;
}

.link-btn {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.link-btn:hover {
  color: #764ba2;
  text-decoration: underline;
}

.balance-btn {
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.balance-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.4);
}

.balance-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 模式2样式 */
.mode2-group-header {
  padding: 15px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
}

.mode2-trending {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
}

.mode2-stats {
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.stat-item {
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.stat-item.success {
  background: rgba(39, 174, 96, 0.3);
}

.stat-item.fail {
  background: rgba(231, 76, 60, 0.3);
}

.stat-item.fail-exclude-partial {
  background: rgba(231, 76, 60, 0.2);
  border: 1px solid rgba(231, 76, 60, 0.5);
}

.stat-item.supplement {
  background: rgba(241, 196, 15, 0.3);
  color: #f1c40f;
  font-weight: 600;
}

.mode2-category {
  border-bottom: 1px solid #e0e0e0;
}

.mode2-category:last-child {
  border-bottom: none;
}

.mode2-category-header {
  padding: 12px 20px;
  background: #f8f9fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background-color 0.2s;
  user-select: none;
}

.mode2-category-header:hover {
  background: #e9ecef;
}

.expand-icon {
  font-size: 12px;
  color: #666;
  width: 20px;
  text-align: center;
}

.category-title {
  font-weight: 600;
  font-size: 14px;
}

.category-title.success {
  color: #27ae60;
}

.category-title.fail {
  color: #e74c3c;
}

.mode2-tasks-list {
  background: white;
}

/* 空状态 */
.empty-section {
  background: white;
  border-radius: 8px;
  padding: 60px 30px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-section p {
  color: #999;
  font-size: 16px;
}

/* Toast 提示 */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 25px;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  background: #27ae60;
}

.toast.error {
  background: #e74c3c;
}

.toast.warning {
  background: #f39c12;
}

.toast.info {
  background: #3498db;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .query-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .datetime-input {
    width: 100%;
  }
  
  .query-btn {
    width: 100%;
  }
  
  .quick-query-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .quick-query-form .form-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .hours-input {
    width: 100%;
  }
  
  .quick-query-btn {
    width: 100%;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-input-wrapper {
    width: 100%;
    max-width: 100%;
  }
  
  .filter-input {
    width: 100%;
    max-width: 100%;
  }
  
  .filter-btn,
  .clear-filter-btn {
    width: 100%;
  }
  
  .history-item {
    max-width: 120px;
  }
  
  .group-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .task-line {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .task-separator {
    display: none;
  }
  
  .task-info.msg-value {
    max-width: 100%;
  }
}
</style>

