<template>
  <div class="app">
    <header class="top-header">
      <h1>任务管理系统</h1>
      <div class="header-actions">
        <button class="btn-header" @click="showAddConfigDialog">添加配置</button>
        <button class="btn-header" @click="showEditConfigDialog">修改配置</button>
      </div>
    </header>

    <main class="main">
      <div class="container">
        <!-- 自动对冲功能 -->
        <section class="section auto-hedge-section">
          <div class="section-header-with-filter">
            <h2>自动对冲</h2>
            <div class="trending-filter">
              <label>筛选主题:</label>
              <input 
                v-model="autoHedgeFilter" 
                type="text" 
                class="filter-input" 
                placeholder="输入 Trending 关键词筛选"
              />
            </div>
          </div>
          <div class="auto-hedge-controls">
            <div class="hedge-amount-info">
              <span class="amount-label">累计对冲数量:</span>
              <span class="amount-value">{{ hedgeStatus.amtSum || 0 }}</span>
            </div>
            
            <!-- 交易费查询 -->
            <div class="transaction-fee-query">
              <div class="time-range-selector">
                <span class="amount-label">交易费查询:</span>
                <input 
                  v-model="feeQuery.startTime" 
                  type="datetime-local" 
                  class="time-input"
                />
                <span class="time-separator">至</span>
                <input 
                  v-model="feeQuery.endTime" 
                  type="datetime-local" 
                  class="time-input"
                />
                <button class="btn btn-secondary btn-sm" @click="queryTransactionFee">
                  查询
                </button>
              </div>
              <div class="fee-result" v-if="feeQuery.totalFee !== null">
                <span class="fee-label">总交易费:</span>
                <span class="fee-value">${{ feeQuery.totalFee.toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="hedge-amount-input">
              <span class="amount-label">总数量:</span>
              <input 
                v-model.number="hedgeStatus.amt" 
                type="number" 
                class="amount-input" 
                min="0"
                placeholder="输入总数量"
              />
              <button class="btn btn-secondary btn-sm" @click="updateHedgeAmount">
                更新对冲数量
              </button>
              <button class="btn btn-warning btn-sm" @click="cleanHedgeAmount">
                清空当前已开
              </button>
            </div>
            
            <!-- 开仓/平仓开关 -->
            <div class="hedge-mode-switch">
              <span class="mode-label">模式:</span>
              <label class="switch-label">
                <input 
                  type="checkbox" 
                  v-model="hedgeMode.isClose" 
                  class="switch-checkbox"
                  :disabled="autoHedgeRunning"
                />
                <span class="switch-slider"></span>
                <span class="switch-text">{{ hedgeMode.isClose ? '平仓' : '开仓' }}</span>
              </label>
            </div>
            
            <!-- 时间过滤输入框 -->
            <div class="hedge-time-filter">
              <span class="filter-label">最近</span>
              <input 
                v-model.number="hedgeMode.timePassMin" 
                type="number" 
                class="time-input" 
                min="0"
                placeholder="60"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
              <span class="filter-label">分钟内有过任意操作的，不参与</span>
            </div>
            
            <!-- 事件间隔设置 -->
            <div class="hedge-interval-setting">
              <span class="filter-label">事件间隔:</span>
              <div class="radio-group-inline">
                <label class="radio-label-inline">
                  <input 
                    type="radio" 
                    v-model="hedgeMode.intervalType" 
                    value="success"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                  />
                  <span>挂单成功再挂另一边</span>
                </label>
                <label class="radio-label-inline">
                  <input 
                    type="radio" 
                    v-model="hedgeMode.intervalType" 
                    value="delay"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                  />
                  <span>延时</span>
                </label>
              </div>
              <input 
                v-if="hedgeMode.intervalType === 'delay'"
                v-model.number="hedgeMode.intervalDelay" 
                type="number" 
                class="delay-input" 
                min="0"
                placeholder="1000"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
              <span v-if="hedgeMode.intervalType === 'delay'" class="filter-label">ms</span>
            </div>
            
            <!-- 最大允许深度设置 -->
            <div class="hedge-depth-filter">
              <span class="filter-label">最大允许深度:</span>
              <input 
                v-model.number="hedgeMode.maxDepth" 
                type="number" 
                class="depth-input" 
                min="0"
                placeholder="1000"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            
            <button 
              :class="['btn', 'btn-primary', { 'btn-running': autoHedgeRunning }]" 
              @click="toggleAutoHedge"
            >
              {{ autoHedgeRunning ? '停止自动分配' : '开始自动分配' }}
            </button>
            <span v-if="autoHedgeRunning" class="status-badge status-running">运行中</span>
            
            <button 
              class="btn btn-info btn-sm" 
              @click="showAllHedgeLogs"
              title="查看所有对冲日志"
            >
              📊 总日志
            </button>
          </div>
          
          <div class="trending-list">
            <div v-if="filteredActiveConfigs.length === 0" class="empty-message">
              {{ activeConfigs.length === 0 ? '暂无启用的主题配置' : '没有匹配的主题' }}
            </div>
            <div v-else class="trending-items">
              <div 
                v-for="config in filteredActiveConfigs" 
                :key="config.id" 
                class="trending-item"
              >
                <div class="trending-header">
                  <div class="trending-name-row">
                    <span class="trending-name">
                      {{ config.trendingPart1 ? `${config.trending}-${config.trendingPart1}` : config.trending }}
                    </span>
                    <button class="btn-log btn-sm" @click="showHedgeLog(config)">
                      📋 日志
                    </button>
                    <input 
                      v-model="config.monitorBrowserId" 
                      type="text" 
                      class="monitor-input" 
                      placeholder="监听深度浏览器ID"
                      :disabled="autoHedgeRunning"
                      @blur="saveMonitorBrowserIds"
                    />
                  </div>
                </div>
                
                <!-- Type 3 任务和对冲信息显示区域 -->
                <div class="task-hedge-container">
                  <!-- 左侧：Type 3 任务信息 -->
                  <div class="type3-task-section">
                    <div class="section-title">Type 3 任务</div>
                    <div v-if="config.type3Task" class="type3-task-info">
                      <div class="task-status-row">
                        <span class="task-label">任务 #{{ config.type3Task.id }}</span>
                        <span class="task-browser">浏览器: {{ config.type3Task.numberList }}</span>
                        <span 
                          class="task-status-badge" 
                          :class="getStatusClass(config.type3Task.status)"
                        >
                          {{ getStatusText(config.type3Task.status) }}
                        </span>
                      </div>
                      <div class="task-time">{{ formatTime(config.type3Task.updateTime) }}</div>
                      <div v-if="config.type3Task.msg" class="task-msg">
                        <span class="msg-content">{{ formatTaskMsg(config.type3Task.msg) }}</span>
                      </div>
                    </div>
                    <div v-else class="no-data">暂无数据</div>
                  </div>
                  
                  <!-- 右侧：对冲信息 -->
                  <div class="hedge-info-section">
                    <div class="section-title">对冲信息</div>
                    <div v-if="config.currentHedge" class="hedge-info">
                      <div class="hedge-status-row">
                        <span class="hedge-label">对冲 #{{ config.currentHedge.id }}</span>
                        <span 
                          class="hedge-status-badge"
                          :class="getHedgeStatusClass(config.currentHedge)"
                        >
                          {{ getHedgeStatusText(config.currentHedge) }}
                        </span>
                      </div>
                      
                      <!-- 任务一 -->
                      <div class="hedge-task-section">
                        <div class="task-title">
                          任务一 - {{ config.currentHedge.firstSide }}
                          <span class="task-amount">x{{ config.currentHedge.share }}</span>
                        </div>
                        <div class="hedge-task-details-grid">
                          <div class="hedge-detail-row">
                            <span>任务ID:</span>
                            <span :class="getTaskStatusClass(
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.yesStatus 
                                : config.currentHedge.noStatus
                            )">
                              {{ 
                                config.currentHedge.firstSide === 'YES' 
                                  ? (config.currentHedge.yesTaskId || '待提交') 
                                  : (config.currentHedge.noTaskId || '待提交') 
                              }}
                            </span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>浏览器:</span>
                            <span>{{ 
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.yesNumber 
                                : config.currentHedge.noNumber 
                            }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>电脑组:</span>
                            <span>{{ 
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.yesGroupNo 
                                : config.currentHedge.noGroupNo 
                            }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>买/卖:</span>
                            <span>{{ config.currentHedge.side === 1 ? '买入' : '卖出' }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>方向:</span>
                            <span>{{ config.currentHedge.firstSide }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>价格:</span>
                            <span>{{ 
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.yesPrice 
                                : config.currentHedge.noPrice 
                            }}¢</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>数量:</span>
                            <span>{{ config.currentHedge.share }}</span>
                          </div>
                        </div>
                      </div>
                      
                      <!-- 任务二 -->
                      <div class="hedge-task-section">
                        <div class="task-title">
                          任务二 - {{ config.currentHedge.firstSide === 'YES' ? 'NO' : 'YES' }}
                          <span class="task-amount">x{{ config.currentHedge.share }}</span>
                        </div>
                        <div class="hedge-task-details-grid">
                          <div class="hedge-detail-row">
                            <span>任务ID:</span>
                            <span :class="getTaskStatusClass(
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.noStatus 
                                : config.currentHedge.yesStatus
                            )">
                              {{ 
                                config.currentHedge.firstSide === 'YES' 
                                  ? (config.currentHedge.noTaskId || '待提交') 
                                  : (config.currentHedge.yesTaskId || '待提交') 
                              }}
                            </span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>浏览器:</span>
                            <span>{{ 
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.noNumber 
                                : config.currentHedge.yesNumber 
                            }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>电脑组:</span>
                            <span>{{ 
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.noGroupNo 
                                : config.currentHedge.yesGroupNo 
                            }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>买/卖:</span>
                            <span>{{ config.currentHedge.side === 1 ? '买入' : '卖出' }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>方向:</span>
                            <span>{{ config.currentHedge.firstSide === 'YES' ? 'NO' : 'YES' }}</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>价格:</span>
                            <span>{{ 
                              config.currentHedge.firstSide === 'YES' 
                                ? config.currentHedge.noPrice 
                                : config.currentHedge.yesPrice 
                            }}¢</span>
                          </div>
                          <div class="hedge-detail-row">
                            <span>数量:</span>
                            <span>{{ config.currentHedge.share }}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div class="hedge-summary">
                        <span>{{ config.currentHedge.isClose ? '卖出' : '买入' }} @ {{ config.currentHedge.price }}¢</span>
                        <span>{{ formatTime(config.currentHedge.startTime) }}</span>
                      </div>
                    </div>
                    <div v-else class="no-data">暂无对冲</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 添加任务和对冲 -->
        <div class="form-sections">
        <!-- 添加任务表单 -->
        <section class="section">
          <h2>添加任务</h2>
          <div v-if="isLoadingConfig" class="loading-message">
            ⏳ 正在加载配置...
          </div>
          <form v-else @submit.prevent="handleSubmit" class="task-form">
            <div class="form-row">
              <div class="form-group">
                <label for="numberList">浏览器编号 *</label>
                <input
                  id="numberList"
                  v-model="formData.numberList"
                  type="text"
                  placeholder="请输入浏览器编号"
                  required
                  @blur="updateGroupNoFromBrowser"
                />
              </div>

              <div class="form-group">
                <label>组号</label>
                <div class="group-no-display">{{ formData.groupNo || '请先输入浏览器编号' }}</div>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="type">类型 *</label>
                <select id="type" v-model="formData.type" required>
                  <option value="1">下单</option>
                </select>
              </div>

              <div class="form-group">
                <label for="trendingId">Trending *</label>
                <select 
                  id="trendingId" 
                  v-model="formData.trendingId" 
                  required
                  :disabled="isLoadingConfig"
                >
                  <option value="" disabled>{{ isLoadingConfig ? '加载中...' : '请选择Trending' }}</option>
                  <option 
                    v-for="config in configList" 
                    :key="config.id" 
                    :value="String(config.id)"
                  >
                    {{ config.trendingPart1 ? `${config.trending}-${config.trendingPart1}` : config.trending }}
                  </option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="exchangeName">交易所 *</label>
                <select 
                  id="exchangeName" 
                  v-model="formData.exchangeName" 
                  required
                  :disabled="isLoadingConfig"
                >
                  <option value="" disabled>{{ isLoadingConfig ? '加载中...' : '请选择交易所' }}</option>
                  <option 
                    v-for="exchange in exchangeList" 
                    :key="exchange" 
                    :value="exchange"
                  >
                    {{ exchange }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label for="side">买卖方向 *</label>
                <select id="side" v-model="formData.side" required>
                  <option value="1">买入</option>
                  <option value="2">卖出</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="psSide">预测方向 *</label>
                <select id="psSide" v-model="formData.psSide" required>
                  <option value="1">Yes</option>
                  <option value="2">No</option>
                </select>
              </div>

              <div class="form-group">
                <!-- 占位，保持布局对齐 -->
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="amt">数量 *</label>
                <input
                  id="amt"
                  v-model.number="formData.amt"
                  type="number"
                  step="0.01"
                  placeholder="请输入数量"
                  required
                />
              </div>

              <div class="form-group">
                <label for="price">价格（选填，不填则为市价）</label>
                <input
                  id="price"
                  v-model.number="formData.price"
                  type="number"
                  step="0.000001"
                  placeholder="请输入价格"
                />
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
                <span v-if="isSubmitting">提交中...</span>
                <span v-else>添加任务</span>
              </button>
              <button type="button" class="btn btn-info" @click="submitOrderbookTask" :disabled="isSubmittingOrderbook">
                <span v-if="isSubmittingOrderbook">提交中...</span>
                <span v-else>📊 获取订单薄</span>
              </button>
              <button type="button" class="btn btn-secondary" @click="resetForm">
                重置
              </button>
            </div>
          </form>
        </section>

          <!-- 对冲块 -->
          <section class="section">
            <div class="section-header">
              <div class="hedge-title-wrapper">
                <div v-if="hedgeTaskStatus.yesTaskId || hedgeTaskStatus.noTaskId" class="hedge-status-display">
                  <span v-if="hedgeTaskStatus.yesTaskId" class="hedge-task-status" :class="getStatusClass(hedgeTaskStatus.yesStatus)">
                    Yes任务#{{ hedgeTaskStatus.yesTaskId }}: {{ getStatusText(hedgeTaskStatus.yesStatus) }}
                  </span>
                  <span v-if="hedgeTaskStatus.noTaskId" class="hedge-task-status" :class="getStatusClass(hedgeTaskStatus.noStatus)">
                    No任务#{{ hedgeTaskStatus.noTaskId }}: {{ getStatusText(hedgeTaskStatus.noStatus) }}
                  </span>
                </div>
                <h2>对冲</h2>
              </div>
              <button type="button" class="btn-secondary" @click="scrollToHedgeHistory">对冲记录</button>
            </div>
            <form @submit.prevent="handleHedgeSubmit" class="hedge-form">
              <div class="form-row">
                <div class="form-group">
                  <label for="hedgeEventLink">事件链接 *</label>
                  <select 
                    id="hedgeEventLink" 
                    v-model="hedgeData.eventLink" 
                    required
                    :disabled="isLoadingConfig"
                  >
                    <option value="" disabled>{{ isLoadingConfig ? '加载中...' : '请选择事件' }}</option>
                    <option 
                      v-for="config in configList" 
                      :key="config.id" 
                      :value="String(config.id)"
                    >
                      {{ config.trendingPart1 ? `${config.trending}-${config.trendingPart1}` : config.trending }}
                    </option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="yesPrice">yes的价格 *</label>
                  <input
                    id="yesPrice"
                    v-model.number="hedgeData.yesPrice"
                    type="number"
                    step="0.000001"
                    placeholder="请输入yes的价格"
                    required
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>买卖方向 *</label>
                  <div class="radio-group">
                    <label class="radio-label">
                      <input type="radio" v-model="hedgeData.direction" value="buy" />
                      <span>买入</span>
                    </label>
                    <label class="radio-label">
                      <input type="radio" v-model="hedgeData.direction" value="sell" />
                      <span>卖出</span>
                    </label>
                  </div>
                </div>

                <div class="form-group">
                  <label>先挂 *</label>
                  <div class="radio-group">
                    <label class="radio-label">
                      <input type="radio" v-model="hedgeData.firstOrder" value="yes" />
                      <span>{{ hedgeData.direction === 'buy' ? '买' : '卖' }}yes</span>
                    </label>
                    <label class="radio-label">
                      <input type="radio" v-model="hedgeData.firstOrder" value="no" />
                      <span>{{ hedgeData.direction === 'buy' ? '买' : '卖' }}no</span>
                    </label>
                  </div>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="yesBrowser">{{ hedgeData.direction === 'buy' ? '买' : '卖' }}yes的浏览器 *</label>
                  <input
                    id="yesBrowser"
                    v-model="hedgeData.yesBrowser"
                    type="text"
                    :placeholder="'请输入' + (hedgeData.direction === 'buy' ? '买' : '卖') + 'yes的浏览器编号'"
                    required
                  />
                </div>

                <div class="form-group">
                  <label for="noBrowser">{{ hedgeData.direction === 'buy' ? '买' : '卖' }}no的浏览器 *</label>
                  <input
                    id="noBrowser"
                    v-model="hedgeData.noBrowser"
                    type="text"
                    :placeholder="'请输入' + (hedgeData.direction === 'buy' ? '买' : '卖') + 'no的浏览器编号'"
                    required
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="hedgeAmount">数量 *</label>
                  <input
                    id="hedgeAmount"
                    v-model.number="hedgeData.amount"
                    type="number"
                    step="0.01"
                    placeholder="请输入数量（不超过最大可开单量）"
                    required
                  />
                </div>

                <div class="form-group">
                  <label>事件间隔 *</label>
                  <div class="radio-group">
                    <label class="radio-label">
                      <input type="radio" v-model="hedgeData.intervalType" value="success" />
                      <span>挂单成功再挂另外一边</span>
                    </label>
                    <label class="radio-label">
                      <input type="radio" v-model="hedgeData.intervalType" value="delay" />
                      <span>延时</span>
                    </label>
                  </div>
                </div>
              </div>

              <div v-if="hedgeData.intervalType === 'delay'" class="form-group">
                <label for="delayMs">延时(ms) *</label>
                <input
                  id="delayMs"
                  v-model.number="hedgeData.delayMs"
                  type="number"
                  placeholder="请输入延时毫秒数"
                  :required="hedgeData.intervalType === 'delay'"
                />
              </div>

              <div class="form-actions">
                <button type="submit" class="btn btn-primary" :disabled="isSubmittingHedge">
                  <span v-if="isSubmittingHedge">提交中...</span>
                  <span v-else>提交对冲</span>
                </button>
                <button type="button" class="btn btn-secondary" @click="resetHedgeForm">
                  重置
                </button>
              </div>
            </form>
          </section>
        </div>

        <!-- 任务列表 -->
        <section class="section">
          <div class="section-header">
            <h2>任务列表</h2>
            <div class="refresh-controls">
              <span class="auto-refresh-status">自动刷新: 每10秒</span>
            <button class="btn-refresh" @click="fetchMissionList" :disabled="isLoadingList">
              <span v-if="isLoadingList">刷新中...</span>
              <span v-else>🔄 刷新</span>
            </button>
            </div>
          </div>
          
          <div v-if="isLoadingList && missionList.length === 0" class="empty">
            加载中...
          </div>
          <div v-else-if="missionList.length === 0" class="empty">
            暂无任务记录
          </div>
          <div v-else class="mission-list">
            <div 
              v-for="item in missionList" 
              :key="item.mission.id" 
              class="mission-card"
            >
              <div class="mission-header">
                <div class="mission-title">
                  <span class="mission-id">任务 #{{ item.mission.id }}</span>
                  <span class="mission-status" :class="getStatusClass(item.mission.status)">
                    {{ getStatusText(item.mission.status) }}
                  </span>
                </div>
                <div class="mission-time">
                  {{ formatTime(item.mission.createTime) }}
                </div>
              </div>

              <div class="mission-body">
                <div class="info-grid">
                  <div class="info-item">
                    <span class="label">组号:</span>
                    <span class="value">{{ item.mission.groupNo }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">类型:</span>
                    <span class="value">{{ getTypeText(item.mission.type) }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">交易所:</span>
                    <span class="value">{{ item.mission.exchangeName }}</span>
                  </div>
                  <div class="info-item" v-if="item.mission.trendingId">
                    <span class="label">Trending ID:</span>
                    <span class="value">{{ item.mission.trendingId }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">方向:</span>
                    <span class="value">{{ getSideText(item.mission.side) }}</span>
                  </div>
                  <div class="info-item" v-if="item.mission.psSide">
                    <span class="label">预测:</span>
                    <span class="value">{{ getPsSideText(item.mission.psSide) }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">数量:</span>
                    <span class="value">{{ item.mission.amt }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">价格:</span>
                    <span class="value">{{ item.mission.price || '市价' }}</span>
                  </div>
                  <div class="info-item" v-if="item.mission.succCount !== null">
                    <span class="label">成功数:</span>
                    <span class="value">{{ item.mission.succCount }}</span>
                  </div>
                  <div class="info-item" v-if="item.mission.numberList">
                    <span class="label">浏览器编号:</span>
                    <span class="value">{{ item.mission.numberList }}</span>
                  </div>
                </div>

                <div v-if="item.exchangeConfig" class="exchange-info">
                  <div class="trending-title">{{ item.exchangeConfig.trending }}</div>
                  <div class="url-links">
                    <a 
                      v-if="item.exchangeConfig.opUrl" 
                      :href="item.exchangeConfig.opUrl" 
                      target="_blank"
                      class="link-btn"
                    >
                      Opinion Trade
                    </a>
                    <a 
                      v-if="item.exchangeConfig.polyUrl" 
                      :href="item.exchangeConfig.polyUrl" 
                      target="_blank"
                      class="link-btn"
                    >
                      Polymarket
                    </a>
                  </div>
                </div>

                <div v-if="item.mission.msg" class="mission-msg">
                  <span class="label">消息:</span>
                  <span class="value">{{ formatTaskMsg(item.mission.msg) }}</span>
                </div>
                
                <!-- 重试按钮 - 仅失败任务显示 -->
                <div v-if="item.mission.status === 3" class="mission-actions">
                  <button 
                    class="btn-retry" 
                    @click="retryMission(item)"
                    :disabled="isRetrying"
                  >
                    {{ isRetrying ? '重试中...' : '🔄 重试' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 对冲记录列表 -->
        <section class="section" ref="hedgeHistorySection">
          <div class="section-header">
            <h2>对冲记录</h2>
            <button class="btn-refresh" @click="fetchHedgeHistory" :disabled="isLoadingHedgeHistory">
              <span v-if="isLoadingHedgeHistory">刷新中...</span>
              <span v-else>🔄 刷新</span>
            </button>
            </div>
          
          <div v-if="isLoadingHedgeHistory && hedgeHistoryList.length === 0" class="empty">
            加载中...
          </div>
          <div v-else-if="hedgeHistoryList.length === 0" class="empty">
            暂无对冲记录
          </div>
          <div v-else class="mission-list">
            <div 
              v-for="item in hedgeHistoryList" 
              :key="item.id" 
              class="mission-card"
            >
              <div class="mission-header">
                <div class="mission-title">
                  <span class="mission-id">对冲记录 #{{ item.id }}</span>
                </div>
                <div class="mission-time">
                  {{ formatTime(item.time) }}
                </div>
              </div>

              <div class="mission-body">
                <div class="info-grid">
                  <div class="info-item">
                    <span class="label">事件链接:</span>
                    <span class="value">{{ item.exchangeConfig?.trending || getTrendingById(item.trendingId) }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">价格:</span>
                    <span class="value">{{ item.price }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">优先类型:</span>
                    <span class="value">{{ item.priorityType === 1 ? '先买yes' : '先买no' }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">Yes浏览器:</span>
                    <span class="value">{{ item.yesNumber }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">No浏览器:</span>
                    <span class="value">{{ item.noNumber }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">数量:</span>
                    <span class="value">{{ item.amount }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">类型:</span>
                    <span class="value">{{ item.type === 1 ? '挂单成功再挂另一边' : '延迟' }}</span>
                  </div>
                  <div class="info-item" v-if="item.type === 2">
                    <span class="label">延迟:</span>
                    <span class="value">{{ item.delayMs }}ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </main>

    <!-- Toast 提示 -->
    <div v-if="toast.show" class="toast" :class="'toast-' + toast.type">
      {{ toast.message }}
    </div>

    <!-- 添加配置弹窗 -->
    <div v-if="showAddConfig" class="modal-overlay" @click="closeAddConfigDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>添加配置</h3>
          <button class="modal-close" @click="closeAddConfigDialog">×</button>
        </div>
        <form @submit.prevent="submitAddConfig" class="modal-form">
          <div class="form-group">
            <label>Trending *   主标题###子标题</label>
            <input v-model="newConfig.trending" type="text" required placeholder="请输入 Trending" />
          </div>
          <!-- <div class="form-group">
            <label>子主题</label>
            <input v-model="newConfig.trendingPart1" type="text" placeholder="请输入子主题（选填）" />
          </div> -->
          <div class="form-group">
            <label>Opinion Trade URL *</label>
            <input v-model="newConfig.opUrl" type="text" required placeholder="https://app.opinion.trade/detail?topicId=..." />
          </div>
          <div class="form-group">
            <label>Polymarket URL *</label>
            <input v-model="newConfig.polyUrl" type="text" required placeholder="https://polymarket.com/event/..." />
          </div>
          <div class="form-group">
            <label>OP Topic ID *</label>
            <input v-model="newConfig.opTopicId" type="text" required placeholder="请输入 Topic ID" />
          </div>
          <div class="form-group">
            <label>权重 *</label>
            <input v-model.number="newConfig.weight" type="number" required placeholder="请输入权重（数字）" min="0" />
          </div>
          <div class="form-group">
            <label class="switch-label-row">
              <span class="label-text">是否开启</span>
              <label class="switch-label">
                <input 
                  type="checkbox" 
                  v-model="newConfig.enabled" 
                  class="switch-checkbox"
                />
                <span class="switch-slider"></span>
                <span class="switch-text">{{ newConfig.enabled ? '启用' : '禁用' }}</span>
              </label>
            </label>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn btn-primary" :disabled="isSubmittingConfig">
              <span v-if="isSubmittingConfig">提交中...</span>
              <span v-else>提交</span>
            </button>
            <button type="button" class="btn btn-secondary" @click="closeAddConfigDialog">取消</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 修改配置弹窗 -->
    <div v-if="showEditConfig" class="modal-overlay" @click="closeEditConfigDialog">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>修改配置</h3>
          <button class="modal-close" @click="closeEditConfigDialog">×</button>
        </div>
        <div class="config-filter-toolbar">
          <div class="trending-filter">
            <label>筛选主题:</label>
            <input 
              v-model="editConfigFilter" 
              type="text" 
              class="filter-input" 
              placeholder="输入 Trending 关键词筛选"
            />
          </div>
          <button type="button" class="btn btn-danger btn-sm" @click="disableAllConfigs">
            全部禁用
          </button>
          <button type="button" class="btn btn-secondary btn-sm" @click="showAllConfigs">
            全部显示
          </button>
          <button type="button" class="btn btn-secondary btn-sm" @click="hideAllConfigs">
            全部隐藏
          </button>
        </div>
        <div class="config-list">
          <div v-if="filteredEditConfigList.length === 0" class="empty">{{ editConfigList.length === 0 ? '暂无配置' : '没有匹配的配置' }}</div>
          <div v-else class="config-items">
            <div v-for="(config, index) in filteredEditConfigList" :key="index" class="config-item">
              <div class="config-item-header">
                <span class="config-index">{{ index + 1 }}</span>
                <label class="switch-label">
                  <input 
                    type="checkbox" 
                    v-model="config.enabled" 
                    class="switch-checkbox"
                  />
                  <span class="switch-slider"></span>
                  <span class="switch-text">{{ config.enabled ? '启用' : '禁用' }}</span>
                </label>
                <label class="switch-label" style="margin-left: 15px;">
                  <input 
                    type="checkbox" 
                    v-model="config.visible" 
                    class="switch-checkbox"
                  />
                  <span class="switch-slider"></span>
                  <span class="switch-text">{{ config.visible ? '显示' : '隐藏' }}</span>
                </label>
                <!-- <button type="button" class="btn-remove" @click="removeConfigItem(index)">删除</button> -->
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Trending *</label>
                  <input v-model="config.trending" type="text" required />
                </div>
                <div class="form-group">
                  <label>子主题</label>
                  <input v-model="config.trendingPart1" type="text" placeholder="选填" />
                </div>
              </div>
              <div class="form-group">
                <label>OP Topic ID *</label>
                <input v-model="config.opTopicId" type="text" required />
              </div>
              <div class="form-group">
                <label>Opinion Trade URL *</label>
                <input v-model="config.opUrl" type="text" required />
              </div>
              <div class="form-group">
                <label>Polymarket URL *</label>
                <input v-model="config.polyUrl" type="text" required />
              </div>
              <div class="form-group">
                <label>权重 *</label>
                <input v-model.number="config.weight" type="number" required placeholder="请输入权重" min="0" />
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-primary" @click="submitEditConfig" :disabled="isSubmittingConfig">
            <span v-if="isSubmittingConfig">保存中...</span>
            <span v-else>保存全部</span>
          </button>
          <button type="button" class="btn btn-secondary" @click="closeEditConfigDialog">取消</button>
        </div>
      </div>
    </div>
    
    <!-- 对冲日志弹窗 -->
    <div v-if="showHedgeLogDialog" class="modal-overlay" @click="closeHedgeLogDialog">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>对冲日志 - {{ currentLogConfig?.trending }}</h3>
          <button class="modal-close" @click="closeHedgeLogDialog">×</button>
        </div>
        <div class="hedge-log-content">
          <div v-if="hedgeLogs.length === 0" class="empty">暂无对冲记录</div>
          <div v-else class="hedge-log-list">
            <div 
              v-for="(log, index) in hedgeLogs" 
              :key="index" 
              class="hedge-log-item"
            >
              <div class="log-header">
                <span class="log-id">对冲 #{{ log.id }}</span>
                <span 
                  class="log-status-badge"
                  :class="getHedgeLogStatusClass(log)"
                >
                  {{ getHedgeLogStatusText(log) }}
                </span>
                <span class="log-time">{{ formatTime(log.startTime) }}</span>
              </div>
              <div class="log-details">
                <div class="log-row">
                  <span class="log-label">模式:</span>
                  <span>{{ log.isClose ? '平仓' : '开仓' }}</span>
                </div>
                <div class="log-row">
                  <span class="log-label">价格:</span>
                  <span>{{ log.price }}</span>
                </div>
                <div class="log-row">
                  <span class="log-label">数量:</span>
                  <span>{{ log.share }}</span>
                </div>
                <div class="log-row">
                  <span class="log-label">先挂:</span>
                  <span>{{ log.firstSide }}</span>
                </div>
                <div class="log-row">
                  <span class="log-label">YES浏览器:</span>
                  <span>{{ log.yesNumber }} - {{ getStatusText(log.yesStatus) }}</span>
                </div>
                <div class="log-row">
                  <span class="log-label">NO浏览器:</span>
                  <span>{{ log.noNumber }} - {{ getStatusText(log.noStatus) }}</span>
                </div>
                <div v-if="log.endTime" class="log-row">
                  <span class="log-label">结束时间:</span>
                  <span>{{ formatTime(log.endTime) }}</span>
                </div>
                <div v-if="log.duration" class="log-row">
                  <span class="log-label">耗时:</span>
                  <span>{{ log.duration }}分钟</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="closeHedgeLogDialog">关闭</button>
        </div>
      </div>
    </div>

    <!-- 总日志弹窗 -->
    <div v-if="showAllHedgeLogsDialog" class="modal-overlay" @click="closeAllHedgeLogsDialog">
      <div class="modal-content extra-large" @click.stop>
        <div class="modal-header">
          <h3>所有对冲日志 (共 {{ allHedgeLogs.length }} 条)</h3>
          <button class="modal-close" @click="closeAllHedgeLogsDialog">×</button>
        </div>
        <div class="all-hedge-log-content">
          <div v-if="allHedgeLogs.length === 0" class="empty">暂无对冲记录</div>
          <div v-else class="all-hedge-log-list">
            <div 
              v-for="(log, index) in paginatedAllHedgeLogs" 
              :key="index" 
              class="compact-hedge-log-item"
              :class="getHedgeLogStatusClass(log)"
            >
              <div class="compact-log-main">
                <span class="compact-log-id">#{{ allHedgeLogs.length - ((allHedgeLogsCurrentPage - 1) * allHedgeLogsPageSize + index) }}</span>
                <span class="compact-log-trending">{{ log.trendingName }}</span>
                <span 
                  class="compact-status-badge"
                  :class="getHedgeLogStatusClass(log)"
                >
                  {{ getHedgeLogStatusText(log) }}
                </span>
                <span class="compact-log-mode">{{ log.isClose ? '平仓' : '开仓' }}</span>
                <span class="compact-log-info">
                  价格:{{ log.price }} | 数量:{{ log.share }} | 先挂:{{ log.firstSide }}
                </span>
                <span class="compact-log-time">{{ formatCompactTime(log.startTime) }}</span>
                <span v-if="log.duration" class="compact-log-duration">{{ log.duration }}分</span>
              </div>
              <div class="compact-log-details">
                <div class="compact-task-row">
                  <span class="task-label">YES:</span>
                  <span class="task-info">
                    <span class="task-group">组{{ log.yesGroupNo || '-' }}</span> | 
                    浏览器{{ log.yesNumber }} | 
                    任务{{ log.yesTaskId || '-' }} | 
                    <span :class="getTaskStatusClass(log.yesStatus)">{{ getStatusText(log.yesStatus) }}</span>
                    <span v-if="log.yesTaskMsg" class="task-msg">| {{ formatTaskMsg(log.yesTaskMsg) }}</span>
                  </span>
                </div>
                <div class="compact-task-row">
                  <span class="task-label">NO:</span>
                  <span class="task-info">
                    <span class="task-group">组{{ log.noGroupNo || '-' }}</span> | 
                    浏览器{{ log.noNumber }} | 
                    任务{{ log.noTaskId || '-' }} | 
                    <span :class="getTaskStatusClass(log.noStatus)">{{ getStatusText(log.noStatus) }}</span>
                    <span v-if="log.noTaskMsg" class="task-msg">| {{ formatTaskMsg(log.noTaskMsg) }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="allHedgeLogs.length > 0" class="pagination">
          <button 
            class="btn btn-sm" 
            @click="prevPage" 
            :disabled="allHedgeLogsCurrentPage === 1"
          >
            上一页
          </button>
          <span class="pagination-info">
            第 {{ allHedgeLogsCurrentPage }} / {{ allHedgeLogsTotalPages }} 页
            (显示 {{ (allHedgeLogsCurrentPage - 1) * allHedgeLogsPageSize + 1 }}-{{ Math.min(allHedgeLogsCurrentPage * allHedgeLogsPageSize, allHedgeLogs.length) }} 条)
          </span>
          <button 
            class="btn btn-sm" 
            @click="nextPage" 
            :disabled="allHedgeLogsCurrentPage === allHedgeLogsTotalPages"
          >
            下一页
          </button>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-warning" @click="clearAllHedgeLogs">清空所有日志</button>
          <button type="button" class="btn btn-secondary" @click="closeAllHedgeLogsDialog">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const isConnected = ref(false)
const isSubmitting = ref(false)
const isSubmittingHedge = ref(false)
const isSubmittingConfig = ref(false)
const isSubmittingOrderbook = ref(false)
const isRetrying = ref(false)
const isLoadingList = ref(false)
const isLoadingConfig = ref(true)
const isLoadingHedgeHistory = ref(false)
const missionList = ref([])
const hedgeHistoryList = ref([])
const hedgeHistorySection = ref(null)

// 自动刷新配置
const autoRefresh = reactive({
  enabled: true,  // 默认启用自动刷新
  interval: 10  // 默认10秒
})

// 配置管理弹窗
const showAddConfig = ref(false)
const showEditConfig = ref(false)
const editConfigList = ref([])

// 配置筛选
const autoHedgeFilter = ref('')  // 自动对冲功能块的筛选
const editConfigFilter = ref('')  // 修改配置弹窗的筛选

// 新配置数据
const newConfig = reactive({
  trending: '',
  trendingPart1: '',
  opUrl: '',
  polyUrl: '',
  opTopicId: '',
  weight: 0,
  enabled: true  // 默认启用
})

// 对冲状态显示
// 对冲任务状态（重命名，避免与对冲数量状态冲突）
const hedgeTaskStatus = reactive({
  yesTaskId: null,
  yesStatus: null,
  noTaskId: null,
  noStatus: null
})

// Toast提示
const toast = reactive({
  show: false,
  message: '',
  type: 'info'  // info, success, warning, error
})

// 配置数据
const exchangeList = ref([])
const configList = ref([])
const accountConfigList = ref([])
const browserToGroupMap = ref({})

// 自动对冲相关
const autoHedgeRunning = ref(false)
const autoHedgeInterval = ref(null)
const activeConfigs = ref([])  // 启用的配置列表
const hedgeStatusInterval = ref(null)  // 对冲状态轮询定时器

// 对冲状态（重命名以避免与下面的 hedgeStatus 冲突）
const hedgeStatus = reactive({
  amtSum: 0,  // 累计对冲数量
  amt: 0      // 总数量
})

// 对冲模式
const hedgeMode = reactive({
  isClose: false,  // false: 开仓, true: 平仓
  timePassMin: 60,  // 最近xx分钟内有过任意操作的，不参与
  intervalType: 'success',  // 'success': 挂单成功再挂另一边, 'delay': 延时
  intervalDelay: 1000,  // 延时的毫秒数
  maxDepth: 100  // 最大允许深度
})

// 交易费查询
const feeQuery = reactive({
  startTime: '',
  endTime: '',
  totalFee: null
})

// 初始化交易费查询的默认时间（最近一小时）
const initFeeQueryTime = () => {
  const now = new Date()
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
  
  // 格式化为 datetime-local 需要的格式
  const formatDateTime = (date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
  }
  
  feeQuery.startTime = formatDateTime(oneHourAgo)
  feeQuery.endTime = formatDateTime(now)
}

// 对冲日志相关
const showHedgeLogDialog = ref(false)
const currentLogConfig = ref(null)
const hedgeLogs = ref([])
const showAllHedgeLogsDialog = ref(false)  // 总日志弹窗
const allHedgeLogs = ref([])  // 所有对冲日志
const allHedgeLogsCurrentPage = ref(1)  // 总日志当前页
const allHedgeLogsPageSize = ref(10)  // 总日志每页显示数量

// 本地存储的对冲记录
const LOCAL_STORAGE_KEY = 'hedge_logs'
const HEDGE_SETTINGS_KEY = 'hedge_settings'
const MONITOR_BROWSER_KEY = 'monitor_browser_ids'
const CONFIG_VISIBLE_KEY = 'config_visible_status'  // 配置显示状态

// 对冲任务暂停状态（按 trendingId 记录）
const pausedType3Tasks = ref(new Set())

/**
 * 表单数据
 */
const formData = reactive({
  groupNo: '',
  numberList: '',
  type: '1',
  trendingId: '',
  exchangeName: '',
  side: '1',
  psSide: '1',
  amt: null,
  price: null
})

/**
 * 对冲表单数据
 */
const hedgeData = reactive({
  eventLink: '',
  yesPrice: null,
  direction: 'buy',  // buy=买入, sell=卖出
  firstOrder: 'yes',
  yesBrowser: '',
  noBrowser: '',
  amount: null,
  intervalType: 'success',
  delayMs: null
})

/**
 * 获取账户配置（浏览器编号和组号的映射关系）
 */
const fetchAccountConfig = async () => {
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache')
    
    if (response.data && response.data.data) {
      accountConfigList.value = response.data.data
      
      // 建立浏览器编号到组号的映射
      const mapping = {}
      response.data.data.forEach(item => {
        if (item.fingerprintNo && item.computeGroup) {
          mapping[item.fingerprintNo] = item.computeGroup
        }
      })
      browserToGroupMap.value = mapping
      
      console.log(`账户配置加载成功，共 ${response.data.data.length} 条记录`)
      console.log('浏览器编号到组号映射:', mapping)
    } else {
      console.warn('获取账户配置失败: 无数据')
    }
  } catch (error) {
    console.error('获取账户配置失败:', error)
  }
}

/**
 * 根据浏览器编号更新组号
 */
const updateGroupNoFromBrowser = () => {
  const browserNo = formData.numberList.trim()
  if (browserNo && browserToGroupMap.value[browserNo]) {
    formData.groupNo = browserToGroupMap.value[browserNo]
    console.log(`浏览器编号 ${browserNo} 对应组号: ${formData.groupNo}`)
  } else if (browserNo) {
    formData.groupNo = ''
    console.warn(`浏览器编号 ${browserNo} 未找到对应的组号`)
  }
}

/**
 * 获取交易所和Trending配置
 */
const fetchExchangeConfig = async () => {
  isLoadingConfig.value = true
  
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/exchangeConfig')
    
    if (response.data && response.data.code === 0) {
      const data = response.data.data
      
      // 设置交易所列表
      exchangeList.value = data.exchangeList || []
      
      // 设置配置列表，将 isOpen 映射为 enabled
      configList.value = (data.configList || []).map(config => ({
        ...config,
        enabled: config.isOpen === 1  // isOpen 1->true, 0->false
      }))
      
      // 设置默认值
      if (exchangeList.value.length > 0 && !formData.exchangeName) {
        formData.exchangeName = exchangeList.value[0]
      }
      
      if (configList.value.length > 0 && !formData.trendingId) {
        formData.trendingId = String(configList.value[0].id)
      }
      
      if (configList.value.length > 0 && !hedgeData.eventLink) {
        hedgeData.eventLink = String(configList.value[0].id)
      }
      
      console.log(`配置加载成功：${exchangeList.value.length} 个交易所，${configList.value.length} 个Trending`)
      
      // 更新活动配置列表
      updateActiveConfigs()
    } else {
      console.warn(`获取配置失败: ${response.data?.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('获取配置失败:', error)
  } finally {
    isLoadingConfig.value = false
  }
}

/**
 * 获取任务列表
 */
const fetchMissionList = async () => {
  isLoadingList.value = true
  
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/list', {
      params: {
        limit: 200
      }
    })
    
    if (response.data && response.data.code === 0) {
      const allMissions = response.data.data.list || []
      
      // 过滤掉 type=3 的任务，只显示 type=1 和 type=2 的任务
      missionList.value = allMissions.filter(item => item.mission.type !== 3)
      
      // 单独处理 type=3 的任务，更新到 activeConfigs 中
      const type3Missions = allMissions.filter(item => item.mission.type === 3)
      updateType3TasksInConfigs(type3Missions)
      
      // 更新对冲任务状态（使用新接口）
      for (const config of activeConfigs.value) {
        if (config.currentHedge && config.currentHedge.finalStatus === 'running') {
          const hedgeRecord = config.currentHedge
          
          // 通过新接口获取任务状态
          if (hedgeRecord.yesTaskId) {
            const yesTaskData = await fetchMissionStatus(hedgeRecord.yesTaskId)
            if (yesTaskData) {
              const oldStatus = hedgeRecord.yesStatus
              hedgeRecord.yesStatus = yesTaskData.status
              if (oldStatus !== yesTaskData.status) {
                console.log(`[fetchMissionList] YES任务 ${hedgeRecord.yesTaskId} 状态变化: ${oldStatus} -> ${yesTaskData.status}`)
              }
            }
          }
          
          if (hedgeRecord.noTaskId) {
            const noTaskData = await fetchMissionStatus(hedgeRecord.noTaskId)
            if (noTaskData) {
              const oldStatus = hedgeRecord.noStatus
              hedgeRecord.noStatus = noTaskData.status
              if (oldStatus !== noTaskData.status) {
                console.log(`[fetchMissionList] NO任务 ${hedgeRecord.noTaskId} 状态变化: ${oldStatus} -> ${noTaskData.status}`)
              }
            }
          }
          
          // 检查对冲任务状态并触发完成逻辑
          const firstSide = hedgeRecord.firstSide
          const firstStatus = firstSide === 'YES' ? hedgeRecord.yesStatus : hedgeRecord.noStatus
          const secondStatus = firstSide === 'YES' ? hedgeRecord.noStatus : hedgeRecord.yesStatus
          
          console.log(`[fetchMissionList] 对冲 ${hedgeRecord.id} - 第一个任务(${firstSide})状态: ${firstStatus}, 第二个任务已提交: ${hedgeRecord.secondTaskSubmitted}`)
          
          // 检查第一个任务是否失败
          if (firstStatus === 3) {
            console.log(`[fetchMissionList] 对冲 ${hedgeRecord.id} 任务一失败，立即停止`)
            hedgeRecord.finalStatus = 'failed'
            finishHedge(config, hedgeRecord)
          }
          // 第一个任务成功，提交第二个任务
          else if (firstStatus === 2 && !hedgeRecord.secondTaskSubmitted) {
            console.log(`[fetchMissionList] 对冲 ${hedgeRecord.id} 任务一成功，开始任务二`)
            hedgeRecord.secondTaskSubmitted = true
            submitSecondHedgeTask(config, hedgeRecord)
          }
          // 第二个任务已提交，检查第二个任务状态
          else if (hedgeRecord.secondTaskSubmitted) {
            // 检查第二个任务是否失败
            if (secondStatus === 3) {
              console.log(`[fetchMissionList] 对冲 ${hedgeRecord.id} 任务二失败，立即停止`)
              hedgeRecord.finalStatus = 'failed'
              finishHedge(config, hedgeRecord)
            }
            // 两个任务都成功
            else if (firstStatus === 2 && secondStatus === 2) {
              console.log(`[fetchMissionList] 对冲 ${hedgeRecord.id} 两个任务都成功`)
              hedgeRecord.finalStatus = 'success'
              finishHedge(config, hedgeRecord)
            }
          }
        }
      }
      
      console.log(`任务列表已刷新，共 ${missionList.value.length} 条记录（已过滤 type=3）`)
    } else {
      console.warn(`获取任务列表失败: ${response.data?.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    isLoadingList.value = false
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  // 检查组号是否已设置
  if (!formData.groupNo) {
    alert('无法获取组号，请确认浏览器编号是否正确')
    return
  }
  
  isSubmitting.value = true
  
  try {
    // 构建提交数据
    const submitData = {
      groupNo: formData.groupNo,
      numberList: parseInt(formData.numberList),
      type: parseInt(formData.type),
      trendingId: parseInt(formData.trendingId),
      exchangeName: formData.exchangeName,
      side: parseInt(formData.side),
      psSide: parseInt(formData.psSide),
      amt: parseFloat(formData.amt)
    }
    
    // 如果填写了价格，则添加价格字段
    if (formData.price !== null && formData.price !== '') {
      submitData.price = parseFloat(formData.price)
    }
    
    console.log('正在提交任务...', submitData)
    
    // 发送请求
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/add',
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('任务添加成功！响应:', response.data)
      alert('任务添加成功！')
      // 清空表单（仅清空需要重新输入的字段）
      formData.numberList = ''
      formData.amt = null
      formData.price = null
      // exchangeName, trendingId, side, psSide 保持上次选择的值，方便批量添加
      
      // 刷新任务列表
      setTimeout(() => {
        fetchMissionList()
      }, 500)
    }
  } catch (error) {
    console.error('提交失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    alert(`任务添加失败: ${errorMsg}`)
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 提交获取订单薄任务（type=3）
 */
const submitOrderbookTask = async () => {
  // 验证必填字段
  if (!formData.numberList) {
    alert('请输入浏览器编号')
    return
  }
  
  if (!formData.trendingId) {
    alert('请选择 Trending')
    return
  }
  
  if (!formData.exchangeName) {
    alert('请选择交易所')
    return
  }
  
  // 检查组号是否已设置
  if (!formData.groupNo) {
    alert('无法获取组号，请确认浏览器编号是否正确')
    return
  }
  
  isSubmittingOrderbook.value = true
  
  try {
    // 构建 type=3 任务数据
    const submitData = {
      groupNo: formData.groupNo,
      numberList: parseInt(formData.numberList),
      type: 3,  // type=3 表示获取订单薄任务
      trendingId: parseInt(formData.trendingId),
      exchangeName: formData.exchangeName,
      side: 1  // 手动提交默认为Buy
    }
    
    console.log('正在提交订单薄任务...', submitData)
    
    // 发送请求
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/add',
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('订单薄任务添加成功！响应:', response.data)
      alert('订单薄任务添加成功！')
      
      // 刷新任务列表
      setTimeout(() => {
        fetchMissionList()
      }, 500)
    }
  } catch (error) {
    console.error('提交订单薄任务失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    alert(`订单薄任务添加失败: ${errorMsg}`)
  } finally {
    isSubmittingOrderbook.value = false
  }
}

/**
 * 显示Toast提示
 */
const showToast = (message, type = 'info') => {
  toast.message = message
  toast.type = type
  toast.show = true
  
  setTimeout(() => {
    toast.show = false
  }, 3000)
}

/**
 * 根据trending ID获取trending名称
 */
const getTrendingById = (id) => {
  const config = configList.value.find(c => c.id === id)
  if (!config) return `ID: ${id}`
  return config.trendingPart1 ? `${config.trending}-${config.trendingPart1}` : config.trending
}

/**
 * 滚动到对冲记录
 */
const scrollToHedgeHistory = () => {
  hedgeHistorySection.value?.scrollIntoView({ behavior: 'smooth' })
}

/**
 * 获取对冲记录列表
 */
const fetchHedgeHistory = async () => {
  isLoadingHedgeHistory.value = true
  
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/hedgeHist')
    
    if (response.data && response.data.code === 0) {
      hedgeHistoryList.value = response.data.data.list || []
      console.log(`对冲记录已加载，共 ${hedgeHistoryList.value.length} 条记录`)
    } else {
      console.warn(`获取对冲记录失败: ${response.data?.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('获取对冲记录失败:', error)
  } finally {
    isLoadingHedgeHistory.value = false
  }
}

/**
 * 提交对冲记录到服务器
 */
const submitHedgeHistory = async (hedgeRecord) => {
  try {
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/hedgeHist',
      hedgeRecord,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('对冲记录提交成功:', response.data)
      fetchHedgeHistory()  // 刷新对冲记录列表
    }
  } catch (error) {
    console.error('对冲记录提交失败:', error)
  }
}

/**
 * 检查对冲历史中是否存在相同浏览器的记录
 */
const checkDuplicateHedge = (trendingId, yesBrowser, noBrowser) => {
  return hedgeHistoryList.value.some(item => 
    item.trendingId === trendingId && 
    (item.yesNumber === yesBrowser || item.yesNumber === noBrowser || 
     item.noNumber === yesBrowser || item.noNumber === noBrowser)
  )
}

/**
 * 提交单个任务
 */
const submitSingleTask = async (taskData) => {
  try {
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/add',
      taskData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.data) {
      const data = response.data.data
      // 如果返回的是对象，直接返回；如果是数字ID，包装成对象
      if (typeof data === 'object') {
        return data
      } else {
        // 如果只返回ID，包装成对象格式
        return { id: data, status: 9 }
      }
    }
    return null
  } catch (error) {
    console.error('任务提交失败:', error)
    throw error
  }
}

/**
 * 轮询任务状态
 */
const pollTaskStatus = async (taskId, callback) => {
  const maxAttempts = 60  // 最多轮询60次 (10分钟)
  let attempts = 0
  
  const poll = async () => {
    if (attempts >= maxAttempts) {
      callback('timeout', null)
      return
    }
    
    attempts++
    
    try {
      const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/list', {
        params: {
          limit: 200
        }
      })
      
      if (response.data && response.data.code === 0) {
        const missions = response.data.data.list || []
        const task = missions.find(m => m.mission.id === taskId)
        
        if (task) {
          const status = task.mission.status
          
          // 更新状态显示
          callback('update', status)
          
          // 2=成功, 3=失败
          if (status === 2 || status === 3) {
            callback('complete', status)
            return
          }
        }
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
    
    // 10秒后再次轮询
    setTimeout(poll, 10000)
  }
  
  poll()
}

/**
 * 提交对冲表单
 */
const handleHedgeSubmit = async () => {
  // 检查是否是卖出方向，需要验证对冲记录
  if (hedgeData.direction === 'sell') {
    const hasDuplicate = checkDuplicateHedge(
      parseInt(hedgeData.eventLink),
      hedgeData.yesBrowser,
      hedgeData.noBrowser
    )
    
    if (hasDuplicate) {
      if (!confirm('存在相同浏览器编号的对冲事件，是否继续？')) {
        return
      }
    }
  }
  
  isSubmittingHedge.value = true
  
  // 重置对冲状态显示
  hedgeTaskStatus.yesTaskId = null
  hedgeTaskStatus.yesStatus = null
  hedgeTaskStatus.noTaskId = null
  hedgeTaskStatus.noStatus = null
  
  try {
    showToast('开始提交对冲任务...', 'info')
    
    // 确定第一个任务和第二个任务的参数
    const side = hedgeData.direction === 'buy' ? 1 : 2  // 1=买入, 2=卖出
    const firstTaskPsSide = hedgeData.firstOrder === 'yes' ? 1 : 2
    const firstTaskBrowser = hedgeData.firstOrder === 'yes' ? hedgeData.yesBrowser : hedgeData.noBrowser
    const secondTaskPsSide = hedgeData.firstOrder === 'yes' ? 2 : 1
    const secondTaskBrowser = hedgeData.firstOrder === 'yes' ? hedgeData.noBrowser : hedgeData.yesBrowser
    
    const yesPrice = parseFloat(hedgeData.yesPrice)
    const noPrice = 100 - yesPrice
    const firstTaskPrice = hedgeData.firstOrder === 'yes' ? yesPrice : noPrice
    
    // 提交第一个任务
    const firstTaskData = {
      groupNo: browserToGroupMap.value[firstTaskBrowser] || '1',
      numberList: parseInt(firstTaskBrowser),
      type: 1,
      trendingId: parseInt(hedgeData.eventLink),
      exchangeName: 'OP',
      side: side,
      psSide: firstTaskPsSide,
      amt: parseFloat(hedgeData.amount),
      price: firstTaskPrice
    }
    
    console.log('提交第一个任务:', firstTaskData)
    const firstTask = await submitSingleTask(firstTaskData)
    
    if (!firstTask || !firstTask.id) {
      throw new Error('第一个任务提交失败')
    }
    
    // 更新状态显示
    if (hedgeData.firstOrder === 'yes') {
      hedgeTaskStatus.yesTaskId = firstTask.id
      hedgeTaskStatus.yesStatus = firstTask.status
    } else {
      hedgeTaskStatus.noTaskId = firstTask.id
      hedgeTaskStatus.noStatus = firstTask.status
    }
    
    showToast(`第一个任务已提交 (ID: ${firstTask.id})`, 'success')
    
    // 根据间隔类型决定何时提交第二个任务
    if (hedgeData.intervalType === 'success') {
      // 挂单成功再挂另一边
      showToast('等待第一个任务完成...', 'info')
      
      pollTaskStatus(firstTask.id, async (event, status) => {
        if (event === 'update') {
          // 更新状态显示
          if (hedgeData.firstOrder === 'yes') {
            hedgeTaskStatus.yesStatus = status
          } else {
            hedgeTaskStatus.noStatus = status
          }
        } else if (event === 'complete') {
          if (status === 2) {
            // 任务成功，提交第二个任务
            showToast('第一个任务成功，提交第二个任务...', 'success')
            await submitSecondTask(side, secondTaskPsSide, secondTaskBrowser, noPrice)
          } else if (status === 3) {
            // 任务失败，取消第二个任务
            showToast('第一个任务失败，取消对冲', 'error')
            clearHedgeStatusAfterDelay()
          }
        } else if (event === 'timeout') {
          showToast('等待超时，取消对冲', 'warning')
          clearHedgeStatusAfterDelay()
        }
      })
    } else {
      // 延时提交
      const delayMs = parseInt(hedgeData.delayMs) || 0
      showToast(`延时 ${delayMs}ms 后提交第二个任务...`, 'info')
      
      // 同时监听第一个任务状态
      pollTaskStatus(firstTask.id, (event, status) => {
        if (event === 'update' || event === 'complete') {
          if (hedgeData.firstOrder === 'yes') {
            hedgeTaskStatus.yesStatus = status
          } else {
            hedgeTaskStatus.noStatus = status
          }
        }
      })
      
      setTimeout(async () => {
        await submitSecondTask(side, secondTaskPsSide, secondTaskBrowser, noPrice)
      }, delayMs)
    }
    
  } catch (error) {
    console.error('对冲任务提交失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`对冲任务失败: ${errorMsg}`, 'error')
  } finally {
    isSubmittingHedge.value = false
  }
}

/**
 * 提交第二个任务
 */
const submitSecondTask = async (side, psSide, browser, price) => {
  try {
    const secondTaskData = {
      groupNo: browserToGroupMap.value[browser] || '1',
      numberList: parseInt(browser),
      type: 1,
      trendingId: parseInt(hedgeData.eventLink),
      exchangeName: 'OP',
      side: side,
      psSide: psSide,
      amt: parseFloat(hedgeData.amount),
      price: price
    }
    
    console.log('提交第二个任务:', secondTaskData)
    const secondTask = await submitSingleTask(secondTaskData)
    
    if (!secondTask || !secondTask.id) {
      throw new Error('第二个任务提交失败')
    }
    
    // 更新状态显示
    if (hedgeData.firstOrder === 'yes') {
      hedgeTaskStatus.noTaskId = secondTask.id
      hedgeTaskStatus.noStatus = secondTask.status
    } else {
      hedgeTaskStatus.yesTaskId = secondTask.id
      hedgeTaskStatus.yesStatus = secondTask.status
    }
    
    showToast(`第二个任务已提交 (ID: ${secondTask.id})`, 'success')
    
    // 监听第二个任务状态
    pollTaskStatus(secondTask.id, async (event, status) => {
      if (event === 'update' || event === 'complete') {
        if (hedgeData.firstOrder === 'yes') {
          hedgeTaskStatus.noStatus = status
        } else {
          hedgeTaskStatus.yesStatus = status
        }
        
        // 如果两个任务都成功了，提交对冲记录
        if (event === 'complete' && status === 2 && 
            hedgeTaskStatus.yesStatus === 2 && hedgeTaskStatus.noStatus === 2) {
          showToast('对冲成功！', 'success')
          
          // 提交对冲记录
          const hedgeRecord = {
            trendingId: parseInt(hedgeData.eventLink),
            price: parseFloat(hedgeData.yesPrice),
            priorityType: hedgeData.firstOrder === 'yes' ? 1 : 2,
            yesNumber: hedgeData.yesBrowser,
            noNumber: hedgeData.noBrowser,
            amount: parseFloat(hedgeData.amount),
            type: hedgeData.intervalType === 'success' ? 1 : 2,
            delayMs: hedgeData.intervalType === 'delay' ? parseInt(hedgeData.delayMs) : null
          }
          
          await submitHedgeHistory(hedgeRecord)
          clearHedgeStatusAfterDelay()
        } else if (event === 'complete' && status === 3) {
          showToast('第二个任务失败', 'error')
          clearHedgeStatusAfterDelay()
        }
      }
    })
    
  } catch (error) {
    console.error('第二个任务提交失败:', error)
    showToast(`第二个任务失败: ${error.message}`, 'error')
    clearHedgeStatusAfterDelay()
  }
}

/**
 * 延迟清除对冲状态显示
 */
const clearHedgeStatusAfterDelay = () => {
  setTimeout(() => {
    hedgeTaskStatus.yesTaskId = null
    hedgeTaskStatus.yesStatus = null
    hedgeTaskStatus.noTaskId = null
    hedgeTaskStatus.noStatus = null
  }, 120000)  // 2分钟后清除
}

/**
 * 重置表单
 */
const resetForm = () => {
  formData.groupNo = ''
  formData.numberList = ''
  formData.type = '1'
  // 重置为第一个选项
  formData.trendingId = configList.value.length > 0 ? String(configList.value[0].id) : ''
  formData.exchangeName = exchangeList.value.length > 0 ? exchangeList.value[0] : ''
  formData.side = '1'
  formData.psSide = '1'
  formData.amt = null
  formData.price = null
  console.log('表单已重置')
}

/**
 * 重置对冲表单（不清空输入内容，只在手动重置时清空）
 */
const resetHedgeForm = () => {
  hedgeData.eventLink = configList.value.length > 0 ? String(configList.value[0].id) : ''
  hedgeData.yesPrice = null
  hedgeData.direction = 'buy'
  hedgeData.firstOrder = 'yes'
  hedgeData.yesBrowser = ''
  hedgeData.noBrowser = ''
  hedgeData.amount = null
  hedgeData.intervalType = 'success'
  hedgeData.delayMs = null
  console.log('对冲表单已重置')
}

/**
 * 显示添加配置弹窗
 */
const showAddConfigDialog = () => {
  // 重置表单
  newConfig.trending = ''
  newConfig.trendingPart1 = ''
  newConfig.opUrl = ''
  newConfig.polyUrl = ''
  newConfig.opTopicId = ''
  newConfig.weight = 0
  newConfig.enabled = true  // 默认启用
  showAddConfig.value = true
}

/**
 * 关闭添加配置弹窗
 */
const closeAddConfigDialog = () => {
  showAddConfig.value = false
}

/**
 * 提交添加配置
 */
const submitAddConfig = async () => {
  isSubmittingConfig.value = true
  
  try {
    const submitData = {
      list: [{
        trending: newConfig.trending,
        trendingPart1: newConfig.trendingPart1 || null,
        opUrl: newConfig.opUrl,
        polyUrl: newConfig.polyUrl,
        opTopicId: newConfig.opTopicId,
        weight: newConfig.weight || 0,
        isOpen: newConfig.enabled ? 1 : 0  // 根据开关设置
      }]
    }
    
    console.log('提交添加配置:', submitData)
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('配置添加成功:', response.data)
      alert('配置添加成功！')
      closeAddConfigDialog()
      // 重新加载配置
      updateActiveConfigs()
      fetchExchangeConfig()
    }
  } catch (error) {
    console.error('配置添加失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    alert(`配置添加失败: ${errorMsg}`)
  } finally {
    isSubmittingConfig.value = false
  }
}

/**
 * 显示修改配置弹窗
 */
const showEditConfigDialog = () => {
  // 深拷贝当前配置列表，并确保 enabled 字段正确映射
  const baseList = JSON.parse(JSON.stringify(configList.value)).map(config => ({
    ...config,
    enabled: config.isOpen === 1 || config.enabled === true,
    weight: config.weight || 0
  }))
  
  // 加载显示状态
  editConfigList.value = loadConfigVisibleStatus(baseList)
  showEditConfig.value = true
}

/**
 * 关闭修改配置弹窗
 */
const closeEditConfigDialog = () => {
  showEditConfig.value = false
  // 关闭时清空筛选
  editConfigFilter.value = ''
}

/**
 * 全部禁用配置
 */
const disableAllConfigs = () => {
  if (confirm('确定要禁用所有配置吗？')) {
    editConfigList.value.forEach(config => {
      config.enabled = false
    })
    alert('已将所有配置设置为禁用状态，请点击"保存全部"以生效')
  }
}

/**
 * 全部显示配置
 */
const showAllConfigs = () => {
  if (confirm('确定要将所有配置设置为显示吗？')) {
    editConfigList.value.forEach(config => {
      config.visible = true
    })
    alert('已将所有配置设置为显示状态，请点击"保存全部"以生效')
  }
}

/**
 * 全部隐藏配置
 */
const hideAllConfigs = () => {
  if (confirm('确定要将所有配置设置为隐藏吗？')) {
    editConfigList.value.forEach(config => {
      config.visible = false
    })
    alert('已将所有配置设置为隐藏状态，请点击"保存全部"以生效')
  }
}

/**
 * 删除配置项
 */
const removeConfigItem = (index) => {
  if (confirm('确定要删除这个配置吗？')) {
    editConfigList.value.splice(index, 1)
  }
}

/**
 * 提交修改配置
 */
const submitEditConfig = async () => {
  isSubmittingConfig.value = true
  
  try {
    // 保存显示状态到本地存储（不提交到服务器）
    saveConfigVisibleStatus(editConfigList.value)
    
    const submitData = {
      list: editConfigList.value.map(config => ({
        id: config.id,  // 带上id表示更新
        trending: config.trending,
        trendingPart1: config.trendingPart1 || null,
        opUrl: config.opUrl,
        polyUrl: config.polyUrl,
        opTopicId: config.opTopicId,
        weight: config.weight || 0,
        isOpen: config.enabled ? 1 : 0  // enabled 映射为 isOpen (true->1, false->0)
        // 注意：visible 字段不提交到服务器
      }))
    }
    
    console.log('提交修改配置:', submitData)
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('配置更新成功:', response.data)
      alert('配置更新成功！')
      closeEditConfigDialog()
      // 重新加载配置
      fetchExchangeConfig()
      // 更新活动配置列表
      updateActiveConfigs()
    }
  } catch (error) {
    console.error('配置更新失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    alert(`配置更新失败: ${errorMsg}`)
  } finally {
    isSubmittingConfig.value = false
  }
}

/**
 * 筛选后的活动配置列表（用于自动对冲功能块显示）
 */
const filteredActiveConfigs = computed(() => {
  if (!autoHedgeFilter.value || !autoHedgeFilter.value.trim()) {
    return activeConfigs.value
  }
  
  const keyword = autoHedgeFilter.value.trim().toLowerCase()
  return activeConfigs.value.filter(config => {
    const trending = (config.trending || '').toLowerCase()
    return trending.includes(keyword)
  })
})

/**
 * 筛选后的编辑配置列表（用于修改配置弹窗显示）
 */
const filteredEditConfigList = computed(() => {
  if (!editConfigFilter.value || !editConfigFilter.value.trim()) {
    return editConfigList.value
  }
  
  const keyword = editConfigFilter.value.trim().toLowerCase()
  return editConfigList.value.filter(config => {
    const trending = (config.trending || '').toLowerCase()
    return trending.includes(keyword)
  })
})

/**
 * 总日志总页数
 */
const allHedgeLogsTotalPages = computed(() => {
  return Math.ceil(allHedgeLogs.value.length / allHedgeLogsPageSize.value) || 1
})

/**
 * 当前页的总日志数据
 */
const paginatedAllHedgeLogs = computed(() => {
  const start = (allHedgeLogsCurrentPage.value - 1) * allHedgeLogsPageSize.value
  const end = start + allHedgeLogsPageSize.value
  return allHedgeLogs.value.slice(start, end)
})

/**
 * 更新活动配置列表（启用的配置）
 */
const updateActiveConfigs = () => {
  // 先加载显示状态
  const configsWithVisible = loadConfigVisibleStatus(configList.value)
  
  activeConfigs.value = configsWithVisible
    .filter(config => config.isOpen === 1 || config.enabled === true)  // 启用的配置
    .filter(config => config.visible !== false)  // 显示开关打开的配置
    .map(config => ({
      ...config,
      monitorBrowserId: config.monitorBrowserId || '',
      orderbookData: config.orderbookData || '',
      weight: config.weight || 0,
      type3Task: config.type3Task || null,
      currentHedge: config.currentHedge || null,
      pendingType3TaskId: config.pendingType3TaskId || null,  // 正在进行的type=3任务ID
      pendingType3TaskStartTime: config.pendingType3TaskStartTime || null  // 任务提交时间
    }))
  
  // 加载本地保存的监听浏览器ID
  loadMonitorBrowserIds()
}

/**
 * 更新配置中的 type=3 任务信息
 */
const updateType3TasksInConfigs = (type3Missions) => {
  for (const config of activeConfigs.value) {
    // 查找与当前配置 trendingId 匹配的 type=3 任务
    // 只显示 status=2（成功）或 status=3（失败）的任务
    const matchedTasks = type3Missions.filter(item => 
      item.mission.trendingId === config.id &&
      (item.mission.status === 2 || item.mission.status === 3)
    )
    
    if (matchedTasks.length > 0) {
      // 按更新时间排序，获取最新的任务
      const latestTask = matchedTasks.sort((a, b) => {
        const timeA = new Date(a.mission.updateTime).getTime()
        const timeB = new Date(b.mission.updateTime).getTime()
        return timeB - timeA  // 降序排序，最新的在前
      })[0]
      
      config.type3Task = {
        id: latestTask.mission.id,
        status: latestTask.mission.status,
        msg: latestTask.mission.msg,
        createTime: latestTask.mission.createTime,
        updateTime: latestTask.mission.updateTime,
        numberList: latestTask.mission.numberList
      }
      
      // 如果这个任务ID正是当前正在等待的任务，且任务已完成，清除pending标记
      if (config.pendingType3TaskId === latestTask.mission.id) {
        console.log(`配置 ${config.id} - 正在等待的任务 ${latestTask.mission.id} 已完成，清除pending标记`)
        config.pendingType3TaskId = null
        config.pendingType3TaskStartTime = null
      }
    } else {
      // 如果没有符合条件的任务，清除显示
      config.type3Task = null
    }
  }
}

/**
 * 切换自动对冲状态
 */
const toggleAutoHedge = () => {
  if (autoHedgeRunning.value) {
    stopAutoHedge()
  } else {
    startAutoHedge()
  }
}

/**
 * 开始自动对冲
 */
const startAutoHedge = () => {
  if (activeConfigs.value.length === 0) {
    alert('没有启用的主题配置')
    return
  }
  
  const hasMonitor = activeConfigs.value.some(c => c.monitorBrowserId)
  if (!hasMonitor) {
    alert('请至少为一个主题配置监听深度浏览器ID')
    return
  }
  
  autoHedgeRunning.value = true
  console.log('开始自动对冲')
  
  // 立即执行一次
  executeAutoHedgeTasks()
  
  // 每10秒检查一次任务状态
  autoHedgeInterval.value = setInterval(() => {
    executeAutoHedgeTasks()
  }, 10000)
}

/**
 * 停止自动对冲
 */
const stopAutoHedge = () => {
  autoHedgeRunning.value = false
  if (autoHedgeInterval.value) {
    clearInterval(autoHedgeInterval.value)
    autoHedgeInterval.value = null
  }
  
  // 清除所有配置的pending标记
  for (const config of activeConfigs.value) {
    if (config.pendingType3TaskId) {
      console.log(`配置 ${config.id} - 清除pending任务标记`)
      config.pendingType3TaskId = null
      config.pendingType3TaskStartTime = null
    }
  }
  
  console.log('停止自动对冲')
}

/**
 * 解析type=3任务消息，提取价格和深度信息
 */
const parseType3Message = (msg, hasSubtopic) => {
  try {
    const parts = msg.split(';')
    if (parts.length < 3) return null
    
    const firstSide = parts[0]
    const group1 = parts[1]
    const group2 = parts[2]
    
    const group1Values = group1.split(',')
    const group2Values = group2.split(',')
    
    let price1Str, price2Str, depth1, depth2
    
    if (hasSubtopic) {
      price1Str = group1Values[group1Values.length - 1].trim()
      price2Str = group2Values[0].trim()
      // 对于有子主题的，深度值在不同位置
      depth1 = group1Values.length >= 2 ? parseFloat(group1Values[1]) : 0
      depth2 = group2Values.length >= 2 ? parseFloat(group2Values[1]) : 0
    } else {
      price1Str = group1Values[0].trim()
      price2Str = group2Values[0].trim()
      // 对于无子主题的，深度值是第二个值
      depth1 = group1Values.length >= 2 ? parseFloat(group1Values[1]) : 0
      depth2 = group2Values.length >= 2 ? parseFloat(group2Values[1]) : 0
    }
    
    const price1 = parseFloat(price1Str.replace(' ¢', '').replace('¢', '').trim())
    const price2 = parseFloat(price2Str.replace(' ¢', '').replace('¢', '').trim())
    
    if (isNaN(price1) || isNaN(price2)) return null
    console.info(`${price1} ---- ${price2}`);
    return {
      firstSide,
      price1,
      price2,
      depth1,
      depth2,
      diff: Math.abs(price1 - price2),
      minPrice: Math.min(price1, price2),
      maxPrice: Math.max(price1, price2)
    }
  } catch (e) {
    console.error('解析 msg 失败:', e)
    return null
  }
}

/**
 * 检查 type=3 任务是否符合对冲条件
 */
const checkHedgeCondition = (task) => {
  if (!task || !autoHedgeRunning.value) return false
  
  if (task.status !== 2) return false
  
  const updateTime = new Date(task.updateTime)
  const now = new Date()
  const timeDiff = (now - updateTime) / 1000
  
  if (timeDiff >= 120) return false
  
  return true
}

/**
 * 显示对冲日志
 */
const showHedgeLog = (config) => {
  currentLogConfig.value = config
  hedgeLogs.value = loadHedgeLogs(config.id)
  showHedgeLogDialog.value = true
}

/**
 * 关闭对冲日志
 */
const closeHedgeLogDialog = () => {
  showHedgeLogDialog.value = false
  currentLogConfig.value = null
  hedgeLogs.value = []
}

/**
 * 加载对冲记录
 */
const loadHedgeLogs = (trendingId) => {
  try {
    const logs = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '[]')
    return logs.filter(log => log.trendingId === trendingId).reverse()
  } catch (e) {
    console.error('加载对冲日志失败:', e)
    return []
  }
}

/**
 * 显示所有对冲日志
 */
const showAllHedgeLogs = async () => {
  try {
    const logs = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '[]')
    
    // 先显示日志列表（不等待任务状态）
    allHedgeLogs.value = [...logs].reverse()  // 最新的在前面
    allHedgeLogsCurrentPage.value = 1  // 重置到第一页
    showAllHedgeLogsDialog.value = true
    
    // 只加载当前页的任务状态
    loadCurrentPageTaskStatus()
  } catch (e) {
    console.error('加载所有对冲日志失败:', e)
    alert('加载日志失败')
  }
}

/**
 * 加载当前页的任务状态
 */
const loadCurrentPageTaskStatus = async () => {
  const start = (allHedgeLogsCurrentPage.value - 1) * allHedgeLogsPageSize.value
  const end = start + allHedgeLogsPageSize.value
  const currentPageLogs = allHedgeLogs.value.slice(start, end)
  
  // 异步获取当前页每个日志的任务状态并更新
  currentPageLogs.forEach(async (log, pageIndex) => {
    const actualIndex = start + pageIndex  // 在完整列表中的实际索引
    
    // 获取YES任务详情
    if (log.yesTaskId) {
      try {
        const yesTaskData = await fetchMissionStatus(log.yesTaskId)
        if (yesTaskData) {
          allHedgeLogs.value[actualIndex].yesStatus = yesTaskData.status
          allHedgeLogs.value[actualIndex].yesTaskMsg = yesTaskData.msg || ''
        }
      } catch (e) {
        console.error(`获取YES任务 ${log.yesTaskId} 详情失败:`, e)
      }
    }
    
    // 获取NO任务详情
    if (log.noTaskId) {
      try {
        const noTaskData = await fetchMissionStatus(log.noTaskId)
        if (noTaskData) {
          allHedgeLogs.value[actualIndex].noStatus = noTaskData.status
          allHedgeLogs.value[actualIndex].noTaskMsg = noTaskData.msg || ''
        }
      } catch (e) {
        console.error(`获取NO任务 ${log.noTaskId} 详情失败:`, e)
      }
    }
  })
}

/**
 * 关闭所有对冲日志弹窗
 */
const closeAllHedgeLogsDialog = () => {
  showAllHedgeLogsDialog.value = false
  allHedgeLogs.value = []
  allHedgeLogsCurrentPage.value = 1
}

/**
 * 跳转到指定页
 */
const goToPage = (page) => {
  if (page < 1 || page > allHedgeLogsTotalPages.value) return
  allHedgeLogsCurrentPage.value = page
  loadCurrentPageTaskStatus()
}

/**
 * 上一页
 */
const prevPage = () => {
  if (allHedgeLogsCurrentPage.value > 1) {
    goToPage(allHedgeLogsCurrentPage.value - 1)
  }
}

/**
 * 下一页
 */
const nextPage = () => {
  if (allHedgeLogsCurrentPage.value < allHedgeLogsTotalPages.value) {
    goToPage(allHedgeLogsCurrentPage.value + 1)
  }
}

/**
 * 清空所有对冲日志
 */
const clearAllHedgeLogs = () => {
  if (confirm('确认要清空所有对冲日志吗？此操作不可恢复！')) {
    try {
      localStorage.removeItem(LOCAL_STORAGE_KEY)
      allHedgeLogs.value = []
      alert('已清空所有对冲日志')
    } catch (e) {
      console.error('清空日志失败:', e)
      alert('清空日志失败')
    }
  }
}

/**
 * 格式化时间（紧凑版）
 */
const formatCompactTime = (timeStr) => {
  if (!timeStr) return '-'
  try {
    const date = new Date(timeStr)
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${month}-${day} ${hours}:${minutes}`
  } catch (e) {
    return timeStr
  }
}

/**
 * 保存对冲设置到本地
 */
const saveHedgeSettings = () => {
  try {
    localStorage.setItem(HEDGE_SETTINGS_KEY, JSON.stringify({
      timePassMin: hedgeMode.timePassMin,
      intervalType: hedgeMode.intervalType,
      intervalDelay: hedgeMode.intervalDelay
    }))
  } catch (e) {
    console.error('保存对冲设置失败:', e)
  }
}

/**
 * 加载对冲设置
 */
const loadHedgeSettings = () => {
  try {
    const settings = JSON.parse(localStorage.getItem(HEDGE_SETTINGS_KEY) || '{}')
    if (settings.timePassMin !== undefined) {
      hedgeMode.timePassMin = settings.timePassMin
    }
    if (settings.intervalType !== undefined) {
      hedgeMode.intervalType = settings.intervalType
    }
    if (settings.intervalDelay !== undefined) {
      hedgeMode.intervalDelay = settings.intervalDelay
    }
  } catch (e) {
    console.error('加载对冲设置失败:', e)
  }
}

/**
 * 保存监听浏览器ID
 */
const saveMonitorBrowserIds = () => {
  try {
    const monitorData = {}
    activeConfigs.value.forEach(config => {
      if (config.monitorBrowserId) {
        monitorData[config.id] = config.monitorBrowserId
      }
    })
    localStorage.setItem(MONITOR_BROWSER_KEY, JSON.stringify(monitorData))
  } catch (e) {
    console.error('保存监听浏览器ID失败:', e)
  }
}

/**
 * 加载监听浏览器ID
 */
const loadMonitorBrowserIds = () => {
  try {
    const monitorData = JSON.parse(localStorage.getItem(MONITOR_BROWSER_KEY) || '{}')
    activeConfigs.value.forEach(config => {
      if (monitorData[config.id]) {
        config.monitorBrowserId = monitorData[config.id]
      }
    })
  } catch (e) {
    console.error('加载监听浏览器ID失败:', e)
  }
}

/**
 * 保存配置显示状态到本地存储
 * @param {Array} configList - 配置列表
 */
const saveConfigVisibleStatus = (configList) => {
  try {
    const visibleData = {}
    configList.forEach(config => {
      if (config.id) {
        visibleData[config.id] = config.visible !== false  // 默认为true
      }
    })
    localStorage.setItem(CONFIG_VISIBLE_KEY, JSON.stringify(visibleData))
    console.log('保存配置显示状态成功:', visibleData)
  } catch (e) {
    console.error('保存配置显示状态失败:', e)
  }
}

/**
 * 加载配置显示状态从本地存储
 * @param {Array} configList - 配置列表
 * @returns {Array} - 带有visible字段的配置列表
 */
const loadConfigVisibleStatus = (configList) => {
  try {
    const visibleData = JSON.parse(localStorage.getItem(CONFIG_VISIBLE_KEY) || '{}')
    return configList.map(config => ({
      ...config,
      visible: visibleData[config.id] !== false  // 默认为true
    }))
  } catch (e) {
    console.error('加载配置显示状态失败:', e)
    return configList.map(config => ({
      ...config,
      visible: true  // 失败时默认全部显示
    }))
  }
}

/**
 * 获取对冲状态文本
 */
const getHedgeStatusText = (hedge) => {
  if (!hedge) return ''
  // 优先使用 finalStatus（新版本）
  if (hedge.finalStatus === 'success') return '全部成功'
  if (hedge.finalStatus === 'failed') return '失败'
  if (hedge.finalStatus === 'running') return '进行中'
  // 兼容旧版本（没有 finalStatus 字段的记录）
  if (hedge.yesStatus === 2 && hedge.noStatus === 2) return '全部成功'
  if (hedge.yesStatus === 3 || hedge.noStatus === 3) return '部分失败'
  if (hedge.yesStatus === 9 || hedge.noStatus === 9) return '进行中'
  return '未知'
}

/**
 * 获取对冲状态样式类
 */
const getHedgeStatusClass = (hedge) => {
  if (!hedge) return ''
  // 优先使用 finalStatus（新版本）
  if (hedge.finalStatus === 'success') return 'hedge-success'
  if (hedge.finalStatus === 'failed') return 'hedge-failed'
  if (hedge.finalStatus === 'running') return 'hedge-running'
  // 兼容旧版本（没有 finalStatus 字段的记录）
  if (hedge.yesStatus === 2 && hedge.noStatus === 2) return 'hedge-success'
  if (hedge.yesStatus === 3 || hedge.noStatus === 3) return 'hedge-failed'
  if (hedge.yesStatus === 9 || hedge.noStatus === 9) return 'hedge-running'
  return ''
}

/**
 * 获取任务状态样式类
 */
const getTaskStatusClass = (status) => {
  const classMap = {
    0: 'task-pending',
    2: 'task-success',
    3: 'task-failed',
    9: 'task-running'
  }
  return classMap[status] || ''
}

/**
 * 获取对冲日志状态文本
 */
const getHedgeLogStatusText = (log) => {
  return getHedgeStatusText(log)
}

/**
 * 获取对冲日志状态样式类
 */
const getHedgeLogStatusClass = (log) => {
  return getHedgeStatusClass(log)
}

/**
 * 监控并执行对冲
 */
const monitorAndExecuteHedge = async (config) => {
  const task = config.type3Task
  if (!task) return
  
  // 检查是否已经有正在进行中的对冲任务
  if (config.currentHedge && config.currentHedge.finalStatus === 'running') {
    const startTime = new Date(config.currentHedge.startTime)
    const now = new Date()
    const elapsed = (now - startTime) / 1000 / 60  // 转换为分钟
    
    // 检查是否超过20分钟超时
    if (elapsed >= 20) {
      console.log(`配置 ${config.id} (${config.trending}) 对冲任务超时（${elapsed.toFixed(1)}分钟），强制结束`)
      config.currentHedge.finalStatus = 'timeout'
      finishHedge(config, config.currentHedge)
      // 继续执行新的对冲
    } else {
      console.log(`配置 ${config.id} (${config.trending}) 已有对冲任务正在进行中（${elapsed.toFixed(1)}/20分钟），跳过新的对冲请求`)
      return
    }
  }
  
  if (!checkHedgeCondition(task)) return
  
  const hasSubtopic = config.trending.includes('###')
  const priceInfo = parseType3Message(task.msg, hasSubtopic)
  
  if (!priceInfo) {
    console.log('价格解析失败:', task.msg)
    return
  }
  
  let orderPrice
  let canHedge = false
  
  if (priceInfo.diff > 0.15) {
    // 差值大于0.15，按原逻辑对冲
    orderPrice = ((priceInfo.price1 + priceInfo.price2)/2).toFixed(1)
    canHedge = true
    console.log(`差值充足 (${priceInfo.diff.toFixed(2)})，订单价格: ${orderPrice}`)
  } else {
    // 差值小于等于0.15，根据开仓/平仓判断
    console.log(`差值不足 (${priceInfo.diff.toFixed(2)})，检查深度条件`)
    
    if (!hedgeMode.isClose) {
      // 开仓模式：判断价格较小的一方的深度
      const smallerDepth = priceInfo.price1 < priceInfo.price2 ? priceInfo.depth1 : priceInfo.depth2
      console.log(`开仓模式，价格较小方深度: ${smallerDepth}, 最大允许深度: ${hedgeMode.maxDepth}`)
      
      if (smallerDepth < hedgeMode.maxDepth) {
        orderPrice = priceInfo.minPrice.toFixed(1)
        canHedge = true
        console.log(`深度满足条件，允许对冲，订单价格: ${orderPrice}`)
      } else {
        console.log(`深度超过限制 (${smallerDepth} >= ${hedgeMode.maxDepth})，不对冲`)
      }
    } else {
      // 平仓模式：判断价格较大的一方的深度
      const largerDepth = priceInfo.price1 > priceInfo.price2 ? priceInfo.depth1 : priceInfo.depth2
      console.log(`平仓模式，价格较大方深度: ${largerDepth}, 最大允许深度: ${hedgeMode.maxDepth}`)
      
      if (largerDepth < hedgeMode.maxDepth) {
        orderPrice = priceInfo.maxPrice.toFixed(1)
        canHedge = true
        console.log(`深度满足条件，允许对冲，订单价格: ${orderPrice}`)
      } else {
        console.log(`深度超过限制 (${largerDepth} >= ${hedgeMode.maxDepth})，不对冲`)
      }
    }
  }
  
  if (!canHedge) {
    return
  }
  
  console.log(`配置 ${config.id} 符合对冲条件，订单价格: ${orderPrice}`)
  
  // 获取当前打开显示的所有主题ID
  const trendingIds = activeConfigs.value.map(c => c.id).join(',')
  console.log(`当前打开显示的主题: ${trendingIds}`)
  
  try {
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeV2',
      {
        trendingId: config.id,
        isClose: hedgeMode.isClose,
        currentPrice: orderPrice,
        timePassMin: hedgeMode.timePassMin,
        trendingIds: trendingIds
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.data) {
      const hedgeData = response.data.data
      console.log('获取对冲双方成功:', hedgeData)
      
      await executeHedgeTask(config, {
        ...hedgeData,
        currentPrice: orderPrice,
        firstSide: priceInfo.firstSide
      })
    }
  } catch (error) {
    console.error('获取对冲双方失败:', error)
  }
}

/**
 * 执行对冲任务
 */
const executeHedgeTask = async (config, hedgeData) => {
  const firstSide = hedgeData.firstSide
  const firstBrowser = firstSide === 'YES' ? hedgeData.yesNumber : hedgeData.noNumber
  const secondBrowser = firstSide === 'YES' ? hedgeData.noNumber : hedgeData.yesNumber
  const firstPsSide = firstSide === 'YES' ? 1 : 2
  const secondPsSide = firstSide === 'YES' ? 2 : 1
  
  // 获取电脑组ID
  const yesGroupNo = browserToGroupMap.value[hedgeData.yesNumber] || '1'
  const noGroupNo = browserToGroupMap.value[hedgeData.noNumber] || '1'
  
  // 计算价格（一方是 currentPrice，另一方是 100 - currentPrice）
  const yesPrice = firstSide === 'YES' ? parseFloat(hedgeData.currentPrice) : (100 - parseFloat(hedgeData.currentPrice))
  const noPrice = firstSide === 'NO' ? parseFloat(hedgeData.currentPrice) : (100 - parseFloat(hedgeData.currentPrice))
  
  const hedgeRecord = {
    id: Date.now(),
    trendingId: config.id,
    trendingName: config.trending,
    yesNumber: hedgeData.yesNumber,
    noNumber: hedgeData.noNumber,
    yesGroupNo: yesGroupNo,
    noGroupNo: noGroupNo,
    share: hedgeMode.isClose ? hedgeData.share : (hedgeData.share * 100),  // 开仓*100，平仓用原数据
    price: hedgeData.currentPrice,
    yesPrice: yesPrice,
    noPrice: noPrice,
    firstSide: hedgeData.firstSide,
    side: hedgeMode.isClose ? 2 : 1,  // 开仓=买入(1)，平仓=卖出(2)
    isClose: hedgeMode.isClose,
    yesTaskId: null,
    noTaskId: null,
    yesStatus: null,
    noStatus: null,
    startTime: new Date().toISOString(),
    endTime: null,
    duration: null,
    secondTaskSubmitted: false,
    finalStatus: 'running'  // running, success, failed
  }
  
  config.currentHedge = hedgeRecord
  pausedType3Tasks.value.add(config.id)
  
  console.log(`开始对冲 ${config.id}:`, hedgeRecord)
  
  try {
    const groupNo = browserToGroupMap.value[firstBrowser] || '1'
    
    const taskData = {
      groupNo: groupNo,
      numberList: parseInt(firstBrowser),
      type: 5,  // 自动对冲使用 type=5
      trendingId: config.id,
      exchangeName: 'OP',
      side: hedgeMode.isClose ? 2 : 1,  // 开仓=1，平仓=2
      psSide: firstPsSide,
      amt: hedgeMode.isClose ? hedgeData.share : (hedgeData.share * 100),  // 开仓*100，平仓用原数据
      price: hedgeData.currentPrice
    }
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/add',
      taskData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.data) {
      const taskData = response.data.data
      // 确保从响应中正确提取id字段
      let taskId = null
      
      if (typeof taskData === 'object' && taskData !== null) {
        // 如果返回的是对象，提取id字段
        taskId = taskData.id
      } else if (typeof taskData === 'number' || typeof taskData === 'string') {
        // 如果直接返回的是数字或字符串ID
        taskId = taskData
      }
      
      // 确保taskId是有效的数字，且不是对象
      if (taskId === undefined || taskId === null || typeof taskId === 'object') {
        console.error('提交第一个对冲任务失败: 无效的任务ID', { taskData, taskId })
        hedgeRecord.finalStatus = 'failed'
        finishHedge(config, hedgeRecord)
        return
      }
      
      // 转换为数字
      taskId = Number(taskId)
      if (isNaN(taskId)) {
        console.error('提交第一个对冲任务失败: 任务ID不是有效数字', { taskData, taskId })
        hedgeRecord.finalStatus = 'failed'
        finishHedge(config, hedgeRecord)
        return
      }
      
      // 转换为字符串以避免传递对象
      taskId = String(taskId)
      console.log(`第一个对冲任务提交成功，任务ID: ${taskId}`)
      
      if (firstSide === 'YES') {
        hedgeRecord.yesTaskId = taskId
        hedgeRecord.yesStatus = 9
      } else {
        hedgeRecord.noTaskId = taskId
        hedgeRecord.noStatus = 9
      }
      
      // 根据事件间隔类型决定何时提交第二个任务
      if (hedgeMode.intervalType === 'delay') {
        // 延时模式：等待指定时间后直接提交第二个任务
        console.log(`[延时模式] 等待 ${hedgeMode.intervalDelay}ms 后提交第二个任务`)
        setTimeout(async () => {
          if (hedgeRecord.finalStatus === 'running' && !hedgeRecord.secondTaskSubmitted) {
            console.log(`[延时模式] 延时结束，提交第二个任务`)
            hedgeRecord.secondTaskSubmitted = true
            await submitSecondHedgeTask(config, hedgeRecord)
          }
        }, hedgeMode.intervalDelay)
      }
      
      monitorHedgeStatus(config, hedgeRecord)
    }
  } catch (error) {
    console.error('提交第一个对冲任务失败:', error)
    hedgeRecord.finalStatus = 'failed'
    finishHedge(config, hedgeRecord)
  }
}

/**
 * 获取单个任务状态
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
 * 监控对冲状态
 */
const monitorHedgeStatus = (config, hedgeRecord) => {
  const startTime = new Date(hedgeRecord.startTime)
  
  const checkStatus = async () => {
    // 检查是否已完成
    if (hedgeRecord.finalStatus !== 'running') {
      return
    }
    
    const now = new Date()
    const elapsed = (now - startTime) / 1000 / 60
    
    // 检查20分钟超时
    if (elapsed >= 20) {
      console.log(`对冲 ${hedgeRecord.id} 超时（${elapsed.toFixed(1)}分钟）- YES任务状态: ${hedgeRecord.yesStatus}, NO任务状态: ${hedgeRecord.noStatus}`)
      hedgeRecord.finalStatus = 'timeout'
      finishHedge(config, hedgeRecord)
      return
    }
    
    // 通过新接口获取任务状态
    if (hedgeRecord.yesTaskId) {
      const yesTaskData = await fetchMissionStatus(hedgeRecord.yesTaskId)
      if (yesTaskData) {
        const oldStatus = hedgeRecord.yesStatus
        hedgeRecord.yesStatus = yesTaskData.status
        if (oldStatus !== yesTaskData.status) {
          console.log(`[monitorHedgeStatus] YES任务 ${hedgeRecord.yesTaskId} 状态变化: ${oldStatus} -> ${yesTaskData.status}`)
        }
      }
    }
    
    if (hedgeRecord.noTaskId) {
      const noTaskData = await fetchMissionStatus(hedgeRecord.noTaskId)
      if (noTaskData) {
        const oldStatus = hedgeRecord.noStatus
        hedgeRecord.noStatus = noTaskData.status
        if (oldStatus !== noTaskData.status) {
          console.log(`[monitorHedgeStatus] NO任务 ${hedgeRecord.noTaskId} 状态变化: ${oldStatus} -> ${noTaskData.status}`)
        }
      }
    }
    
    const firstSide = hedgeRecord.firstSide
    const firstStatus = firstSide === 'YES' ? hedgeRecord.yesStatus : hedgeRecord.noStatus
    const secondStatus = firstSide === 'YES' ? hedgeRecord.noStatus : hedgeRecord.yesStatus
    
    console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} - 第一个任务(${firstSide})状态: ${firstStatus}, 第二个任务已提交: ${hedgeRecord.secondTaskSubmitted}`)
    
    // 检查第一个任务是否失败
    if (firstStatus === 3) {
      console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} 任务一失败，等待任务二完成或超时`)
      // 不立即停止，等待第二个任务也完成（如果已提交）
      if (hedgeRecord.secondTaskSubmitted) {
        // 如果第二个任务也已完成（成功或失败），则结束对冲
        if (secondStatus === 2 || secondStatus === 3) {
          console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} 两个任务都已完成（任务一失败，任务二状态: ${secondStatus}）`)
          hedgeRecord.finalStatus = 'failed'
          finishHedge(config, hedgeRecord)
          return
        }
      } else {
        // 第二个任务还未提交，且第一个任务失败，直接结束
        console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} 任务一失败且任务二未提交，立即停止`)
        hedgeRecord.finalStatus = 'failed'
        finishHedge(config, hedgeRecord)
        return
      }
    }
    
    // 第一个任务成功，提交第二个任务（仅在挂单成功模式下）
    if (firstStatus === 2 && !hedgeRecord.secondTaskSubmitted && hedgeMode.intervalType === 'success') {
      console.log(`[挂单成功模式] 对冲 ${hedgeRecord.id} 任务一成功，开始任务二`)
      hedgeRecord.secondTaskSubmitted = true
      await submitSecondHedgeTask(config, hedgeRecord)
    }
    
    // 第二个任务已提交，检查第二个任务状态
    if (hedgeRecord.secondTaskSubmitted) {
      // 检查第二个任务是否失败
      if (secondStatus === 3) {
        console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} 任务二失败`)
        // 检查第一个任务是否也已完成
        if (firstStatus === 2 || firstStatus === 3) {
          console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} 两个任务都已完成（任务一状态: ${firstStatus}，任务二失败）`)
          hedgeRecord.finalStatus = 'failed'
          finishHedge(config, hedgeRecord)
          return
        }
      }
      
      // 两个任务都成功
      if (firstStatus === 2 && secondStatus === 2) {
        console.log(`[monitorHedgeStatus] 对冲 ${hedgeRecord.id} 两个任务都成功`)
        hedgeRecord.finalStatus = 'success'
        finishHedge(config, hedgeRecord)
        return
      }
    }
    
    setTimeout(checkStatus, 5000)
  }
  
  checkStatus()
}

/**
 * 提交第二个对冲任务
 */
const submitSecondHedgeTask = async (config, hedgeRecord) => {
  const secondSide = hedgeRecord.firstSide === 'YES' ? 'NO' : 'YES'
  const secondBrowser = secondSide === 'YES' ? hedgeRecord.yesNumber : hedgeRecord.noNumber
  const secondPsSide = secondSide === 'YES' ? 1 : 2
  
  try {
    const groupNo = browserToGroupMap.value[secondBrowser] || '1'
    
    // 任务二的价格 = 100 - 任务一的价格
    const secondPrice = (100 - parseFloat(hedgeRecord.price)).toFixed(1)
    console.log(`任务二价格计算: 100 - ${hedgeRecord.price} = ${secondPrice}`)
    
    // 获取第一个任务的ID
    const firstTaskId = hedgeRecord.firstSide === 'YES' ? hedgeRecord.yesTaskId : hedgeRecord.noTaskId
    
    const taskData = {
      groupNo: groupNo,
      numberList: parseInt(secondBrowser),
      type: 5,  // 自动对冲使用 type=5
      trendingId: config.id,
      exchangeName: 'OP',
      side: hedgeRecord.isClose ? 2 : 1,  // 开仓=1，平仓=2
      psSide: secondPsSide,
      amt: hedgeRecord.share,
      price: parseFloat(secondPrice),
      tp1: firstTaskId  // 任务二需要传递任务一的ID
    }
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/add',
      taskData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.data) {
      const taskData = response.data.data
      // 确保从响应中正确提取id字段
      let taskId = null
      
      if (typeof taskData === 'object' && taskData !== null) {
        // 如果返回的是对象，提取id字段
        taskId = taskData.id
      } else if (typeof taskData === 'number' || typeof taskData === 'string') {
        // 如果直接返回的是数字或字符串ID
        taskId = taskData
      }
      
      // 确保taskId是有效的数字，且不是对象
      if (taskId === undefined || taskId === null || typeof taskId === 'object') {
        console.error('提交第二个对冲任务失败: 无效的任务ID', { taskData, taskId })
        hedgeRecord.finalStatus = 'failed'
        finishHedge(config, hedgeRecord)
        return
      }
      
      // 转换为数字
      taskId = Number(taskId)
      if (isNaN(taskId)) {
        console.error('提交第二个对冲任务失败: 任务ID不是有效数字', { taskData, taskId })
        hedgeRecord.finalStatus = 'failed'
        finishHedge(config, hedgeRecord)
        return
      }
      
      // 转换为字符串以避免传递对象
      taskId = String(taskId)
      console.log(`第二个对冲任务提交成功，任务ID: ${taskId}`)
      
      if (secondSide === 'YES') {
        hedgeRecord.yesTaskId = taskId
        hedgeRecord.yesStatus = 9
      } else {
        hedgeRecord.noTaskId = taskId
        hedgeRecord.noStatus = 9
      }
    } else {
      console.error('提交第二个对冲任务失败: 无任务ID返回')
      hedgeRecord.finalStatus = 'failed'
      finishHedge(config, hedgeRecord)
    }
  } catch (error) {
    console.error('提交第二个对冲任务失败:', error)
    hedgeRecord.finalStatus = 'failed'
    finishHedge(config, hedgeRecord)
  }
}

/**
 * 完成对冲
 */
const finishHedge = (config, hedgeRecord) => {
  // 防止重复调用
  if (hedgeRecord.endTime) {
    console.log(`对冲 ${hedgeRecord.id} 已经完成，跳过重复处理`)
    return
  }
  
  hedgeRecord.endTime = new Date().toISOString()
  
  const startTime = new Date(hedgeRecord.startTime)
  const endTime = new Date(hedgeRecord.endTime)
  hedgeRecord.duration = Math.round((endTime - startTime) / 1000 / 60)
  
  // 保存日志到本地
  saveHedgeLog(hedgeRecord)
  
  // 解除暂停状态，允许新的对冲任务
  pausedType3Tasks.value.delete(config.id)
  
  console.log(`对冲 ${hedgeRecord.id} 已结束，状态: ${hedgeRecord.finalStatus}，用时: ${hedgeRecord.duration}分钟，YES状态: ${hedgeRecord.yesStatus}, NO状态: ${hedgeRecord.noStatus}，日志已保存`)
  
  // 清除当前对冲记录，允许新的对冲任务开始
  // 注意：清除后下次循环就可以开始新的对冲了
  config.currentHedge = null
}

/**
 * 保存对冲记录到本地存储
 */
const saveHedgeLog = (hedgeRecord) => {
  try {
    const logs = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '[]')
    logs.push(hedgeRecord)
    
    if (logs.length > 500) {
      logs.splice(0, logs.length - 500)
    }
    
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(logs))
  } catch (e) {
    console.error('保存对冲日志失败:', e)
  }
}

/**
 * 获取对冲状态
 */
const fetchHedgeStatus = async () => {
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/hedge/status')
    
    if (response.data && response.data.data) {
      const data = response.data.data
      hedgeStatus.amtSum = data.amtSum || 0
      hedgeStatus.amt = data.amt || 0
      console.log('对冲状态已更新:', hedgeStatus)
    }
  } catch (error) {
    console.error('获取对冲状态失败:', error)
  }
}

/**
 * 更新对冲数量
 */
const updateHedgeAmount = async () => {
  try {
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/updateHedge',
      { amt: hedgeStatus.amt },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('对冲数量更新成功')
      showToast('对冲数量更新成功')
      // 更新状态
      fetchHedgeStatus()
    }
  } catch (error) {
    console.error('更新对冲数量失败:', error)
    showToast('更新对冲数量失败', 'error')
  }
}

/**
 * 清空当前已开
 */
const cleanHedgeAmount = async () => {
  if (!confirm('确定要清空当前已开的对冲数量吗？')) {
    return
  }
  
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/hedge/cleanAmt')
    
    if (response.data) {
      console.log('清空成功')
      showToast('清空成功')
      // 更新状态
      fetchHedgeStatus()
    }
  } catch (error) {
    console.error('清空失败:', error)
    showToast('清空失败', 'error')
  }
}

/**
 * 查询交易费
 */
const queryTransactionFee = async () => {
  if (!feeQuery.startTime || !feeQuery.endTime) {
    showToast('请选择开始和结束时间', 'warning')
    return
  }
  
  try {
    // 将 datetime-local 格式转换为时间戳
    const startTimestamp = new Date(feeQuery.startTime).getTime()
    const endTimestamp = new Date(feeQuery.endTime).getTime()
    
    if (startTimestamp >= endTimestamp) {
      showToast('开始时间必须早于结束时间', 'warning')
      return
    }
    
    // 调用新的 listPart 接口
    const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/listPart', {
      params: {
        type: 5,
        startTime: startTimestamp,
        endTime: endTimestamp
      }
    })
    
    if (response.data && response.data.code === 0) {
      const missions = response.data.data.list || []
      let totalFee = 0
      
      // 遍历所有任务
      missions.forEach(item => {
        const mission = item.mission
        // 只处理状态为2（成功）的任务
        if (mission && mission.status === 2 && mission.msg) {
          try {
            // 解析 msg JSON
            const msgData = JSON.parse(mission.msg)
            if (msgData.transaction_fee) {
              // 提取交易费数字部分（移除 $ 符号和逗号）
              const feeStr = msgData.transaction_fee.replace(/[$,]/g, '')
              const fee = parseFloat(feeStr) || 0
              totalFee += fee
            }
          } catch (error) {
            console.error('解析任务消息失败:', mission.id, error)
          }
        }
      })
      
      feeQuery.totalFee = totalFee
      showToast(`查询成功，共 ${missions.length} 个任务`, 'success')
    } else {
      showToast('查询失败', 'error')
    }
  } catch (error) {
    console.error('查询交易费失败:', error)
    showToast('查询交易费失败: ' + (error.message || '未知错误'), 'error')
  }
}

/**
 * 执行自动对冲任务
 */
const executeAutoHedgeTasks = async () => {
  console.log('执行自动对冲任务...')
  
  // 检查是否可以下发新的对冲任务
  const canStartNewHedge = !(hedgeStatus.amtSum >= hedgeStatus.amt || hedgeStatus.amt === 0)
  if (!canStartNewHedge) {
    console.log('对冲数量已满或总数量为0，不下发新对冲任务')
  }
  
  for (const config of activeConfigs.value) {
    // 检查该主题是否正在执行对冲
    if (pausedType3Tasks.value.has(config.id)) {
      // 检查是否超时
      if (config.currentHedge && config.currentHedge.finalStatus === 'running') {
        const startTime = new Date(config.currentHedge.startTime)
        const now = new Date()
        const elapsed = (now - startTime) / 1000 / 60
        
        if (elapsed >= 20) {
          console.log(`配置 ${config.id} 对冲任务超时（${elapsed.toFixed(1)}分钟），强制结束`)
          config.currentHedge.finalStatus = 'timeout'
          finishHedge(config, config.currentHedge)
          // 继续执行，可以开始新的对冲
        } else {
          console.log(`配置 ${config.id} 正在执行对冲（${elapsed.toFixed(1)}/20分钟），跳过`)
          continue
        }
      } else {
        // pausedType3Tasks中有但currentHedge不在运行中，清理状态
        console.log(`配置 ${config.id} pausedType3Tasks状态不一致，清理`)
        pausedType3Tasks.value.delete(config.id)
      }
    }
    
    // 只有在可以开始新对冲时才执行
    if (!canStartNewHedge) {
      continue
    }
    
    // 先尝试监控并执行对冲
    await monitorAndExecuteHedge(config)
    
    // 如果没有监听浏览器ID，跳过
    if (!config.monitorBrowserId) {
      continue
    }
    
    // 检查是否有正在进行的 type=3 任务
    if (config.pendingType3TaskId) {
      const taskId = config.pendingType3TaskId
      const startTime = config.pendingType3TaskStartTime
      const now = Date.now()
      const elapsed = (now - startTime) / 1000 / 60  // 转换为分钟
      
      // 获取任务状态
      try {
        const taskData = await fetchMissionStatus(taskId)
        
        if (taskData) {
          const status = taskData.status
          console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 状态: ${status}, 已用时: ${elapsed.toFixed(1)}分钟`)
          
          // 任务已完成（成功或失败）
          if (status === 2 || status === 3) {
            console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 已完成，清除标记`)
            config.pendingType3TaskId = null
            config.pendingType3TaskStartTime = null
            // 继续执行，会在下面提交新任务
          }
          // 任务超时（超过3分钟）
          else if (elapsed >= 3) {
            console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 超时（${elapsed.toFixed(1)}分钟），清除标记`)
            config.pendingType3TaskId = null
            config.pendingType3TaskStartTime = null
            // 继续执行，会在下面提交新任务
          }
          // 任务还在进行中
          else {
            console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 还在进行中，跳过`)
            continue  // 跳过，不提交新任务
          }
        } else {
          // 无法获取任务状态，检查超时
          if (elapsed >= 3) {
            console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 无法获取状态且超时，清除标记`)
            config.pendingType3TaskId = null
            config.pendingType3TaskStartTime = null
          } else {
            console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 无法获取状态，继续等待`)
            continue
          }
        }
      } catch (error) {
        console.error(`获取任务 ${taskId} 状态失败:`, error)
        // 检查超时
        if (elapsed >= 3) {
          console.log(`配置 ${config.id} - Type=3 任务 ${taskId} 获取状态失败且超时，清除标记`)
          config.pendingType3TaskId = null
          config.pendingType3TaskStartTime = null
        } else {
          continue
        }
      }
    }
    
    // 如果没有正在进行的任务（或任务已完成/超时），提交新的 type=3 任务
    if (!config.pendingType3TaskId) {
      try {
        // 提交 type=3 任务
        const taskData = {
          groupNo: browserToGroupMap.value[config.monitorBrowserId],
          numberList: config.monitorBrowserId,
          type: 3,
          trendingId: String(config.id),
          exchangeName: 'OP',
          side: hedgeMode.isClose ? 2 : 1  // 平仓时为Sell，开仓时为Buy
        }
        
        console.log(`配置 ${config.id} - 提交新的 type=3 任务 (${taskData.side}):`, taskData)
        
        const response = await axios.post(
          'https://sg.bicoin.com.cn/99l/mission/add',
          taskData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data && response.data.data) {
          const taskData = response.data.data
          // 确保从响应中正确提取id字段
          let taskId = null
          
          if (typeof taskData === 'object' && taskData !== null) {
            // 如果返回的是对象，提取id字段
            taskId = taskData.id
          } else if (typeof taskData === 'number' || typeof taskData === 'string') {
            // 如果直接返回的是数字或字符串ID
            taskId = taskData
          }
          
          // 确保taskId是有效的数字或字符串，且不是对象
          if (taskId === undefined || taskId === null || typeof taskId === 'object') {
            console.error(`配置 ${config.id} - type=3 任务提交失败: 无效的任务ID`, { taskData, taskId })
          } else {
            // 转换为数字（确保不会传递对象或字符串对象）
            taskId = Number(taskId)
            
            if (isNaN(taskId)) {
              console.error(`配置 ${config.id} - type=3 任务提交失败: 任务ID不是有效数字`, taskData)
            } else {
              config.pendingType3TaskId = taskId
              config.pendingType3TaskStartTime = Date.now()
              console.log(`配置 ${config.id} - type=3 任务提交成功，任务ID: ${taskId}`)
            }
          }
        }
      } catch (error) {
        console.error(`配置 ${config.id} - 提交任务失败:`, error)
      }
    }
  }
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    0: '待处理',
    1: '处理中',
    2: '成功',
    3: '失败',
    9: '进行中'
  }
  return statusMap[status] || `状态${status}`
}

/**
 * 获取状态样式类
 */
const getStatusClass = (status) => {
  const classMap = {
    0: 'status-pending',
    1: 'status-running',
    2: 'status-completed',
    3: 'status-failed',
    9: 'status-running'
  }
  return classMap[status] || 'status-unknown'
}

/**
 * 重试失败的任务
 */
const retryMission = async (item) => {
  if (isRetrying.value) {
    return
  }
  
  const mission = item.mission
  
  // 确认是否重试
  if (!confirm(`确认重试任务 #${mission.id}？`)) {
    return
  }
  
  isRetrying.value = true
  
  try {
    // 构建重试任务数据
    const submitData = {
      groupNo: mission.groupNo,
      numberList: parseInt(mission.numberList),
      type: parseInt(mission.type),
      trendingId: parseInt(mission.trendingId),
      exchangeName: mission.exchangeName,
      side: parseInt(mission.side),
      psSide: parseInt(mission.psSide),
      amt: parseFloat(mission.amt)
    }
    
    // 如果有价格，则添加价格字段
    if (mission.price !== null && mission.price !== undefined && mission.price !== '') {
      submitData.price = parseFloat(mission.price)
    }
    
    console.log('正在重试任务...', submitData)
    
    // 发送请求
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/add',
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('任务重试成功！响应:', response.data)
      alert('任务重试成功！')
      
      // 刷新任务列表
      setTimeout(() => {
        fetchMissionList()
      }, 500)
    }
  } catch (error) {
    console.error('重试失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    alert(`任务重试失败: ${errorMsg}`)
  } finally {
    isRetrying.value = false
  }
}

/**
 * 获取类型文本
 */
const getTypeText = (type) => {
  const typeMap = {
    1: '下单'
  }
  return typeMap[type] || `类型${type}`
}

/**
 * 获取方向文本
 */
const getSideText = (side) => {
  if (side === null || side === undefined) return '-'
  const sideMap = {
    1: '买入',
    2: '卖出'
  }
  return sideMap[side] || `方向${side}`
}

/**
 * 获取预测方向文本
 */
const getPsSideText = (psSide) => {
  if (psSide === null || psSide === undefined) return '-'
  const psSideMap = {
    1: 'Yes',
    2: 'No'
  }
  return psSideMap[psSide] || `${psSide}`
}

/**
 * 格式化时间
 */
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
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
 * 格式化任务消息（支持JSON格式的Type 5消息）
 */
/**
 * 格式化任务消息显示
 * @param {string} msg - 任务消息JSON字符串
 * @returns {string} - 格式化后的消息文本
 */
const formatTaskMsg = (msg) => {
  if (!msg) return ''
  
  // 尝试解析JSON格式的Type 5消息
  try {
    const data = JSON.parse(msg)
    
    if (data.type === 'TYPE5_SUCCESS') {
      // Type 5 成功：全部成交
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
    } else if (data.type === 'TYPE5_PARTIAL') {
      // Type 5 部分成交：有挂单
      let result = `⚠️ 部分成交`
      
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
        const initialAmount = parseFloat(data.initial_filled_amount) || 0
        let filledAmount = 0
        if (typeof data.filled_amount === 'string' && data.filled_amount.includes('<')) {
          filledAmount = 0
        } else {
          filledAmount = parseFloat(data.filled_amount) || 0
        }
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
}

// 定时刷新
let refreshInterval = null

/**
 * 启动自动刷新定时器
 */
const startAutoRefresh = () => {
  // 清除旧的定时器
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
  
  // 如果启用了自动刷新，创建新的定时器
  if (autoRefresh.enabled && autoRefresh.interval > 0) {
    const intervalMs = autoRefresh.interval * 1000
    refreshInterval = setInterval(() => {
      fetchMissionList()
    }, intervalMs)
    console.log(`自动刷新已启动，间隔: ${autoRefresh.interval}秒`)
  }
}

/**
 * 切换自动刷新
 */
const toggleAutoRefresh = () => {
  if (autoRefresh.enabled) {
    startAutoRefresh()
  } else {
    // 关闭自动刷新
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
    console.log('自动刷新已关闭')
  }
}

/**
 * 重置自动刷新（间隔时间改变时）
 */
const resetAutoRefresh = () => {
  if (autoRefresh.enabled) {
    startAutoRefresh()
  }
}

onMounted(() => {
  isConnected.value = true
  console.log('任务管理系统已启动')
  
  // 初始化交易费查询时间
  initFeeQueryTime()
  
  // 加载对冲设置
  loadHedgeSettings()
  
  // 加载账户配置（浏览器编号和组号映射）
  fetchAccountConfig()
  
  // 加载配置
  fetchExchangeConfig()
  
  // 初始加载任务列表
  fetchMissionList()
  
  // 初始加载对冲记录
  fetchHedgeHistory()
  
  // 启动自动刷新（默认启用，10秒间隔）
  startAutoRefresh()
  
  // 获取对冲状态
  fetchHedgeStatus()
  
  // 启动对冲状态定时刷新（每30秒）
  hedgeStatusInterval.value = setInterval(() => {
    fetchHedgeStatus()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (autoHedgeInterval.value) {
    clearInterval(autoHedgeInterval.value)
  }
  if (hedgeStatusInterval.value) {
    clearInterval(hedgeStatusInterval.value)
  }
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.top-header {
  background: rgba(255, 255, 255, 0.95);
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.top-header h1 {
  font-size: 1.8rem;
  color: #333;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.btn-header {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
}

.btn-header:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.header {
  background: rgba(255, 255, 255, 0.95);
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 1.8rem;
  color: #333;
  font-weight: 600;
}

.status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ccc;
  transition: background 0.3s;
}

.status-dot.active {
  background: #4caf50;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
}

.main {
  padding: 2rem;
}

.container {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  gap: 2rem;
}

.form-sections {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

@media (max-width: 1024px) {
  .form-sections {
    grid-template-columns: 1fr;
  }
}

.section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.auto-hedge-section {
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.auto-hedge-section h2 {
  color: white;
  margin-bottom: 1rem;
}

.section-header-with-filter {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 15px;
}

.section-header-with-filter h2 {
  margin: 0;
}

.trending-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trending-filter label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  white-space: nowrap;
}

.trending-filter .filter-input {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  font-size: 14px;
  width: 250px;
  background: rgba(255, 255, 255, 0.95);
  color: #333;
}

.trending-filter .filter-input:focus {
  outline: none;
  border-color: white;
  background: white;
}

.auto-hedge-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.hedge-amount-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.hedge-amount-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.transaction-fee-query {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.time-range-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.time-input {
  padding: 0.4rem 0.8rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  font-size: 0.875rem;
}

.time-separator {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.fee-result {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(40, 167, 69, 0.2);
  border-radius: 4px;
  border: 1px solid rgba(40, 167, 69, 0.4);
}

.fee-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.fee-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #4caf50;
}

.amount-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.amount-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
}

.amount-input {
  width: 150px;
  padding: 0.4rem 0.8rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  font-size: 1rem;
}

.btn-sm {
  padding: 0.4rem 0.8rem;
  font-size: 0.875rem;
}

.btn-running {
  background: #dc3545;
}

.btn-running:hover {
  background: #c82333;
}

.btn-warning {
  background: #ffc107;
  color: #333;
}

.btn-warning:hover {
  background: #e0a800;
}

.trending-list {
  margin-top: 1rem;
}

.trending-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.trending-item {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.trending-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.trending-name {
  font-weight: 600;
  flex: 1;
}

.monitor-input {
  flex: 1;
  max-width: 250px;
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 0.875rem;
}

.monitor-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.monitor-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.3);
}

.monitor-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.orderbook-result {
  font-size: 0.875rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  word-break: break-all;
}

.result-label {
  color: rgba(255, 255, 255, 0.8);
  margin-right: 0.5rem;
}

.result-data {
  font-family: monospace;
}

.type3-task-info {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  border-left: 3px solid rgba(255, 255, 255, 0.5);
}

.task-status-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.task-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.task-browser {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.task-status-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.task-status-badge.status-completed {
  background: #28a745;
  color: white;
}

.task-status-badge.status-failed {
  background: #dc3545;
  color: white;
}

.task-status-badge.status-running {
  background: #ffc107;
  color: #333;
}

.task-status-badge.status-pending {
  background: #6c757d;
  color: white;
}

.task-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  margin-left: auto;
}

.task-msg {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  word-break: break-all;
  white-space: pre-wrap;
  word-wrap: break-word;
  flex: 1 1 100%;
  max-width: 100%;
  min-width: 0;
}

.msg-label {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  margin-right: 0.5rem;
}

.msg-content {
  font-family: monospace;
  font-size: 0.8rem;
}

.empty-message {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  padding: 1rem;
}

/* 对冲模式开关 */
.hedge-mode-switch {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.mode-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

/* 时间过滤输入框 */
.hedge-time-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.filter-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
}

.time-input {
  width: 80px;
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #2c3e50;
  font-size: 0.875rem;
  text-align: center;
}

.time-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

.time-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 事件间隔设置 */
.hedge-interval-setting {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  flex-wrap: wrap;
}

.radio-group-inline {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.radio-label-inline {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
}

.radio-label-inline input[type="radio"] {
  cursor: pointer;
}

.radio-label-inline input[type="radio"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.radio-label-inline span {
  font-weight: 500;
}

.delay-input {
  width: 100px;
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #2c3e50;
  font-size: 0.875rem;
  text-align: center;
}

.delay-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

.delay-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 最大允许深度设置 */
.hedge-depth-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.depth-input {
  width: 100px;
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #2c3e50;
  font-size: 0.875rem;
  text-align: center;
}

.depth-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

.depth-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Trending 头部布局 */
.trending-header {
  margin-bottom: 1rem;
}

.trending-name-row {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0;
}

.btn-log {
  padding: 0.3rem 0.6rem;
  background: rgba(255, 255, 255, 0.3);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
}

.btn-log:hover {
  background: rgba(255, 255, 255, 0.4);
}

/* Type 3 任务和对冲信息容器 */
.task-hedge-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

.type3-task-section,
.hedge-info-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 0.75rem;
}

.section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}

.no-data {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.875rem;
  padding: 1rem 0;
}

/* 对冲信息样式 */
.hedge-info {
  font-size: 0.875rem;
}

.hedge-status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.hedge-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.hedge-status-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

.hedge-success {
  background: #28a745;
  color: white;
}

.hedge-failed {
  background: #dc3545;
  color: white;
}

.hedge-running {
  background: #ffc107;
  color: #333;
}

.hedge-details {
  margin: 0.5rem 0;
}

.hedge-detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  font-size: 0.8rem;
}

.hedge-time {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 0.5rem;
}

/* 对冲任务分段显示 */
.hedge-task-section {
  margin: 0.75rem 0;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  border-left: 3px solid rgba(255, 255, 255, 0.3);
}

.hedge-task-section .task-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hedge-task-section .task-amount {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: normal;
}

.hedge-task-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.hedge-task-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.hedge-summary {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: 0.5rem;
  padding-top: 0.5rem;
}

.task-pending {
  color: #6c757d;
}

.task-success {
  color: #28a745;
}

.task-failed {
  color: #dc3545;
}

.task-running {
  color: #ffc107;
}

/* 对冲日志弹窗样式 */
.hedge-log-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 1rem;
}

.hedge-log-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hedge-log-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid #667eea;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #dee2e6;
}

.log-id {
  font-weight: 600;
  color: #333;
}

.log-status-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.log-time {
  font-size: 0.75rem;
  color: #6c757d;
}

.log-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.log-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
}

.log-label {
  font-weight: 500;
  color: #6c757d;
}

/* 总日志弹窗样式 */
.all-hedge-log-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 1rem;
}

.all-hedge-log-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.compact-hedge-log-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 0.75rem;
  border-left: 4px solid #667eea;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.compact-hedge-log-item:hover {
  background: #e9ecef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.compact-hedge-log-item.log-status-success {
  border-left-color: #28a745;
}

.compact-hedge-log-item.log-status-failed {
  border-left-color: #dc3545;
}

.compact-hedge-log-item.log-status-timeout {
  border-left-color: #ffc107;
}

.compact-log-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.compact-log-id {
  font-weight: 700;
  color: #495057;
  min-width: 40px;
}

.compact-log-trending {
  font-weight: 600;
  color: #212529;
  flex: 1;
  min-width: 150px;
}

.compact-status-badge {
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.compact-log-mode {
  padding: 0.15rem 0.5rem;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.compact-log-info {
  color: #6c757d;
  font-size: 0.8rem;
}

.compact-log-time {
  color: #6c757d;
  font-size: 0.75rem;
  white-space: nowrap;
}

.compact-log-duration {
  color: #667eea;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.compact-log-details {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding-left: 1rem;
  border-left: 2px solid #dee2e6;
}

.compact-task-row {
  display: flex;
  gap: 0.5rem;
  font-size: 0.8rem;
  flex-wrap: wrap;
  width: 100%;
}

.task-label {
  font-weight: 600;
  color: #495057;
  min-width: 35px;
}

.task-info {
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.task-group {
  font-weight: 600;
  color: #667eea;
  background: #e7eaf7;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.task-msg {
  color: #dc3545;
  font-style: italic;
  word-wrap: break-word;
  white-space: pre-wrap;
  flex: 1 1 100%;
  max-width: 100%;
  min-width: 0;
}

.task-success {
  color: #28a745;
  font-weight: 600;
}

.task-failed {
  color: #dc3545;
  font-weight: 600;
}

.task-running {
  color: #ffc107;
  font-weight: 600;
}

.task-unknown {
  color: #6c757d;
}

/* 分页控件样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-top: 1px solid #dee2e6;
  background: #f8f9fa;
}

.pagination-info {
  font-size: 0.875rem;
  color: #495057;
  font-weight: 500;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.btn-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auto-refresh-status {
  color: #667eea;
  font-weight: 500;
  font-size: 0.875rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #667eea;
}

.section-header h2 {
  margin: 0;
}

.refresh-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.auto-refresh-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #333;
  user-select: none;
}

.auto-refresh-label input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.refresh-interval {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.interval-input {
  width: 70px;
  padding: 0.4rem 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  text-align: center;
  transition: all 0.3s;
}

.interval-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.interval-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

.interval-unit {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.section h2 {
  font-size: 1.3rem;
  color: #333;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #667eea;
}

.btn-refresh {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-refresh:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty {
  text-align: center;
  color: #999;
  padding: 2rem;
  font-size: 0.9rem;
}

.loading-message {
  text-align: center;
  padding: 2rem;
  color: #667eea;
  font-size: 1rem;
}

/* 表单样式 */
.task-form,
.hedge-form {
  display: grid;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.3s;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input::placeholder {
  color: #999;
}

.group-no-display {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  background-color: #f5f5f5;
  color: #333;
  min-height: 50px;
  display: flex;
  align-items: center;
}

.form-group select:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.7;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.btn {
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-info {
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
}

.btn-info:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(23, 162, 184, 0.4);
}

/* 单选框样式 */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: #333;
}

.radio-label input[type="radio"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

.radio-label span {
  user-select: none;
}

/* 任务列表样式 */
.mission-list {
  display: grid;
  gap: 1.5rem;
  max-height: 900px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.mission-list::-webkit-scrollbar {
  width: 8px;
}

.mission-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.mission-list::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.mission-list::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.mission-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s;
  background: #fafafa;
}

.mission-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.mission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e0e0e0;
}

.mission-title {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.mission-id {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.mission-status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-running {
  background: #d1ecf1;
  color: #0c5460;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.status-failed {
  background: #f8d7da;
  color: #721c24;
}

.status-cancelled {
  background: #f8d7da;
  color: #721c24;
}

.status-unknown {
  background: #e0e0e0;
  color: #666;
}

.mission-time {
  font-size: 0.85rem;
  color: #999;
}

.mission-body {
  display: grid;
  gap: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-item .label {
  font-weight: 500;
  color: #666;
  font-size: 0.9rem;
}

.info-item .value {
  color: #333;
  font-size: 0.9rem;
}

.exchange-info {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.trending-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.75rem;
  font-size: 0.95rem;
}

.url-links {
  display: flex;
  gap: 0.75rem;
}

.link-btn {
  padding: 0.4rem 0.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.link-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.mission-msg {
  background: #fff3cd;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid #ffc107;
  display: flex;
  gap: 0.5rem;
}

.mission-msg .label {
  font-weight: 500;
  color: #856404;
}

.mission-msg .value {
  color: #856404;
  flex: 1;
}

/* 任务操作按钮区域 */
.mission-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.btn-retry {
  padding: 0.5rem 1.2rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
  font-weight: 500;
}

.btn-retry:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.btn-retry:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 0;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-content.large {
  max-width: 900px;
}

.modal-content.extra-large {
  max-width: 1200px;
  max-height: 90vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.modal-close:hover {
  color: #333;
}

.modal-form {
  padding: 2rem;
  display: grid;
  gap: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e0e0e0;
  justify-content: flex-end;
}

.config-filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.config-filter-toolbar .trending-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-filter-toolbar .trending-filter label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.config-filter-toolbar .filter-input {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  width: 250px;
}

.config-filter-toolbar .filter-input:focus {
  outline: none;
  border-color: #007bff;
}

.config-list {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
}

.config-items {
  display: grid;
  gap: 1.5rem;
}

.config-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  background: #fafafa;
}

.config-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.config-index {
  font-size: 1.1rem;
  font-weight: 600;
  color: #667eea;
}

.switch-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0;
}

.switch-label-row .label-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.switch-checkbox {
  display: none;
}

.switch-slider {
  position: relative;
  width: 44px;
  height: 22px;
  background: #ccc;
  border-radius: 22px;
  transition: background 0.3s;
}

.switch-slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 2px;
  top: 2px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s;
}

.switch-checkbox:checked + .switch-slider {
  background: #667eea;
}

.switch-checkbox:checked + .switch-slider::before {
  transform: translateX(22px);
}

.switch-text {
  font-size: 0.875rem;
  color: #333;
}

.btn-remove {
  padding: 0.4rem 0.8rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.btn-remove:hover {
  background: #c82333;
}

/* 对冲标题和状态 */
.hedge-title-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.hedge-status-display {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.hedge-task-status {
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
}

/* Toast 提示 */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-info {
  background: #17a2b8;
}

.toast-success {
  background: #28a745;
}

.toast-warning {
  background: #ffc107;
  color: #333;
}

.toast-error {
  background: #dc3545;
}
</style>

