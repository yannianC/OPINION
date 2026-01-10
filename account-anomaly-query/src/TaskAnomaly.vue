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
        
        <div class="time-range-query-form">
          <div class="form-group">
            <label>时间区间查询:</label>
            <div class="time-range-inputs">
              <input 
                v-model="timeRangeStart" 
                type="text" 
                class="time-range-input"
                placeholder="开始时间，如: 24-16"
                pattern="\d{1,2}-\d{1,2}"
              />
              <span class="time-range-separator">到</span>
              <input 
                v-model="timeRangeEnd" 
                type="text" 
                class="time-range-input"
                placeholder="结束时间，如: 24-18"
                pattern="\d{1,2}-\d{1,2}"
              />
            </div>
            <span class="time-range-hint">格式：日-时，如 24-16 表示24日16时</span>
          </div>
          <button 
            class="time-range-query-btn" 
            @click="queryTimeRange"
            :disabled="loading || !timeRangeStart || !timeRangeEnd"
          >
            {{ loading ? '查询中...' : '时间区间查询' }}
          </button>
        </div>
      </section>

      <!-- 结果区域 -->
      <section class="results-section" v-if="Object.keys(results).length > 0">
        <div class="results-header">
          <!-- 统计信息 -->
          <div class="statistics-section">
            <div class="statistics-title">
              任务统计（共 {{ taskStatistics.total.total }} 个任务，
              <span class="buy-count">买入: {{ taskStatistics.total.buy }}</span>，
              <span class="sell-count">卖出: {{ taskStatistics.total.sell }}</span>）
            </div>
            <div class="statistics-items">
              <div class="stat-item">
                <span class="stat-label">全部成交:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.allFilled.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.allFilled.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">部分成交:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.partialFilled.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.partialFilled.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">单边成交:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.singleSideFilled.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.singleSideFilled.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">IP问题:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.ipProblem.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.ipProblem.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">余额或仓位不对:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.balanceOrPosition.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.balanceOrPosition.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">挂单失败（普通）:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.orderFailed.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.orderFailed.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">限价距离市价差距过大:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.priceGapTooLarge.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.priceGapTooLarge.sell }}</span>
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">已有挂单:</span>
                <span class="stat-value">
                  <span class="buy-count">买入: {{ taskStatistics.alreadyHasOrder.buy }}</span>
                  <span>/</span>
                  <span class="sell-count">卖出: {{ taskStatistics.alreadyHasOrder.sell }}</span>
                </span>
              </div>
              <div class="stat-item stat-item-expandable">
                <div class="stat-item-header">
                  <span class="stat-label">挂单失败（全部）:</span>
                  <span class="stat-value">
                    <span class="buy-count">买入: {{ taskStatistics.orderFailed.buy + taskStatistics.priceGapTooLarge.buy + taskStatistics.alreadyHasOrder.buy }}</span>
                    <span>/</span>
                    <span class="sell-count">卖出: {{ taskStatistics.orderFailed.sell + taskStatistics.priceGapTooLarge.sell + taskStatistics.alreadyHasOrder.sell }}</span>
                  </span>
                  <button 
                    v-if="(taskStatistics.orderFailed.buy + taskStatistics.orderFailed.sell + taskStatistics.priceGapTooLarge.buy + taskStatistics.priceGapTooLarge.sell + taskStatistics.alreadyHasOrder.buy + taskStatistics.alreadyHasOrder.sell) > 0"
                    class="expand-msg-btn"
                    @click="showOrderFailedMsgs = !showOrderFailedMsgs"
                  >
                    {{ showOrderFailedMsgs ? '收起' : '查看msg' }}
                  </button>
                </div>
                <div v-if="showOrderFailedMsgs && (taskStatistics.orderFailed.buy + taskStatistics.orderFailed.sell + taskStatistics.priceGapTooLarge.buy + taskStatistics.priceGapTooLarge.sell + taskStatistics.alreadyHasOrder.buy + taskStatistics.alreadyHasOrder.sell) > 0" class="msg-list">
                  <div class="msg-list-title">挂单失败的不同msg（共 {{ uniqueOrderFailedMsgs.length }} 种）:</div>
                  <div class="msg-list-items">
                    <div 
                      v-for="(item, index) in uniqueOrderFailedMsgs" 
                      :key="index"
                      class="msg-list-item"
                    >
                      <span class="msg-count">[{{ item.count }}次]</span>
                      <span class="msg-content">{{ item.msg }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 汇总统计 -->
            <div class="summary-statistics">
              <div class="summary-item buy-summary">
                <div class="summary-title">开仓（买入）统计：</div>
                <div class="summary-content">
                  开仓组数{{ taskStatistics.total.buy/2}}，
                  开仓成功率{{ buyStatistics.successRate }}%，
                  部分成交{{ buyStatistics.partialFilled }}%，
                  单边成交{{ buyStatistics.singleSideFilled }}%，
                  失败的{{ buyStatistics.notFilled }}%，
                  失败原因：IP问题{{ buyStatistics.ipProblem }}%，
                  资产更新不及时{{ buyStatistics.balanceOrPosition }}%，
                  挂单失败{{ buyStatistics.orderFailed }}%，
                  限价距离市价差距过大{{ buyStatistics.priceGapTooLarge }}%，
                  已有挂单{{ buyStatistics.alreadyHasOrder }}%
                </div>
              </div>
              <div class="summary-item sell-summary">
                <div class="summary-title">平仓（卖出）统计：</div>
                <div class="summary-content">
                  平仓组数{{ taskStatistics.total.sell/2}}，
                  平仓成功率{{ sellStatistics.successRate }}%，
                  部分成交{{ sellStatistics.partialFilled }}%，
                  单边成交{{ sellStatistics.singleSideFilled }}%，
                  失败的{{ sellStatistics.notFilled }}%，
                  失败原因：IP问题{{ sellStatistics.ipProblem }}%，
                  资产更新不及时{{ sellStatistics.balanceOrPosition }}%，
                  挂单失败{{ sellStatistics.orderFailed }}%，
                  限价距离市价差距过大{{ sellStatistics.priceGapTooLarge }}%，
                  已有挂单{{ sellStatistics.alreadyHasOrder }}%
                </div>
              </div>
            </div>
          </div>
          <h2>查询结果 (共 {{ Object.keys(results).length }} 个任务组)</h2>
          
          <!-- 模式1：组状态统计区域 -->
          <div v-if="queryMode === 1" class="group-status-statistics">
            <div class="status-stat-row">
              <span class="status-stat-item status-success" @click="setStatusFilter('success')">
                全部成功: {{ groupStatusStatistics.success }}
              </span>
              <span class="status-stat-item status-repaired" @click="setStatusFilter('repaired')">
                修复后全部成功: {{ groupStatusStatistics.repaired }}
              </span>
              <span class="status-stat-item status-failed" @click="setStatusFilter('failed')">
                失败: {{ groupStatusStatistics.failed }}
              </span>
              <span class="status-stat-item status-no-impact" @click="setStatusFilter('noImpact')">
                失败无影响: {{ groupStatusStatistics.noImpact }}
              </span>
              <span class="status-stat-item status-running" @click="setStatusFilter('running')">
                进行中: {{ groupStatusStatistics.running }}
              </span>
            </div>
          </div>
          
          <!-- 模式1：仓位统计区域（仅失败状态） -->
          <div v-if="queryMode === 1 && groupStatusStatistics.failed > 0" class="position-statistics">
            <div class="position-stat-header">
              <span class="position-stat-title">失败任务仓位统计</span>
              <button 
                class="btn-query-position-stat"
                @click="queryPositionStatistics"
                :disabled="isQueryingPositionStat"
              >
                {{ isQueryingPositionStat ? '查询中...' : '查询统计' }}
              </button>
              <span v-if="positionStatistics.validCount > 0 || positionStatistics.invalidCount > 0" class="position-stat-summary">
                仓位已更新: <strong class="stat-valid">{{ positionStatistics.validCount }}</strong> 组
                <button class="btn-stat-detail" @click="showStatDetail('仓位已更新的任务组', positionStatistics.validTaskIds)">详情</button>
                | 仓位未更新: <strong class="stat-invalid">{{ positionStatistics.invalidCount }}</strong> 组
                <button class="btn-stat-detail" @click="showStatDetail('仓位未更新的任务组', positionStatistics.invalidTaskIds)">详情</button>
                <button 
                  class="btn-fetch-invalid-position"
                  @click="fetchInvalidPositionData"
                  :disabled="isFetchingInvalidPosition"
                >
                  {{ isFetchingInvalidPosition ? `抓取中(${invalidPositionFetchProgress})` : '抓取仓位未更新的仓位' }}
                </button>
              </span>
            </div>
            
            <!-- 按主题分组的详细统计（过滤掉完全一致的主题） -->
            <div v-if="filteredPositionDetails.length > 0" class="position-detail-section">
              <div class="position-detail-title">仓位已更新的任务详细统计（按主题分组，已过滤完全一致的）：</div>
              
              <div v-for="item in filteredPositionDetails" :key="item.trending" class="trending-stat-group">
                <div class="trending-name">{{ item.trending }}</div>
                
                <!-- 两边数量一致但有挂单未成交的统计 -->
                <div v-if="item.detail.balanced.length > 0" class="stat-category balanced">
                  <div class="stat-category-header">
                    <span class="category-label">两边数量一致（{{ item.detail.balanced.length }}组）:</span>
                  </div>
                  <div v-for="(statItem, idx) in item.detail.balanced" :key="'b'+idx" class="stat-detail-item">
                    <span class="stat-description">{{ statItem.description }}</span>
                    <button class="btn-detail" @click="showStatDetail('两边数量一致 - ' + statItem.description, statItem.taskIds)">详情</button>
                  </div>
                </div>
                
                <!-- 两边数量不一致的统计 -->
                <div v-if="item.detail.unbalanced.length > 0" class="stat-category unbalanced">
                  <div class="stat-category-header">
                    <span class="category-label">两边数量不一致（{{ item.detail.unbalanced.length }}组）:</span>
                  </div>
                  <div v-for="(statItem, idx) in item.detail.unbalanced" :key="'u'+idx" class="stat-detail-item">
                    <span class="stat-description">{{ statItem.description }}</span>
                    <button class="btn-detail" @click="showStatDetail('两边数量不一致 - 需' + statItem.needDirection + statItem.needSide + ':' + statItem.needAmount, statItem.taskIds)">详情</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
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
          
          <!-- 精确筛选区域 -->
          <div class="filter-section precise-filter">
            <div class="filter-group">
              <label>任务ID:</label>
              <input 
                v-model="filterTaskId" 
                type="text" 
                class="filter-input-small"
                placeholder="如: 123 或 123,456 或 100-200"
              />
            </div>
            <div class="filter-group">
              <label>电脑组:</label>
              <input 
                v-model="filterGroupNo" 
                type="text" 
                class="filter-input-small"
                placeholder="如: 1 或 1,2,3 或 1-5"
              />
            </div>
            <div class="filter-group">
              <label>浏览器编号:</label>
              <input 
                v-model="filterBrowserId" 
                type="text" 
                class="filter-input-small"
                placeholder="如: 521 或 521,522 或 500-600"
              />
            </div>
            <button 
              v-if="filterTaskId || filterGroupNo || filterBrowserId" 
              class="clear-filter-btn"
              @click="clearPreciseFilters"
            >
              清除精确筛选
            </button>
            
            <!-- 模式1：状态筛选 -->
            <div v-if="queryMode === 1" class="status-filter-section">
              <label>状态筛选:</label>
              <select v-model="statusFilter" class="status-filter-select">
                <option value="all">全部</option>
                <option value="success">全部成功</option>
                <option value="repaired">修复后全部成功</option>
                <option value="failed">失败</option>
                <option value="noImpact">失败无影响</option>
                <option value="running">进行中</option>
              </select>
              <button 
                v-if="statusFilter !== 'all'" 
                class="clear-status-filter-btn"
                @click="statusFilter = 'all'"
              >
                清除状态筛选
              </button>
            </div>
            
            <!-- 模式1：一键获取失败状态的服务数据 -->
            <button 
              v-if="queryMode === 1 && groupStatusStatistics.failed > 0"
              class="batch-fetch-btn"
              @click="batchFetchFailedServerData"
              :disabled="isBatchFetchingServerData || isBatchSubmittingPosition"
            >
              {{ isBatchFetchingServerData ? `获取中 (${batchFetchProgress.current}/${batchFetchProgress.total})...` : `一键获取失败状态的服务数据 (${groupStatusStatistics.failed})` }}
            </button>
            
            <!-- 模式1：一键抓取失败状态的仓位 -->
            <button 
              v-if="queryMode === 1 && groupStatusStatistics.failed > 0"
              class="batch-position-btn"
              @click="batchSubmitPositionUpdate"
              :disabled="isBatchSubmittingPosition || isBatchFetchingServerData"
            >
              {{ isBatchSubmittingPosition ? `提交中 (${batchPositionProgress.current}/${batchPositionProgress.total}) 成功:${batchPositionProgress.success} 失败:${batchPositionProgress.failed}` : `一键抓取失败状态的仓位 (${groupStatusStatistics.failed})` }}
            </button>
          </div>
        </div>
        
        <div class="tasks-container">
          <!-- 模式1的显示 -->
          <div v-if="queryMode === 1" class="task-groups-list-wrapper" ref="taskGroupsListRef" @scroll="handleTaskGroupsScroll">
            <div class="task-groups-spacer-top" :style="{ height: taskGroupsTopSpacer + 'px' }"></div>
            <div class="task-groups-list">
              <div 
                v-for="(item, itemIndex) in visibleTaskGroups" 
                :key="item.groupKey"
                :class="['task-group-card', `group-color-${item.colorIndex}`]"
                :ref="el => setTaskGroupRef(el, itemIndex)"
              >
              <!-- 组头部：总状态和获取服务器数据按钮 -->
              <div :class="['mode1-group-header', 'header-' + item.group.finalStatus]">
                <div class="mode1-group-status">
                  <span class="group-status-label">总状态:</span>
                  <span 
                    class="group-status-badge"
                    :class="getGroupStatusClass(item.group.finalStatus)"
                  >
                    {{ getGroupStatusText(item.group.finalStatus) }}
                  </span>
                </div>
                <button 
                  class="btn-fetch-server-data" 
                  @click="fetchServerDataForGroup(item.group)"
                  :disabled="isFetchingServerDataForGroup(item.groupKey)"
                  style="margin-left: 8px; padding: 4px 12px; font-size: 12px;"
                >
                  {{ isFetchingServerDataForGroup(item.groupKey) ? '获取中...' : '获取服务器数据' }}
                </button>
              </div>
              
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
                      <button 
                        v-if="task.browserId"
                        class="btn-view-log" 
                        @click="openBroLogDialog(task.browserId)"
                        style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                      >
                        查看日志
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
                    <span class="task-separator">|</span>
                    <span 
                      v-if="getPositionUpdateStatus(task)"
                      :class="['task-info', 'position-status', getPositionUpdateStatus(task) === '仓位还未更新' ? 'position-not-updated' : 'position-updated']"
                    >
                      {{ getPositionUpdateStatus(task) }}
                    </span>
                  </div>
                  
                  <!-- 显示服务器数据（如果已获取，优先显示；否则显示tp7和tp8） -->
                  <div v-if="task.serverData" class="task-server-data">
                    <div v-if="task.serverData.openOrderList && task.serverData.openOrderList.length > 0" class="server-data-group">
                      <div class="server-data-title">挂单数据:</div>
                      <div v-for="(order, idx) in task.serverData.openOrderList" :key="idx" class="server-data-item">
                        <span>{{ formatOpenOrderMsg(order) }}</span>
                      </div>
                    </div>
                    <div v-if="task.serverData.closedOrderList && task.serverData.closedOrderList.length > 0" class="server-data-group">
                      <div class="server-data-title">已成交数据:</div>
                      <div v-for="(order, idx) in task.serverData.closedOrderList" :key="idx" class="server-data-item">
                        <span>{{ formatClosedOrderMsg(order) }}</span>
                      </div>
                    </div>
                  </div>
                  <!-- 如果没有serverData，显示tp7和tp8（从任务信息中获取的） -->
                  <div v-else-if="task.tp7 || task.tp8" class="task-order-info">
                    <div v-if="task.tp7" class="order-info-item">
                      <span class="order-label">挂单数据:</span>
                      <span class="order-content">{{ task.tp7 }}</span>
                    </div>
                    <div v-if="task.tp8" class="order-info-item">
                      <span class="order-label">已成交数据:</span>
                      <span class="order-content">{{ task.tp8 }}</span>
                    </div>
                  </div>
                </div>
              </div>
              </div>
            </div>
            <div class="task-groups-spacer-bottom" :style="{ height: taskGroupsBottomSpacer + 'px' }"></div>
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
                        <button 
                          v-if="task.browserId"
                          class="btn-view-log" 
                          @click="openBroLogDialog(task.browserId)"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          查看日志
                        </button>
                        <button 
                          class="btn-snap" 
                          @click="snapAllPos"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          快照
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
                      <span class="task-separator">|</span>
                      <span 
                        v-if="getPositionUpdateStatus(task)"
                        :class="['task-info', 'position-status', getPositionUpdateStatus(task) === '仓位还未更新' ? 'position-not-updated' : 'position-updated']"
                      >
                        {{ getPositionUpdateStatus(task) }}
                      </span>
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
                        <button 
                          v-if="task.browserId"
                          class="btn-view-log" 
                          @click="openBroLogDialog(task.browserId)"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          查看日志
                        </button>
                        <button 
                          class="btn-snap" 
                          @click="snapAllPos"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          快照
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
                      <span class="task-separator">|</span>
                      <span 
                        v-if="getPositionUpdateStatus(task)"
                        :class="['task-info', 'position-status', getPositionUpdateStatus(task) === '仓位还未更新' ? 'position-not-updated' : 'position-updated']"
                      >
                        {{ getPositionUpdateStatus(task) }}
                      </span>
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
                        <button 
                          v-if="task.browserId"
                          class="btn-view-log" 
                          @click="openBroLogDialog(task.browserId)"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          查看日志
                        </button>
                        <button 
                          class="btn-snap" 
                          @click="snapAllPos"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          快照
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
                      <span class="task-separator">|</span>
                      <span 
                        v-if="getPositionUpdateStatus(task)"
                        :class="['task-info', 'position-status', getPositionUpdateStatus(task) === '仓位还未更新' ? 'position-not-updated' : 'position-updated']"
                      >
                        {{ getPositionUpdateStatus(task) }}
                      </span>
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
                        <button 
                          v-if="task.browserId"
                          class="btn-view-log" 
                          @click="openBroLogDialog(task.browserId)"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          查看日志
                        </button>
                        <button 
                          class="btn-snap" 
                          @click="snapAllPos"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          快照
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
                      <span class="task-separator">|</span>
                      <span 
                        v-if="getPositionUpdateStatus(task)"
                        :class="['task-info', 'position-status', getPositionUpdateStatus(task) === '仓位还未更新' ? 'position-not-updated' : 'position-updated']"
                      >
                        {{ getPositionUpdateStatus(task) }}
                      </span>
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

    <!-- 浏览器日志弹窗 -->
    <div v-if="showBroLogDialog" class="modal-overlay" @click="closeBroLogDialog">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>浏览器日志 (浏览器ID: {{ currentBroNumber }})</h3>
          <button class="modal-close" @click="closeBroLogDialog">×</button>
        </div>
        <div class="bro-log-content">
          <div v-if="isLoadingBroLogs" class="loading">加载中...</div>
          <div v-else-if="broLogs.length === 0" class="empty">暂无日志记录</div>
          <div v-else class="bro-log-list">
            <div 
              v-for="(logItem, index) in broLogs" 
              :key="index" 
              class="bro-log-item"
            >
              <div class="bro-log-time">{{ formatBeijingTime(logItem.time) }}</div>
              <div class="bro-log-text">{{ logItem.log }}</div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="closeBroLogDialog">关闭</button>
        </div>
      </div>
    </div>

    <!-- 统计详情弹窗 -->
    <div v-if="showStatDetailDialog" class="modal-overlay" @click.self="closeStatDetailDialog">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ statDetailTitle }}</h3>
          <button class="modal-close" @click="closeStatDetailDialog">&times;</button>
        </div>
        <div class="modal-body">
          <div class="stat-detail-task-list">
            <div class="stat-detail-label">相关任务ID（共 {{ statDetailTaskIds.length }} 个）：</div>
            <div class="stat-detail-ids">
              <span v-for="(taskId, idx) in statDetailTaskIds" :key="idx" class="task-id-tag">
                {{ taskId }}
              </span>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="closeStatDetailDialog">关闭</button>
        </div>
      </div>
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
      recentHours: 1, // 默认查询最近3小时
      timeRangeStart: '', // 时间区间开始：格式为"日-时"，如"24-16"
      timeRangeEnd: '', // 时间区间结束：格式为"日-时"，如"24-18"
      loading: false,
      results: {},
      hasQueried: false,
      filterKeyword: '', // 筛选关键词
      filterTaskId: '', // 任务ID筛选
      filterGroupNo: '', // 电脑组筛选
      filterBrowserId: '', // 浏览器编号筛选
      filterHistory: [], // 筛选历史
      expandedGroups: {}, // 模式2中展开的分组 {trendingId: {successYes: true, successNo: true}}
      selectedGroup: 'default', // 当前选择的分组
      groupConfigList: [], // 分组配置列表
      sideFilter: 'all', // 模式1的交易方向筛选：'all'全部, 'buy'买入, 'sell'卖出
      taskStatistics: {
        total: { buy: 0, sell: 0, total: 0 },
        allFilled: { buy: 0, sell: 0 },        // 全部成交的
        partialFilled: { buy: 0, sell: 0 },    // 部分成交的
        singleSideFilled: { buy: 0, sell: 0 }, // Position未检测到变化超时，但对方已变化，保留挂单的（单边成交的）
        ipProblem: { buy: 0, sell: 0 },        // ip问题（包含执行异常）
        balanceOrPosition: { buy: 0, sell: 0 }, // 余额或仓位不对（包含开仓有对向仓位）
        orderFailed: { buy: 0, sell: 0 },      // 挂单失败（普通）
        priceGapTooLarge: { buy: 0, sell: 0 }, // 限价距离市价差距过大
        alreadyHasOrder: { buy: 0, sell: 0 }   // 已有挂单
      },
      orderFailedMsgs: [], // 存储"挂单失败"的所有不同msg（包含重复，用于统计）
      showOrderFailedMsgs: false, // 是否显示"挂单失败"的msg列表
      statusFilter: 'all', // 模式1的总状态筛选：'all'全部, 'success'成功, 'failed'失败, 'noImpact'失败无影响, 'running'进行中, 'repaired'修复后全部成功
      isBatchFetchingServerData: false, // 是否正在批量获取失败状态的服务器数据
      batchFetchProgress: { current: 0, total: 0 }, // 批量获取进度
      isBatchSubmittingPosition: false, // 是否正在批量提交更新仓位任务
      batchPositionProgress: { current: 0, total: 0, success: 0, failed: 0 }, // 批量提交仓位任务进度
      // 账户配置缓存数据
      accountConfigCache: [], // 账户配置缓存列表
      accountConfigMap: {}, // fingerprintNo -> config 映射
      // 仓位统计数据
      positionStatistics: {
        validCount: 0, // 仓位已更新的任务组数
        invalidCount: 0, // 仓位未更新的任务组数
        validTaskIds: [], // 仓位已更新的任务ID列表
        invalidTaskIds: [], // 仓位未更新的任务ID列表
        detailByTrending: {} // 按主题分组的详细统计
      },
      // 统计详情弹窗
      showStatDetailDialog: false,
      statDetailTitle: '',
      statDetailTaskIds: [],
      isQueryingPositionStat: false, // 是否正在查询仓位统计
      isFetchingInvalidPosition: false, // 是否正在抓取仓位未更新的仓位
      invalidPositionFetchProgress: '', // 抓取仓位进度
      toast: {
        show: false,
        message: '',
        type: 'info'
      },
      // 浏览器日志弹窗
      showBroLogDialog: false,  // 浏览器日志弹窗
      broLogs: [],  // 浏览器日志列表
      currentBroNumber: null,  // 当前查看的浏览器ID
      isLoadingBroLogs: false,  // 是否正在加载日志
      // 获取服务器数据
      fetchingServerDataGroups: new Set(),  // 正在获取服务器数据的组key集合
      // 虚拟滚动相关
      taskGroupsScrollTop: 0,  // 任务组列表滚动位置
      taskGroupHeights: [],  // 每个任务组的高度
      taskGroupRefs: [],  // 任务组DOM引用
      estimatedGroupHeight: 200,  // 估算的任务组高度
      visibleBuffer: 3  // 可见区域缓冲区（上下各显示3个）
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
      let result = keywordFiltered
      if (this.queryMode === 1 && this.sideFilter !== 'all') {
        const sideFiltered = {}
        Object.keys(result).forEach(groupKey => {
          const group = result[groupKey]
          
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
        result = sideFiltered
      }
      
      // 模式1时应用总状态筛选
      if (this.queryMode === 1 && this.statusFilter !== 'all') {
        const statusFiltered = {}
        Object.keys(result).forEach(groupKey => {
          const group = result[groupKey]
          if (group.finalStatus === this.statusFilter) {
            statusFiltered[groupKey] = group
          }
        })
        result = statusFiltered
      }
      
      // 模式1时应用精确筛选（任务ID、电脑组、浏览器编号）
      if (this.queryMode === 1) {
        const hasTaskIdFilter = this.filterTaskId && this.filterTaskId.trim() !== ''
        const hasGroupNoFilter = this.filterGroupNo && this.filterGroupNo.trim() !== ''
        const hasBrowserIdFilter = this.filterBrowserId && this.filterBrowserId.trim() !== ''
        
        if (hasTaskIdFilter || hasGroupNoFilter || hasBrowserIdFilter) {
          const preciseFiltered = {}
          
          // 解析筛选条件
          const taskIdSet = hasTaskIdFilter ? this.parseFilterInput(this.filterTaskId) : null
          const groupNoSet = hasGroupNoFilter ? this.parseFilterInput(this.filterGroupNo) : null
          const browserIdSet = hasBrowserIdFilter ? this.parseFilterInput(this.filterBrowserId) : null
          
          Object.keys(result).forEach(groupKey => {
            const group = result[groupKey]
            
            // 检查组内是否有任务匹配筛选条件
            const hasMatch = group.tasks.some(task => {
              // 任务ID筛选
              if (taskIdSet && !taskIdSet.has(String(task.id))) {
                return false
              }
              // 电脑组筛选
              if (groupNoSet && !groupNoSet.has(String(task.groupNo))) {
                return false
              }
              // 浏览器编号筛选
              if (browserIdSet && !browserIdSet.has(String(task.browserId))) {
                return false
              }
              return true
            })
            
            if (hasMatch) {
              preciseFiltered[groupKey] = group
            }
          })
          result = preciseFiltered
        }
      }
      
      return result
    },
    
    // 组状态统计（用于统计面板显示）
    groupStatusStatistics() {
      if (this.queryMode !== 1) return { success: 0, failed: 0, noImpact: 0, running: 0, repaired: 0, unknown: 0 }
      
      const stats = { success: 0, failed: 0, noImpact: 0, running: 0, repaired: 0, unknown: 0 }
      
      Object.values(this.results).forEach(group => {
        const status = group.finalStatus || 'unknown'
        if (stats[status] !== undefined) {
          stats[status]++
        } else {
          stats.unknown++
        }
      })
      
      return stats
    },
    
    // 过滤后的仓位详细统计（过滤掉完全一致的主题）
    filteredPositionDetails() {
      const result = []
      for (const [trending, detail] of Object.entries(this.positionStatistics.detailByTrending)) {
        // 过滤掉完全一致的（balanced和unbalanced都为空，或者balanced里没有挂单未成交的）
        const hasUnbalanced = detail.unbalanced && detail.unbalanced.length > 0
        // balanced中过滤掉完全成交的（pendingAmount为0的）
        const filteredBalanced = (detail.balanced || []).filter(item => parseFloat(item.pendingAmount) > 0)
        
        if (hasUnbalanced || filteredBalanced.length > 0) {
          result.push({
            trending,
            detail: {
              balanced: filteredBalanced,
              unbalanced: detail.unbalanced || []
            }
          })
        }
      }
      return result
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
    
    // 可见的任务组（虚拟滚动）
    visibleTaskGroups() {
      if (this.queryMode !== 1) return []
      
      const allGroups = this.taskGroupsWithIndex
      if (allGroups.length === 0) return []
      
      // 如果任务组数量较少，直接返回全部（不需要虚拟滚动）
      if (allGroups.length <= 30) {
        return allGroups
      }
      
      // 计算可见范围（使用更大的容器高度，可以查看更多数据）
      const containerHeight = window.innerHeight - 50 // 视口高度减去查询区域的大概高度，让列表占据更多空间
      const startIndex = Math.max(0, Math.floor(this.taskGroupsScrollTop / this.estimatedGroupHeight) - this.visibleBuffer)
      const visibleCount = Math.ceil(containerHeight / this.estimatedGroupHeight) + this.visibleBuffer * 2
      const endIndex = Math.min(allGroups.length, startIndex + visibleCount)
      
      return allGroups.slice(startIndex, endIndex)
    },
    
    // 顶部占位高度
    taskGroupsTopSpacer() {
      if (this.queryMode !== 1) return 0
      const allGroups = this.taskGroupsWithIndex
      if (allGroups.length <= 30) return 0
      
      const startIndex = Math.max(0, Math.floor(this.taskGroupsScrollTop / this.estimatedGroupHeight) - this.visibleBuffer)
      return startIndex * this.estimatedGroupHeight
    },
    
    // 底部占位高度
    taskGroupsBottomSpacer() {
      if (this.queryMode !== 1) return 0
      const allGroups = this.taskGroupsWithIndex
      if (allGroups.length <= 30) return 0
      
      const containerHeight = window.innerHeight - 50 // 视口高度减去查询区域的大概高度，让列表占据更多空间
      const startIndex = Math.max(0, Math.floor(this.taskGroupsScrollTop / this.estimatedGroupHeight) - this.visibleBuffer)
      const visibleCount = Math.ceil(containerHeight / this.estimatedGroupHeight) + this.visibleBuffer * 2
      const endIndex = Math.min(allGroups.length, startIndex + visibleCount)
      const remainingCount = allGroups.length - endIndex
      
      return remainingCount * this.estimatedGroupHeight
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
    },
    
    // 获取"挂单失败"的唯一msg列表及出现次数
    uniqueOrderFailedMsgs() {
      const msgCountMap = new Map()
      
      // 统计每个msg出现的次数
      this.orderFailedMsgs.forEach(msg => {
        const count = msgCountMap.get(msg) || 0
        msgCountMap.set(msg, count + 1)
      })
      
      // 转换为数组并按出现次数降序排序
      return Array.from(msgCountMap.entries())
        .map(([msg, count]) => ({ msg, count }))
        .sort((a, b) => b.count - a.count)
    },
    
    // 计算开仓（买入）成功率统计
    buyStatistics() {
      const total = this.taskStatistics.total.buy
      if (total === 0) {
        return {
          successRate: 0,
          partialFilled: 0,
          singleSideFilled: 0,
          notFilled: 0,
          ipProblem: 0,
          balanceOrPosition: 0,
          orderFailed: 0,
          priceGapTooLarge: 0,
          alreadyHasOrder: 0
        }
      }
      
      const ipProblem = (this.taskStatistics.ipProblem.buy / total) * 100
      const balanceOrPosition = (this.taskStatistics.balanceOrPosition.buy / total) * 100
      const orderFailed = (this.taskStatistics.orderFailed.buy / total) * 100
      const priceGapTooLarge = (this.taskStatistics.priceGapTooLarge.buy / total) * 100
      const alreadyHasOrder = (this.taskStatistics.alreadyHasOrder.buy / total) * 100
      const notFilled = ipProblem + balanceOrPosition + orderFailed + priceGapTooLarge + alreadyHasOrder
      
      return {
        successRate: ((this.taskStatistics.allFilled.buy / total) * 100).toFixed(2),
        partialFilled: ((this.taskStatistics.partialFilled.buy / total) * 100).toFixed(2),
        singleSideFilled: ((this.taskStatistics.singleSideFilled.buy / total) * 100).toFixed(2),
        notFilled: notFilled.toFixed(2),
        ipProblem: ipProblem.toFixed(2),
        balanceOrPosition: balanceOrPosition.toFixed(2),
        orderFailed: orderFailed.toFixed(2),
        priceGapTooLarge: priceGapTooLarge.toFixed(2),
        alreadyHasOrder: alreadyHasOrder.toFixed(2)
      }
    },
    
    // 计算平仓（卖出）成功率统计
    sellStatistics() {
      const total = this.taskStatistics.total.sell
      if (total === 0) {
        return {
          successRate: 0,
          partialFilled: 0,
          singleSideFilled: 0,
          notFilled: 0,
          ipProblem: 0,
          balanceOrPosition: 0,
          orderFailed: 0,
          priceGapTooLarge: 0,
          alreadyHasOrder: 0
        }
      }
      
      const ipProblem = (this.taskStatistics.ipProblem.sell / total) * 100
      const balanceOrPosition = (this.taskStatistics.balanceOrPosition.sell / total) * 100
      const orderFailed = (this.taskStatistics.orderFailed.sell / total) * 100
      const priceGapTooLarge = (this.taskStatistics.priceGapTooLarge.sell / total) * 100
      const alreadyHasOrder = (this.taskStatistics.alreadyHasOrder.sell / total) * 100
      const notFilled = ipProblem + balanceOrPosition + orderFailed + priceGapTooLarge + alreadyHasOrder
      
      return {
        successRate: ((this.taskStatistics.allFilled.sell / total) * 100).toFixed(2),
        partialFilled: ((this.taskStatistics.partialFilled.sell / total) * 100).toFixed(2),
        singleSideFilled: ((this.taskStatistics.singleSideFilled.sell / total) * 100).toFixed(2),
        notFilled: notFilled.toFixed(2),
        ipProblem: ipProblem.toFixed(2),
        balanceOrPosition: balanceOrPosition.toFixed(2),
        orderFailed: orderFailed.toFixed(2),
        priceGapTooLarge: priceGapTooLarge.toFixed(2),
        alreadyHasOrder: alreadyHasOrder.toFixed(2)
      }
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
    
    // 根据msg分类任务
    classifyTaskByMsg(msg, status) {
      if (!msg || msg.trim() === '') {
        // 如果没有msg，只要status不等于3，就算全部成交（成功）
        if (status !== 3) {
          return 'allFilled' // 状态不等于3，视为全部成交
        }
        return 'orderFailed' // status === 3 归为挂单失败
      }
      
      // 先尝试解析JSON格式（优先级最高，因为JSON格式的消息有明确的类型）
      try {
        const data = JSON.parse(msg)
        
        if (data.type === 'TYPE1_SUCCESS' || data.type === 'TYPE5_SUCCESS') {
          // 全部成交
          return 'allFilled'
        } else if (data.type === 'TYPE1_PARTIAL' || data.type === 'TYPE5_PARTIAL') {
          // 部分成交
          return 'partialFilled'
        }
      } catch (e) {
        // 不是JSON格式，继续处理文本匹配
      }
      
      // Position未检测到变化超时，但对方已变化，保留挂单的（单边成交的）
      if (msg.includes('Position未检测到变化超时') && msg.includes('对方已变化')) {
        return 'singleSideFilled'
      }
      
      // ip问题：NEED_IP_RETRY、"okx确认交易按钮不能点击,检查okx是否正常" 和 "执行异常"
      if (msg.includes('NEED_IP_RETRY') || msg.includes('okx确认交易按钮不能点击') || msg.includes('检查okx是否正常') || msg.includes('执行异常')) {
        return 'ipProblem'
      }
      
      // 余额或仓位不对："提交订单失败"、包含"无仓位可平" 或 包含"对向仓位且数量"
      if (msg.includes('提交订单失败') || msg.includes('无仓位可平') || msg.includes('对向仓位且数量')) {
        return 'balanceOrPosition'
      }
      
      // 挂单失败细分：限价距离市价差距过大
      if (msg.includes('限价距离市价差距过大')) {
        return 'priceGapTooLarge'
      }
      
      // 挂单失败细分：已有挂单
      if (msg.includes('已有挂单')) {
        return 'alreadyHasOrder'
      }
      
      // 其他错误都归为挂单失败（普通）
      return 'orderFailed'
    },
    
    // 重置统计数据
    resetStatistics() {
      this.taskStatistics = {
        total: { buy: 0, sell: 0, total: 0 },
        allFilled: { buy: 0, sell: 0 },
        partialFilled: { buy: 0, sell: 0 },
        singleSideFilled: { buy: 0, sell: 0 },
        ipProblem: { buy: 0, sell: 0 },
        balanceOrPosition: { buy: 0, sell: 0 },
        orderFailed: { buy: 0, sell: 0 },
        priceGapTooLarge: { buy: 0, sell: 0 },
        alreadyHasOrder: { buy: 0, sell: 0 }
      }
      this.orderFailedMsgs = []
    },
    
    // 统计任务
    countTask(task) {
      const category = this.classifyTaskByMsg(task.msg, task.status)
      // 判断是买入还是卖出：side === 1 为买入，否则为卖出
      const side = task.side === 1 ? 'buy' : 'sell'
      
      // 统计总数
      this.taskStatistics.total[side]++
      this.taskStatistics.total.total++
      
      // 统计对应类别
      this.taskStatistics[category][side]++
      
      // 如果是挂单失败，收集msg
      if (category === 'orderFailed') {
        const msg = task.msg || '(无msg)'
        this.orderFailedMsgs.push(msg)
      }
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
    
    queryTimeRange() {
      if (!this.timeRangeStart || !this.timeRangeEnd) {
        this.showToast('请输入开始时间和结束时间', 'warning')
        return
      }
      
      // 解析时间格式：日-时，如 "24-16"
      const parseTimeRange = (timeStr) => {
        const parts = timeStr.trim().split('-')
        if (parts.length !== 2) {
          return null
        }
        const day = parseInt(parts[0], 10)
        const hour = parseInt(parts[1], 10)
        
        if (isNaN(day) || isNaN(hour) || day < 1 || day > 31 || hour < 0 || hour > 23) {
          return null
        }
        
        return { day, hour }
      }
      
      const startParts = parseTimeRange(this.timeRangeStart)
      const endParts = parseTimeRange(this.timeRangeEnd)
      
      if (!startParts || !endParts) {
        this.showToast('时间格式不正确，请输入"日-时"格式，如：24-16', 'warning')
        return
      }
      
      // 获取当前年月
      const now = new Date()
      const year = now.getFullYear()
      const month = now.getMonth() // 0-11
      
      // 构造开始和结束时间
      const startDate = new Date(year, month, startParts.day, startParts.hour, 0, 0)
      const endDate = new Date(year, month, endParts.day, endParts.hour, 0, 0)
      
      // 验证日期是否有效（防止输入无效日期，如2月30日）
      if (startDate.getDate() !== startParts.day || startDate.getMonth() !== month) {
        this.showToast(`无效的开始日期：${startParts.day}日（当前月没有这一天）`, 'warning')
        return
      }
      
      if (endDate.getDate() !== endParts.day || endDate.getMonth() !== month) {
        this.showToast(`无效的结束日期：${endParts.day}日（当前月没有这一天）`, 'warning')
        return
      }
      
      // 转换为 datetime-local 格式 (YYYY-MM-DDTHH:mm)
      const formatDateTime = (date) => {
        const y = date.getFullYear()
        const m = String(date.getMonth() + 1).padStart(2, '0')
        const d = String(date.getDate()).padStart(2, '0')
        const h = String(date.getHours()).padStart(2, '0')
        const min = String(date.getMinutes()).padStart(2, '0')
        return `${y}-${m}-${d}T${h}:${min}`
      }
      
      // 验证时间范围
      if (startDate.getTime() >= endDate.getTime()) {
        this.showToast('开始时间必须早于结束时间', 'warning')
        return
      }
      
      // 设置查询时间
      this.query.startTime = formatDateTime(startDate)
      this.query.endTime = formatDateTime(endDate)
      
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
            // 重置仓位统计（需要点击按钮才计算）
            this.positionStatistics = {
              validCount: 0,
              invalidCount: 0,
              detailByTrending: {}
            }
          } else {
            this.processMode2Data(missions)
          }
          
          // 获取账户配置缓存，用于计算仓位抓取时间
          await this.fetchAccountConfigCache()
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
      // 重置统计数据
      this.resetStatistics()
      
      // 处理数据：先收集所有任务，建立任务1和任务2的映射关系
      const allTasksMap = new Map() // id -> task (所有任务，包括成功的)
      const task2ToTask1Map = new Map() // task2Id -> task1Id (任务2的id -> 任务1的id)
      const task1ToTask2Map = new Map() // task1Id -> task2Id (任务1的id -> 任务2的id)
      
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
          status: mission.status, // 保存状态，用于判断是否失败
          tp7: mission.tp7 || null, // 保存tp7（openorder字符串）
          tp8: mission.tp8 || null // 保存tp8（closeorder字符串）
        }
        
        // 记录所有任务（使用字符串作为key）
        allTasksMap.set(taskId, task)
        
        // 建立任务2到任务1的映射（如果任务的tp1存在，说明它是任务2，tp1是任务1的id）
        if (tp1Id) {
          task2ToTask1Map.set(taskId, tp1Id)
          task1ToTask2Map.set(tp1Id, taskId)
        }
      })
      
      // 第二步：对所有任务进行分组（不再只显示失败的）
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
      
      // 遍历所有任务，为每个任务找到它的组
      allTasksMap.forEach((task, taskId) => {
        // 如果是分组模式，检查主题是否在分组配置中
        if (this.selectedGroup !== 'default' && !this.isTopicInGroupConfig(task.trending)) {
          return
        }
        
        // 确定这个任务属于哪个组（任务1的id）
        let task1Id = null
        
        // 如果任务有tp1，说明它是任务2，tp1就是任务1的id
        if (task.tp1) {
          task1Id = task.tp1
        } else {
          // 如果任务没有tp1，说明它是任务1
          task1Id = task.id
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
      
      // 第三步：为每个任务计算同组任务ID，并转换为对象格式用于显示
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
        
        // 计算总状态
        const finalStatus = this.calculateGroupStatus(tasksWithGroupId)
        
        groupsArray.push({
          groupId: displayKey, // 用于显示
          internalGroupId: internalGroupId, // 用于颜色计算，确保同组任务使用相同颜色
          tasks: tasksWithGroupId,
          task1CreateTime: group.task1CreateTime,
          trending: trending, // 添加trending用于分组排序
          finalStatus: finalStatus // 总状态
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
          tasks: group.tasks,
          finalStatus: group.finalStatus
        }
      })
      
      // 统计所有任务（包括成功和失败的任务）
      allTasksMap.forEach((task) => {
        // 如果是分组模式，检查主题是否在分组配置中
        if (this.selectedGroup !== 'default' && !this.isTopicInGroupConfig(task.trending)) {
          return
        }
        this.countTask(task)
      })
      
      this.results = sortedGroups
      
      // 不再自动加载链上余额，改为点击按钮时加载
      
      const totalGroups = Object.keys(sortedGroups).length
      this.hasQueried = true
      this.showToast(`查询成功，共 ${totalGroups} 个任务组`, 'success')
    },
    
    // 处理模式2的数据
    processMode2Data(missions) {
      // 重置统计数据
      this.resetStatistics()
      
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
      
      // 统计所有任务（包括成功和失败的任务）
      groupsByTrendingId.forEach((group) => {
        // 如果是分组模式，检查主题是否在分组配置中
        if (this.selectedGroup !== 'default' && !this.isTopicInGroupConfig(group.trending)) {
          return
        }
        group.tasks.forEach(task => {
          this.countTask(task)
        })
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
    
    // 清除精确筛选
    clearPreciseFilters() {
      this.filterTaskId = ''
      this.filterGroupNo = ''
      this.filterBrowserId = ''
      this.showToast('精确筛选已清除', 'info')
    },
    
    /**
     * 解析筛选输入，支持逗号分隔和区间格式
     * 如: "123" -> Set(['123'])
     * 如: "123,456,789" -> Set(['123', '456', '789'])
     * 如: "100-200" -> Set(['100', '101', ..., '200'])
     * 如: "1,5-10,20" -> Set(['1', '5', '6', '7', '8', '9', '10', '20'])
     * @returns {Set} 包含所有匹配值的 Set
     */
    parseFilterInput(input) {
      if (!input || input.trim() === '') return new Set()
      
      const result = new Set()
      const parts = input.split(',').map(p => p.trim()).filter(p => p)
      
      for (const part of parts) {
        if (part.includes('-')) {
          // 区间格式
          const [start, end] = part.split('-').map(s => parseInt(s.trim()))
          if (!isNaN(start) && !isNaN(end) && start <= end) {
            for (let i = start; i <= end; i++) {
              result.add(String(i))
            }
          }
        } else {
          // 单个值
          result.add(part)
        }
      }
      
      return result
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
    },
    
    /**
     * 格式化毫秒时间戳为北京时间
     */
    formatBeijingTime(timestamp) {
      if (!timestamp) return '-'
      try {
        const date = new Date(Number(timestamp))
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        const seconds = String(date.getSeconds()).padStart(2, '0')
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
      } catch (e) {
        return timestamp
      }
    },
    
    /**
     * 打开浏览器日志弹窗
     */
    async openBroLogDialog(number) {
      if (!number) return
      this.currentBroNumber = number
      this.showBroLogDialog = true
      this.broLogs = []
      await this.fetchBroLogs(number)
    },
    
    /**
     * 获取浏览器日志
     */
    async fetchBroLogs(number) {
      if (!number) return
      this.isLoadingBroLogs = true
      try {
        const response = await axios.get('https://sg.bicoin.com.cn/99l/bro/getBroLog', {
          params: {
            number: number,
            size: 1000
          }
        })
        if (response.data?.code === 0 && response.data?.data?.list) {
          this.broLogs = response.data.data.list
        } else {
          console.error('获取浏览器日志失败:', response.data)
          this.broLogs = []
        }
      } catch (error) {
        console.error('获取浏览器日志失败:', error)
        this.broLogs = []
      } finally {
        this.isLoadingBroLogs = false
      }
    },
    
    /**
     * 关闭浏览器日志弹窗
     */
    closeBroLogDialog() {
      this.showBroLogDialog = false
      this.broLogs = []
      this.currentBroNumber = null
    },
    
    /**
     * 执行快照
     */
    async snapAllPos() {
      try {
        const response = await axios.post('https://sg.bicoin.com.cn/99l/boost/snapAllPos', {})
        if (response.data && response.data.code === 0) {
          this.showToast('快照执行成功', 'success')
        } else {
          this.showToast('快照执行失败', 'error')
        }
      } catch (error) {
        console.error('执行快照失败:', error)
        this.showToast('执行快照失败: ' + (error.message || '未知错误'), 'error')
      }
    },
    
    /**
     * 判断任务是否成功（根据 status 和 msg）
     */
    isTaskSuccess(status, msg) {
      // 如果 status === 2，直接返回成功
      if (status === 2) {
        return true
      }
      
      // 如果 status !== 2，需要判断 msg
      if (!msg) {
        return false
      }
      
      // 尝试解析 msg 是否为 JSON 格式
      let msgObj = null
      try {
        // 如果 msg 是 JSON 字符串，尝试解析
        if (typeof msg === 'string' && msg.trim().startsWith('{')) {
          msgObj = JSON.parse(msg)
        }
      } catch (e) {
        // 解析失败，说明不是 JSON 格式，继续使用字符串匹配逻辑
        msgObj = null
      }
      
      // 如果是 JSON 格式
      if (msgObj && typeof msgObj === 'object') {
        // 检查 type 字段
        if (msgObj.type === 'TYPE1_SUCCESS' || msgObj.type === 'TYPE5_SUCCESS') {
          // 全部成交
          return true
        } else if (msgObj.type === 'TYPE1_PARTIAL' || msgObj.type === 'TYPE5_PARTIAL') {
          // 部分成交，需要检查进度是否大于80%
          if (msgObj.progress) {
            try {
              // 解析 progress 字段，格式如："551.41 / 552.86 shares" 或 "$306.06 / $312.98"
              const progressMatch = msgObj.progress.match(/\$?([\d,]+\.?\d*)\s*\/\s*\$?([\d,]+\.?\d*)/)
              if (progressMatch) {
                const filled = parseFloat(progressMatch[1].replace(/,/g, ''))
                const total = parseFloat(progressMatch[2].replace(/,/g, ''))
                
                if (total > 0 && filled / total > 0.8) {
                  return true
                }
              }
            } catch (e) {
              console.error('解析JSON中的进度失败:', e)
            }
          }
          return false
        }
      }
      
      // 如果不是 JSON 格式，使用原有的字符串匹配逻辑
      // 检查是否是"全部成交"
      if (msg.includes('全部成交') || msg.includes('✅ 全部成交') || msg.includes('SUCCESS')) {
        return true
      }
      
      // 检查是否是"部分成交"，需要判断进度是否大于80%
      if (msg.includes('部分成交') || msg.includes('⚠️ 部分成交') || msg.includes('PARTIAL')) {
        // 尝试从 msg 中提取进度信息
        const progressMatch = msg.match(/进度[:\s]*\$?([\d,]+\.?\d*)\s*\/\s*\$?([\d,]+\.?\d*)/i)
        if (progressMatch) {
          try {
            const filled = parseFloat(progressMatch[1].replace(/,/g, ''))
            const total = parseFloat(progressMatch[2].replace(/,/g, ''))
            
            if (total > 0 && filled / total > 0.8) {
              return true
            }
          } catch (e) {
            console.error('解析进度失败:', e)
          }
        }
      }
      
      return false
    },
    
    /**
     * 从 msg 中提取 [x] 开头的数字
     */
    extractBracketNumber(msg) {
      if (!msg) return null
      const match = msg.match(/\[(\d+)\]/)
      if (match) {
        const num = parseInt(match[1])
        if (num < 10) {
          return num
        }
      }
      return null
    },
    
    /**
     * 计算组的总状态
     */
    calculateGroupStatus(tasks) {
      if (!tasks || tasks.length === 0) {
        return 'unknown'
      }
      
      // 优先检查是否有 [x] 格式的失败无影响（x < 10）
      for (const task of tasks) {
        if (task.msg) {
          const bracketNum = this.extractBracketNumber(task.msg)
          if (bracketNum !== null) {
            return 'noImpact'
          }
        }
      }
      
      // 检查所有任务是否都成功（包括tp7/tp8修复成功）
      let hasRepaired = false
      const allSuccessOrRepaired = tasks.every(task => {
        // 原本就成功
        if (this.isTaskSuccess(task.status, task.msg)) {
          return true
        }
        // 通过tp7/tp8修复成功
        if (this.isTaskRepairedSuccess(task)) {
          hasRepaired = true
          return true
        }
        return false
      })
      
      if (allSuccessOrRepaired) {
        // 如果有任何一个是修复成功的，返回 'repaired'
        if (hasRepaired) {
          return 'repaired'
        }
        return 'success'
      }
      
      // 检查是否有任务失败（status === 3）
      const hasFailed = tasks.some(task => task.status === 3 && !this.isTaskRepairedSuccess(task))
      if (hasFailed) {
        return 'failed'
      }
      
      // 检查是否有任务正在进行中（status === 9）
      const hasRunning = tasks.some(task => task.status === 9 || task.status === 0 || task.status === 1)
      if (hasRunning) {
        return 'running'
      }
      
      return 'unknown'
    },
    
    /**
     * 获取组状态文本
     */
    getGroupStatusText(finalStatus) {
      const statusMap = {
        'success': '全部成功',
        'repaired': '修复后全部成功',
        'failed': '失败',
        'running': '进行中',
        'noImpact': '失败无影响',
        'unknown': '未知'
      }
      return statusMap[finalStatus] || '未知'
    },
    
    /**
     * 获取组状态样式类
     */
    getGroupStatusClass(finalStatus) {
      const classMap = {
        'success': 'status-success',
        'repaired': 'status-repaired',
        'failed': 'status-failed',
        'running': 'status-running',
        'noImpact': 'status-no-impact',
        'unknown': 'status-unknown'
      }
      return classMap[finalStatus] || 'status-unknown'
    },
    
    /**
     * 检查是否正在获取服务器数据
     */
    isFetchingServerDataForGroup(groupKey) {
      return this.fetchingServerDataGroups.has(groupKey)
    },
    
    /**
     * 获取服务器数据（针对组）
     * @param {Object} group - 任务组
     * @param {boolean} batchMode - 是否是批量模式（批量模式下只获取失败且未修复的子任务）
     */
    async fetchServerDataForGroup(group, batchMode = false) {
      if (!group || !group.tasks || group.tasks.length === 0) {
        if (!batchMode) this.showToast('任务组数据不完整', 'warning')
        return
      }
      
      const groupKey = group.groupId || `group-${Date.now()}`
      
      // 检查是否正在获取
      if (this.isFetchingServerDataForGroup(groupKey)) {
        return
      }
      
      // 标记为正在获取
      this.fetchingServerDataGroups.add(groupKey)
      
      try {
        // 为组内每个任务获取服务器数据
        const tasks = group.tasks
        const requests = []
        
        for (const task of tasks) {
          if (!task.browserId || !task.trending) {
            continue
          }
          
          // 批量模式下，只获取失败且未修复成功的子任务
          if (batchMode) {
            // 子任务状态是2（成功）的，不需要获取
            if (task.status === 2) {
              continue
            }
            // 已经修复成功的，不需要获取
            if (this.isTaskRepairedSuccess(task)) {
              continue
            }
          }
          
          // 确定side参数：1=开仓（买入），2=平仓（卖出）
          const side = task.side === 1 ? 'buy' : 'sell'
          
          // 获取updateTime并转换为时间戳
          let time = null
          if (task.updateTime) {
            time = new Date(task.updateTime).getTime()
          }
          
          // 构建请求数据
          const requestData = {
            number: task.browserId,
            trending: task.trending,
            side: side,
            price: task.price,
            amt: task.amt
          }
          
          // 如果有time，添加到请求数据中
          if (time) {
            requestData.time = time
          }
          
          // 发送请求
          const promise = axios.post(
            'https://sg.bicoin.com.cn/99l/hedge/filterOrder',
            requestData,
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          ).then(response => {
            return { task, response }
          }).catch(error => {
            console.error(`获取任务 ${task.id} 服务器数据失败:`, error)
            return { task, error }
          })
          
          requests.push(promise)
        }
        
        // 并行发送所有请求
        const results = await Promise.all(requests)
        
        // 处理返回的数据
        for (const result of results) {
          if (result.error) {
            continue
          }
          
          const { task, response } = result
          if (response.data && response.data.code === 0 && response.data.data) {
            const serverData = response.data.data.hist || {}
            
            // 更新任务的服务器数据（Vue 3 直接赋值即可）
            task.serverData = serverData
            
            // 处理openorder和closeorder
            let openOrderStr = null
            let closeOrderStr = null
            
            // 处理挂单数据（openOrderList）
            if (serverData.openOrderList && serverData.openOrderList.length > 0) {
              // 如果有多个，取时间最新的（按ctime排序）
              const sortedOpenOrders = [...serverData.openOrderList].sort((a, b) => {
                const timeA = a.ctime || 0
                const timeB = b.ctime || 0
                return timeB - timeA
              })
              openOrderStr = this.formatOpenOrderMsg(sortedOpenOrders[0])
            }
            
            // 处理已成交数据（closedOrderList）
            if (serverData.closedOrderList && serverData.closedOrderList.length > 0) {
              // 如果有多个，取时间最新的（按time或convertTime排序）
              const sortedClosedOrders = [...serverData.closedOrderList].sort((a, b) => {
                // 处理时间：如果是字符串，转换为时间戳；如果是数字，直接使用
                let timeA = 0
                if (a.convertTime) {
                  timeA = typeof a.convertTime === 'string' ? new Date(a.convertTime).getTime() : a.convertTime
                } else if (a.time) {
                  timeA = typeof a.time === 'string' ? new Date(a.time).getTime() : a.time
                }
                
                let timeB = 0
                if (b.convertTime) {
                  timeB = typeof b.convertTime === 'string' ? new Date(b.convertTime).getTime() : b.convertTime
                } else if (b.time) {
                  timeB = typeof b.time === 'string' ? new Date(b.time).getTime() : b.time
                }
                
                return timeB - timeA
              })
              closeOrderStr = this.formatClosedOrderMsg(sortedClosedOrders[0])
            }
            
            // 如果有openorder或closeorder，保存到tp7和tp8
            if (openOrderStr || closeOrderStr) {
              await this.updateMissionTp(task.id, openOrderStr, closeOrderStr)
              
              // 更新任务的tp7和tp8（Vue 3 直接赋值即可）
              if (openOrderStr) {
                task.tp7 = openOrderStr
              }
              if (closeOrderStr) {
                task.tp8 = closeOrderStr
              }
            }
          }
        }
        
        // 获取完成后，重新计算组的总状态
        this.recalculateGroupStatus(group)
        
        if (!batchMode) {
          this.showToast('获取服务器数据成功', 'success')
        }
      } catch (error) {
        console.error('获取服务器数据失败:', error)
        if (!batchMode) {
          this.showToast('获取服务器数据失败: ' + (error.message || '未知错误'), 'error')
        }
      } finally {
        // 移除标记
        this.fetchingServerDataGroups.delete(groupKey)
      }
    },
    
    /**
     * 重新计算组的总状态（考虑tp7/tp8修复）
     */
    recalculateGroupStatus(group) {
      if (!group || !group.tasks) return
      
      const newStatus = this.calculateGroupStatus(group.tasks)
      group.finalStatus = newStatus
    },
    
    /**
     * 设置状态筛选
     */
    setStatusFilter(status) {
      this.statusFilter = status
    },
    
    /**
     * 批量获取失败状态的服务数据（并发5个一组）
     */
    async batchFetchFailedServerData() {
      if (this.isBatchFetchingServerData) return
      
      // 获取所有失败状态的组（排除已修复的）
      const failedGroups = []
      Object.values(this.results).forEach(group => {
        // 只获取失败状态的组，排除已修复的（repaired）
        if (group.finalStatus === 'failed') {
          failedGroups.push(group)
        }
      })
      
      if (failedGroups.length === 0) {
        this.showToast('没有失败状态的组需要获取', 'info')
        return
      }
      
      this.isBatchFetchingServerData = true
      this.batchFetchProgress = { current: 0, total: failedGroups.length }
      
      const concurrency = 5 // 并发数
      
      try {
        // 分批并发处理
        for (let i = 0; i < failedGroups.length; i += concurrency) {
          const batch = failedGroups.slice(i, i + concurrency)
          const promises = batch.map(group => this.fetchServerDataForGroup(group, true)) // true表示是批量模式
          
          await Promise.all(promises)
          
          this.batchFetchProgress.current = Math.min(i + concurrency, failedGroups.length)
          
          // 批次之间间隔200ms
          if (i + concurrency < failedGroups.length) {
            await new Promise(resolve => setTimeout(resolve, 200))
          }
        }
        this.showToast(`批量获取完成，共处理 ${failedGroups.length} 个组`, 'success')
      } catch (error) {
        console.error('批量获取服务器数据失败:', error)
        this.showToast('批量获取服务器数据失败: ' + (error.message || '未知错误'), 'error')
      } finally {
        this.isBatchFetchingServerData = false
        this.batchFetchProgress = { current: 0, total: 0 }
      }
    },
    
    /**
     * 提交单个浏览器的更新仓位任务（type=2，带重试机制）
     * @param {number} browserId - 浏览器ID
     * @param {number} groupNo - 电脑组
     * @param {number} maxRetries - 最大重试次数
     * @returns {Promise<{success: boolean, error?: string}>}
     */
    async submitSinglePositionUpdate(browserId, groupNo, maxRetries = 3) {
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
            // 重试前等待3秒
            console.log(`浏览器ID ${browserId} 更新仓位第 ${attempt} 次重试，等待3秒...`)
            await new Promise(resolve => setTimeout(resolve, 3000))
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
          console.error(`浏览器ID ${browserId} 更新仓位异常${attempt > 0 ? `（第${attempt}次重试）` : ''}:`, lastError)
        }
      }
      
      return { success: false, error: lastError }
    },
    
    /**
     * 批量提交更新仓位任务（并发5个一组，带重试机制）
     */
    async batchSubmitPositionUpdate() {
      if (this.isBatchSubmittingPosition) return
      
      // 收集所有需要更新仓位的浏览器
      const tasksToUpdate = []
      
      Object.values(this.results).forEach(group => {
        // 只处理失败状态的组
        if (group.finalStatus !== 'failed') return
        
        group.tasks.forEach(task => {
          // 子任务状态是2（成功）的，不需要更新仓位
          if (task.status === 2) return
          // 已经修复成功的，不需要更新仓位
          if (this.isTaskRepairedSuccess(task)) return
          // 没有浏览器ID的，跳过
          if (!task.browserId || !task.groupNo) return
          
          tasksToUpdate.push({
            browserId: task.browserId,
            groupNo: task.groupNo,
            taskId: task.id
          })
        })
      })
      
      if (tasksToUpdate.length === 0) {
        this.showToast('没有需要更新仓位的浏览器', 'info')
        return
      }
      
      // 去重（同一浏览器不重复提交）
      const uniqueTasks = []
      const seenBrowserIds = new Set()
      for (const task of tasksToUpdate) {
        if (!seenBrowserIds.has(task.browserId)) {
          seenBrowserIds.add(task.browserId)
          uniqueTasks.push(task)
        }
      }
      
      this.isBatchSubmittingPosition = true
      this.batchPositionProgress = { current: 0, total: uniqueTasks.length, success: 0, failed: 0 }
      
      const concurrency = 5 // 并发数
      
      try {
        // 分批并发处理
        for (let i = 0; i < uniqueTasks.length; i += concurrency) {
          const batch = uniqueTasks.slice(i, i + concurrency)
          
          const promises = batch.map(async (task) => {
            const result = await this.submitSinglePositionUpdate(task.browserId, task.groupNo)
            return { task, result }
          })
          
          const results = await Promise.all(promises)
          
          // 统计成功/失败
          for (const { result } of results) {
            if (result.success) {
              this.batchPositionProgress.success++
            } else {
              this.batchPositionProgress.failed++
            }
          }
          
          this.batchPositionProgress.current = Math.min(i + concurrency, uniqueTasks.length)
          
          // 批次之间间隔300ms
          if (i + concurrency < uniqueTasks.length) {
            await new Promise(resolve => setTimeout(resolve, 300))
          }
        }
        
        const { success, failed } = this.batchPositionProgress
        this.showToast(`批量提交完成，成功: ${success}，失败: ${failed}`, success > 0 ? 'success' : 'error')
      } catch (error) {
        console.error('批量提交更新仓位失败:', error)
        this.showToast('批量提交更新仓位失败: ' + (error.message || '未知错误'), 'error')
      } finally {
        this.isBatchSubmittingPosition = false
        // 保留进度显示一段时间后重置
        setTimeout(() => {
          this.batchPositionProgress = { current: 0, total: 0, success: 0, failed: 0 }
        }, 5000)
      }
    },
    
    /**
     * 查询仓位统计（点击按钮触发）
     */
    async queryPositionStatistics() {
      if (this.isQueryingPositionStat) return
      
      this.isQueryingPositionStat = true
      
      try {
        // 获取账户配置缓存
        await this.fetchAccountConfigCache()
        // 计算仓位统计
        this.calculatePositionStatistics()
        this.showToast('仓位统计查询完成', 'success')
      } catch (error) {
        console.error('查询仓位统计失败:', error)
        this.showToast('查询仓位统计失败', 'error')
      } finally {
        this.isQueryingPositionStat = false
      }
    },
    
    /**
     * 抓取仓位未更新的仓位
     * 为仓位未更新的且状态不等于2的任务提交type=2的任务
     */
    async fetchInvalidPositionData() {
      if (this.isFetchingInvalidPosition) return
      
      // 收集需要抓取仓位的浏览器
      const tasksToFetch = []
      
      Object.values(this.results).forEach(group => {
        if (group.finalStatus !== 'failed') return
        
        // 检查这个组是否仓位未更新
        const isPositionValid = this.checkGroupPositionValid(group)
        if (isPositionValid) return // 仓位已更新，跳过
        
        // 遍历组内任务
        if (group.tasks) {
          group.tasks.forEach(task => {
            // 只处理状态不等于2的任务
            if (task.status === 2) return
            
            const browserId = task.browserId
            const groupNo = task.groupNo || group.groupNo
            
            if (browserId && !tasksToFetch.some(t => t.browserId === browserId)) {
              tasksToFetch.push({
                browserId,
                groupNo,
                taskId: task.id
              })
            }
          })
        }
      })
      
      if (tasksToFetch.length === 0) {
        this.showToast('没有需要抓取仓位的任务', 'info')
        return
      }
      
      this.isFetchingInvalidPosition = true
      const total = tasksToFetch.length
      let completed = 0
      let success = 0
      let failed = 0
      
      // 并发控制，5个一批
      const concurrency = 5
      
      for (let i = 0; i < tasksToFetch.length; i += concurrency) {
        const batch = tasksToFetch.slice(i, i + concurrency)
        
        await Promise.all(batch.map(async (task) => {
          try {
            const result = await this.submitSinglePositionUpdate(task.browserId, task.groupNo, 3)
            if (result) {
              success++
            } else {
              failed++
            }
          } catch (error) {
            console.error(`提交仓位更新失败 - 浏览器:${task.browserId}`, error)
            failed++
          } finally {
            completed++
            this.invalidPositionFetchProgress = `${completed}/${total}`
          }
        }))
      }
      
      this.isFetchingInvalidPosition = false
      this.showToast(`仓位抓取完成: 成功 ${success}, 失败 ${failed}`, success > 0 ? 'success' : 'error')
    },
    
    /**
     * 获取账户配置缓存
     */
    async fetchAccountConfigCache() {
      try {
        const response = await axios.get('https://sg.bicoin.com.cn/99l/boost/findAccountConfigCacheSimple')
        if (response.data && response.data.data) {
          this.accountConfigCache = response.data.data || []
          // 建立 fingerprintNo -> config 映射
          this.accountConfigMap = {}
          this.accountConfigCache.forEach(config => {
            if (config.fingerprintNo) {
              this.accountConfigMap[config.fingerprintNo] = config
            }
          })
          console.log(`账户配置缓存加载成功，共 ${this.accountConfigCache.length} 条`)
        }
      } catch (error) {
        console.error('获取账户配置缓存失败:', error)
        this.accountConfigCache = []
        this.accountConfigMap = {}
      }
    },
    
    /**
     * 计算仓位统计（仅对失败状态的任务组）
     */
    calculatePositionStatistics() {
      // 重置统计数据
      this.positionStatistics = {
        validCount: 0,
        invalidCount: 0,
        validTaskIds: [],
        invalidTaskIds: [],
        detailByTrending: {}
      }
      
      // 遍历所有失败状态的任务组
      Object.values(this.results).forEach(group => {
        if (group.finalStatus !== 'failed') return
        
        // 获取组内所有任务ID
        const taskIds = group.tasks ? group.tasks.map(t => t.id) : []
        
        // 检查组内任务的仓位数据是否正确
        const isPositionValid = this.checkGroupPositionValid(group)
        
        if (isPositionValid) {
          this.positionStatistics.validCount++
          this.positionStatistics.validTaskIds.push(...taskIds)
          // 计算详细统计
          this.calculateGroupDetailStatistics(group)
        } else {
          this.positionStatistics.invalidCount++
          this.positionStatistics.invalidTaskIds.push(...taskIds)
        }
      })
    },
    
    /**
     * 获取任务的仓位更新状态描述
     * 返回格式: "仓位已在任务结束后X分钟更新" 或 "仓位还未更新"
     */
    getPositionUpdateStatus(task) {
      if (!task || !task.browserId) return null
      
      const config = this.accountConfigMap[String(task.browserId)]
      if (!config) return null
      
      // d 字段是仓位抓取时间（时间戳字符串）
      const catchTime = config.d ? parseInt(config.d) : null
      if (!catchTime) return null
      
      // 任务的 updateTime（任务结束时间）
      const updateTime = task.updateTime ? new Date(task.updateTime).getTime() : null
      if (!updateTime) return null
      
      // 计算仓位抓取时间与任务结束时间的差值（分钟）
      const diffMinutes = Math.round((catchTime - updateTime) / 60000)
      
      if (catchTime < updateTime) {
        // 仓位抓取时间小于任务结束时间，说明仓位还未更新
        return '仓位还未更新'
      } else {
        // 仓位抓取时间大于任务结束时间
        return `仓位已在任务结束后${diffMinutes}分钟更新`
      }
    },
    
    /**
     * 检查任务组的仓位数据是否正确
     * 判断条件：账户配置中的 d 字段（仓位抓取时间）大于任务的 updateTime 30分钟以上
     */
    checkGroupPositionValid(group) {
      if (!group.tasks || group.tasks.length === 0) return false
      
      // 检查组内所有任务
      for (const task of group.tasks) {
        const browserId = task.browserId
        if (!browserId) continue
        
        const config = this.accountConfigMap[String(browserId)]
        if (!config) continue
        
        // d 字段是仓位抓取时间（时间戳字符串）
        const catchTime = config.d ? parseInt(config.d) : null
        if (!catchTime) continue
        
        // 任务的 updateTime
        const updateTime = task.updateTime ? new Date(task.updateTime).getTime() : null
        if (!updateTime) continue
        
        // 判断仓位抓取时间是否大于任务结束时间30分钟（30 * 60 * 1000 = 1800000ms）
        if (catchTime > updateTime + 1800000) {
          return true // 只要有一个任务的仓位数据正确，就认为组的仓位数据正确
        }
      }
      
      return false
    },
    
    /**
     * 计算任务组的详细统计
     */
    calculateGroupDetailStatistics(group) {
      if (!group.tasks || group.tasks.length !== 2) return
      
      const trending = group.tasks[0].trending
      if (!trending) return
      
      // 初始化该主题的统计
      if (!this.positionStatistics.detailByTrending[trending]) {
        this.positionStatistics.detailByTrending[trending] = {
          balanced: [], // 两边数量一致的
          unbalanced: [] // 两边数量不一致的
        }
      }
      
      // 解析两个子任务的数据
      const task1Data = this.parseTaskOrderData(group.tasks[0])
      const task2Data = this.parseTaskOrderData(group.tasks[1])
      
      if (!task1Data || !task2Data) return
      
      // 判断两边总数量是否一致（允许5%误差）
      const avgTotal = (task1Data.total + task2Data.total) / 2
      const totalDiff = Math.abs(task1Data.total - task2Data.total)
      const diffPercent = avgTotal > 0 ? (totalDiff / avgTotal) * 100 : 0
      
      if (diffPercent <= 5) {
        // 两边总数量一致
        const pendingAmount = Math.max(task1Data.pending, task2Data.pending)
        const pendingTask = task1Data.pending >= task2Data.pending ? group.tasks[0] : group.tasks[1]
        const pendingSide = pendingTask.psSide === 1 ? 'YES' : 'NO'
        const pendingDirection = pendingTask.side === 1 ? '买入' : '卖出'
        
        this.positionStatistics.detailByTrending[trending].balanced.push({
          taskIds: group.tasks.map(t => t.id),
          pendingAmount: pendingAmount.toFixed(2),
          pendingSide,
          pendingDirection,
          description: `${pendingAmount.toFixed(2)} ${pendingSide} ${pendingDirection}挂单未成交`
        })
      } else {
        // 两边总数量不一致
        const task1 = group.tasks[0]
        const task2 = group.tasks[1]
        
        // 计算各方的已成交和挂单
        const filledYes = task1.psSide === 1 ? task1Data.filled : (task2.psSide === 1 ? task2Data.filled : 0)
        const filledNo = task1.psSide === 2 ? task1Data.filled : (task2.psSide === 2 ? task2Data.filled : 0)
        const pendingYes = task1.psSide === 1 ? task1Data.pending : (task2.psSide === 1 ? task2Data.pending : 0)
        const pendingNo = task1.psSide === 2 ? task1Data.pending : (task2.psSide === 2 ? task2Data.pending : 0)
        
        const totalYes = filledYes + pendingYes
        const totalNo = filledNo + pendingNo
        const diff = totalYes - totalNo
        
        const needSide = diff > 0 ? 'NO' : 'YES'
        const needDirection = group.tasks[0].side === 1 ? '买入' : '卖出'
        const needAmount = Math.abs(diff)
        
        this.positionStatistics.detailByTrending[trending].unbalanced.push({
          taskIds: group.tasks.map(t => t.id),
          filledYes: filledYes.toFixed(2),
          filledNo: filledNo.toFixed(2),
          pendingYes: pendingYes.toFixed(2),
          pendingNo: pendingNo.toFixed(2),
          needSide,
          needDirection,
          needAmount: needAmount.toFixed(2),
          description: `已成交YES:${filledYes.toFixed(2)}, NO:${filledNo.toFixed(2)}, 挂单YES:${pendingYes.toFixed(2)}, NO:${pendingNo.toFixed(2)}, 需${needDirection}${needSide}:${needAmount.toFixed(2)}`
        })
      }
    },
    
    /**
     * 解析任务的订单数据（优先级：tp8 > tp7 > msg）
     * @returns {Object|null} { total: 总数量, filled: 已成交数量, pending: 未成交数量 }
     */
    parseTaskOrderData(task) {
      if (!task) return null
      
      // 如果子任务状态是2（成功），直接使用 amt 字段作为 total 和 filled
      if (task.status === 2) {
        const amt = parseFloat(task.amt) || 0
        return {
          total: amt,
          filled: amt,
          pending: 0
        }
      }
      
      // 优先使用 tp8（已成交数据）
      if (task.tp8) {
        return this.parseTp8Data(task.tp8, task.side)
      }
      
      // 其次使用 tp7（挂单数据）
      if (task.tp7) {
        return this.parseTp7Data(task.tp7, task.side)
      }
      
      // 最后使用 msg
      if (task.msg) {
        const msgResult = this.parseMsgData(task.msg, task.side)
        if (msgResult) {
          // 如果返回 useAmt 标记，表示 PARTIAL 类型但没有有效 progress，使用 amt
          if (msgResult.useAmt) {
            const amt = parseFloat(task.amt) || 0
            return {
              total: amt,
              filled: 0,
              pending: amt
            }
          }
          return msgResult
        }
      }
      
      return null
    },
    
    /**
     * 解析 tp8 数据
     * 格式: "时间: 2026-01-09 14:23:17 (不同时区) | 方向: 卖 | 结果: NO | 价格: 82.3 | 进度: 100.00% (399.46/399.46) | 状态: filled"
     * 买入时: "时间: 2026-01-09 13:57:51 | 方向: 买 | 结果: YES | 价格: 7.9 | 进度: 100.00% (52.21/52.21) | 状态: filled"
     * @param {string} tp8 - tp8 数据字符串
     * @param {number} taskSide - 任务方向 (1=买入, 2=卖出)
     */
    parseTp8Data(tp8, taskSide) {
      if (!tp8) return null
      
      // 检查状态，如果是 canceled，返回全0
      const statusMatch = tp8.match(/状态:\s*(\w+)/)
      if (statusMatch && statusMatch[1] === 'canceled') {
        return {
          total: 0,
          filled: 0,
          pending: 0
        }
      }
      
      // 提取方向
      const sideMatch = tp8.match(/方向:\s*(买|卖)/)
      const isBuy = sideMatch && sideMatch[1] === '买'
      
      // 提取价格（美分）
      const priceMatch = tp8.match(/价格:\s*([\d.]+)/)
      const price = priceMatch ? parseFloat(priceMatch[1]) : 0
      
      // 提取进度信息 (已成交/总数)
      const progressMatch = tp8.match(/进度:\s*[\d.]+%\s*\(([\d.]+)\/([\d.]+)\)/)
      if (progressMatch) {
        let filled = parseFloat(progressMatch[1])
        let total = parseFloat(progressMatch[2])
        
        // 买入时，进度是金额（美元），价格是美分，需要转换为数量
        // 数量 = 金额 * 100 / 价格
        if (isBuy && price > 0) {
          filled = (filled * 100) / price
          total = (total * 100) / price
        }
        
        return {
          total,
          filled,
          pending: 0 // tp8是已成交数据，没有挂单
        }
      }
      return null
    },
    
    /**
     * 解析 tp7 数据（挂单数据）
     * 格式: "创建时间: 2026-01-09 13:27:46 | 方向: 卖 | 结果: YES | 价格: 0.177 | 进度: 51.57% (206.00/399.46)"
     * 买入时进度是金额，需要转换为数量。tp7 的价格单位是美元
     * @param {string} tp7 - tp7 数据字符串
     * @param {number} taskSide - 任务方向 (1=买入, 2=卖出)
     */
    parseTp7Data(tp7, taskSide) {
      if (!tp7) return null
      
      // 提取方向
      const sideMatch = tp7.match(/方向:\s*(买|卖)/)
      const isBuy = sideMatch && sideMatch[1] === '买'
      
      // 提取价格（美元）
      const priceMatch = tp7.match(/价格:\s*([\d.]+)/)
      const price = priceMatch ? parseFloat(priceMatch[1]) : 0
      
      // 提取进度信息 (已成交/总数)
      const progressMatch = tp7.match(/进度:\s*[\d.]+%\s*\(([\d.]+)\/([\d.]+)\)/)
      if (progressMatch) {
        let filled = parseFloat(progressMatch[1])
        let total = parseFloat(progressMatch[2])
        
        // 买入时，进度是金额（美元），价格是美元，需要转换为数量
        // 数量 = 金额 / 价格
        if (isBuy && price > 0) {
          filled = filled / price
          total = total / price
        }
        
        return {
          total,
          filled,
          pending: total - filled // 挂单的未成交部分
        }
      }
      return null
    },
    
    /**
     * 解析 msg 数据
     * TYPE5_PARTIAL: {"type": "TYPE5_PARTIAL", "filled_amount": "816.32", "progress": "0 / 273.88 shares", ...}
     * TYPE5_SUCCESS: {"type": "TYPE5_SUCCESS", "filled_amount": "273.88", ...}
     * 买入时 PARTIAL 类型的进度是金额，需要转换为数量；SUCCESS 类型不需要转换
     * @param {string} msg - msg 数据字符串
     * @param {number} taskSide - 任务方向 (1=买入, 2=卖出)
     * @returns {Object|null} { total, filled, pending } 或 { useAmt: true } 表示使用 amt，或 null
     */
    parseMsgData(msg, taskSide) {
      if (!msg) return null
      
      try {
        let msgObj = null
        if (typeof msg === 'string' && msg.trim().startsWith('{')) {
          msgObj = JSON.parse(msg)
        }
        
        // 如果不是 JSON 对象（如错误信息字符串），返回全0
        if (!msgObj) {
          return {
            total: 0,
            filled: 0,
            pending: 0
          }
        }
        
        if (msgObj.type === 'TYPE5_SUCCESS' || msgObj.type === 'TYPE1_SUCCESS') {
          // 完全成交 - 不需要转换，filled_amount 已经是数量
          const filled = parseFloat(String(msgObj.filled_amount).replace(/,/g, '')) || 0
          return {
            total: filled,
            filled: filled,
            pending: 0
          }
        } else if (msgObj.type === 'TYPE5_PARTIAL' || msgObj.type === 'TYPE1_PARTIAL') {
          // 部分成交，从 progress 中提取
          // progress 格式: "0 / 273.88 shares" 或 "1,797.46 / 3,389.75 shares"（注意数字中可能有逗号）
          // 买入时进度是金额，需要转换
          const price = parseFloat(String(msgObj.filled_price).replace(/,/g, '')) || 0
          const isBuy = taskSide === 1
          
          if (msgObj.progress) {
            // 移除数字中的逗号后再匹配
            const cleanProgress = msgObj.progress.replace(/,/g, '')
            const progressMatch = cleanProgress.match(/([\d.]+)\s*\/\s*([\d.]+)/)
            if (progressMatch) {
              let filled = parseFloat(progressMatch[1])
              let total = parseFloat(progressMatch[2])
              
              // 买入时，进度是金额（美元），价格是美分，需要转换为数量
              // 数量 = 金额 * 100 / 价格
              if (isBuy && price > 0) {
                filled = (filled * 100) / price
                total = (total * 100) / price
              }
              
              return {
                total,
                filled,
                pending: total - filled
              }
            }
          }
          // PARTIAL 类型但没有有效 progress（如只有初始数量和现有数量），返回特殊标记让调用方使用 amt
          return { useAmt: true }
        } else {
          // 其他类型的 JSON 消息（非 SUCCESS/PARTIAL），返回全0
          return {
            total: 0,
            filled: 0,
            pending: 0
          }
        }
      } catch (e) {
        console.error('解析msg失败:', e)
      }
      
      // 解析失败，返回全0
      return {
        total: 0,
        filled: 0,
        pending: 0
      }
    },
    
    /**
     * 显示统计详情弹窗
     */
    showStatDetail(title, taskIds) {
      this.statDetailTitle = title
      this.statDetailTaskIds = taskIds
      this.showStatDetailDialog = true
    },
    
    /**
     * 关闭统计详情弹窗
     */
    closeStatDetailDialog() {
      this.showStatDetailDialog = false
      this.statDetailTitle = ''
      this.statDetailTaskIds = []
    },
    
    /**
     * 根据tp7/tp8判断任务是否已修复成功
     * @param {Object} task 任务对象
     * @returns {boolean} 是否修复成功
     */
    isTaskRepairedSuccess(task) {
      if (!task) return false
      
      // 如果任务原本就成功，不算修复
      if (task.status === 2) return false
      
      // 检查tp8（已成交数据）
      if (task.tp8) {
        // tp8格式: "时间: 2026-01-09 14:23:17 (不同时区) | 方向: 卖 | 结果: NO | 价格: 82.3 | 进度: 100.00% (399.46/399.46) | 状态: filled"
        // 检查状态是否为filled，且进度>=80%
        if (task.tp8.includes('状态: filled')) {
          const progressMatch = task.tp8.match(/进度:\s*([\d.]+)%/)
          if (progressMatch) {
            const progress = parseFloat(progressMatch[1])
            if (progress >= 80) {
              return true
            }
          }
        }
      }
      
      // 检查tp7（挂单数据）
      if (task.tp7) {
        // tp7格式: "创建时间: 2026-01-09 13:27:46 | 方向: 卖 | 结果: YES | 价格: 0.177 | 进度: 51.57% (206.00/399.46)"
        const progressMatch = task.tp7.match(/进度:\s*([\d.]+)%/)
        if (progressMatch) {
          const progress = parseFloat(progressMatch[1])
          if (progress >= 80) {
            return true
          }
        }
      }
      
      // 检查serverData
      if (task.serverData) {
        // 检查closedOrderList
        if (task.serverData.closedOrderList && task.serverData.closedOrderList.length > 0) {
          for (const order of task.serverData.closedOrderList) {
            if (order.status === 'filled') {
              const progress = order.fillAmt && order.amt ? (order.fillAmt / order.amt * 100) : 0
              if (progress >= 80) {
                return true
              }
            }
          }
        }
        
        // 检查openOrderList
        if (task.serverData.openOrderList && task.serverData.openOrderList.length > 0) {
          for (const order of task.serverData.openOrderList) {
            const progress = order.amt && order.restAmt !== undefined ? ((order.amt - order.restAmt) / order.amt * 100) : 0
            if (progress >= 80) {
              return true
            }
          }
        }
      }
      
      return false
    },
    
    /**
     * 格式化挂单数据为字符串
     */
    formatOpenOrderMsg(order) {
      if (!order) return ''
      const time = this.timestampToBeijingTime(order.ctime)
      const side = this.formatSide(order.side)
      const progress = ((order.amt - order.restAmt) / order.amt * 100).toFixed(2)
      return `创建时间: ${time} | 方向: ${side} | 结果: ${order.outCome} | 价格: ${order.price} | 进度: ${progress}% (${(order.amt - order.restAmt).toFixed(2)}/${order.amt})`
    },
    
    /**
     * 格式化已成交数据为字符串
     */
    formatClosedOrderMsg(order) {
      if (!order) return ''
      const time = order.convertTime ? this.timestampToBeijingTime(order.convertTime) : this.timestampToBeijingTime(order.time, true)
      const timezoneNote = !order.convertTime ? ' (不同时区)' : ''
      const side = this.formatSide(order.side)
      const progress = ((order.fillAmt / order.amt) * 100).toFixed(2)
      return `时间: ${time}${timezoneNote} | 方向: ${side} | 结果: ${order.outCome} | 价格: ${order.price} | 进度: ${progress}% (${order.fillAmt}/${order.amt}) | 状态: ${order.status}`
    },
    
    /**
     * 格式化side值（1=买，2=卖）
     */
    formatSide(side) {
      if (side === 1 || side === '1') return '买'
      if (side === 2 || side === '2') return '卖'
      if (side === 'BUY' || side === 'buy') return '买'
      if (side === 'SELL' || side === 'sell') return '卖'
      return side
    },
    
    /**
     * 将时间戳或时间字符串转换为北京时间
     */
    timestampToBeijingTime(timestamp, isDifferentTimezone = false) {
      if (!timestamp) return '-'
      try {
        let date
        if (typeof timestamp === 'string') {
          // 尝试解析字符串时间
          date = new Date(timestamp)
        } else {
          // 如果是数字时间戳
          date = new Date(timestamp)
        }
        
        // 如果标记为不同时区，需要转换（假设原时间是UTC或其他时区）
        const beijingTime = isDifferentTimezone ? new Date(date.getTime() + 8 * 60 * 60 * 1000) : date
        
        const year = beijingTime.getFullYear()
        const month = String(beijingTime.getMonth() + 1).padStart(2, '0')
        const day = String(beijingTime.getDate()).padStart(2, '0')
        const hours = String(beijingTime.getHours()).padStart(2, '0')
        const minutes = String(beijingTime.getMinutes()).padStart(2, '0')
        const seconds = String(beijingTime.getSeconds()).padStart(2, '0')
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
      } catch (e) {
        console.error('时间转换失败:', e)
        return '-'
      }
    },
    
    /**
     * 处理任务组列表滚动
     */
    handleTaskGroupsScroll(event) {
      this.taskGroupsScrollTop = event.target.scrollTop
    },
    
    /**
     * 设置任务组DOM引用
     */
    setTaskGroupRef(el, index) {
      if (el) {
        this.taskGroupRefs[index] = el
        // 更新实际高度
        this.$nextTick(() => {
          if (el.offsetHeight) {
            this.taskGroupHeights[index] = el.offsetHeight
          }
        })
      }
    },
    
    /**
     * 更新任务的tp7和tp8
     */
    async updateMissionTp(taskId, tp7, tp8) {
      if (!taskId) {
        return
      }
      
      try {
        const requestData = {
          id: parseInt(taskId)
        }
        
        if (tp7) {
          requestData.tp7 = tp7
        }
        if (tp8) {
          requestData.tp8 = tp8
        }
        
        const response = await axios.post(
          'https://sg.bicoin.com.cn/99l/mission/updateMissionTp',
          requestData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data && response.data.code === 0) {
          console.log(`任务 ${taskId} 的tp7和tp8保存成功`)
        } else {
          console.error(`任务 ${taskId} 的tp7和tp8保存失败:`, response.data)
        }
      } catch (error) {
        console.error(`更新任务 ${taskId} 的tp7和tp8失败:`, error)
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

/* 时间区间查询区域 */
.time-range-query-form {
  display: flex;
  gap: 15px;
  align-items: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.time-range-query-form .form-group {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.time-range-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-range-input {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  width: 120px;
  transition: border-color 0.3s;
}

.time-range-input:focus {
  outline: none;
  border-color: #667eea;
}

.time-range-separator {
  font-weight: 500;
  color: #555;
  font-size: 14px;
  white-space: nowrap;
}

.time-range-hint {
  font-size: 12px;
  color: #999;
  margin-top: -4px;
}

.time-range-query-btn {
  padding: 10px 25px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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

.time-range-query-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
}

.time-range-query-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 结果区域 */
.results-section {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 300px); /* 页面高度减去查询区域高度 */
}

.results-header {
  margin-bottom: 20px;
  flex-shrink: 0; /* 防止被压缩 */
}

.results-section h2 {
  margin-bottom: 15px;
  color: #333;
  font-size: 20px;
}

/* 统计信息区域 */
.statistics-section {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.statistics-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
}

.statistics-title .buy-count {
  color: #27ae60;
  font-weight: 600;
}

.statistics-title .sell-count {
  color: #e74c3c;
  font-weight: 600;
}

.statistics-items {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.statistics-items .stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.statistics-items .stat-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.statistics-items .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  display: flex;
  gap: 8px;
  align-items: center;
}

.statistics-items .stat-value .buy-count {
  color: #27ae60;
}

.statistics-items .stat-value .sell-count {
  color: #e74c3c;
}

.statistics-items .stat-item-expandable {
  flex-direction: column;
  align-items: stretch;
  width: 100%;
}

.stat-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-msg-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.expand-msg-btn:hover {
  background: #764ba2;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.msg-list {
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.msg-list-title {
  font-size: 13px;
  font-weight: 600;
  color: #555;
  margin-bottom: 10px;
}

.msg-list-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.msg-list-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-size: 12px;
  line-height: 1.5;
}

.msg-count {
  flex-shrink: 0;
  color: #667eea;
  font-weight: 600;
}

.msg-content {
  flex: 1;
  color: #333;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 汇总统计 */
.summary-statistics {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.summary-item {
  padding: 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-item.buy-summary {
  border-left: 4px solid #27ae60;
}

.summary-item.sell-summary {
  border-left: 4px solid #e74c3c;
}

.summary-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.summary-item.buy-summary .summary-title {
  color: #27ae60;
}

.summary-item.sell-summary .summary-title {
  color: #e74c3c;
}

.summary-content {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

/* 筛选区域 */
.filter-section {
  display: flex;
  gap: 10px;
  align-items: center;
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

/* 精确筛选区域 */
.filter-section.precise-filter {
  background: #f8f9fa;
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  margin-top: 10px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 13px;
  font-weight: 500;
  color: #555;
  white-space: nowrap;
}

.filter-input-small {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  width: 160px;
  transition: border-color 0.3s;
}

.filter-input-small:focus {
  outline: none;
  border-color: #667eea;
}

.filter-input-small::placeholder {
  color: #aaa;
  font-size: 12px;
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
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 重要：允许flex子元素缩小 */
}

/* 虚拟滚动容器 - 使用更大的高度 */
.task-groups-list-wrapper {
  flex: 1;
  height: calc(100vh - 50px); /* 使用更大的高度，减去查询区域的大概高度 */
  min-height: calc(100vh - 50px); /* 最小高度也设置大一些 */
  max-height: calc(100vh - 50px); /* 设置最大高度，确保容器有固定高度 */
  overflow-y: auto;
  overflow-x: hidden;
}

.task-groups-spacer-top,
.task-groups-spacer-bottom {
  width: 100%;
  flex-shrink: 0;
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

.position-status {
  font-weight: 500;
}

.position-not-updated {
  color: #e67e22;
  background-color: rgba(230, 126, 34, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
}

.position-updated {
  color: #27ae60;
  background-color: rgba(39, 174, 96, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
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

.btn-view-log {
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-view-log:hover {
  background: #5568d3;
}

.btn-snap {
  background: #43e97b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-snap:hover {
  background: #2dd163;
}

/* 仓位统计区域 */
.position-statistics {
  background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%);
  border-radius: 8px;
  padding: 15px 20px;
  margin-bottom: 15px;
  border: 1px solid #fecaca;
}

.position-stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.position-stat-title {
  font-size: 15px;
  font-weight: 600;
  color: #991b1b;
}

.btn-query-position-stat {
  padding: 5px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 12px;
}

.btn-query-position-stat:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.btn-query-position-stat:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.position-stat-summary {
  font-size: 14px;
  color: #666;
}

.position-stat-summary .stat-valid {
  color: #16a34a;
}

.position-stat-summary .stat-invalid {
  color: #dc2626;
}

.btn-stat-detail {
  padding: 2px 8px;
  background: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  margin-left: 4px;
  transition: all 0.2s;
}

.btn-stat-detail:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-fetch-invalid-position {
  padding: 5px 14px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 12px;
}

.btn-fetch-invalid-position:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
}

.btn-fetch-invalid-position:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.position-detail-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #fecaca;
}

.position-detail-title {
  font-size: 14px;
  font-weight: 600;
  color: #555;
  margin-bottom: 12px;
}

.trending-stat-group {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid #e5e7eb;
}

.trending-name {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.stat-category {
  margin-bottom: 8px;
}

.stat-category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.category-label {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
}

.stat-category.balanced .category-label {
  color: #16a34a;
}

.stat-category.unbalanced .category-label {
  color: #dc2626;
}

.stat-detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 13px;
}

.stat-description {
  color: #374151;
  flex: 1;
}

.btn-detail {
  padding: 3px 10px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
  margin-left: 10px;
}

.btn-detail:hover {
  background: #5568d3;
}

/* 统计详情弹窗 */
.stat-detail-task-list {
  padding: 10px 0;
}

.stat-detail-label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  margin-bottom: 12px;
}

.stat-detail-ids {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-id-tag {
  padding: 4px 12px;
  background: #e5e7eb;
  color: #374151;
  border-radius: 4px;
  font-size: 13px;
  font-family: monospace;
}

/* 弹窗样式 */
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
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  max-width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-content.large {
  width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 28px;
  color: white;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-actions {
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

/* 浏览器日志弹窗样式 */
.bro-log-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 1rem;
}

.bro-log-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bro-log-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 0.75rem;
  border-left: 4px solid #667eea;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.bro-log-item:hover {
  background: #e9ecef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.bro-log-time {
  color: #6c757d;
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.bro-log-text {
  color: #212529;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.empty {
  text-align: center;
  padding: 20px;
  color: #999;
}

/* 模式1组头部样式 */
.mode1-group-header {
  padding: 12px 20px;
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #764ba2 66%, #764ba2 100%);
  color: white;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 根据状态修改header右边1/3的背景颜色 */
.mode1-group-header.header-success {
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #27ae60 66%, #27ae60 100%);
}

.mode1-group-header.header-repaired {
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #3498db 66%, #3498db 100%);
}

.mode1-group-header.header-failed {
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #e74c3c 66%, #e74c3c 100%);
}

.mode1-group-header.header-running {
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #f39c12 66%, #f39c12 100%);
}

.mode1-group-header.header-noImpact {
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #f39c12 66%, #f39c12 100%);
}

.mode1-group-header.header-unknown {
  background: linear-gradient(to right, #667eea 0%, #764ba2 66%, #95a5a6 66%, #95a5a6 100%);
}

.mode1-group-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-status-label {
  font-size: 14px;
  font-weight: 500;
}

.group-status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
}

.group-status-badge.status-success {
  background: rgba(39, 174, 96, 0.3);
  color: #27ae60;
}

.group-status-badge.status-failed {
  background: rgba(231, 76, 60, 0.3);
  color: #e74c3c;
}

.group-status-badge.status-running {
  background: rgba(241, 196, 15, 0.3);
  color: #f39c12;
}

.group-status-badge.status-unknown {
  background: rgba(149, 165, 166, 0.3);
  color: #95a5a6;
}

.group-status-badge.status-no-impact {
  background: rgba(241, 196, 15, 0.3);
  color: #f39c12;
}

.group-status-badge.status-repaired {
  background: rgba(52, 152, 219, 0.3);
  color: #3498db;
}

/* 组状态统计区域 */
.group-status-statistics {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  padding: 15px 20px;
  margin-bottom: 15px;
  border: 1px solid #dee2e6;
}

.status-stat-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.status-stat-item {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.status-stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.status-stat-item.status-success {
  background: rgba(39, 174, 96, 0.15);
  color: #27ae60;
  border-color: rgba(39, 174, 96, 0.3);
}

.status-stat-item.status-repaired {
  background: rgba(52, 152, 219, 0.15);
  color: #3498db;
  border-color: rgba(52, 152, 219, 0.3);
}

.status-stat-item.status-failed {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
  border-color: rgba(231, 76, 60, 0.3);
}

.status-stat-item.status-no-impact {
  background: rgba(241, 196, 15, 0.15);
  color: #f39c12;
  border-color: rgba(241, 196, 15, 0.3);
}

.status-stat-item.status-running {
  background: rgba(155, 89, 182, 0.15);
  color: #9b59b6;
  border-color: rgba(155, 89, 182, 0.3);
}

/* 状态筛选区域 */
.status-filter-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 15px;
  padding-left: 15px;
  border-left: 1px solid #ddd;
}

.status-filter-section label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  white-space: nowrap;
}

.status-filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  min-width: 140px;
  transition: border-color 0.3s;
}

.status-filter-select:focus {
  outline: none;
  border-color: #667eea;
}

.clear-status-filter-btn {
  padding: 6px 12px;
  background: #95a5a6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.clear-status-filter-btn:hover {
  background: #7f8c8d;
}

/* 批量获取按钮 */
.batch-fetch-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 15px;
  white-space: nowrap;
}

.batch-fetch-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
}

.batch-fetch-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 批量更新仓位按钮 */
.batch-position-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 10px;
  white-space: nowrap;
}

.batch-position-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(155, 89, 182, 0.4);
}

.batch-position-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-fetch-server-data {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-fetch-server-data:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.btn-fetch-server-data:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 订单信息样式 */
.task-order-info {
  padding: 8px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  font-size: 13px;
}

.order-info-item {
  margin-bottom: 6px;
}

.order-info-item:last-child {
  margin-bottom: 0;
}

.order-label {
  font-weight: 600;
  color: #555;
  margin-right: 8px;
}

.order-content {
  color: #333;
  word-break: break-word;
}

/* 服务器数据样式 */
.task-server-data {
  padding: 8px 20px;
  background: #f0f7ff;
  border-top: 1px solid #e0e0e0;
}

.server-data-group {
  margin-bottom: 12px;
}

.server-data-group:last-child {
  margin-bottom: 0;
}

.server-data-title {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 6px;
}

.server-data-item {
  padding: 6px 10px;
  background: white;
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #333;
  word-break: break-word;
}

.server-data-item:last-child {
  margin-bottom: 0;
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
  
  .time-range-query-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .time-range-query-form .form-group {
    align-items: stretch;
  }
  
  .time-range-inputs {
    flex-direction: column;
    gap: 8px;
  }
  
  .time-range-input {
    width: 100%;
  }
  
  .time-range-query-btn {
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
  
  .statistics-items {
    flex-direction: column;
  }
  
  .statistics-items .stat-item {
    width: 100%;
    justify-content: space-between;
  }
  
  .stat-item-header {
    flex-wrap: wrap;
  }
  
  .expand-msg-btn {
    margin-left: 0;
    margin-top: 4px;
    width: 100%;
  }
  
  .msg-list-items {
    max-height: 200px;
  }
  
  .summary-content {
    font-size: 13px;
  }
}
</style>

