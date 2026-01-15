<template>
  <div class="app">
    <header class="top-header">
      <h1>页面1-对冲</h1>
      <div class="header-actions">
        <div style="display: inline-flex; align-items: center; gap: 8px; margin-right: 10px;">
          <label style="font-size: 14px;">yes数量大于:</label>
          <input 
            v-model.number="yesCountThreshold" 
            type="number" 
            min="0"
            step="0.01"
            placeholder="输入阈值"
            style="width: 120px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
          />
          <button 
            class="btn-header" 
            @click="fetchTopicsByYesCount"
            :disabled="isFetchingTopics"
          >
            {{ isFetchingTopics ? '获取中...' : '获取主题' }}
          </button>
        </div>
        <div style="display: inline-flex; align-items: center; gap: 8px; margin-right: 10px;">
          <label style="font-size: 14px;">模式:</label>
          <label class="switch-label" style="cursor: pointer;">
            <input type="checkbox" v-model="isFastMode" class="switch-checkbox">
            <span class="switch-slider"></span>
            <span class="switch-text">{{ isFastMode ? '快速' : '正常' }}</span>
          </label>
        </div>
        <select v-model="selectedNumberType" class="group-select" style="margin-right: 10px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
          <option value="1">全部账户</option>
          <option value="2">1000个账户</option>
          <option value="3">1000个账户中未达标的</option>
        </select>
        <select v-model="selectedGroup" class="group-select" style="margin-right: 10px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
          <option value="default">默认</option>
          <option value="1">分组1</option>
          <option value="2">分组2</option>
        </select>
        <div style="display: inline-flex; align-items: center; gap: 8px; margin-right: 10px;">
          <label style="font-size: 14px;">每轮时间（小时）:</label>
          <input 
            v-model.number="groupExecution.roundTimeHours" 
            type="number" 
            min="0.1"
            step="0.1"
            style="width: 80px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
            :disabled="groupExecution.isRunning"
          />
          <label style="font-size: 14px;">每轮间隔时间（分钟）:</label>
          <input 
            v-model.number="groupExecution.intervalMinutes" 
            type="number" 
            min="0"
            step="1"
            style="width: 80px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
            :disabled="groupExecution.isRunning"
          />
          <button 
            class="btn-header" 
            @click="toggleGroupExecution"
            :class="{ 'btn-running': groupExecution.isRunning }"
          >
            {{ groupExecution.isRunning ? '停止分组执行' : '开始分组执行' }}
          </button>
          <span v-if="groupExecution.isRunning && groupExecution.unrefreshedCount > 0" style="margin-left: 10px; color: #ff6b6b; font-size: 14px;">
            上一轮仓位未刷新数量：{{ groupExecution.unrefreshedCount }}
            <button 
              class="btn-header" 
              @click="showUnrefreshedBrowsersDialog = true"
              style="margin-left: 8px; padding: 4px 8px; font-size: 12px;"
            >
              查看
            </button>
          </span>
          <button 
            v-if="groupExecution.isRunning"
            class="btn-header" 
            @click="checkUnfinishedType2Browsers"
            :disabled="isLoadingUnfinishedType2"
            style="margin-left: 10px; padding: 4px 8px; font-size: 12px;"
          >
            {{ isLoadingUnfinishedType2 ? '查询中...' : '查看未完成type2任务' }}
          </button>
        </div>
        <button class="btn-header" @click="openTaskAnomaly" style="margin-right: 10px;">查询上轮日志</button>
        <button class="btn-header" @click="syncConfigFromMarkets">更新配置</button>
        <button class="btn-header" @click="showEditConfigDialog">修改配置</button>
      </div>
    </header>

    <main class="main">
      <div class="container">
        <!-- 查询功能 -->
        <section class="section query-section">
          <div class="section-header-with-filter">
            <div class="query-wrapper">
              <div class="query-controls">
                <div class="form-group">
                  <label for="queryTrendingId">Trending *</label>
                  <div class="trending-autocomplete-wrapper">
                    <input
                      id="queryTrendingId"
                      v-model="queryTrendingSearchText"
                      type="text"
                      placeholder="输入文字筛选或选择Trending"
                      :disabled="isLoadingConfig || isQuerying"
                      @input="onQueryTrendingSearchInput"
                      @focus="showQueryTrendingDropdown = true"
                      @blur="handleQueryTrendingBlur"
                      autocomplete="off"
                    />
                    <div 
                      v-if="showQueryTrendingDropdown && filteredQueryTrendingList.length > 0" 
                      class="trending-dropdown"
                    >
                      <div
                        v-for="config in filteredQueryTrendingList"
                        :key="config.id"
                        class="trending-dropdown-item"
                        @mousedown.prevent="selectQueryTrending(config)"
                      >
                        {{ config.trending }}
                      </div>
                    </div>
                  </div>
                </div>
                <button 
                  class="btn btn-primary" 
                  @click="handleQuery"
                  :disabled="!querySelectedConfig || isQuerying"
                >
                  {{ isQuerying ? '插入中...' : '插入' }}
                </button>
                <button 
                  class="btn btn-primary" 
                  @click="handleTest"
                  :disabled="!querySelectedConfig || isTesting"
                  style="margin-left: 8px;"
                >
                  {{ isTesting ? '测试中...' : '测试' }}
                </button>
              </div>
              <div v-if="testResult && !testResult.meetsCondition" class="query-result" style="margin-top: 8px;">
                <div class="query-result-error">
                  ❌ 不符合订单薄条件
                  <div class="query-result-reason">{{ testResult.reason }}</div>
                </div>
              </div>
              <div v-if="queryResult && !queryResult.meetsCondition" class="query-result">
                <div class="query-result-error">
                  ❌ 不符合订单薄条件
                  <div class="query-result-reason">{{ queryResult.reason }}</div>
                </div>
              </div>
              <div style="margin-top: 15px; text-align: right;">
                <span style="font-size: 24px; font-weight: bold; color: #28a745;">
                  正在运行的任务组数: {{ runningHedgeGroupsCount }}
                </span>
              </div>
            </div>
          </div>
        </section>
        
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
            <div class="trending-filter">
              <label>ip最大延迟(毫秒):</label>
              <input 
                v-model="hedgeMode.maxIpDelay" 
                type="number" 
                class="filter-input" 
                min="0"
                placeholder=""
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            <div class="trending-filter">
              <label>
                <input 
                  type="checkbox" 
                  v-model="hedgeMode.needJudgeDF"
                  :disabled="autoHedgeRunning"
                  @change="saveHedgeSettings"
                />
                不交易变红且抓取仓位时间距离现在超过xx小时的仓位(小时):
              </label>
              <input 
                v-model.number="hedgeMode.maxDHour" 
                type="number" 
                class="filter-input" 
                min="0"
                placeholder="12"
                :disabled="autoHedgeRunning || !hedgeMode.needJudgeDF"
                @blur="saveHedgeSettings"
              />
            </div>
            <div class="trending-filter">
              <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                <input 
                  type="checkbox" 
                  v-model="hedgeMode.needJudgeBalancePriority"
                  :true-value="1"
                  :false-value="0"
                  :disabled="autoHedgeRunning"
                  style="width: 18px; height: 18px; cursor: pointer;"
                  @change="saveHedgeSettings"
                />
                <span style="cursor: pointer;">可用少于</span>
                <input 
                  v-model.number="hedgeMode.balancePriority" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  placeholder="2000"
                  :disabled="autoHedgeRunning || hedgeMode.needJudgeBalancePriority === 0"
                  @blur="saveHedgeSettings"
                  style="width: 100px;"
                />
                <span style="cursor: pointer;">的账户，优先maker</span>
              </label>
            </div>
            <div class="trending-filter">
              <label>订单薄至少组数:</label>
              <input 
                v-model.number="hedgeMode.minOrderbookDepth" 
                type="number" 
                class="filter-input" 
                min="1"
                placeholder="3"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            <div class="trending-filter">
              <label>最大价差:</label>
              <input 
                v-model.number="hedgeMode.maxPriceDiff" 
                type="number" 
                class="filter-input" 
                min="0"
                step="0.1"
                placeholder="15"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            <div class="trending-filter">
              <label>先挂方价格区间:</label>
              <input 
                v-model.number="hedgeMode.priceRangeMin" 
                type="number" 
                class="filter-input" 
                min="0"
                max="100"
                placeholder="65"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
              <span style="margin: 0 5px;">-</span>
              <input 
                v-model.number="hedgeMode.priceRangeMax" 
                type="number" 
                class="filter-input" 
                min="0"
                max="100"
                placeholder="85"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            <div class="trending-filter">
              <label>最小累计深度:</label>
              <input 
                v-model.number="hedgeMode.minTotalDepth" 
                type="number" 
                class="filter-input" 
                min="0"
                placeholder="2000"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            <div class="trending-filter">
              <label style="color: red;">挂单超过XX小时撤单:</label>
              <input 
                v-model.number="hedgeMode.openOrderCancelHours" 
                type="number" 
                class="filter-input" 
                min="1"
                placeholder="72"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
                style="width: 80px;"
              />
            </div>
          </div>
          
          <!-- 深度差相关设置 -->
          <div class="depth-diff-settings" style="margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; border: 1px solid #ddd;">
            <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #000;">深度差相关设置</h3>
            <!-- 深度差阈值配置 -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值1:</label>
                <input 
                  v-model.number="hedgeMode.depthThreshold1" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="15"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值2:</label>
                <input 
                  v-model.number="hedgeMode.depthThreshold2" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="2"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值3:</label>
                <input 
                  v-model.number="hedgeMode.depthThreshold3" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="0.2"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
              </div>
            </div>
            <!-- 深度差>阈值1的配置 -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
              <div class="trending-filter">
                <label style="display: flex; align-items: center; gap: 8px; color: #000;">
                  <input 
                    type="checkbox" 
                    v-model="hedgeMode.enableDepthDiffParamsGt15"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                    style="width: 18px; height: 18px; cursor: pointer;"
                  />
                  <span>深度差>阈值1 </span>
                </label>
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差>阈值1延时检测时间(秒):</label>
                <input 
                  v-model="hedgeMode.delayTimeGt15" 
                  type="text" 
                  class="filter-input" 
                  placeholder="300,600"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 120px;"
                />
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差>阈值1价格波动(%):</label>
                <input 
                  v-model.number="hedgeMode.priceVolatilityGt15Min" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  max="100"
                  step="0.1"
                  placeholder="1"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
                <span style="margin: 0 5px;">-</span>
                <input 
                  v-model.number="hedgeMode.priceVolatilityGt15Max" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  max="100"
                  step="0.1"
                  placeholder="10"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
              </div>
            </div>
            <!-- 深度差阈值2-阈值1的配置 -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
              <div class="trending-filter">
                <label style="display: flex; align-items: center; gap: 8px; color: #000;">
                  <input 
                    type="checkbox" 
                    v-model="hedgeMode.enableDepthDiffParams2To15"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                    style="width: 18px; height: 18px; cursor: pointer;"
                  />
                  <span>深度差阈值2-阈值1 </span>
                </label>
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值2-阈值1延时检测时间(秒):</label>
                <input 
                  v-model="hedgeMode.delayTime2To15" 
                  type="text" 
                  class="filter-input" 
                  placeholder="30,60"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 120px;"
                />
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值2-阈值1价格波动(%):</label>
                <input 
                  v-model.number="hedgeMode.priceVolatility2To15Min" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  max="100"
                  step="0.1"
                  placeholder="1"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
                <span style="margin: 0 5px;">-</span>
                <input 
                  v-model.number="hedgeMode.priceVolatility2To15Max" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  max="100"
                  step="0.1"
                  placeholder="10"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
              </div>
            </div>
            <!-- 深度差阈值3-阈值2的配置 -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
              <div class="trending-filter">
                <label style="display: flex; align-items: center; gap: 8px; color: #000;">
                  <input 
                    type="checkbox" 
                    v-model="hedgeMode.enableDepthDiffParams02To2"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                    style="width: 18px; height: 18px; cursor: pointer;"
                  />
                  <span>深度差阈值3-阈值2 </span>
                </label>
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值3-阈值2延时检测时间(秒):</label>
                <input 
                  v-model="hedgeMode.delayTime02To2" 
                  type="text" 
                  class="filter-input" 
                  placeholder="0.5,0.5"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 120px;"
                />
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差阈值3-阈值2价格波动(%):</label>
                <input 
                  v-model.number="hedgeMode.priceVolatility02To2Min" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  max="100"
                  step="0.1"
                  placeholder="1"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
                <span style="margin: 0 5px;">-</span>
                <input 
                  v-model.number="hedgeMode.priceVolatility02To2Max" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  max="100"
                  step="0.1"
                  placeholder="10"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px;"
                />
              </div>
            </div>
            <!-- 深度差0.1的配置 -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
              <div class="trending-filter">
                <label style="display: flex; align-items: center; gap: 8px; color: #000;">
                  <input 
                    type="checkbox" 
                    v-model="hedgeMode.enableDepthDiffParams01"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                    style="width: 18px; height: 18px; cursor: pointer;"
                  />
                  <span>深度差0.1 </span>
                </label>
              </div>
              <div class="trending-filter">
                <label style="color: #000;">深度差0.1最大多吃价值(U):</label>
                <input 
                  v-model.number="hedgeMode.maxEatValue01" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="20"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 100px;"
                />
              </div>
              <div class="trending-filter">
                <label style="color: #000;">最大允许深度:</label>
                <input 
                  v-model.number="hedgeMode.maxDepth" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  placeholder="1000"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 100px;"
                />
              </div>
            </div>
          </div>
          
          <!-- 订单薄更新设置 -->
          <div class="orderbook-update-settings" style="margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; border: 1px solid #ddd;">
            <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #000;">订单薄更新设置</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px 20px; align-items: center;">
              <div class="trending-filter">
                <label style="color: #000;">事件yes持仓</label>
                <select 
                  v-model="hedgeMode.yesPositionCompareType" 
                  class="filter-input" 
                  :disabled="autoHedgeRunning"
                  @change="saveHedgeSettings"
                  style="width: 80px; margin: 0 5px;"
                >
                  <option value="less">小于</option>
                  <option value="greater">大于</option>
                </select>
                <input 
                  v-model.number="hedgeMode.yesPositionThreshold" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="0.2"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px; margin: 0 5px;"
                />
                <span style="color: #000;">(万)时，才交易</span>
              </div>
             
              <div class="trending-filter">
                <label style="color: #000;">总任务数:</label>
                <select 
                  v-model="hedgeMode.totalTaskCountOperator" 
                  class="filter-input" 
                  :disabled="autoHedgeRunning"
                  @change="saveHedgeSettings"
                  style="width: 80px;"
                >
                  <option value="gt">大于</option>
                  <option value="lt">小于</option>
                </select>
                <input 
                  v-model.number="hedgeMode.totalTaskCountThreshold" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  placeholder="999"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 100px; margin: 0 5px;"
                />
                <span style="color: #000;">时才分配任务</span>
              </div>

              <div class="trending-filter">
                <label style="color: red;">账号仓位价值(页面8-Portfolio)小于</label>
                <input 
                  v-model.number="hedgeMode.maxPosWorthOpen" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="0"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 70px; margin: 0 0px;"
                />
                <span style="color: red;">(万)才开仓</span>
              </div>
             
              <div class="trending-filter" style="grid-column: 1 / -1;">
                <label style="color: red;">加权时间</label>
                <select 
                  v-model="hedgeMode.weightedTimeCompareType" 
                  class="filter-input" 
                  :disabled="autoHedgeRunning"
                  @change="saveHedgeSettings"
                  style="width: 80px; margin: 0 5px;"
                >
                  <option value="less">小于</option>
                  <option value="greater">大于</option>
                </select>
                <input 
                  v-model.number="hedgeMode.weightedTimeHourOpen" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="0"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 70px; margin: 0 5px;"
                />
                <span style="color: red;">(小时)且事件yes持仓</span>
                <select 
                  v-model="hedgeMode.weightedTimeYesPositionCompareType" 
                  class="filter-input" 
                  :disabled="autoHedgeRunning"
                  @change="saveHedgeSettings"
                  style="width: 80px; margin: 0 5px;"
                >
                  <option value="less">小于</option>
                  <option value="greater">大于</option>
                </select>
                <input 
                  v-model.number="hedgeMode.weightedTimeYesPositionThreshold" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="0.1"
                  placeholder="0"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 70px; margin: 0 5px;"
                />
                <span style="color: red;">(万)不交易</span>
              </div>

              <div class="trending-filter">
                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                  <input 
                    type="checkbox" 
                    v-model="hedgeMode.needJudgeTimeRandom"
                    :true-value="1"
                    :false-value="0"
                    :disabled="autoHedgeRunning"
                    @change="saveHedgeSettings"
                  />
                  <span style="color: #000;">账号随机8小时不交易</span>
                </label>
              </div>

              <div class="trending-filter" style="grid-column: 1 / -1;">
                <label style="color: red;">最近24小时交易量小于</label>
                <input 
                  v-model.number="hedgeMode.maxVolume24hOpen" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="1"
                  placeholder="99"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 70px; margin: 0 0px;"
                />
                <span style="color: red;">(万)且最近7天平均交易量小于</span>
                <input 
                  v-model.number="hedgeMode.maxVolume7dAvgOpen" 
                  type="number" 
                  class="filter-input" 
                  min="0"
                  step="1"
                  placeholder="99"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 70px; margin: 0 0px;"
                />
                <span style="color: red;">(万)时，才参与交易</span>
              </div>

              <div class="trending-filter">
                <label style="color: #000;">订单薄不匹配时X（分钟）内不抓取:</label>
                <input 
                  v-model.number="hedgeMode.orderbookMismatchInterval" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  placeholder="10"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                />
              </div>

              <div class="trending-filter">
                <label style="color: #000;">每一轮任务个数阈值</label>
                <input 
                  v-model.number="hedgeMode.taskCountThreshold" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  placeholder="5"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 60px; margin: 0 5px;"
                />
                <span style="color: #000;">（小于这个数，下一轮等待</span>
                <input 
                  v-model.number="hedgeMode.waitTimeLessThanThreshold" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  placeholder="300"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px; margin: 0 5px;"
                />
                <span style="color: #000;">秒，大于等待</span>
                <input 
                  v-model.number="hedgeMode.waitTimeGreaterThanThreshold" 
                  type="number" 
                  class="filter-input" 
                  min="1"
                  placeholder="60"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                  style="width: 80px; margin: 0 5px;"
                />
                <span style="color: #000;">秒）</span>
              </div>
         
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
              <div class="fee-result" v-if="feeQuery.totalFee !== null || feeQuery.chainFee !== null">
                <span class="fee-label">本地手续费:</span>
                <span class="fee-value">${{ (feeQuery.totalFee || 0).toFixed(2) }}</span>
                <span class="fee-label" style="margin-left: 20px;">链上手续费:</span>
                <span class="fee-value">${{ (feeQuery.chainFee || 0).toFixed(2) }}</span>
                <button 
                  v-if="feeQuery.feeAddresses && feeQuery.feeAddresses.length > 0"
                  class="btn btn-secondary btn-sm" 
                  style="margin-left: 15px;"
                  @click="showFeeDetailDialog = true"
                >
                  详情
                </button>
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
              <span class="filter-label">开仓使用：最近</span>
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
            
            <div class="hedge-time-filter">
              <span class="filter-label">平仓使用：最近</span>
              <input 
                v-model.number="hedgeMode.minCloseMin" 
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
            
            <!-- 最小开单设置 -->
            <div class="hedge-amount-range">
              <span class="filter-label">最小开单:</span>
              <input 
                v-model.number="hedgeMode.minUAmt" 
                type="number" 
                class="amount-range-input" 
                min="0"
                placeholder="10"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            
            <!-- 最大开单设置 -->
            <div class="hedge-amount-range">
              <span class="filter-label">最大开单:</span>
              <input 
                v-model.number="hedgeMode.maxUAmt" 
                type="number" 
                class="amount-range-input" 
                min="0"
                placeholder="1500"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            
            <!-- 平仓最小数量设置 -->
            <div class="hedge-amount-range">
              <span class="filter-label">平仓最小数量（参数1）:</span>
              <input 
                v-model.number="hedgeMode.minCloseAmt" 
                type="number" 
                class="amount-range-input" 
                min="0"
                placeholder="0"
                :disabled="autoHedgeRunning"
                @blur="saveHedgeSettings"
              />
            </div>
            
            <!-- 合计最小平仓值（参数2）和合计最大平仓值（参数3）- 仅在平仓模式且模式2或模式3时显示 -->
            <template v-if="hedgeMode.isClose && (hedgeMode.hedgeMode === 2 || hedgeMode.hedgeMode === 3)">
              <div class="hedge-amount-range">
                <span class="filter-label">合计最小平仓值（参数2）:</span>
                <input 
                  v-model.number="hedgeMode.minTotalCloseAmt" 
                  type="number" 
                  class="amount-range-input" 
                  min="0"
                  placeholder="0"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                />
              </div>
              
              <div class="hedge-amount-range">
                <span class="filter-label">合计最大平仓值（参数3）:</span>
                <input 
                  v-model.number="hedgeMode.maxTotalCloseAmt" 
                  type="number" 
                  class="amount-range-input" 
                  min="0"
                  placeholder="0"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                />
              </div>
              
              <div class="hedge-amount-range">
                <span class="filter-label">taker最小数量（参数4）:</span>
                <input 
                  v-model.number="hedgeMode.takerMinAmt" 
                  type="number" 
                  class="amount-range-input" 
                  min="0"
                  placeholder="200"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                />
              </div>
            </template>
            
            <!-- 模式选择下拉框 - 一直显示 -->
            <div class="hedge-mode-select">
              <span class="filter-label">模式:</span>
              <select 
                v-model.number="hedgeMode.hedgeMode" 
                class="mode-select"
                :disabled="autoHedgeRunning"
                @change="saveHedgeSettings"
              >
                <option :value="1">模式1</option>
                <option :value="2">模式2</option>
                <option :value="3">模式3</option>
              </select>
            </div>
            
            <!-- 模式一开仓专属设置 - 仅在开仓且模式一时显示 -->
            <template v-if="!hedgeMode.isClose && hedgeMode.hedgeMode === 1">
              <div class="hedge-amount-range">
                <span class="filter-label">优先开仓区间:</span>
                <input 
                  v-model="hedgeMode.posPriorityArea" 
                  type="text" 
                  class="amount-range-input" 
                  placeholder="0.02,250"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                />
              </div>
              
              <div class="hedge-amount-range">
                <span class="filter-label">开仓最大仓位限制:</span>
                <input 
                  v-model.number="hedgeMode.maxPosLimit" 
                  type="number" 
                  class="amount-range-input" 
                  min="0"
                  placeholder="3000"
                  :disabled="autoHedgeRunning"
                  @blur="saveHedgeSettings"
                />
              </div>
            </template>
            
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
            
            <div style="display: inline-flex; align-items: center; gap: 8px;">
              <input 
                type="number" 
                v-model.number="randomGetCount" 
                min="1" 
                max="50"
                style="width: 60px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                :disabled="isRandomGetting"
                title="输入要获取的主题数量"
              />
              <button 
                class="btn btn-success btn-sm" 
                @click="randomGetAvailableTopic(flase)"
                :disabled="isRandomGetting"
                title="随机获取可用的主题"
              >
                {{ isRandomGetting ? '🔄 获取中...' : '🎲 随机获取主题' }}
              </button>
              <button 
                class="btn btn-warning btn-sm" 
                @click="randomGetAvailableTopic(true)"
                :disabled="isRandomGetting || !failedTopics || failedTopics.length === 0"
                title="在上一轮失败的主题中再次获取"
              >
                {{ isRandomGetting ? '🔄 获取中...' : `🔄 重试失败主题 (${failedTopics?.length || 0})` }}
              </button>
              <label style="font-size: 14px; margin-left: 8px;">一个主题同时任务个数：</label>
              <input 
                type="number" 
                v-model.number="hedgeTasksPerTopic" 
                min="1" 
                max="10"
                style="width: 60px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                :disabled="autoHedgeRunning"
                title="输入一个主题同时执行的对冲任务数量"
              />
              <label style="font-size: 14px; margin-left: 8px;">每轮最多任务数：</label>
              <input 
                type="number" 
                v-model.number="hedgeMaxTasksPerRound" 
                min="1" 
                max="10"
                style="width: 60px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                :disabled="autoHedgeRunning"
                title="每一轮循环中，每个主题最多新增的任务数量（限制单轮爆发量）"
              />
              <label style="font-size: 14px; margin-left: 8px;">任务间隔(分钟)：</label>
              <input 
                type="number" 
                v-model.number="hedgeTaskInterval" 
                min="0" 
                max="60"
                style="width: 60px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                :disabled="autoHedgeRunning"
                title="一组任务结束后，等待多少分钟再请求分配新任务"
              />
              <label style="font-size: 14px; margin-left: 8px;">可加仓时间（小时）：</label>
              <input 
                type="number" 
                v-model.number="hedgeMode.maxOpenHour" 
                min="1" 
                style="width: 60px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                :disabled="autoHedgeRunning"
                title="可加仓时间（小时）"
              />
              <label style="font-size: 14px; margin-left: 8px;">可平仓随机区间（小时）：</label>
              <input 
                type="text" 
                v-model="hedgeMode.closeOpenHourArea" 
                style="width: 80px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                :disabled="autoHedgeRunning"
                title="可平仓随机区间（小时），格式：12,36"
                placeholder="12,36"
              />
            </div>
            
            <div style="display: inline-flex; align-items: center; gap: 8px; margin-left: 16px;">
              <span style="font-size: 14px;">主题数量：{{ filteredActiveConfigs.length }}</span>
              <label style="font-size: 14px; margin-left: 8px; display: flex; align-items: center; gap: 4px;">
                <input 
                  type="checkbox" 
                  v-model="enableBatchMode"
                  :disabled="autoHedgeRunning"
                  title="勾选后启用分批执行模式"
                />
                <span>分批执行</span>
              </label>
              <template v-if="enableBatchMode">
                <label style="font-size: 14px; margin-left: 8px;">每一批的个数：</label>
                <input 
                  type="number" 
                  v-model.number="batchSize" 
                  min="1" 
                  style="width: 60px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                  :disabled="autoHedgeRunning"
                  title="输入每一批要处理的主题数量"
                />
                <label style="font-size: 14px; margin-left: 8px;">每一批的执行时间（分钟）：</label>
                <input 
                  type="number" 
                  v-model.number="batchExecutionTime" 
                  min="1" 
                  style="width: 80px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;"
                  :disabled="autoHedgeRunning"
                  title="输入每一批的执行时间（分钟）"
                />
                <span v-if="autoHedgeRunning" style="font-size: 14px; margin-left: 8px; color: #007bff; font-weight: bold;">
                  当前执行批次：{{ currentBatchIndex + 1 }}/{{ Math.ceil(filteredActiveConfigs.length / batchSize) }}
                </span>
              </template>
            </div>
            
            <div style="display: inline-flex; align-items: center; gap: 8px; margin-left: 16px;">
              <span style="font-size: 14px; color: rgba(255, 255, 255, 0.8);">排序：</span>
              <button 
                :class="['btn', 'btn-sm', hedgeSortBy === 'yesAmt' ? 'btn-primary' : 'btn-secondary']"
                @click="hedgeSortBy = hedgeSortBy === 'yesAmt' ? '' : 'yesAmt'"
                style="padding: 4px 12px; font-size: 12px;"
              >
                按YES金额{{ hedgeSortBy === 'yesAmt' ? ' ✓' : '' }}
              </button>
              <button 
                :class="['btn', 'btn-sm', hedgeSortBy === 'weightedAvgTime' ? 'btn-primary' : 'btn-secondary']"
                @click="hedgeSortBy = hedgeSortBy === 'weightedAvgTime' ? '' : 'weightedAvgTime'"
                style="padding: 4px 12px; font-size: 12px;"
              >
                按创建时间加权平均值{{ hedgeSortBy === 'weightedAvgTime' ? ' ✓' : '' }}
              </button>
              <button 
                :class="['btn', 'btn-sm', hedgeSortBy === 'volume24h' ? 'btn-primary' : 'btn-secondary']"
                @click="hedgeSortBy = hedgeSortBy === 'volume24h' ? '' : 'volume24h'"
                style="padding: 4px 12px; font-size: 12px;"
              >
                按24h量{{ hedgeSortBy === 'volume24h' ? ' ✓' : '' }}
              </button>
              <button 
                :class="['btn', 'btn-sm', hedgeSortBy === 'volume7dAvg' ? 'btn-primary' : 'btn-secondary']"
                @click="hedgeSortBy = hedgeSortBy === 'volume7dAvg' ? '' : 'volume7dAvg'"
                style="padding: 4px 12px; font-size: 12px;"
              >
                按7天平均量{{ hedgeSortBy === 'volume7dAvg' ? ' ✓' : '' }}
              </button>
            </div>
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
                      {{ config.trending }}
                    </span>
                    <button 
                      v-if="config.opUrl" 
                      class="btn-link btn-sm" 
                      @click="openOpUrl(config.opUrl)"
                      title="在新标签页打开主题页面"
                    >
                      🔗 打开
                    </button>
                    <button class="btn-log btn-sm" @click="showHedgeLog(config)">
                      📋 日志
                    </button>
                    <button 
                      class="btn-log btn-sm" 
                      @click="updateOrderbookForConfig(config)"
                      :disabled="isUpdatingOrderbook(config)"
                      style="margin-left: 4px;"
                      title="手动更新订单薄"
                    >
                      {{ isUpdatingOrderbook(config) ? '更新中...' : '更新订单薄' }}
                    </button>
                    <button 
                      class="btn-position btn-sm" 
                      @click="openPositionDetail(config)"
                      style="margin-left: 4px;"
                      title="查看持仓详情"
                    >
                      查看持仓
                    </button>
                    <button 
                      class="btn-position btn-sm" 
                      @click="openOpenOrderDetail(config)"
                      style="margin-left: 4px;"
                      title="查看挂单详情"
                    >
                      查看挂单
                    </button>
                    <button class="btn-close-task btn-sm" @click="closeConfigTask(config)">
                      ❌ 关闭任务
                    </button>
                    <span v-if="getPositionText(config)" :class="['position-info', shouldShowPositionGreen(config) ? 'position-info-green' : '']" style="margin-left: 8px; font-size: 0.75rem; color: rgba(255, 255, 255, 0.8);">
                      {{ getPositionText(config) }}
                    </span>
                    <span class="config-stats" style="margin-left: 8px; font-size: 0.7rem; color: #4ade80;">
                      <span style="margin-right: 6px;" title="创建时间加权平均值（小时）">加权时间:{{ config.weightedAvgTime !== undefined && config.weightedAvgTime !== null ? (config.weightedAvgTime / 3600000).toFixed(2) : '0.00' }}h</span>
                      <span style="margin-right: 6px;" title="YES数量（万）">YES金额:{{ config.yesAmt !== undefined && config.yesAmt !== null ? (config.yesAmt / 10000).toFixed(2) : '0.00' }}万</span>
                      <span style="margin-right: 6px;" title="最近24小时交易量（万）">24h量:{{ config.volume24h !== undefined && config.volume24h !== null ? (config.volume24h / 10000).toFixed(2) : '0.00' }}万</span>
                      <span style="margin-right: 6px;" title="7天平均每天交易量（万）">7d均:{{ config.volume7dAvg !== undefined && config.volume7dAvg !== null ? (config.volume7dAvg / 10000).toFixed(2) : '0.00' }}万</span>
                      <span title="本周交易量（周日早上8点开始）（万）">1周量:{{ config.volume1w !== undefined && config.volume1w !== null ? (config.volume1w / 10000).toFixed(2) : '0.00' }}万</span>
                    </span>
                    <button 
                      class="btn-test btn-sm" 
                      @click="handleTestForConfig(config)"
                      :disabled="isTestingConfig(config)"
                      style="margin-left: 8px;"
                    >
                      {{ isTestingConfig(config) ? '测试中...' : '测试' }}
                    </button>
                    <label style="font-size: 12px; margin-left: 8px; color: rgba(255, 255, 255, 0.8);">同时任务:</label>
                    <input 
                      type="number" 
                      v-model.number="config.tasksPerTopic" 
                      min="1" 
                      max="10"
                      placeholder="默认"
                      style="width: 60px; padding: 2px 4px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; margin-left: 4px;"
                      title="留空使用全局设置，填写则使用此值"
                    />
                    <label style="font-size: 12px; margin-left: 8px; color: rgba(255, 255, 255, 0.8);">最大允许深度:</label>
                    <input 
                      type="number" 
                      v-model.number="config.maxDepth" 
                      min="0"
                      placeholder="默认"
                      style="width: 80px; padding: 2px 4px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; margin-left: 4px;"
                      title="留空使用全局设置，填写则使用此值"
                    />
                    <button 
                      class="btn-sm" 
                      @click="saveTopicSettings(config)"
                      style="margin-left: 4px; padding: 2px 8px; font-size: 11px; background-color: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;"
                      title="保存该主题的设置（同时任务和最大允许深度）"
                    >
                      保存
                    </button>
                    <span style="font-size: 12px; margin-left: 8px; color: rgba(255, 255, 255, 0.8);">
                      今日开单量：{{ config.currentAmt !== undefined && config.currentAmt !== null ? config.currentAmt.toFixed(2) : '0.00' }}
                    </span>
                    <label style="font-size: 12px; margin-left: 8px; color: rgba(255, 255, 255, 0.8);">今日最大开单量：</label>
                    <input 
                      type="number" 
                      v-model.number="config.maxDailyAmount" 
                      :placeholder="config.c !== undefined && config.c !== null && config.c !== '' ? config.c : '未设置'"
                      min="0"
                      step="0.01"
                      style="width: 100px; padding: 2px 4px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; margin-left: 4px;"
                      title="今日最大开单量，留空表示未设置"
                    />
                    <button 
                      class="btn-sm" 
                      @click="saveMaxDailyAmount(config)"
                      :disabled="isSavingMaxDailyAmount(config)"
                      style="margin-left: 4px; padding: 2px 8px; font-size: 11px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;"
                      title="保存最大开单量设置"
                    >
                      {{ isSavingMaxDailyAmount(config) ? '保存中...' : '保存最大开单量' }}
                    </button>
                    <span v-if="config.errorMessage" class="error-badge">
                      {{ config.errorMessage }}
                    </span>
                  </div>
                </div>
                
                <!-- 订单薄数据和对冲信息显示区域 -->
                <div class="task-hedge-container">
                  <!-- 左侧：订单薄数据 -->
                  <div class="type3-task-section">
                    <div class="section-title">订单薄数据</div>
                    <div v-if="config.orderbookData" class="type3-task-info">
                      <div class="task-status-row">
                        <span class="task-label">先挂方: {{ config.orderbookData.firstSide }}</span>
                        <span class="task-status-badge status-success">已更新</span>
                      </div>
                      <div v-if="config.orderbookData.pollTime" :class="['task-time', isOrderbookConditionMet(config.orderbookData) ? 'task-time-success' : 'task-time-error']">
                        {{ getOrderbookStatusText(config.orderbookData) }}
                      </div>
                      <div class="task-msg">
                        <div class="orderbook-detail">
                          <div v-if="config.orderbookData.price1 !== null && config.orderbookData.price1 !== undefined" class="price-row">
                            <span class="label">先挂价格:</span>
                            <span class="value">{{ config.orderbookData.price1.toFixed(2) }}¢</span>
                          </div>
                          <div v-if="config.orderbookData.price2 !== null && config.orderbookData.price2 !== undefined" class="price-row">
                            <span class="label">后挂价格:</span>
                            <span class="value">{{ config.orderbookData.price2.toFixed(2) }}¢</span>
                          </div>
                          <div v-if="config.orderbookData.diff !== null && config.orderbookData.diff !== undefined" class="price-row">
                            <span class="label">价差:</span>
                            <span class="value highlight">{{ config.orderbookData.diff.toFixed(2) }}¢</span>
                          </div>
                          <div v-if="config.orderbookData.depth1 !== null && config.orderbookData.depth1 !== undefined && config.orderbookData.depth2 !== null && config.orderbookData.depth2 !== undefined" class="price-row">
                            <span class="label">深度:</span>
                            <span class="value">{{ config.orderbookData.depth1.toFixed(2) }} / {{ config.orderbookData.depth2.toFixed(2) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div v-else-if="config.isFetching" class="no-data">
                      正在请求订单薄...
                    </div>
                    <div v-else class="no-data">暂无数据</div>
                  </div>
                  
                  <!-- 右侧：对冲信息 -->
                  <div class="hedge-info-section">
                    <div class="section-title">对冲信息</div>
                    <div v-if="config.currentHedges && config.currentHedges.length > 0" class="hedge-info-list">
                      <div 
                        v-for="(hedge, index) in config.currentHedges.filter(h => {
                          // 模式1：只显示运行中的
                          if (!h.isMode2) {
                            return h.finalStatus === 'running'
                          }
                          // 模式2：只要状态是running就显示（因为模式2在创建时就有yesList和noList）
                          // 或者有已提交的任务，或者有计划任务列表
                          return h.finalStatus === 'running' || 
                                 (h.yesTasks && h.yesTasks.length > 0) || 
                                 (h.noTasks && h.noTasks.length > 0) ||
                                 (h.yesList && h.yesList.length > 0) ||
                                 (h.noList && h.noList.length > 0)
                        })" 
                        :key="hedge.id"
                        class="hedge-info"
                        :style="{ marginBottom: index < config.currentHedges.filter(h => {
                          if (!h.isMode2) {
                            return h.finalStatus === 'running'
                          }
                          return h.finalStatus === 'running' || 
                                 (h.yesTasks && h.yesTasks.length > 0) || 
                                 (h.noTasks && h.noTasks.length > 0) ||
                                 (h.yesList && h.yesList.length > 0) ||
                                 (h.noList && h.noList.length > 0)
                        }).length - 1 ? '16px' : '0' }"
                      >
                        <div class="hedge-status-row">
                          <span class="hedge-label">对冲 #{{ hedge.id }} ({{ index + 1 }}/{{ config.currentHedges.filter(h => h.finalStatus === 'running').length }})</span>
                          <span 
                            class="hedge-status-badge"
                            :class="getHedgeStatusClass(hedge)"
                          >
                            {{ getHedgeStatusText(hedge) }}
                          </span>
                          <span v-if="hedge.isMode2" class="hedge-mode-badge">模式2</span>
                        </div>
                        
                        <!-- 模式1：原有展示方式 -->
                        <template v-if="!hedge.isMode2">
                          <!-- 任务一 -->
                          <div class="hedge-task-section">
                            <div class="task-title">
                              任务一 - {{ hedge.firstSide }}
                              <span class="task-amount">x{{ hedge.firstShareReduction ? (hedge.share - hedge.firstShareReduction).toFixed(2) : hedge.share }}</span>
                            </div>
                            <div class="hedge-task-details-grid">
                              <div class="hedge-detail-row">
                                <span>任务ID:</span>
                                <span :class="getTaskStatusClass(
                                  hedge.firstSide === 'YES' 
                                    ? hedge.yesStatus 
                                    : hedge.noStatus
                                )">
                                  {{ 
                                    hedge.firstSide === 'YES' 
                                      ? (hedge.yesTaskId || '待提交') 
                                      : (hedge.noTaskId || '待提交') 
                                  }}
                                </span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>浏览器:</span>
                                <span>{{ 
                                  hedge.firstSide === 'YES' 
                                    ? hedge.yesNumber 
                                    : hedge.noNumber 
                                }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>电脑组:</span>
                                <span>{{ 
                                  hedge.firstSide === 'YES' 
                                    ? hedge.yesGroupNo 
                                    : hedge.noGroupNo 
                                }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>买/卖:</span>
                                <span>{{ hedge.side === 1 ? '买入' : '卖出' }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>方向:</span>
                                <span>{{ hedge.firstSide }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>价格:</span>
                                <span>{{ 
                                  hedge.firstSide === 'YES' 
                                    ? hedge.yesPrice 
                                    : hedge.noPrice 
                                }}¢</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>数量:</span>
                                <span>{{ hedge.firstShareReduction ? (hedge.share - hedge.firstShareReduction).toFixed(2) : hedge.share }}</span>
                              </div>
                            </div>
                          </div>
                          
                          <!-- 任务二 -->
                          <div class="hedge-task-section">
                            <div class="task-title">
                              任务二 - {{ hedge.firstSide === 'YES' ? 'NO' : 'YES' }}
                              <span class="task-amount">x{{ hedge.share }}</span>
                            </div>
                            <div class="hedge-task-details-grid">
                              <div class="hedge-detail-row">
                                <span>任务ID:</span>
                                <span :class="getTaskStatusClass(
                                  hedge.firstSide === 'YES' 
                                    ? hedge.noStatus 
                                    : hedge.yesStatus
                                )">
                                  {{ 
                                    hedge.firstSide === 'YES' 
                                      ? (hedge.noTaskId || '待提交') 
                                      : (hedge.yesTaskId || '待提交') 
                                  }}
                                </span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>浏览器:</span>
                                <span>{{ 
                                  hedge.firstSide === 'YES' 
                                    ? hedge.noNumber 
                                    : hedge.yesNumber 
                                }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>电脑组:</span>
                                <span>{{ 
                                  hedge.firstSide === 'YES' 
                                    ? hedge.noGroupNo 
                                    : hedge.yesGroupNo 
                                }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>买/卖:</span>
                                <span>{{ hedge.side === 1 ? '买入' : '卖出' }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>方向:</span>
                                <span>{{ hedge.firstSide === 'YES' ? 'NO' : 'YES' }}</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>价格:</span>
                                <span>{{ 
                                  hedge.firstSide === 'YES' 
                                    ? hedge.noPrice 
                                    : hedge.yesPrice 
                                }}¢</span>
                              </div>
                              <div class="hedge-detail-row">
                                <span>数量:</span>
                                <span>{{ hedge.share }}</span>
                              </div>
                            </div>
                          </div>
                        </template>
                        
                        <!-- 模式2：多任务展示方式 -->
                        <template v-else>
                          <!-- YES任务列表：优先显示已提交的任务，如果没有则显示计划任务 -->
                          <div v-if="(hedge.yesTasks && hedge.yesTasks.length > 0) || (hedge.yesList && hedge.yesList.length > 0)" class="hedge-task-section">
                            <div class="task-title">
                              YES任务 ({{ (hedge.yesTasks && hedge.yesTasks.length > 0) ? hedge.yesTasks.length : (hedge.yesList ? hedge.yesList.length : 0) }}个)
                            </div>
                            <!-- 显示已提交的任务 -->
                            <template v-if="hedge.yesTasks && hedge.yesTasks.length > 0">
                              <div v-for="(task, taskIndex) in hedge.yesTasks" :key="taskIndex" class="hedge-task-item">
                                <div class="hedge-task-details-grid">
                                  <div class="hedge-detail-row">
                                    <span>任务ID:</span>
                                    <span :class="getTaskStatusClass(task.status)">
                                      {{ task.taskId || '待提交' }}
                                    </span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>浏览器:</span>
                                    <span>{{ task.number }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>电脑组:</span>
                                    <span>{{ task.groupNo }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>价格:</span>
                                    <span>{{ task.price }}¢</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>数量:</span>
                                    <span>{{ task.share }}</span>
                                  </div>
                                </div>
                              </div>
                            </template>
                            <!-- 显示计划任务（还未提交） -->
                            <template v-else-if="hedge.yesList && hedge.yesList.length > 0">
                              <div v-for="(item, itemIndex) in hedge.yesList" :key="itemIndex" class="hedge-task-item">
                                <div class="hedge-task-details-grid">
                                  <div class="hedge-detail-row">
                                    <span>任务ID:</span>
                                    <span class="task-pending">待提交</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>浏览器:</span>
                                    <span>{{ item.number }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>电脑组:</span>
                                    <span>{{ getGroupNo(item.number) }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>价格:</span>
                                    <span>{{ hedge.firstSide === 'YES' ? parseFloat(hedge.price) : (100 - parseFloat(hedge.price)) }}¢</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>数量:</span>
                                    <span>{{ item.share }}</span>
                                  </div>
                                </div>
                              </div>
                            </template>
                          </div>
                          
                          <!-- NO任务列表：优先显示已提交的任务，如果没有则显示计划任务 -->
                          <div v-if="(hedge.noTasks && hedge.noTasks.length > 0) || (hedge.noList && hedge.noList.length > 0)" class="hedge-task-section">
                            <div class="task-title">
                              NO任务 ({{ (hedge.noTasks && hedge.noTasks.length > 0) ? hedge.noTasks.length : (hedge.noList ? hedge.noList.length : 0) }}个)
                            </div>
                            <!-- 显示已提交的任务 -->
                            <template v-if="hedge.noTasks && hedge.noTasks.length > 0">
                              <div v-for="(task, taskIndex) in hedge.noTasks" :key="taskIndex" class="hedge-task-item">
                                <div class="hedge-task-details-grid">
                                  <div class="hedge-detail-row">
                                    <span>任务ID:</span>
                                    <span :class="getTaskStatusClass(task.status)">
                                      {{ task.taskId || '待提交' }}
                                    </span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>浏览器:</span>
                                    <span>{{ task.number }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>电脑组:</span>
                                    <span>{{ task.groupNo }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>价格:</span>
                                    <span>{{ task.price }}¢</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>数量:</span>
                                    <span>{{ task.share }}</span>
                                  </div>
                                </div>
                              </div>
                            </template>
                            <!-- 显示计划任务（还未提交） -->
                            <template v-else-if="hedge.noList && hedge.noList.length > 0">
                              <div v-for="(item, itemIndex) in hedge.noList" :key="itemIndex" class="hedge-task-item">
                                <div class="hedge-task-details-grid">
                                  <div class="hedge-detail-row">
                                    <span>任务ID:</span>
                                    <span class="task-pending">待提交</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>浏览器:</span>
                                    <span>{{ item.number }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>电脑组:</span>
                                    <span>{{ getGroupNo(item.number) }}</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>价格:</span>
                                    <span>{{ hedge.firstSide === 'NO' ? (100 - parseFloat(hedge.price)) : parseFloat(hedge.price) }}¢</span>
                                  </div>
                                  <div class="hedge-detail-row">
                                    <span>数量:</span>
                                    <span>{{ item.share }}</span>
                                  </div>
                                </div>
                              </div>
                            </template>
                          </div>
                          
                          <!-- 所有任务ID汇总 -->
                          <div v-if="hedge.allTaskIds && hedge.allTaskIds.length > 0" class="hedge-summary">
                            <span>任务ID组: {{ hedge.allTaskIds.join(', ') }}</span>
                          </div>
                        </template>
                        
                        <div class="hedge-summary">
                          <span>{{ hedge.isClose ? '卖出' : '买入' }} @ {{ hedge.price }}¢</span>
                          <span>{{ formatTime(hedge.startTime) }}</span>
                        </div>
                      </div>
                      <!-- 显示最新的两条错误信息 -->
                      <div 
                        v-for="(hedge, index) in config.currentHedges.filter(h => h.errorMsg).slice(-2)" 
                        :key="'error-' + hedge.id"
                        class="hedge-info hedge-error"
                      >
                        <div class="hedge-status-row">
                          <span class="hedge-label">错误</span>
                          <span class="hedge-status-badge status-failed">失败</span>
                        </div>
                        <div class="hedge-error-msg">{{ hedge.errorMsg }}</div>
                        <div class="hedge-summary">
                          <span>{{ formatTime(hedge.startTime) }}</span>
                        </div>
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
                <div style="display: flex; gap: 8px; align-items: center;">
                  <input
                    id="numberList"
                    v-model="formData.numberList"
                    type="text"
                    placeholder="请输入浏览器编号"
                    required
                    @blur="updateGroupNoFromBrowser"
                    style="flex: 1;"
                  />
                  <button 
                    type="button" 
                    class="btn btn-info btn-sm" 
                    @click="handleQuickSelectOrderAcc"
                    :disabled="isQuickSelecting || !canQuickSelect"
                    style="white-space: nowrap;"
                  >
                    <span v-if="isQuickSelecting">获取中...</span>
                    <span v-else>自动获取</span>
                  </button>
                </div>
                <div v-if="blackListText" class="blacklist-display" style="margin-top: 8px; color: #ff6b6b; font-size: 14px;">
                  拉黑的浏览器: {{ blackListText }}
                </div>
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
                <div class="trending-autocomplete-wrapper">
                  <input
                    id="trendingId"
                    v-model="trendingSearchText"
                    type="text"
                    placeholder="输入文字筛选或选择Trending"
                    required
                    :disabled="isLoadingConfig"
                    @input="onTrendingSearchInput"
                    @focus="showTrendingDropdown = true"
                    @blur="handleTrendingBlur"
                    autocomplete="off"
                  />
                  <div 
                    v-if="showTrendingDropdown && filteredTrendingList.length > 0" 
                    class="trending-dropdown"
                  >
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
              <!-- <button type="button" class="btn btn-info" @click="submitOrderbookTask" :disabled="isSubmittingOrderbook">
                <span v-if="isSubmittingOrderbook">提交中...</span>
                <span v-else>📊 获取订单薄</span>
              </button> -->
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
                  <span v-if="hedgeTaskStatus.yesTaskId" class="hedge-task-status" :class="getStatusClass(hedgeTaskStatus.yesStatus, hedgeTaskStatus.yesTaskMsg)">
                    Yes任务#{{ hedgeTaskStatus.yesTaskId }}: {{ getStatusText(hedgeTaskStatus.yesStatus, hedgeTaskStatus.yesTaskMsg) }}
                  </span>
                  <span v-if="hedgeTaskStatus.noTaskId" class="hedge-task-status" :class="getStatusClass(hedgeTaskStatus.noStatus, hedgeTaskStatus.noTaskMsg)">
                    No任务#{{ hedgeTaskStatus.noTaskId }}: {{ getStatusText(hedgeTaskStatus.noStatus, hedgeTaskStatus.noTaskMsg) }}
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
                      {{ config.trending }}
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
                  :min="hedgeMode.isClose && hedgeMode.hedgeMode === 2 ? 20000 : 0"
                  @blur="validateDelayMs"
                />
                <span v-if="hedgeMode.isClose && hedgeMode.hedgeMode === 2" style="font-size: 0.75rem; color: #666; margin-left: 8px;">
                  平仓模式2：最小延时20秒（20000ms）
                </span>
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
          <div class="trending-filter">
            <label>当前状态:</label>
            <select v-model="editConfigStatusFilter" class="filter-select">
              <option value="">全部</option>
              <option value="已拉黑">已拉黑</option>
              <option value="未添加">未添加</option>
              <option value="待执行">待执行</option>
              <option value="进行中">进行中</option>
            </select>
          </div>
          <div class="trending-filter">
            <label>所属批次:</label>
            <select v-model="editConfigBatchFilter" class="filter-select">
              <option value="">全部</option>
              <option v-for="batch in availableBatches" :key="batch" :value="batch">{{ batch }}</option>
            </select>
          </div>
          <div class="trending-filter">
            <label>今日最大开单量:</label>
            <input 
              v-model.number="bulkMaxDailyAmount" 
              type="number" 
              class="filter-input" 
              placeholder="输入最大开单量"
              min="0"
              step="0.01"
              style="width: 150px;"
            />
            <button 
              type="button" 
              class="btn btn-primary btn-sm" 
              @click="applyBulkMaxDailyAmount"
              style="margin-left: 8px;"
            >
              一键填入
            </button>
          </div>
          <button type="button" class="btn btn-danger btn-sm" @click="disableAllConfigs">
            全部禁用
          </button>
          <button type="button" class="btn btn-success btn-sm" @click="enableAllConfigs">
            全部启用
          </button>
          <button type="button" class="btn btn-secondary btn-sm" @click="showAllConfigs">
            全部显示
          </button>
          <button type="button" class="btn btn-secondary btn-sm" @click="hideAllConfigs">
            全部隐藏
          </button>
          <button type="button" class="btn btn-warning btn-sm" @click="cancelAllBlacklist">
            取消所有拉黑
          </button>
          <button type="button" class="btn btn-success btn-sm" @click="showOnlyValidOrderbooks" :class="{ 'btn-active': showOnlyValid }">
            {{ showOnlyValid ? '显示全部' : '只显示符合对冲条件的' }}
          </button>
          <button type="button" class="btn btn-info btn-sm" @click="fetchAllOrderbooks" :disabled="isFetchingOrderbooks">
            {{ isFetchingOrderbooks ? '获取中...' : '获取主题订单薄' }}
          </button>
        </div>
        <div class="config-list">
          <div v-if="filteredEditConfigList.length === 0" class="empty">{{ editConfigList.length === 0 ? '暂无配置' : '没有匹配的配置' }}</div>
          <div v-else class="config-table-wrapper">
            <table class="config-table">
              <thead>
                <tr>
                  <th style="width: 50px;">序号</th>
                  <th style="width: 80px;">ID</th>
                  <th style="width: 100px;">启用</th>
                  <th style="width: 100px;">显示</th>
                  <th style="width: 400px;">Trending *</th>
                  <th style="width: 300px;">Opinion Trade URL *</th>
                  <th style="width: 100px;">权重 *</th>
                  <th style="width: 100px;">所属批次</th>
                  <th style="width: 100px;">分组</th>
                  <th style="width: 100px;">是否拉黑</th>
                  <th style="width: 100px;">当前状态</th>
                  <th style="width: 200px;">当前订单薄</th>
                  <th style="width: 100px;">评分</th>
                  <th style="width: 120px;">今日开单量</th>
                  <th style="width: 150px;">今日最大开单量</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(config, index) in filteredEditConfigList" :key="index" class="config-table-row">
                  <td class="config-index">{{ index + 1 }}</td>
                  <td>{{ config.id || '-' }}</td>
                  <td>
                    <label class="switch-label">
                      <input 
                        type="checkbox" 
                        v-model="config.enabled" 
                        class="switch-checkbox"
                      />
                      <span class="switch-slider"></span>
                      <span class="switch-text">{{ config.enabled ? '启用' : '禁用' }}</span>
                    </label>
                  </td>
                  <td>
                    <label class="switch-label">
                      <input 
                        type="checkbox" 
                        v-model="config.visible" 
                        class="switch-checkbox"
                      />
                      <span class="switch-slider"></span>
                      <span class="switch-text">{{ config.visible ? '显示' : '隐藏' }}</span>
                    </label>
                  </td>
                  <td>
                    <input v-model="config.trending" type="text" required class="table-input" />
                  </td>
                  <td>
                    <input v-model="config.opUrl" type="text" required class="table-input" />
                  </td>
                  <td>
                    <input v-model.number="config.weight" type="number" required placeholder="权重" min="0" class="table-input" />
                  </td>
                  <td>
                    <span>{{ getConfigBatch(config) || '-' }}</span>
                  </td>
                  <td>
                    <input 
                      v-model="config.group" 
                      type="text" 
                      placeholder="分组" 
                      class="table-input" 
                    />
                  </td>
                  <td>
                    <label class="switch-label">
                      <input 
                        type="checkbox" 
                        v-model="config.isBlacklisted" 
                        class="switch-checkbox"
                        @change="saveConfigBlacklist(config)"
                      />
                      <span class="switch-slider"></span>
                      <span class="switch-text">{{ config.isBlacklisted ? '已拉黑' : '未拉黑' }}</span>
                    </label>
                  </td>
                  <td>
                    <span :class="getConfigStatusClass(config)">{{ getConfigStatus(config) }}</span>
                  </td>
                  <td>
                    <div v-if="config.orderbookInfo" 
                         :class="['orderbook-display', config.orderbookInfo.meetsCondition ? 'orderbook-valid' : 'orderbook-invalid']">
                      <div class="orderbook-line">
                        <span class="orderbook-label">先挂:</span>
                        <span>{{ config.orderbookInfo.firstSide }}</span>
                      </div>
                      <div class="orderbook-line">
                        <span class="orderbook-label">买一:</span>
                        <span>{{ config.orderbookInfo.price1.toFixed(2) }}¢</span>
                        <span class="orderbook-depth">({{ config.orderbookInfo.depth1.toFixed(2) }})</span>
                      </div>
                      <div class="orderbook-line">
                        <span class="orderbook-label">卖一:</span>
                        <span>{{ config.orderbookInfo.price2.toFixed(2) }}¢</span>
                        <span class="orderbook-depth">({{ config.orderbookInfo.depth2.toFixed(2) }})</span>
                      </div>
                    </div>
                    <div v-else class="orderbook-empty">未获取</div>
                  </td>
                  <td>
                    <input 
                      v-model.number="config.rating" 
                      type="number" 
                      placeholder="评分" 
                      class="table-input" 
                      @blur="saveConfigRating(config)"
                    />
                  </td>
                  <td>
                    <span>{{ config.currentAmt !== undefined && config.currentAmt !== null ? config.currentAmt.toFixed(2) : '0.00' }}</span>
                  </td>
                  <td>
                    <input 
                      v-model="config.editMaxDailyAmount" 
                      type="number" 
                      :placeholder="config.c !== undefined && config.c !== null && config.c !== '' ? config.c : '未设置'"
                      min="0"
                      step="0.01"
                      class="table-input"
                      style="width: 100%;"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="quick-blacklist-section" style="padding: 15px; border-top: 1px solid #e0e0e0; background-color: #f9f9f9;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <label style="font-size: 14px; font-weight: 500; white-space: nowrap;">快速拉黑主题:</label>
            <input 
              v-model="quickBlacklistInput" 
              type="text" 
              class="filter-input" 
              placeholder="输入主题名，用分号(;)分隔，可从事件异常页面复制"
              style="flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
            />
            <button 
              type="button" 
              class="btn btn-danger" 
              @click="quickBlacklist"
              style="padding: 8px 16px; font-size: 14px; white-space: nowrap;"
            >
              快速拉黑
            </button>
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
                <span v-if="log.isMode2" class="log-mode-badge">模式2</span>
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
                
                <!-- 模式1：原有展示方式 -->
                <template v-if="!log.isMode2">
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
                    <span>{{ log.yesNumber }} - {{ getStatusText(log.yesStatus, log.yesTaskMsg) }}</span>
                  </div>
                  <div class="log-row">
                    <span class="log-label">NO浏览器:</span>
                    <span>{{ log.noNumber }} - {{ getStatusText(log.noStatus, log.noTaskMsg) }}</span>
                  </div>
                </template>
                
                <!-- 模式2：多任务展示方式 -->
                <template v-else>
                  <div class="log-row">
                    <span class="log-label">先挂:</span>
                    <span>{{ log.firstSide }}</span>
                  </div>
                  <div v-if="log.yesTasks && log.yesTasks.length > 0" class="log-row">
                    <span class="log-label">YES任务 ({{ log.yesTasks.length }}个):</span>
                    <div class="log-task-list">
                      <div v-for="(task, taskIndex) in log.yesTasks" :key="taskIndex" class="log-task-item">
                        浏览器{{ task.number }} | 任务{{ task.taskId || '-' }} | 数量{{ task.share }} | {{ getStatusText(task.status, task.msg) }}
                      </div>
                    </div>
                  </div>
                  <div v-if="log.noTasks && log.noTasks.length > 0" class="log-row">
                    <span class="log-label">NO任务 ({{ log.noTasks.length }}个):</span>
                    <div class="log-task-list">
                      <div v-for="(task, taskIndex) in log.noTasks" :key="taskIndex" class="log-task-item">
                        浏览器{{ task.number }} | 任务{{ task.taskId || '-' }} | 数量{{ task.share }} | {{ getStatusText(task.status, task.msg) }}
                      </div>
                    </div>
                  </div>
                  <div v-if="log.allTaskIds && log.allTaskIds.length > 0" class="log-row">
                    <span class="log-label">任务ID组:</span>
                    <span>{{ log.allTaskIds.join(', ') }}</span>
                  </div>
                </template>
                
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
                <button 
                  class="btn-fetch-server-data" 
                  @click="fetchServerData(log)"
                  :disabled="isFetchingServerData(log)"
                  style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                >
                  {{ isFetchingServerData(log) ? '获取中...' : '获取服务器数据' }}
                </button>
                <span 
                  class="compact-status-badge"
                  :class="getHedgeLogStatusClass(log)"
                >
                  {{ getHedgeLogStatusText(log) }}
                </span>
                <span class="compact-log-mode">{{ log.isClose ? '平仓' : '开仓' }}</span>
                <span v-if="log.isMode2" class="compact-log-mode-badge">模式2</span>
                <span class="compact-log-info">
                  <template v-if="!log.isMode2">
                    价格:{{ log.price }} | 数量:{{ log.share }} | 先挂:{{ log.firstSide }}
                  </template>
                  <template v-else>
                    价格:{{ log.price }} | 先挂:{{ log.firstSide }} | 
                    YES:{{ log.yesTasks ? log.yesTasks.length : 0 }}个 | 
                    NO:{{ log.noTasks ? log.noTasks.length : 0 }}个
                  </template>
                </span>
                <span class="compact-log-time">{{ formatCompactTime(log.startTime) }}</span>
                <span v-if="log.duration" class="compact-log-duration">{{ log.duration }}分</span>
              </div>
              <div class="compact-log-details">
                <!-- 模式1：原有展示方式 -->
                <template v-if="!log.isMode2">
                  <div class="compact-task-row">
                    <span class="task-label">YES:</span>
                    <span class="task-info">
                      <span class="task-group">组{{ log.yesGroupNo || '-' }}</span> | 
                      浏览器{{ log.yesNumber }} | 
                      任务{{ log.yesTaskId || '-' }} | 
                      <span :class="getTaskStatusClass(log.yesStatus, log.yesTaskMsg)">{{ getStatusText(log.yesStatus, log.yesTaskMsg) }}</span>
                      <span v-if="log.yesTaskMsg" class="task-msg">| {{ formatTaskMsg(log.yesTaskMsg) }}</span>
                      <span v-if="log.yesNumber && log.trendingName" class="on-chain-balance">
                        | 链上余额:
                        <span :class="['balance-value', 
                          log.yesOnChainBalance === undefined || log.yesOnChainBalance === '' ? 'loading' : 
                          log.yesOnChainBalance === '获取失败' ? 'error' : 'success']">
                          {{ log.yesOnChainBalance === undefined || log.yesOnChainBalance === '' ? '加载中...' : log.yesOnChainBalance }}
                        </span>
                        <button 
                          class="btn-view-log" 
                          @click="openBroLogDialog(log.yesNumber)"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          查看日志
                        </button>
                      </span>
                    </span>
                  </div>
                  <!-- YES服务器数据 -->
                  <div v-if="log.yesServerData" class="server-data-section">
                    <div v-if="(!log.yesServerData.openOrderList || log.yesServerData.openOrderList.length === 0) && (!log.yesServerData.closedOrderList || log.yesServerData.closedOrderList.length === 0)" class="server-data-empty">
                      暂无服务器数据
                    </div>
                    <div v-else>
                      <!-- 挂单数据 -->
                      <div v-if="log.yesServerData.openOrderList && log.yesServerData.openOrderList.length > 0" class="server-data-group">
                        <div class="server-data-title">挂单数据:</div>
                        <div v-for="(order, idx) in log.yesServerData.openOrderList" :key="idx" class="server-data-item">
                          <span>
                            创建时间: {{ timestampToBeijingTime(order.ctime) }} | 
                            方向: {{ formatSide(order.side) }} | 
                            结果: {{ order.outCome }} | 
                            价格: {{ order.price }} | 
                            进度: {{ ((order.amt - order.restAmt) / order.amt * 100).toFixed(2) }}% ({{ (order.amt - order.restAmt).toFixed(2) }}/{{ order.amt }})
                          </span>
                          <button 
                            class="btn-save-success" 
                            @click="saveTaskAsSuccess(log, log.yesTaskId, formatOpenOrderMsg(order), 'yes')"
                            :disabled="log.yesStatus === 2"
                          >
                            保存为成功
                          </button>
                        </div>
                      </div>
                      <!-- 已成交数据 -->
                      <div v-if="log.yesServerData.closedOrderList && log.yesServerData.closedOrderList.length > 0" class="server-data-group">
                        <div class="server-data-title">已成交数据:</div>
                        <div v-for="(order, idx) in log.yesServerData.closedOrderList" :key="idx" class="server-data-item">
                          <span>
                            时间: {{ order.convertTime ? timestampToBeijingTime(order.convertTime) : timestampToBeijingTime(order.time, true) }}{{ !order.convertTime ? ' (不同时区)' : '' }} | 
                            方向: {{ formatSide(order.side) }} | 
                            结果: {{ order.outCome }} | 
                            价格: {{ order.price }} | 
                            进度: {{ ((order.fillAmt / order.amt) * 100).toFixed(2) }}% ({{ order.fillAmt }}/{{ order.amt }}) | 
                            状态: {{ order.status }}
                          </span>
                          <button 
                            class="btn-save-success" 
                            @click="saveTaskAsSuccess(log, log.yesTaskId, formatClosedOrderMsg(order), 'yes')"
                            :disabled="log.yesStatus === 2"
                          >
                            保存为成功
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="compact-task-row">
                    <span class="task-label">NO:</span>
                    <span class="task-info">
                      <span class="task-group">组{{ log.noGroupNo || '-' }}</span> | 
                      浏览器{{ log.noNumber }} | 
                      任务{{ log.noTaskId || '-' }} | 
                      <span :class="getTaskStatusClass(log.noStatus, log.noTaskMsg)">{{ getStatusText(log.noStatus, log.noTaskMsg) }}</span>
                      <span v-if="log.noTaskMsg" class="task-msg">| {{ formatTaskMsg(log.noTaskMsg) }}</span>
                      <span v-if="log.noNumber && log.trendingName" class="on-chain-balance">
                        | 链上余额:
                        <span :class="['balance-value', 
                          log.noOnChainBalance === undefined || log.noOnChainBalance === '' ? 'loading' : 
                          log.noOnChainBalance === '获取失败' ? 'error' : 'success']">
                          {{ log.noOnChainBalance === undefined || log.noOnChainBalance === '' ? '加载中...' : log.noOnChainBalance }}
                        </span>
                        <button 
                          class="btn-view-log" 
                          @click="openBroLogDialog(log.noNumber)"
                          style="margin-left: 8px; padding: 2px 8px; font-size: 12px;"
                        >
                          查看日志
                        </button>
                      </span>
                    </span>
                  </div>
                  <!-- NO服务器数据 -->
                  <div v-if="log.noServerData" class="server-data-section">
                    <div v-if="(!log.noServerData.openOrderList || log.noServerData.openOrderList.length === 0) && (!log.noServerData.closedOrderList || log.noServerData.closedOrderList.length === 0)" class="server-data-empty">
                      暂无服务器数据
                    </div>
                    <div v-else>
                      <!-- 挂单数据 -->
                      <div v-if="log.noServerData.openOrderList && log.noServerData.openOrderList.length > 0" class="server-data-group">
                        <div class="server-data-title">挂单数据:</div>
                        <div v-for="(order, idx) in log.noServerData.openOrderList" :key="idx" class="server-data-item">
                          <span>
                            创建时间: {{ timestampToBeijingTime(order.ctime) }} | 
                            方向: {{ formatSide(order.side) }} | 
                            结果: {{ order.outCome }} | 
                            价格: {{ order.price }} | 
                            进度: {{ ((order.amt - order.restAmt) / order.amt * 100).toFixed(2) }}% ({{ (order.amt - order.restAmt).toFixed(2) }}/{{ order.amt }})
                          </span>
                          <button 
                            class="btn-save-success" 
                            @click="saveTaskAsSuccess(log, log.noTaskId, formatOpenOrderMsg(order), 'no')"
                            :disabled="log.noStatus === 2"
                          >
                            保存为成功
                          </button>
                        </div>
                      </div>
                      <!-- 已成交数据 -->
                      <div v-if="log.noServerData.closedOrderList && log.noServerData.closedOrderList.length > 0" class="server-data-group">
                        <div class="server-data-title">已成交数据:</div>
                        <div v-for="(order, idx) in log.noServerData.closedOrderList" :key="idx" class="server-data-item">
                          <span>
                            时间: {{ order.convertTime ? timestampToBeijingTime(order.convertTime) : timestampToBeijingTime(order.time, true) }}{{ !order.convertTime ? ' (不同时区)' : '' }} | 
                            方向: {{ formatSide(order.side) }} | 
                            结果: {{ order.outCome }} | 
                            价格: {{ order.price }} | 
                            进度: {{ ((order.fillAmt / order.amt) * 100).toFixed(2) }}% ({{ order.fillAmt }}/{{ order.amt }}) | 
                            状态: {{ order.status }}
                          </span>
                          <button 
                            class="btn-save-success" 
                            @click="saveTaskAsSuccess(log, log.noTaskId, formatClosedOrderMsg(order), 'no')"
                            :disabled="log.noStatus === 2"
                          >
                            保存为成功
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
                
                <!-- 模式2：多任务展示方式 -->
                <template v-else>
                  <!-- YES任务：优先显示已提交的任务，如果没有则显示计划任务 -->
                  <div v-if="(log.yesTasks && log.yesTasks.length > 0) || (log.yesList && log.yesList.length > 0)" class="compact-task-row">
                    <span class="task-label">YES ({{ (log.yesTasks && log.yesTasks.length > 0) ? log.yesTasks.length : (log.yesList ? log.yesList.length : 0) }}个):</span>
                    <span class="task-info">
                      <template v-if="log.yesTasks && log.yesTasks.length > 0">
                        <!-- 显示已提交的任务 -->
                        <template v-for="(task, taskIndex) in log.yesTasks" :key="taskIndex">
                          <span class="task-group">组{{ task.groupNo || '-' }}</span> | 
                          浏览器{{ task.number }} | 
                          任务{{ task.taskId || '-' }} | 
                          数量{{ task.share }} | 
                          <span :class="getTaskStatusClass(task.status, task.msg)">{{ getStatusText(task.status, task.msg) }}</span>
                          <span v-if="task.msg" class="task-msg">| {{ formatTaskMsg(task.msg) }}</span>
                          <span v-if="taskIndex < log.yesTasks.length - 1">; </span>
                        </template>
                      </template>
                      <template v-else-if="log.yesList && log.yesList.length > 0">
                        <!-- 显示计划任务（还未提交） -->
                        <template v-for="(item, itemIndex) in log.yesList" :key="itemIndex">
                          <span class="task-group">组{{ getGroupNo(item.number) }}</span> | 
                          浏览器{{ item.number }} | 
                          任务待提交 | 
                          数量{{ item.share }} | 
                          <span class="task-pending">待提交</span>
                          <span v-if="itemIndex < log.yesList.length - 1">; </span>
                        </template>
                      </template>
                    </span>
                  </div>
                  <!-- YES任务服务器数据 -->
                  <template v-if="log.yesTasks && log.yesTasks.length > 0">
                    <div v-for="(task, taskIndex) in log.yesTasks" :key="`yes-server-${taskIndex}`" v-if="task.serverData" class="server-data-section">
                      <div class="server-data-task-label">浏览器{{ task.number }} 服务器数据:</div>
                      <div v-if="(!task.serverData.openOrderList || task.serverData.openOrderList.length === 0) && (!task.serverData.closedOrderList || task.serverData.closedOrderList.length === 0)" class="server-data-empty">
                        暂无服务器数据
                      </div>
                      <div v-else>
                        <!-- 挂单数据 -->
                        <div v-if="task.serverData.openOrderList && task.serverData.openOrderList.length > 0" class="server-data-group">
                          <div class="server-data-title">挂单数据:</div>
                          <div v-for="(order, idx) in task.serverData.openOrderList" :key="idx" class="server-data-item">
                            <span>
                              创建时间: {{ timestampToBeijingTime(order.ctime) }} | 
                              方向: {{ formatSide(order.side) }} | 
                              结果: {{ order.outCome }} | 
                              价格: {{ order.price }} | 
                              进度: {{ ((order.amt - order.restAmt) / order.amt * 100).toFixed(2) }}% ({{ (order.amt - order.restAmt).toFixed(2) }}/{{ order.amt }})
                            </span>
                            <button 
                              class="btn-save-success" 
                              @click="saveTaskAsSuccess(log, task.taskId, formatOpenOrderMsg(order), 'mode2')"
                              :disabled="task.status === 2"
                            >
                              保存为成功
                            </button>
                          </div>
                        </div>
                        <!-- 已成交数据 -->
                        <div v-if="task.serverData.closedOrderList && task.serverData.closedOrderList.length > 0" class="server-data-group">
                          <div class="server-data-title">已成交数据:</div>
                          <div v-for="(order, idx) in task.serverData.closedOrderList" :key="idx" class="server-data-item">
                            <span>
                              时间: {{ order.convertTime ? timestampToBeijingTime(order.convertTime) : timestampToBeijingTime(order.time, true) }}{{ !order.convertTime ? ' (不同时区)' : '' }} | 
                              方向: {{ formatSide(order.side) }} | 
                              结果: {{ order.outCome }} | 
                              价格: {{ order.price }} | 
                              进度: {{ ((order.fillAmt / order.amt) * 100).toFixed(2) }}% ({{ order.fillAmt }}/{{ order.amt }}) | 
                              状态: {{ order.status }}
                            </span>
                            <button 
                              class="btn-save-success" 
                              @click="saveTaskAsSuccess(log, task.taskId, formatClosedOrderMsg(order), 'mode2')"
                              :disabled="task.status === 2"
                            >
                              保存为成功
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                  <!-- NO任务：优先显示已提交的任务，如果没有则显示计划任务 -->
                  <div v-if="(log.noTasks && log.noTasks.length > 0) || (log.noList && log.noList.length > 0)" class="compact-task-row">
                    <span class="task-label">NO ({{ (log.noTasks && log.noTasks.length > 0) ? log.noTasks.length : (log.noList ? log.noList.length : 0) }}个):</span>
                    <span class="task-info">
                      <template v-if="log.noTasks && log.noTasks.length > 0">
                        <!-- 显示已提交的任务 -->
                        <template v-for="(task, taskIndex) in log.noTasks" :key="taskIndex">
                          <span class="task-group">组{{ task.groupNo || '-' }}</span> | 
                          浏览器{{ task.number }} | 
                          任务{{ task.taskId || '-' }} | 
                          数量{{ task.share }} | 
                          <span :class="getTaskStatusClass(task.status, task.msg)">{{ getStatusText(task.status, task.msg) }}</span>
                          <span v-if="task.msg" class="task-msg">| {{ formatTaskMsg(task.msg) }}</span>
                          <span v-if="taskIndex < log.noTasks.length - 1">; </span>
                        </template>
                      </template>
                      <template v-else-if="log.noList && log.noList.length > 0">
                        <!-- 显示计划任务（还未提交） -->
                        <template v-for="(item, itemIndex) in log.noList" :key="itemIndex">
                          <span class="task-group">组{{ getGroupNo(item.number) }}</span> | 
                          浏览器{{ item.number }} | 
                          任务待提交 | 
                          数量{{ item.share }} | 
                          <span class="task-pending">待提交</span>
                          <span v-if="itemIndex < log.noList.length - 1">; </span>
                        </template>
                      </template>
                    </span>
                  </div>
                  <!-- NO任务服务器数据 -->
                  <template v-if="log.noTasks && log.noTasks.length > 0">
                    <div v-for="(task, taskIndex) in log.noTasks" :key="`no-server-${taskIndex}`" v-if="task.serverData" class="server-data-section">
                      <div class="server-data-task-label">浏览器{{ task.number }} 服务器数据:</div>
                      <div v-if="(!task.serverData.openOrderList || task.serverData.openOrderList.length === 0) && (!task.serverData.closedOrderList || task.serverData.closedOrderList.length === 0)" class="server-data-empty">
                        暂无服务器数据
                      </div>
                      <div v-else>
                        <!-- 挂单数据 -->
                        <div v-if="task.serverData.openOrderList && task.serverData.openOrderList.length > 0" class="server-data-group">
                          <div class="server-data-title">挂单数据:</div>
                          <div v-for="(order, idx) in task.serverData.openOrderList" :key="idx" class="server-data-item">
                            <span>
                              创建时间: {{ timestampToBeijingTime(order.ctime) }} | 
                              方向: {{ formatSide(order.side) }} | 
                              结果: {{ order.outCome }} | 
                              价格: {{ order.price }} | 
                              进度: {{ ((order.amt - order.restAmt) / order.amt * 100).toFixed(2) }}% ({{ (order.amt - order.restAmt).toFixed(2) }}/{{ order.amt }})
                            </span>
                            <button 
                              class="btn-save-success" 
                              @click="saveTaskAsSuccess(log, task.taskId, formatOpenOrderMsg(order), 'mode2')"
                              :disabled="task.status === 2"
                            >
                              保存为成功
                            </button>
                          </div>
                        </div>
                        <!-- 已成交数据 -->
                        <div v-if="task.serverData.closedOrderList && task.serverData.closedOrderList.length > 0" class="server-data-group">
                          <div class="server-data-title">已成交数据:</div>
                          <div v-for="(order, idx) in task.serverData.closedOrderList" :key="idx" class="server-data-item">
                            <span>
                              时间: {{ order.convertTime ? timestampToBeijingTime(order.convertTime) : timestampToBeijingTime(order.time, true) }}{{ !order.convertTime ? ' (不同时区)' : '' }} | 
                              方向: {{ formatSide(order.side) }} | 
                              结果: {{ order.outCome }} | 
                              价格: {{ order.price }} | 
                              进度: {{ ((order.fillAmt / order.amt) * 100).toFixed(2) }}% ({{ order.fillAmt }}/{{ order.amt }}) | 
                              状态: {{ order.status }}
                            </span>
                            <button 
                              class="btn-save-success" 
                              @click="saveTaskAsSuccess(log, task.taskId, formatClosedOrderMsg(order), 'mode2')"
                              :disabled="task.status === 2"
                            >
                              保存为成功
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                  <div v-if="log.allTaskIds && log.allTaskIds.length > 0" class="compact-task-row">
                    <span class="task-label">任务ID组:</span>
                    <span class="task-info">{{ log.allTaskIds.join(', ') }}</span>
                  </div>
                </template>
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
    
    <!-- 交易费详情弹窗 -->
    <div v-if="showFeeDetailDialog" class="modal-overlay" @click="showFeeDetailDialog = false">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>链上手续费详情</h3>
          <button class="modal-close" @click="showFeeDetailDialog = false">×</button>
        </div>
        <div class="modal-body">
          <table class="data-table" style="width: 100%;">
            <thead>
              <tr>
                <th>浏览器编号</th>
                <th>电脑组</th>
                <th>地址</th>
                <th>手续费</th>
                <th>交易笔数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in sortedFeeAddresses" :key="index">
                <td>{{ item.fingerprint_no }}</td>
                <td>{{ getGroupNo(item.fingerprint_no) }}</td>
                <td style="word-break: break-all; max-width: 300px;">{{ item.wallet_address }}</td>
                <td>${{ item.total_fee.toFixed(6) }}</td>
                <td>{{ item.transaction_count }}</td>
              </tr>
              <tr v-if="!sortedFeeAddresses || sortedFeeAddresses.length === 0">
                <td colspan="5" style="text-align: center; padding: 20px;">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="showFeeDetailDialog = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 未刷新浏览器弹窗 -->
    <div v-if="showUnrefreshedBrowsersDialog" class="modal-overlay" @click="showUnrefreshedBrowsersDialog = false">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>上一轮仓位未刷新浏览器列表 (共 {{ groupExecution.unrefreshedBrowsers.length }} 个)</h3>
          <button class="modal-close" @click="showUnrefreshedBrowsersDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div style="max-height: 500px; overflow-y: auto;">
            <div v-if="groupExecution.unrefreshedBrowsers.length === 0" style="text-align: center; padding: 20px; color: #999;">
              暂无未刷新的浏览器
            </div>
            <table v-else class="config-table" style="width: 100%; margin-top: 10px;">
              <thead>
                <tr>
                  <th style="width: 150px;">浏览器编号</th>
                  <th style="width: 100px;">电脑组</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(browserInfo, index) in (groupExecution.unrefreshedBrowserInfo.length > 0 ? groupExecution.unrefreshedBrowserInfo : groupExecution.unrefreshedBrowsers.map(id => ({ fingerprintNo: id, computeGroup: '-' })))" :key="index">
                  <td>{{ browserInfo.fingerprintNo }}</td>
                  <td>{{ browserInfo.computeGroup }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="showUnrefreshedBrowsersDialog = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 未完成type2任务浏览器弹窗 -->
    <div v-if="showUnfinishedType2Dialog" class="modal-overlay" @click="showUnfinishedType2Dialog = false">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>未完成type2任务浏览器列表 (共 {{ unfinishedType2Browsers.length }} 个)</h3>
          <button class="modal-close" @click="showUnfinishedType2Dialog = false">×</button>
        </div>
        <div class="modal-body">
          <div style="max-height: 500px; overflow-y: auto;">
            <div v-if="unfinishedType2Browsers.length === 0" style="text-align: center; padding: 20px; color: #999;">
              暂无未完成type2任务的浏览器
            </div>
            <table v-else class="config-table" style="width: 100%; margin-top: 10px;">
              <thead>
                <tr>
                  <th style="width: 150px;">浏览器编号</th>
                  <th style="width: 100px;">电脑组</th>
                  <th style="width: 200px;">任务ID</th>
                  <th style="width: 100px;">任务状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(browserInfo, index) in unfinishedType2Browsers" :key="index">
                  <td>{{ browserInfo.fingerprintNo }}</td>
                  <td>{{ browserInfo.computeGroup }}</td>
                  <td>{{ browserInfo.taskId || '-' }}</td>
                  <td>{{ getTaskStatusText(browserInfo.status) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="showUnfinishedType2Dialog = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
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
const isQuickSelecting = ref(false)  // 是否正在自动获取
const trendingSearchText = ref('')  // Trending搜索文本
const showTrendingDropdown = ref(false)  // 是否显示Trending下拉列表
const blackListText = ref('')  // 拉黑的浏览器列表

// 查询功能相关
const queryTrendingSearchText = ref('')  // 查询Trending搜索文本
const showQueryTrendingDropdown = ref(false)  // 是否显示查询Trending下拉列表
const querySelectedConfig = ref(null)  // 查询选中的配置
const isQuerying = ref(false)  // 是否正在查询
const isTesting = ref(false)  // 是否正在测试
const queryResult = ref(null)  // 查询结果
const testResult = ref(null)  // 测试结果
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
const originalConfigList = ref([])  // 保存原始配置数据，用于比较是否修改
const isFetchingOrderbooks = ref(false)  // 是否正在获取订单薄

// 配置筛选
const autoHedgeFilter = ref('')  // 自动对冲功能块的筛选
const editConfigFilter = ref('')  // 修改配置弹窗的筛选
const showOnlyValid = ref(false)  // 是否只显示符合对冲条件的
const editConfigStatusFilter = ref('')  // 修改配置弹窗的状态筛选
const editConfigBatchFilter = ref('')  // 修改配置弹窗的批次筛选
const quickBlacklistInput = ref('')  // 快速拉黑输入框内容
const bulkMaxDailyAmount = ref(null)  // 批量设置最大开单量的值
const selectedGroup = ref('default')  // 当前选择的分组：default/1/2
const selectedNumberType = ref('2')  // 账号类型：1-全部账户, 2-1000个账户, 3-1000个账户中未达标的
const isFastMode = ref(false)  // 模式开关：false=正常模式(tp3=0), true=快速模式(tp3=1)
const yesCountThreshold = ref(0)  // yes数量阈值
const isFetchingTopics = ref(false)  // 是否正在获取主题

// 分组执行相关
const groupExecution = reactive({
  isRunning: false,
  roundTimeHours: 2,  // 每轮时间（小时）
  intervalMinutes: 15,  // 每轮间隔时间（分钟）
  timer: null,  // 定时器
  intervalTimer: null,  // 间隔定时器
  currentRoundStartTime: null,  // 当前轮开始时间戳
  previousRoundEndTime: null,  // 上一轮结束时间戳（即当前轮开始时间）
  checkTimer: null,  // 检查定时器
  unrefreshedCount: 0,  // 上一轮仓位未刷新数量
  unrefreshedBrowsers: [],  // 未刷新的浏览器ID列表
  unrefreshedBrowserInfo: []  // 未刷新的浏览器详细信息（包含电脑组）
})

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
const isAccountConfigMapped = ref(false)  // 账户配置是否成功映射

// 自动对冲相关
const autoHedgeRunning = ref(false)
const autoHedgeInterval = ref(null)
const activeConfigs = ref([])  // 启用的配置列表
const lastRoundTaskCount = ref(0)  // 上一轮开出的任务总数
const lastRoundEndTime = ref(null)  // 上一轮结束时间
const hedgeStatusInterval = ref(null)  // 对冲状态轮询定时器
const configAutoRefreshInterval = ref(null)  // 配置自动刷新定时器（每小时05分）
const isRandomGetting = ref(false)  // 是否正在随机获取主题
const randomGetCount = ref(1)  // 一次性获取的主题数量
const positionTopics = ref(new Set())  // 持仓主题列表（用于平仓时判断）
const failedTopics = ref([])  // 请求失败的主题列表（API rate limit exceeded）
const hedgeTasksPerTopic = ref(2)  // 一个主题同时执行的对冲任务数量，默认为2
const hedgeMaxTasksPerRound = ref(2)  // 每一轮每个主题最多任务数，默认为10
const hedgeTaskInterval = ref(0)  // 任务间隔（分钟），默认为0（不等待）
const runningHedgeGroupsCount = ref(0)  // 当前正在运行的任务组数

// 自动对冲排序相关
const hedgeSortBy = ref('')  // 排序方式: '' 默认按持仓, 'yesAmt' 按YES金额, 'weightedAvgTime' 按创建时间加权平均值, 'volume24h' 按24h量, 'volume7dAvg' 按7天平均量

// 分批执行相关
const enableBatchMode = ref(false)  // 是否启用分批执行模式，默认不勾选
const batchSize = ref(10)  // 每一批的个数

// 持仓数据相关
const positionDataMap = ref(new Map())  // 存储每个事件的持仓数据，key为事件名(trending)，value为{yesPosition, noPosition}
const idToTrendingMap = ref(new Map())  // 存储 id -> trending 的映射
const testingConfigIds = ref(new Set())  // 正在测试的配置ID集合
const savingMaxDailyAmountIds = ref(new Set())  // 正在保存最大开单量的配置ID集合
const updatingOrderbookConfigIds = ref(new Set())  // 正在更新订单薄的配置ID集合
const batchExecutionTime = ref(1)  // 每一批的执行时间（分钟），默认1分钟
const currentBatchIndex = ref(0)  // 当前执行批次索引
const batchTimer = ref(null)  // 批次定时器

// 订单薄API配置
const ORDERBOOK_API_KEY = 'xbR1ek3ekhnhykU8aZdvyAb6vRFcmqpU'
const ORDERBOOK_API_URL = 'https://proxy.opinion.trade:8443/openapi/token/orderbook'

// 对冲状态（重命名以避免与下面的 hedgeStatus 冲突）
const hedgeStatus = reactive({
  amtSum: 0,  // 累计对冲数量
  amt: 0      // 总数量
})

// 对冲模式
const hedgeMode = reactive({
  isClose: false,  // false: 开仓, true: 平仓
  timePassMin: 60,  // 最近xx分钟内有过任意操作的，不参与
  minCloseMin: 60,  // 平仓使用：最近xx分钟内有过任意操作的，不参与
  intervalType: 'delay',  // 'success': 挂单成功再挂另一边, 'delay': 延时
  intervalDelay: 1000,  // 延时的毫秒数
  maxDepth: 100,  // 最大允许深度
  minUAmt: 10,  // 最小开单
  maxUAmt: 1500,  // 最大开单
  minCloseAmt: 500,  // 平仓最小数量（参数1）
  minTotalCloseAmt: 0,  // 合计最小平仓值（参数2）
  maxTotalCloseAmt: 0,  // 合计最大平仓值（参数3）
  takerMinAmt: 200,  // taker最小数量（参数4）
  hedgeMode: 1,  // 1: 模式1, 2: 模式2, 3: 模式3
  minOrderbookDepth: 3,  // 订单薄至少几组数据
  maxPriceDiff: 15,  // 买1-买3或卖1-卖3的最大价差
  priceRangeMin: 65,  // 先挂方价格区间最小值
  priceRangeMax: 85,  // 先挂方价格区间最大值
  minTotalDepth: 2000,  // 买1-N和卖1-N累加的最小深度
  maxOpenHour: 4,  // 可加仓时间（小时）
  closeOpenHourArea: '12,36',  // 可平仓随机区间（小时）
  maxIpDelay: '',  // ip最大延迟（毫秒）
  needJudgeDF: false,  // 是否过滤超时仓位
  maxDHour: 12,  // 仓位抓取时间距离现在超过的小时数（超过此时间的仓位不参与交易）
  needJudgeTimeRandom: 0,  // 账号随机8小时不交易，0-关闭 1-开启
  // 资产优先级校验设置
  needJudgeBalancePriority: 0,  // 是否需要校验资产优先级 0不要 1要
  balancePriority: 2000,  // 资产优先级校验值
  // 订单薄更新设置
  yesPositionThreshold: 0.2,  // yes持仓阈值（万），默认0.2万
  yesPositionCompareType: 'less',  // yes持仓比较类型：'less'（小于）或'greater'（大于），默认'less'
  maxVolume24hOpen: 99,  // 最近24小时交易量大于XX（万）不交易，默认99万
  maxVolume7dAvgOpen: 99,  // 最近7天平均交易量大于XX（万）不交易，默认99万
  maxPosWorthOpen: 99,  // 仓位价值大于XX（万）不开仓，默认0（不限制）
  orderbookMismatchInterval: 10,  // 订单薄不匹配时抓一轮的间隔时间（分钟），默认10分钟
  weightedTimeHourOpen: 0,  // 加权时间阈值（小时），默认0（不限制），适用于开仓和平仓模式
  weightedTimeCompareType: 'greater',  // 加权时间比较类型：'less'（小于）或'greater'（大于），默认'greater'
  weightedTimeYesPositionThreshold: 0,  // 加权时间条件中的yes持仓阈值（万），默认0（不限制）
  weightedTimeYesPositionCompareType: 'greater',  // 加权时间条件中的yes持仓比较类型：'less'（小于）或'greater'（大于），默认'greater'
  taskCountThreshold: 5,  // 每一轮任务个数阈值，默认5个
  waitTimeLessThanThreshold: 300,  // 小于阈值时的等待时间（秒），默认300秒（5分钟）
  waitTimeGreaterThanThreshold: 60,  // 大于阈值时的等待时间（秒），默认60秒（1分钟）
  // 模式一开仓专属设置
  posPriorityArea: '0.02,250',  // 优先开仓区间
  maxPosLimit: 3000,  // 开仓最大仓位限制
  // 深度差相关设置
  // 深度差阈值配置
  depthThreshold1: 15,  // 深度差阈值1（默认15）
  depthThreshold2: 2,   // 深度差阈值2（默认2）
  depthThreshold3: 0.2, // 深度差阈值3（默认0.2）
  // 各深度区间延时检测时间
  delayTimeGt15: '300,600',  // 深度差15以上挂单后延时检测时间（秒）
  delayTime2To15: '30,60',  // 深度差2-15挂单后延时检测时间（秒）
  delayTime02To2: '0.5,0.5',  // 深度差0.2-2挂单后延时检测时间（秒）
  maxEatValue01: 20,  // 深度差0.1时，最大多吃价值（U）
  // 各深度区间开关（控制是否传递tp2和tp4）
  enableDepthDiffParamsGt15: false,  // 深度差>阈值1的开关
  enableDepthDiffParams2To15: false, // 深度差阈值2-阈值1的开关
  enableDepthDiffParams02To2: false, // 深度差阈值3-阈值2的开关
  enableDepthDiffParams01: false,     // 深度差0.1的开关（控制是否执行逻辑C）
  // 各深度区间价格波动配置（百分比）
  priceVolatilityGt15Min: 1,   // 深度差>阈值1的价格波动最小值%
  priceVolatilityGt15Max: 10,  // 深度差>阈值1的价格波动最大值%
  priceVolatility2To15Min: 1,  // 深度差阈值2-阈值1的价格波动最小值%
  priceVolatility2To15Max: 10, // 深度差阈值2-阈值1的价格波动最大值%
  priceVolatility02To2Min: 1,  // 深度差阈值3-阈值2的价格波动最小值%
  priceVolatility02To2Max: 10, // 深度差阈值3-阈值2的价格波动最大值%
  // 兼容旧配置（保留，但不再使用）
  enableDepthDiffParams: false,  // 是否在mission/add请求中传递tp2和tp4参数（默认关闭）- 已废弃，使用各区间独立开关
  maxPriceVolatility: 10,  // 先挂方价格最大波动（买卖深度差的百分比）- 已废弃，使用各区间独立配置
  // 总任务数控制设置
  totalTaskCountOperator: 'lt',  // 总任务数比较操作符：gt=大于，lt=小于
  totalTaskCountThreshold: 999,  // 总任务数阈值
  openOrderCancelHours: 72  // 挂单超过XX小时撤单（默认72小时）
})

// 交易费查询
const feeQuery = reactive({
  startTime: '',
  endTime: '',
  totalFee: null,  // 本地手续费
  chainFee: null,  // 链上手续费
  feeAddresses: []  // 地址列表
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
const showUnrefreshedBrowsersDialog = ref(false)  // 显示未刷新浏览器弹窗
const showUnfinishedType2Dialog = ref(false)  // 显示未完成type2任务浏览器弹窗
const unfinishedType2Browsers = ref([])  // 未完成type2任务的浏览器列表
const isLoadingUnfinishedType2 = ref(false)  // 是否正在加载未完成type2任务
const currentLogConfig = ref(null)
const hedgeLogs = ref([])
const showAllHedgeLogsDialog = ref(false)  // 总日志弹窗
const allHedgeLogs = ref([])  // 所有对冲日志
const allHedgeLogsCurrentPage = ref(1)  // 总日志当前页
const allHedgeLogsPageSize = ref(10)  // 总日志每页显示数量
const fetchingServerDataLogs = ref(new Set())  // 正在获取服务器数据的日志ID集合

// 交易费详情弹窗
const showFeeDetailDialog = ref(false)

// 浏览器日志弹窗
const showBroLogDialog = ref(false)  // 浏览器日志弹窗
const broLogs = ref([])  // 浏览器日志列表
const currentBroNumber = ref(null)  // 当前查看的浏览器ID
const isLoadingBroLogs = ref(false)  // 是否正在加载日志

// 排序后的地址列表（按手续费从高到低）
const sortedFeeAddresses = computed(() => {
  if (!feeQuery.feeAddresses || feeQuery.feeAddresses.length === 0) {
    return []
  }
  // 按手续费从高到低排序
  return [...feeQuery.feeAddresses].sort((a, b) => {
    return (b.total_fee || 0) - (a.total_fee || 0)
  })
})

// 获取电脑组号（支持字符串和数字类型的fingerprint_no）
const getGroupNo = (fingerprintNo) => {
  if (!fingerprintNo || !browserToGroupMap.value) {
    return '-'
  }
  const fingerprintNoStr = String(fingerprintNo)
  const fingerprintNoNum = Number(fingerprintNo)
  // 先尝试字符串，再尝试数字
  return browserToGroupMap.value[fingerprintNoStr] || 
         browserToGroupMap.value[fingerprintNoNum] || 
         '-'
}

// 本地存储的对冲记录
const LOCAL_STORAGE_KEY = 'hedge_logs'
const HEDGE_SETTINGS_KEY = 'hedge_settings'
const MONITOR_BROWSER_KEY = 'monitor_browser_ids'
const CONFIG_VISIBLE_KEY = 'config_visible_status'  // 配置显示状态
const CONFIG_TOPIC_SETTINGS_KEY = 'config_topic_settings'  // 每个主题的设置（同时任务和最大允许深度）
const CONFIG_BLACKLIST_KEY = 'config_blacklist'  // 配置拉黑状态

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
      
      // 建立浏览器编号到组号的映射（同时支持字符串和数字作为key）
      const mapping = {}
      response.data.data.forEach(item => {
        if (item.fingerprintNo && item.computeGroup) {
          const fingerprintNo = item.fingerprintNo
          const fingerprintNoStr = String(fingerprintNo)
          const fingerprintNoNum = Number(fingerprintNo)
          // 同时用字符串和数字作为key，确保无论API返回什么类型都能匹配
          mapping[fingerprintNoStr] = item.computeGroup
          if (!isNaN(fingerprintNoNum)) {
            mapping[fingerprintNoNum] = item.computeGroup
          }
        }
      })
      browserToGroupMap.value = mapping
      
      // 检查映射是否成功（至少有一个映射关系）
      isAccountConfigMapped.value = Object.keys(mapping).length > 0
      
      console.log(`账户配置加载成功，共 ${response.data.data.length} 条记录`)
      console.log('浏览器编号到组号映射:', mapping)
    } else {
      console.warn('获取账户配置失败: 无数据')
      isAccountConfigMapped.value = false
    }
  } catch (error) {
    console.error('获取账户配置失败:', error)
    isAccountConfigMapped.value = false
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
  // 如果输入的内容完全匹配某个选项，自动选择
  const exactMatch = configList.value.find(config => {
    return config.trending === trendingSearchText.value
  })
  if (exactMatch) {
    formData.trendingId = String(exactMatch.id)
  }
}

/**
 * 选择Trending
 */
const selectTrending = (config) => {
  formData.trendingId = String(config.id)
  trendingSearchText.value = config.trending
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
 * 过滤后的查询Trending列表
 */
const filteredQueryTrendingList = computed(() => {
  if (!queryTrendingSearchText.value || queryTrendingSearchText.value.trim() === '') {
    return configList.value
  }
  const searchLower = queryTrendingSearchText.value.toLowerCase().trim()
  return configList.value.filter(config => {
    return config.trending.toLowerCase().includes(searchLower)
  })
})

/**
 * 查询Trending搜索输入处理
 */
const onQueryTrendingSearchInput = () => {
  showQueryTrendingDropdown.value = true
  // 如果输入的内容完全匹配某个选项，自动选择
  const exactMatch = configList.value.find(config => {
    return config.trending === queryTrendingSearchText.value
  })
  if (exactMatch) {
    querySelectedConfig.value = exactMatch
  }
}

/**
 * 选择查询Trending
 */
const selectQueryTrending = (config) => {
  querySelectedConfig.value = config
  queryTrendingSearchText.value = config.trending
  showQueryTrendingDropdown.value = false
}

/**
 * 查询Trending输入框失焦处理
 */
const handleQueryTrendingBlur = () => {
  // 延迟隐藏，以便点击下拉项时能触发
  setTimeout(() => {
    showQueryTrendingDropdown.value = false
  }, 200)
}

/**
 * 处理插入（查询并添加到对冲列表）
 */
const handleQuery = async () => {
  if (!querySelectedConfig.value) {
    showToast('请先选择Trending配置', 'warning')
    return
  }
  
  isQuerying.value = true
  queryResult.value = null
  
  try {
    // 获取订单薄信息
    const priceInfo = await parseOrderbookData(querySelectedConfig.value, hedgeMode.isClose)
    
    // 判断是否符合条件
    const meetsCondition = checkOrderbookHedgeCondition(priceInfo, querySelectedConfig.value)
    
    if (meetsCondition) {
      // 符合条件，添加到对冲列表
      const config = querySelectedConfig.value
      
      // 1. 更新服务器端配置（启用配置）
      const updateData = {
        list: [{
          id: config.id,
          trending: config.trending,
          trendingPart1: config.trendingPart1 || null,
          trendingPart2: config.trendingPart2 || null,
          trendingPart3: config.trendingPart3 || null,
          opUrl: config.opUrl || '',
          polyUrl: config.polyUrl || '',
          opTopicId: config.opTopicId || '',
          weight: config.weight || 0,
          isOpen: 1  // 启用
        }]
      }
      
      const updateResponse = await axios.post(
        'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
        updateData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (updateResponse.data && updateResponse.data.code === 0) {
        // 2. 更新本地显示状态
        const visibleData = JSON.parse(localStorage.getItem(CONFIG_VISIBLE_KEY) || '{}')
        visibleData[config.id] = true
        localStorage.setItem(CONFIG_VISIBLE_KEY, JSON.stringify(visibleData))
        
        // 3. 更新本地配置列表
        const configInList = configList.value.find(c => c.id === config.id)
        if (configInList) {
          configInList.isOpen = 1
          configInList.enabled = true
        }
        
        // 4. 更新活动配置列表
        updateActiveConfigs()
        
        // 5. 清空查询结果和输入
        queryResult.value = null
        querySelectedConfig.value = null
        queryTrendingSearchText.value = ''
        
        showToast(`成功将 ${config.trending} 添加到对冲列表`, 'success')
      } else {
        throw new Error(updateResponse.data?.msg || '更新配置失败')
      }
    } else {
      // 不符合条件，显示错误信息
      let reason = '不符合对冲条件'
      
      // 检查价差
      const maxDepth = getMaxDepth(querySelectedConfig.value)
      if (priceInfo.diff <= 0.15) {
        if (!hedgeMode.isClose) {
          // 开仓模式：检查买一价值（买一价 × 买一深度 / 100）
          const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
          if (bidValue >= maxDepth) {
            reason = `先挂方买一价值 ${bidValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
          } else {
            reason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
          }
        } else {
          // 平仓模式：检查卖一价值（卖一价 × 卖一深度 / 100）
          const askValue = priceInfo.price2 * priceInfo.depth2 / 100
          if (askValue >= maxDepth) {
            reason = `先挂方卖一价值 ${askValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
          } else {
            reason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
          }
        }
      }
      
      queryResult.value = {
        meetsCondition: false,
        reason: reason,
        priceInfo: priceInfo
      }
    }
  } catch (error) {
    // 获取订单薄失败，说明不符合条件
    let reason = error.message || '获取订单薄数据失败'
    
    queryResult.value = {
      meetsCondition: false,
      reason: reason
    }
    console.error('插入失败:', error)
  } finally {
    isQuerying.value = false
  }
}

/**
 * 处理测试（发送测试请求）
 */
const handleTest = async () => {
  if (!querySelectedConfig.value) {
    showToast('请先选择Trending配置', 'warning')
    return
  }
  
  isTesting.value = true
  testResult.value = null
  
  const config = querySelectedConfig.value
  
  // 设置 isFetching 标志，防止自动对冲逻辑同时请求订单薄
  const originalIsFetching = config.isFetching || false
  config.isFetching = true
  
  try {
    // 重试逻辑：最多重试5次
    const maxRetries = 5
    let retryCount = 0
    let priceInfo = null
    
    // 获取订单薄信息，如果失败则重试（最多5次）
    while (retryCount < maxRetries) {
      try {
        priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
        // 成功获取订单薄，跳出重试循环
        break
      } catch (error) {
        retryCount++
        console.warn(`获取订单薄失败，重试 ${retryCount}/${maxRetries}:`, error.message)
        
        if (retryCount >= maxRetries) {
          // 达到最大重试次数，设置错误结果
          const reason = error.message || '获取订单薄数据失败（已重试5次）'
          testResult.value = {
            meetsCondition: false,
            reason: reason
          }
          console.error('获取订单薄失败，已达到最大重试次数:', error)
          return
        }
        
        // 等待一段时间后重试（避免立即重试）
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    // 判断是否符合条件
    const meetsCondition = checkOrderbookHedgeCondition(priceInfo, config)
    
    if (!meetsCondition) {
      // 不符合条件，显示错误信息（与 handleQuery 的逻辑相同）
      let reason = '不符合对冲条件'
      
      // 检查价差
      const maxDepth = getMaxDepth(config)
      if (priceInfo.diff <= 0.15) {
        if (!hedgeMode.isClose) {
          // 开仓模式：检查买一价值（买一价 × 买一深度 / 100）
          const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
          if (bidValue >= maxDepth) {
            reason = `先挂方买一价值 ${bidValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
          } else {
            reason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
          }
        } else {
          // 平仓模式：检查卖一价值（卖一价 × 卖一深度 / 100）
          const askValue = priceInfo.price2 * priceInfo.depth2 / 100
          if (askValue >= maxDepth) {
            reason = `先挂方卖一价值 ${askValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
          } else {
            reason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
          }
        }
      }
      
      testResult.value = {
        meetsCondition: false,
        reason: reason,
        priceInfo: priceInfo
      }
      return
    }
    
    // 符合条件，继续发送测试请求到 calReadyToHedgeV4Test
    // 计算订单价格（与 executeHedgeFromOrderbook 中的逻辑相同）
    let orderPrice
    if (priceInfo.finalPrice !== null && priceInfo.finalPrice !== undefined) {
      orderPrice = priceInfo.finalPrice.toFixed(1)
    } else {
      // 兼容旧逻辑
      if (priceInfo.diff > 0.15) {
        // 先挂方买卖价差大于0.15，取平均价
        orderPrice = ((priceInfo.price1 + priceInfo.price2) / 2).toFixed(1)
      } else {
        // 差值小于等于0.15，根据开仓/平仓取价格
        if (!hedgeMode.isClose) {
          // 开仓模式：取较小的价格（买一价）
          orderPrice = priceInfo.minPrice.toFixed(1)
        } else {
          // 平仓模式：取较大的价格（卖一价）
          orderPrice = priceInfo.maxPrice.toFixed(1)
        }
      }
    }
    
    // 构建请求参数（与第7210-7239行的逻辑相同）
    const requestData = {
      trendingId: config.id,  // 使用输入框对应的trendingId
      isClose: hedgeMode.isClose,
      currentPrice: orderPrice,
      priceOutCome: priceInfo.firstSide,  // 先挂方 (YES/NO)
      timePassMin: hedgeMode.timePassMin,
      minUAmt: hedgeMode.minUAmt,  // 最小开单
      maxUAmt: hedgeMode.maxUAmt,   // 最大开单
      minCloseAmt: hedgeMode.minCloseAmt,  // 平仓最小数量（参数1）
      maxOpenHour: hedgeMode.maxOpenHour,  // 可加仓时间（小时）
      closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
      numberType: parseInt(selectedNumberType.value)  // 账号类型：1-全部账户, 2-1000个账户, 3-1000个账户中未达标的
    }
    // 如果 maxIpDelay 有值，则添加到请求参数中
    if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
      requestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
    }
    // 添加 needJudgeDF 和 maxDHour 字段
    requestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
    requestData.maxDHour = Number(hedgeMode.maxDHour) || 12
    // 添加 minCloseMin 字段
    requestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
    // 添加资产优先级校验字段
    requestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
    requestData.balancePriority = hedgeMode.balancePriority
    
    // 发送测试请求到 calReadyToHedgeV4Test
    console.log('发送测试请求到 calReadyToHedgeV4Test:', requestData)
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeV4Test',
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    console.log('测试请求响应:', response.data)
    
    // 判断返回结果
    if (response.data && response.data.code === 0 && response.data.data) {
      const uid = response.data.data.uid
      if (uid) {
        // 获取配置ID
        const trendingId = config.id
        // 获取最小开单值
        const minUAmt = hedgeMode.minUAmt || 0
        showToast('测试请求发送成功，5秒后打开持仓详情页面', 'success')
        
        // 等待5秒后打开持仓详情页面
        await new Promise(resolve => setTimeout(resolve, 5000))
        
        // 打开持仓详情页面，传递 uid、trendingId 和 minUAmt
        const url = `https://oss.w3id.info/Opanomaly/index.html#/position-detail?uid=${uid}&id=${trendingId}&minUAmt=${minUAmt}`
        window.open(url, '_blank')
        showToast('已打开持仓详情页面', 'success')
      } else {
        showToast('测试请求发送成功，但未获取到uid', 'warning')
      }
    } else {
      const errorMsg = response.data?.msg || '测试请求失败'
      showToast(`测试请求失败: ${errorMsg}`, 'error')
    }
    
    // 清空测试结果（因为成功发送了请求）
    testResult.value = null
  } catch (error) {
    console.error('测试过程发生错误:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`测试失败: ${errorMsg}`, 'error')
  } finally {
    // 恢复 isFetching 标志
    config.isFetching = originalIsFetching
    isTesting.value = false
  }
}

/**
 * 判断持仓数量是否满足绿色显示条件（yes和no都大于0.1w，即1000）
 */
const shouldShowPositionGreen = (config) => {
  if (!config || !config.trending) {
    return false
  }
  
  const positionData = positionDataMap.value.get(config.trending.trim())
  if (!positionData) {
    return false
  }
  
  // 判断yes和no持仓数量都大于0.1w（1000）
  return positionData.yesPosition > 1000 && positionData.noPosition > 1000
}

/**
 * 获取持仓文本（格式化显示）
 */
const getPositionText = (config) => {
  if (!config || !config.trending) {
    return ''
  }
  
  const positionData = positionDataMap.value.get(config.trending.trim())
  if (!positionData) {
    return ''
  }
  
  const yesPosition = (positionData.yesPosition / 10000).toFixed(2)
  const noPosition = (positionData.noPosition / 10000).toFixed(2)
  
  return `持仓: YES ${yesPosition}万 / NO ${noPosition}万`
}

/**
 * 检查配置是否正在测试
 */
const isTestingConfig = (config) => {
  if (!config || !config.id) {
    return false
  }
  return testingConfigIds.value.has(String(config.id))
}

/**
 * 保存主题设置到本地存储
 */
const saveTopicSettings = (config) => {
  if (!config || !config.id) {
    showToast('配置不存在，无法保存', 'warning')
    return
  }
  
  try {
    // 获取当前保存的所有主题设置
    const savedSettings = JSON.parse(localStorage.getItem(CONFIG_TOPIC_SETTINGS_KEY) || '{}')
    
    // 判断是否有值需要保存
    const hasTasksPerTopic = config.tasksPerTopic !== undefined && config.tasksPerTopic !== null && config.tasksPerTopic !== ''
    const hasMaxDepth = config.maxDepth !== undefined && config.maxDepth !== null && config.maxDepth !== ''
    
    const configId = String(config.id)
    
    // 如果两个值都为空，则删除该主题的设置，使用总设置的值
    if (!hasTasksPerTopic && !hasMaxDepth) {
      delete savedSettings[configId]
      // 清空config中的保存值
      config.savedTasksPerTopic = undefined
      config.savedMaxDepth = undefined
      // 保存到本地存储
      localStorage.setItem(CONFIG_TOPIC_SETTINGS_KEY, JSON.stringify(savedSettings))
      showToast(`主题"${config.trending}"的单独设置已清除，将使用总设置的值`, 'success')
      console.log(`主题 ${config.id} 设置已清除，将使用总设置`)
      return
    }
    
    // 保存设置（有值则保存，无值则删除）
    if (!savedSettings[configId]) {
      savedSettings[configId] = {}
    }
    
    // 处理"同时任务"字段
    if (hasTasksPerTopic) {
      savedSettings[configId].tasksPerTopic = Number(config.tasksPerTopic)
      config.savedTasksPerTopic = Number(config.tasksPerTopic)
    } else {
      // 如果为空，则删除该字段
      delete savedSettings[configId].tasksPerTopic
      config.savedTasksPerTopic = undefined
    }
    
    // 处理"最大允许深度"字段
    if (hasMaxDepth) {
      savedSettings[configId].maxDepth = Number(config.maxDepth)
      config.savedMaxDepth = Number(config.maxDepth)
    } else {
      // 如果为空，则删除该字段
      delete savedSettings[configId].maxDepth
      config.savedMaxDepth = undefined
    }
    
    // 保存到本地存储
    localStorage.setItem(CONFIG_TOPIC_SETTINGS_KEY, JSON.stringify(savedSettings))
    
    showToast(`主题"${config.trending}"的设置已保存`, 'success')
    console.log(`主题 ${config.id} 设置已保存:`, savedSettings[configId])
  } catch (e) {
    console.error('保存主题设置失败:', e)
    showToast('保存失败: ' + (e.message || '未知错误'), 'error')
  }
}

/**
 * 加载主题设置从本地存储
 */
const loadTopicSettings = () => {
  try {
    const savedSettings = JSON.parse(localStorage.getItem(CONFIG_TOPIC_SETTINGS_KEY) || '{}')
    return savedSettings
  } catch (e) {
    console.error('加载主题设置失败:', e)
    return {}
  }
}

/**
 * 检查配置是否正在保存最大开单量
 */
const isSavingMaxDailyAmount = (config) => {
  if (!config || !config.id) {
    return false
  }
  return savingMaxDailyAmountIds.value.has(String(config.id))
}

/**
 * 保存最大开单量（更新c字段）
 */
const saveMaxDailyAmount = async (config) => {
  if (!config || !config.id) {
    showToast('配置不存在，无法保存', 'warning')
    return
  }
  
  const configId = String(config.id)
  
  // 检查是否正在保存
  if (savingMaxDailyAmountIds.value.has(configId)) {
    return
  }
  
  savingMaxDailyAmountIds.value.add(configId)
  
  try {
    // 获取当前输入框的值
    const maxDailyAmount = config.maxDailyAmount
    
    // 构建更新数据
    const updateData = {
      list: [{
        id: config.id,
        trending: config.trending,
        trendingPart1: config.trendingPart1 || null,
        trendingPart2: config.trendingPart2 || null,
        trendingPart3: config.trendingPart3 || null,
        opUrl: config.opUrl || '',
        polyUrl: config.polyUrl || '',
        opTopicId: config.opTopicId || '',
        weight: config.weight || 0,
        isOpen: config.isOpen !== undefined ? config.isOpen : (config.enabled ? 1 : 0),
        c: (maxDailyAmount !== undefined && maxDailyAmount !== null && maxDailyAmount !== '') ? String(maxDailyAmount) : null  // 如果输入框为空，设置为null
      }]
    }
    
    console.log(`保存主题 ${config.id} 的最大开单量:`, updateData)
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      updateData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.code === 0) {
      // 更新本地配置中的c字段
      config.c = (maxDailyAmount !== undefined && maxDailyAmount !== null && maxDailyAmount !== '') ? String(maxDailyAmount) : null
      // 同步到configList中对应的配置
      const configInList = configList.value.find(c => c.id === config.id)
      if (configInList) {
        configInList.c = config.c
      }
      // 清空输入框的值（因为已经保存）
      config.maxDailyAmount = undefined
      
      showToast(`主题"${config.trending}"的最大开单量已保存`, 'success')
      console.log(`主题 ${config.id} 最大开单量已保存:`, config.c)
    } else {
      throw new Error(response.data?.msg || '保存失败')
    }
  } catch (error) {
    console.error('保存最大开单量失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`保存最大开单量失败: ${errorMsg}`, 'error')
  } finally {
    savingMaxDailyAmountIds.value.delete(configId)
  }
}

/**
 * 获取指定主题的任务数量（优先使用保存的设置，否则使用全局设置）
 * 注意：只有保存后的设置才会生效，输入框中未保存的值不会影响实际使用的设置
 */
const getTasksPerTopic = (config) => {
  if (!config) {
    return Math.max(1, Math.floor(hedgeTasksPerTopic.value) || 2)
  }
  // 优先使用保存的设置（只有点击保存后才会生效）
  if (config.savedTasksPerTopic !== undefined && config.savedTasksPerTopic !== null && config.savedTasksPerTopic !== '') {
    return Math.max(1, Math.floor(config.savedTasksPerTopic) || 2)
  }
  // 否则使用全局设置（输入框中未保存的值不会影响实际使用的设置）
  return Math.max(1, Math.floor(hedgeTasksPerTopic.value) || 2)
}

/**
 * 获取指定主题的最大允许深度（优先使用保存的设置，否则使用全局设置）
 * 注意：只有保存后的设置才会生效，输入框中未保存的值不会影响实际使用的设置
 */
const getMaxDepth = (config) => {
  if (!config) {
    return hedgeMode.maxDepth || 100
  }
  // 优先使用保存的设置（只有点击保存后才会生效）
  if (config.savedMaxDepth !== undefined && config.savedMaxDepth !== null && config.savedMaxDepth !== '') {
    return Number(config.savedMaxDepth) || hedgeMode.maxDepth || 100
  }
  // 否则使用全局设置（输入框中未保存的值不会影响实际使用的设置）
  return hedgeMode.maxDepth || 100
}

/**
 * 为指定配置执行测试
 */
const handleTestForConfig = async (config) => {
  if (!config) {
    showToast('配置不存在', 'warning')
    return
  }
  
  const configId = String(config.id)
  testingConfigIds.value.add(configId)
  
  // 设置 isFetching 标志，防止自动对冲逻辑同时请求订单薄
  const originalIsFetching = config.isFetching || false
  config.isFetching = true
  
  try {
    // 重试逻辑：最多重试5次
    const maxRetries = 5
    let retryCount = 0
    let priceInfo = null
    
    // 获取订单薄信息，如果失败则重试（最多5次）
    while (retryCount < maxRetries) {
      try {
        priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
        // 成功获取订单薄，跳出重试循环
        break
      } catch (error) {
        retryCount++
        console.warn(`获取订单薄失败，重试 ${retryCount}/${maxRetries}:`, error.message)
        
        if (retryCount >= maxRetries) {
          // 达到最大重试次数，显示错误
          const reason = error.message || '获取订单薄数据失败（已重试5次）'
          showToast(`测试失败: ${reason}`, 'error')
          config.errorMessage = reason
          return
        }
        
        // 等待一段时间后重试（避免立即重试）
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    // 判断是否符合条件
    const meetsCondition = checkOrderbookHedgeCondition(priceInfo, config)
    
    if (!meetsCondition) {
      // 不符合条件，显示错误信息
      let reason = '不符合对冲条件'
      
      // 检查价差
      const maxDepth = getMaxDepth(config)
      if (priceInfo.diff <= 0.15) {
        if (!hedgeMode.isClose) {
          // 开仓模式：检查买一价值（买一价 × 买一深度 / 100）
          const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
          if (bidValue >= maxDepth) {
            reason = `先挂方买一价值 ${bidValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
          } else {
            reason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
          }
        } else {
          // 平仓模式：检查卖一价值（卖一价 × 卖一深度 / 100）
          const askValue = priceInfo.price2 * priceInfo.depth2 / 100
          if (askValue >= maxDepth) {
            reason = `先挂方卖一价值 ${askValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
          } else {
            reason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
          }
        }
      }
      
      config.errorMessage = reason
      showToast(`测试失败: ${reason}`, 'error')
      return
    }
    
    // 符合条件，继续发送测试请求到 calReadyToHedgeV4Test
    // 计算订单价格（与 executeHedgeFromOrderbook 中的逻辑相同）
    let orderPrice
    if (priceInfo.finalPrice !== null && priceInfo.finalPrice !== undefined) {
      orderPrice = priceInfo.finalPrice.toFixed(1)
    } else {
      // 兼容旧逻辑
      if (priceInfo.diff > 0.15) {
        // 先挂方买卖价差大于0.15，取平均价
        orderPrice = ((priceInfo.price1 + priceInfo.price2) / 2).toFixed(1)
      } else {
        // 差值小于等于0.15，根据开仓/平仓取价格
        if (!hedgeMode.isClose) {
          // 开仓模式：取较小的价格（买一价）
          orderPrice = priceInfo.minPrice.toFixed(1)
        } else {
          // 平仓模式：取较大的价格（卖一价）
          orderPrice = priceInfo.maxPrice.toFixed(1)
        }
      }
    }
    
    // 构建请求参数
    const requestData = {
      trendingId: config.id,
      isClose: hedgeMode.isClose,
      currentPrice: orderPrice,
      priceOutCome: priceInfo.firstSide,  // 先挂方 (YES/NO)
      timePassMin: hedgeMode.timePassMin,
      minUAmt: hedgeMode.minUAmt,  // 最小开单
      maxUAmt: hedgeMode.maxUAmt,   // 最大开单
      minCloseAmt: hedgeMode.minCloseAmt,  // 平仓最小数量（参数1）
      maxOpenHour: hedgeMode.maxOpenHour,  // 可加仓时间（小时）
      closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
      numberType: parseInt(selectedNumberType.value)  // 账号类型：1-全部账户, 2-1000个账户, 3-1000个账户中未达标的
    }
    // 如果 maxIpDelay 有值，则添加到请求参数中
    if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
      requestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
    }
    // 添加 needJudgeDF 和 maxDHour 字段
    requestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
    requestData.maxDHour = Number(hedgeMode.maxDHour) || 12
    // 添加 minCloseMin 字段
    requestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
    // 添加资产优先级校验字段
    requestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
    requestData.balancePriority = hedgeMode.balancePriority
    
    // 发送测试请求到 calReadyToHedgeV4Test
    console.log('发送测试请求到 calReadyToHedgeV4Test:', requestData)
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeV4Test',
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    console.log('测试请求响应:', response.data)
    
    // 判断返回结果
    if (response.data && response.data.code === 0 && response.data.data) {
      const uid = response.data.data.uid
      if (uid) {
        // 获取配置ID
        const trendingId = config.id
        // 获取最小开单值
        const minUAmt = hedgeMode.minUAmt || 0
        showToast('测试请求发送成功，5秒后打开持仓详情页面', 'success')
        
        // 等待5秒后打开持仓详情页面
        await new Promise(resolve => setTimeout(resolve, 5000))
        
        // 打开持仓详情页面，传递 uid、trendingId 和 minUAmt
        const url = `https://oss.w3id.info/Opanomaly/index.html#/position-detail?uid=${uid}&id=${trendingId}&minUAmt=${minUAmt}`
        window.open(url, '_blank')
        showToast('已打开持仓详情页面', 'success')
        // 清除错误信息
        config.errorMessage = null
      } else {
        showToast('测试请求发送成功，但未获取到uid', 'warning')
      }
    } else {
      const errorMsg = response.data?.msg || '测试请求失败'
      showToast(`测试请求失败: ${errorMsg}`, 'error')
      config.errorMessage = errorMsg
    }
  } catch (error) {
    console.error('测试过程发生错误:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`测试失败: ${errorMsg}`, 'error')
    config.errorMessage = errorMsg
  } finally {
    // 恢复 isFetching 标志
    config.isFetching = originalIsFetching
    testingConfigIds.value.delete(configId)
  }
}

/**
 * 判断是否可以点击自动获取按钮
 * 需要：预测方向、买卖方向、Trending和价格
 */
const canQuickSelect = computed(() => {
  return formData.trendingId && 
         formData.psSide && 
         formData.side && 
         formData.price !== null && 
         formData.price !== '' &&
         !isNaN(parseFloat(formData.price))
})

/**
 * 自动获取订单账户信息
 */
const handleQuickSelectOrderAcc = async () => {
  if (!canQuickSelect.value) {
    showToast('请先选择预测方向、买卖方向、Trending和价格', 'warning')
    return
  }

  isQuickSelecting.value = true
  blackListText.value = ''  // 清空之前的拉黑列表

  try {
    // 构建请求参数
    const requestData = {
      trendingId: parseInt(formData.trendingId),
      outcome: parseInt(formData.psSide),  // 1=Yes, 2=No
      price: parseFloat(formData.price),
      isClose: false,  // 根据需求设置，这里默认false
      share: parseFloat(formData.amt) || 0  // 如果数量为空，传0
    }

    console.log('正在自动获取订单账户信息...', requestData)

    // 发送请求
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/quickSelectOrderAcc',
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data && response.data.data) {
      const responseData = response.data.data
      
      // 处理blackList
      if (responseData.blackList && Array.isArray(responseData.blackList) && responseData.blackList.length > 0) {
        blackListText.value = responseData.blackList.join(', ')
      } else {
        blackListText.value = ''
      }
      
      // 处理list数据
      if (responseData.list && responseData.list.length > 0) {
        const result = responseData.list[0]
        
        // 填充表单
        if (result.number) {
          formData.numberList = String(result.number)
          // 自动更新组号
          updateGroupNoFromBrowser()
        }
        
        if (result.group) {
          formData.groupNo = String(result.group)
        }
        
        if (result.share) {
          formData.amt = parseFloat(result.share)
        }

        showToast('自动获取成功！', 'success')
        console.log('自动获取成功:', result)
      } else {
        showToast('未找到匹配的账户信息', 'warning')
      }
    } else {
      showToast('未找到匹配的账户信息', 'warning')
    }
  } catch (error) {
    console.error('自动获取失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`自动获取失败: ${errorMsg}`, 'error')
  } finally {
    isQuickSelecting.value = false
  }
}

/**
 * 加载持仓数据（从 getAllPosSnap 获取）
 */
const loadPositionData = async () => {
  try {
    console.log('[持仓数据] 开始加载持仓数据...')
    const response = await axios.get('https://sg.bicoin.com.cn/99l/boost/getAllPosSnap')
    
    if (response.data && response.data.data && response.data.data.list) {
      const data = response.data.data.list
      console.log(`[持仓数据] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 过滤掉 amt < 1 的数据
      const filteredData = data.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt >= 1
      })
      console.log(`[持仓数据] 过滤后剩余 ${filteredData.length} 条数据`)
      
      // 使用 Map 存储每个事件的持仓数据
      const eventMap = new Map()
      
      // 处理每条数据
      for (const row of filteredData) {
        // 从 trendingKey 中提取 id（格式：id::方向）
        if (!row.trendingKey) {
          continue
        }
        
        const parts = row.trendingKey.split('::')
        if (parts.length < 2) {
          continue
        }
        
        const configId = parts[0].trim()
        const direction = parts[1].trim()
        
        // 通过 id 查找对应的 trending（事件名）
        const eventName = idToTrendingMap.value.get(configId)
        if (!eventName) {
          continue
        }
        
        // 初始化事件数据
        if (!eventMap.has(eventName)) {
          eventMap.set(eventName, {
            yesPosition: 0,
            noPosition: 0
          })
        }
        
        const event = eventMap.get(eventName)
        const amount = Math.abs(parseFloat(row.amt) || 0)
        
        // 根据 outCome 判断方向（YES/NO）
        const outComeUpper = (row.outCome || direction).toUpperCase()
        if (outComeUpper === 'YES') {
          event.yesPosition += amount
        } else if (outComeUpper === 'NO') {
          event.noPosition += amount
        }
      }
      
      // 更新 positionDataMap
      positionDataMap.value = eventMap
      console.log(`[持仓数据] 持仓数据加载完成，共 ${eventMap.size} 个事件`)
    } else {
      console.warn('[持仓数据] 未获取到持仓数据')
    }
  } catch (error) {
    console.error('[持仓数据] 加载持仓数据失败:', error)
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
        // 同步搜索文本
        const defaultConfig = configList.value[0]
        trendingSearchText.value = defaultConfig.trending
      }
      
      if (configList.value.length > 0 && !hedgeData.eventLink) {
        hedgeData.eventLink = String(configList.value[0].id)
      }
      
      // 如果已有trendingId，同步搜索文本
      if (formData.trendingId && configList.value.length > 0) {
        const selectedConfig = configList.value.find(c => String(c.id) === formData.trendingId)
        if (selectedConfig) {
          trendingSearchText.value = selectedConfig.trending
        }
      }
      
      console.log(`配置加载成功：${exchangeList.value.length} 个交易所，${configList.value.length} 个Trending`)
      
      // 构建 id -> trending 的映射
      const newIdToTrendingMap = new Map()
      for (const config of configList.value) {
        if (config.id && config.trending) {
          newIdToTrendingMap.set(String(config.id), config.trending.trim())
        }
      }
      idToTrendingMap.value = newIdToTrendingMap
      console.log(`id -> trending 映射完成，共 ${newIdToTrendingMap.size} 个映射`)
      
      // 更新活动配置列表
      updateActiveConfigs()
      
      // 加载持仓数据
      loadPositionData()
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
 * 静默刷新配置（不显示 loading 状态）
 * 用于每小时05分的自动更新
 */
const silentRefreshExchangeConfig = async () => {
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/exchangeConfig')
    
    if (response.data && response.data.code === 0) {
      const data = response.data.data
      
      // 设置交易所列表
      exchangeList.value = data.exchangeList || []
      
      // 设置配置列表，将 isOpen 映射为 enabled
      // 保留现有配置的本地状态（如 tasksPerTopic, maxDepth 等用户输入的值）
      const newConfigList = (data.configList || []).map(config => {
        const existingConfig = configList.value.find(c => c.id === config.id)
        return {
          ...config,
          enabled: config.isOpen === 1,
          // 保留用户可能已修改的本地状态
          tasksPerTopic: existingConfig?.tasksPerTopic ?? config.tasksPerTopic,
          maxDepth: existingConfig?.maxDepth ?? config.maxDepth,
          maxDailyAmount: existingConfig?.maxDailyAmount ?? config.maxDailyAmount,
        }
      })
      
      configList.value = newConfigList
      
      // 构建 id -> trending 的映射
      const newIdToTrendingMap = new Map()
      for (const config of configList.value) {
        if (config.id && config.trending) {
          newIdToTrendingMap.set(String(config.id), config.trending.trim())
        }
      }
      idToTrendingMap.value = newIdToTrendingMap
      
      // 更新活动配置列表
      updateActiveConfigs()
      
      console.log(`[${new Date().toLocaleTimeString()}] 配置静默刷新成功：${configList.value.length} 个Trending`)
    }
  } catch (error) {
    console.error('配置静默刷新失败:', error)
  }
}

/**
 * 启动每小时05分自动刷新配置的定时器
 * 每分钟检查一次，如果是xx:05分则刷新配置
 */
const startConfigAutoRefresh = () => {
  // 清除旧的定时器
  if (configAutoRefreshInterval.value) {
    clearInterval(configAutoRefreshInterval.value)
    configAutoRefreshInterval.value = null
  }
  
  // 记录上次刷新的小时，避免同一个05分重复刷新
  let lastRefreshedHour = -1
  
  // 每分钟检查一次
  configAutoRefreshInterval.value = setInterval(() => {
    const now = new Date()
    const currentMinute = now.getMinutes()
    const currentHour = now.getHours()
    
    // 检查是否是05分，且这个小时还没有刷新过
    if (currentMinute === 5 && currentHour !== lastRefreshedHour) {
      lastRefreshedHour = currentHour
      console.log(`[${now.toLocaleTimeString()}] 到达每小时05分，开始静默刷新配置...`)
      silentRefreshExchangeConfig()
    }
  }, 60000)  // 每60秒检查一次
  
  console.log('配置自动刷新定时器已启动（每小时05分刷新）')
}

/**
 * 根据yes数量获取主题并添加到自动对冲列表
 */
const fetchTopicsByYesCount = async () => {
  if (!yesCountThreshold.value || yesCountThreshold.value <= 0) {
    showToast('请输入有效的yes数量阈值', 'warning')
    return
  }
  
  isFetchingTopics.value = true
  
  try {
    // 1. 请求 positions/summary/trades API
    showToast('正在获取交易数据，请稍候...', 'info')
    const tradesResponse = await axios.get('https://enstudyai.fatedreamer.com/t3/api/positions/summary/trades')
    
    // 检查数据结构，支持多种可能的数据格式
    let items = []
    if (tradesResponse.data) {
      if (Array.isArray(tradesResponse.data)) {
        items = tradesResponse.data
      } else if (tradesResponse.data.items && Array.isArray(tradesResponse.data.items)) {
        items = tradesResponse.data.items
      } else if (tradesResponse.data.data && Array.isArray(tradesResponse.data.data)) {
        items = tradesResponse.data.data
      } else if (tradesResponse.data.list && Array.isArray(tradesResponse.data.list)) {
        items = tradesResponse.data.list
      }
    }
    
    if (items.length === 0) {
      console.error('API返回的完整数据结构:', tradesResponse.data)
      throw new Error('获取交易数据失败：未找到有效的数据数组')
    }
    
    console.log(`获取到 ${items.length} 条数据`)
    console.log('API返回的原始数据示例（第1条）:', JSON.stringify(items[0], null, 2))
    
    // 2. 统计每个主题的yes数量（参照 dataweb/src/App.vue 的处理方式）
    const topicYesCountMap = new Map()
    
    for (const item of items) {
      if (item.wallet_address && item.markets) {
        // 处理 markets 数据，类似于 formatChainMarkets 的逻辑
        const markets = item.markets
        if (typeof markets === 'string') {
          // 如果是字符串，尝试解析
          const marketPairs = markets.split(';').filter(pair => pair.trim())
          for (const pair of marketPairs) {
            const parts = pair.split('|||')
            if (parts.length >= 2) {
              const title = parts[0].trim()
              const marketData = parts[1] || ''
              
              // 解析市场数据，提取yes数量
              // 格式可能是 "YES:100,NO:50" 或其他格式
              if (marketData) {
                // 尝试从 marketData 中提取 yes 数量
                // 这里需要根据实际数据结构调整
                const yesMatch = marketData.match(/yes[:_]\s*([\d.]+)/i)
                if (yesMatch) {
                  const yesCount = parseFloat(yesMatch[1]) || 0
                  const existingCount = topicYesCountMap.get(title) || 0
                  topicYesCountMap.set(title, existingCount + yesCount)
                }
              }
            }
          }
        } else if (Array.isArray(markets)) {
          // 如果是数组格式（标准格式：markets: [{ title, yes_amount, no_amount, ... }]）
          for (const market of markets) {
            if (market && market.title) {
              const title = market.title.trim()
              // 使用 yes_amount 字段（这是API返回的标准字段名）
              const yesAmount = parseFloat(market.yes_amount || market.yesAmount || 0) || 0
              if (yesAmount > 0) {
                const existingCount = topicYesCountMap.get(title) || 0
                topicYesCountMap.set(title, existingCount + yesAmount)
              }
            }
          }
        } else if (typeof markets === 'object') {
          // 如果是对象格式
          if (markets.title) {
            const title = markets.title.trim()
            const yesCount = parseFloat(markets.yes_total || markets.yesCount || markets.yes || 0) || 0
            const existingCount = topicYesCountMap.get(title) || 0
            topicYesCountMap.set(title, existingCount + yesCount)
          }
        }
      }
      
      // 也尝试直接从 item 中提取主题和yes数量
      if (item.title || item.topic || item.market_title || item.marketName || item.market_name) {
        const title = (item.title || item.topic || item.market_title || item.marketName || item.market_name || '').trim()
        if (title) {
          const yesCount = parseFloat(
            item.yes_total || item.yesCount || item.yes || item.yes_amount || 
            item.yesAmount || item.yesTotal || 0
          ) || 0
          if (yesCount > 0) {
            const existingCount = topicYesCountMap.get(title) || 0
            topicYesCountMap.set(title, existingCount + yesCount)
          }
        }
      }
      
      // 如果是直接包含主题和数量的格式
      if (item.market && typeof item.market === 'string') {
        // 尝试解析 market 字符串格式
        const marketPairs = item.market.split(';').filter(pair => pair.trim())
        for (const pair of marketPairs) {
          const parts = pair.split('|||')
          if (parts.length >= 1) {
            const title = parts[0].trim()
            if (title) {
              // 尝试从后续部分提取数值
              let yesCount = 0
              for (let i = 1; i < parts.length; i++) {
                const num = parseFloat(parts[i])
                if (!isNaN(num) && num > 0) {
                  yesCount = num
                  break
                }
              }
              if (yesCount > 0) {
                const existingCount = topicYesCountMap.get(title) || 0
                topicYesCountMap.set(title, existingCount + yesCount)
              }
            }
          }
        }
      }
    }
    
    console.log(`统计完成，共找到 ${topicYesCountMap.size} 个主题`)
    if (topicYesCountMap.size > 0) {
      const sortedTopics = Array.from(topicYesCountMap.entries())
        .sort((a, b) => b[1] - a[1])  // 按数量降序排序
      console.log('主题yes数量统计（前20个，按数量排序）:', sortedTopics
        .slice(0, 20)
        .map(([title, count]) => ({ title, count })))
      console.log('所有主题数量统计（完整列表）:', sortedTopics.map(([title, count]) => ({ title, count })))
    } else {
      console.warn('未找到任何主题数据')
      console.warn('原始数据示例（前2条）:', items.slice(0, 2))
      console.warn('原始数据结构:', items.length > 0 ? Object.keys(items[0]) : '空数据')
      showToast('未找到任何主题数据，请检查API返回的数据格式', 'warning')
      return
    }
    
    // 3. 筛选yes数量大于阈值的主题
    const filteredTopics = []
    for (const [title, yesCount] of topicYesCountMap.entries()) {
      if (yesCount > yesCountThreshold.value) {
        filteredTopics.push({ title, yesCount })
      }
    }
    
    if (filteredTopics.length === 0) {
      // 显示统计信息帮助用户调整阈值
      const allCounts = Array.from(topicYesCountMap.values()).sort((a, b) => b - a)
      const maxCount = allCounts[0] || 0
      const minCount = allCounts[allCounts.length - 1] || 0
      const avgCount = allCounts.length > 0 ? allCounts.reduce((a, b) => a + b, 0) / allCounts.length : 0
      
      console.log(`主题数量统计: 最大=${maxCount.toFixed(2)}, 最小=${minCount.toFixed(2)}, 平均=${avgCount.toFixed(2)}, 阈值=${yesCountThreshold.value}`)
      
      showToast(
        `没有找到yes数量大于 ${yesCountThreshold.value} 的主题。` +
        `当前最大数量为 ${maxCount.toFixed(2)}，请调整阈值重试。`,
        'warning'
      )
      return
    }
    
    console.log(`筛选出 ${filteredTopics.length} 个符合条件的主题:`, filteredTopics)
    
    // 4. 获取 exchangeConfig 数据
    const exchangeConfigResponse = await axios.get('https://sg.bicoin.com.cn/99l/mission/exchangeConfig')
    
    if (!exchangeConfigResponse.data || exchangeConfigResponse.data.code !== 0) {
      throw new Error('获取配置数据失败')
    }
    
    const exchangeConfigList = exchangeConfigResponse.data.data?.configList || []
    const configMap = new Map()
    exchangeConfigList.forEach(config => {
      // 使用 trending 字段进行匹配（可能包含完整标题或部分标题）
      if (config.trending) {
        configMap.set(config.trending.trim().toLowerCase(), config)
        // 也尝试使用 trendingPart1 和 trendingPart2 组合
        if (config.trendingPart1 && config.trendingPart2) {
          const combined = `${config.trendingPart1} ${config.trendingPart2}`.trim().toLowerCase()
          configMap.set(combined, config)
        }
      }
    })
    
    // 5. 匹配符合条件的主题并更新配置
    const matchedConfigs = []
    for (const topic of filteredTopics) {
      const titleLower = topic.title.toLowerCase().trim()
      
      // 尝试精确匹配
      let matchedConfig = configMap.get(titleLower)
      
      // 如果没有精确匹配，尝试部分匹配（标题包含配置的trending，或配置的trending包含标题）
      if (!matchedConfig) {
        for (const [configKey, config] of configMap.entries()) {
          if (titleLower.includes(configKey) || configKey.includes(titleLower)) {
            matchedConfig = config
            break
          }
        }
      }
      
      // 如果还是没有匹配，尝试在 configList 中查找
      if (!matchedConfig) {
        matchedConfig = configList.value.find(c => {
          const configTitle = (c.trending || '').toLowerCase().trim()
          return titleLower === configTitle || 
                 titleLower.includes(configTitle) || 
                 configTitle.includes(titleLower)
        })
      }
      
      if (matchedConfig) {
        matchedConfigs.push({
          config: matchedConfig,
          topic: topic,
          yesCount: topic.yesCount
        })
      }
    }
    
    if (matchedConfigs.length === 0) {
      showToast(`找到 ${filteredTopics.length} 个符合条件的主题，但在配置中未找到匹配项`, 'warning')
      return
    }
    
    console.log(`找到 ${matchedConfigs.length} 个匹配的配置:`, matchedConfigs.map(m => ({
      trending: m.config.trending,
      yesCount: m.yesCount
    })))
    
    // 6. 批量更新配置：启用和显示
    const updateData = {
      list: matchedConfigs.map(m => ({
        id: m.config.id,
        trending: m.config.trending,
        trendingPart1: m.config.trendingPart1 || null,
        trendingPart2: m.config.trendingPart2 || null,
        trendingPart3: m.config.trendingPart3 || null,
        opUrl: m.config.opUrl || '',
        polyUrl: m.config.polyUrl || '',
        opTopicId: m.config.opTopicId || '',
        weight: m.config.weight || 0,
        isOpen: 1  // 启用
      }))
    }
    
    // 提交到服务器
    const updateResponse = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      updateData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (updateResponse.data && updateResponse.data.code === 0) {
      // 更新本地显示状态
      const visibleData = JSON.parse(localStorage.getItem(CONFIG_VISIBLE_KEY) || '{}')
      matchedConfigs.forEach(m => {
        visibleData[m.config.id] = true
      })
      localStorage.setItem(CONFIG_VISIBLE_KEY, JSON.stringify(visibleData))
      
      // 更新本地配置列表
      matchedConfigs.forEach(m => {
        const configInList = configList.value.find(c => c.id === m.config.id)
        if (configInList) {
          configInList.isOpen = 1
          configInList.enabled = true
        }
      })
      
      showToast(`成功添加 ${matchedConfigs.length} 个主题到自动对冲列表`, 'success')
      
      // 异步刷新配置列表（不阻塞界面响应）
      fetchExchangeConfig().catch(err => {
        console.error('刷新配置列表失败:', err)
      })
    } else {
      throw new Error(updateResponse.data?.msg || '更新配置失败')
    }
    
  } catch (error) {
    console.error('获取主题失败:', error)
    showToast('获取主题失败: ' + (error.message || '网络错误'), 'error')
  } finally {
    isFetchingTopics.value = false
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
      
      // 显示所有任务（不再过滤type=3，因为不再使用type=3任务）
      missionList.value = allMissions
      
      // 更新对冲任务状态（使用新接口）
      // 监控所有运行中的对冲任务，不仅仅是 currentHedge
      for (const config of activeConfigs.value) {
        // 获取所有运行中的对冲任务
        const runningHedges = (config.currentHedges || []).filter(h => h.finalStatus === 'running')
        
        for (const hedgeRecord of runningHedges) {
          // 跳过模式2的任务，它们有自己的监控逻辑
          if (hedgeRecord.isMode2) {
            continue
          }
          
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
  
  // 如果是type=1或type=5，根据模式添加tp3参数
  const taskType = parseInt(formData.type)
  if (taskType === 1 || taskType === 5) {
    submitData.tp3 = isFastMode.value ? "1" : "0"
  }
  
  console.log('正在提交任务...', submitData)
  
  // 重试机制：最多重试5次
  const maxRetries = 5
  let lastError = null
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
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
      
      // 判断返回的 code 是否等于 0
      if (response.data && response.data.code === 0) {
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
        
        isSubmitting.value = false
        return // 成功，退出函数
      } else {
        // code 不等于 0，视为失败
        const errorMsg = response.data?.msg || `返回码: ${response.data?.code || '未知'}`
        lastError = new Error(errorMsg)
        console.warn(`第 ${attempt} 次提交失败: ${errorMsg}`)
        
        // 如果不是最后一次尝试，等待3秒后重试
        if (attempt < maxRetries) {
          console.log(`等待 3 秒后进行第 ${attempt + 1} 次重试...`)
          await new Promise(resolve => setTimeout(resolve, 3000))
        }
      }
    } catch (error) {
      lastError = error
      console.error(`第 ${attempt} 次提交异常:`, error)
      const errorMsg = error.response?.data?.message || error.message || '未知错误'
      console.warn(`第 ${attempt} 次提交失败: ${errorMsg}`)
      
      // 如果不是最后一次尝试，等待3秒后重试
      if (attempt < maxRetries) {
        console.log(`等待 3 秒后进行第 ${attempt + 1} 次重试...`)
        await new Promise(resolve => setTimeout(resolve, 3000))
      }
    }
  }
  
  // 所有重试都失败
  console.error('提交失败: 已重试 ' + maxRetries + ' 次，均失败')
  const finalErrorMsg = lastError?.response?.data?.message || lastError?.message || '未知错误'
  alert(`任务添加失败: ${finalErrorMsg}（已重试 ${maxRetries} 次）`)
  isSubmitting.value = false
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
  return config.trending
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
      // fetchHedgeHistory()  // 刷新对冲记录列表
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
  
  // 重置Trending搜索文本
  if (configList.value.length > 0 && formData.trendingId) {
    const defaultConfig = configList.value.find(c => String(c.id) === formData.trendingId) || configList.value[0]
    trendingSearchText.value = defaultConfig.trending
  } else {
    trendingSearchText.value = ''
  }
  
  // 清空拉黑浏览器列表
  blackListText.value = ''
  
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
 * 验证延时时间（平仓模式2时，最小20秒）
 */
const validateDelayMs = () => {
  if (hedgeMode.isClose && hedgeMode.hedgeMode === 2) {
    if (!hedgeData.delayMs || hedgeData.delayMs < 20000) {
      hedgeData.delayMs = 20000
      console.log('平仓模式2：延时时间已自动调整为20秒（20000ms）')
    }
  }
}

/**
 * 监听自动对冲模块的平仓模式2状态，自动设置手动对冲表单的默认值
 */
watch(
  () => [hedgeMode.isClose, hedgeMode.hedgeMode],
  ([isClose, mode]) => {
    // 当是平仓模式2时
    if (isClose && mode === 2) {
      // 默认选择延时
      if (hedgeData.intervalType !== 'delay') {
        hedgeData.intervalType = 'delay'
      }
      // 如果延时时间小于20秒（20000ms），强制改为20秒
      validateDelayMs()
    }
  },
  { immediate: true }
)

/**
 * 监听延时时间变化，确保平仓模式2时至少20秒
 */
watch(
  () => hedgeData.delayMs,
  (newDelayMs) => {
    if (hedgeMode.isClose && hedgeMode.hedgeMode === 2 && newDelayMs !== null && newDelayMs < 20000) {
      hedgeData.delayMs = 20000
      console.log('平仓模式2：延时时间已自动调整为20秒（20000ms）')
    }
  }
)

/**
 * 监听trendingId变化，同步搜索文本
 */
watch(
  () => formData.trendingId,
  (newTrendingId) => {
    if (newTrendingId && configList.value.length > 0) {
      const selectedConfig = configList.value.find(c => String(c.id) === newTrendingId)
      if (selectedConfig) {
        if (trendingSearchText.value !== selectedConfig.trending) {
          trendingSearchText.value = selectedConfig.trending
        }
      }
    }
  }
)

/**
 * 打开查询上轮日志页面
 */
const openTaskAnomaly = () => {
  // 分组映射：分组1->传1, 分组2->传2, 默认->不传
  let groupParam = ''
  if (selectedGroup.value === '1') {
    groupParam = '?group=1'
  } else if (selectedGroup.value === '2') {
    groupParam = '?group=2'
  }
  // 默认分组不传参数
  
  const url = `https://oss.w3id.info/Opanomaly/index.html#/task-anomaly${groupParam}`
  window.open(url, '_blank')
}

/**
 * 加载分组配置
 */
const loadGroupConfig = async (groupNo) => {
  try {
    console.log(`正在加载分组${groupNo}配置...`)
    showToast(`正在加载分组${groupNo}配置...`, 'info')
    
    const groupResponse = await axios.get(`https://sg.bicoin.com.cn/99l/mission/exchangeConfigByGroupNo?groupNo=${groupNo}`)
    
    if (groupResponse.data?.code !== 0) {
      throw new Error('获取分组配置数据失败')
    }
    
    const groupData = groupResponse.data.data
    const groupConfigList = groupData.configList || []
    
    // 将分组配置转换为标准格式并更新configList，自动启用和显示所有主题
    configList.value = groupConfigList.map(config => ({
      ...config,
      enabled: true,  // 自动启用
      visible: true   // 自动显示
    }))
    
    // 更新exchangeList
    if (groupData.exchangeList) {
      exchangeList.value = groupData.exchangeList
    }
    
    // 更新活动配置列表（这会隐藏原有的主题列表，显示新的分组主题）
    updateActiveConfigs()
    
    showToast(`分组${groupNo}配置加载成功！共 ${groupConfigList.length} 个主题`, 'success')
    console.log(`分组${groupNo}配置加载成功，共 ${groupConfigList.length} 个主题`)
  } catch (error) {
    console.error('加载分组配置失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`加载分组配置失败: ${errorMsg}`, 'error')
  }
}

/**
 * 监听分组选择变化，自动加载对应分组的配置
 */
watch(
  () => selectedGroup.value,
  (newGroup, oldGroup) => {
    // 避免初始化时触发（oldGroup为undefined时是初始化）
    if (oldGroup === undefined) {
      return
    }
    
    if (newGroup === 'default') {
      // 切换到默认模式，恢复原始配置
      fetchExchangeConfig()
    } else {
      // 切换到分组模式，加载对应分组的配置
      loadGroupConfig(newGroup)
    }
  }
)

/**
 * 从 markets 同步配置到 exchangeConfig
 */
/**
 * 分页获取所有市场数据（带重试机制）
 */
const fetchAllMarkets = async () => {
  const allMarkets = []
  let page = 1
  const limit = 20
  const maxRetries = 3
  
  while (true) {
    let retries = 0
    let success = false
    let response = null
    
    // 重试逻辑
    while (retries < maxRetries && !success) {
      try {
        response = await axios.get('https://openapi.opinion.trade/openapi/market', {
          params: {
            page: page,
            limit: limit,
            status: 'activated',
            marketType: 2
          },
          headers: {
            'apikey': ORDERBOOK_API_KEY
          }
        })
        
        if (response.data?.errno === 0 && response.data?.result) {
          success = true
        } else {
          throw new Error(`API返回错误: ${response.data?.errmsg || '未知错误'}`)
        }
      } catch (error) {
        retries++
        if (retries >= maxRetries) {
          throw new Error(`获取第 ${page} 页数据失败，已重试 ${maxRetries} 次: ${error.message}`)
        }
        console.warn(`获取第 ${page} 页数据失败，正在重试 (${retries}/${maxRetries})...`)
        // 等待一段时间后重试
        await new Promise(resolve => setTimeout(resolve, 1000 * retries))
      }
    }
    
    const result = response.data.result
    const markets = result.list || []
    
    if (markets.length === 0) {
      break
    }
    
    allMarkets.push(...markets)
    console.log(`已获取第 ${page} 页，共 ${markets.length} 个市场，累计 ${allMarkets.length} 个`)
    
    // 如果当前页数量小于 limit，说明已经是最后一页
    if (markets.length < limit) {
      break
    }
    
    page++
  }
  
  console.log(`总共获取 ${allMarkets.length} 个市场`)
  return allMarkets
}

/**
 * 处理市场数据，转换为完整主题列表
 */
const processMarketsToFullTopics = (markets) => {
  const fullTopics = []
  
  markets.forEach(mainMarket => {
    if (mainMarket.childMarkets && mainMarket.childMarkets.length > 0) {
      // 有子主题的情况
      mainMarket.childMarkets.forEach(childMarket => {
        // 只处理有yesTokenId和noTokenId的子主题
        if (!childMarket.yesTokenId || !childMarket.noTokenId) {
          console.warn(`子主题 ${childMarket.marketTitle} 缺少tokenId，跳过`)
          return
        }
        
        fullTopics.push({
          trending: `${mainMarket.marketTitle}###${childMarket.marketTitle}`,
          yesTokenId: childMarket.yesTokenId,
          noTokenId: childMarket.noTokenId,
          marketId: childMarket.marketId
        })
      })
    } else {
      // 没有子主题，使用主主题自己
      if (!mainMarket.yesTokenId || !mainMarket.noTokenId) {
        console.warn(`主主题 ${mainMarket.marketTitle} 缺少tokenId，跳过`)
        return
      }
      
      fullTopics.push({
        trending: mainMarket.marketTitle,
        yesTokenId: mainMarket.yesTokenId,
        noTokenId: mainMarket.noTokenId,
        marketId: mainMarket.marketId
      })
    }
  })
  
  return fullTopics
}

const syncConfigFromMarkets = async () => {
  try {
    showToast('正在同步配置...', 'info')
    
    // 如果选择了分组模式，调用分组API并替换主题列表
    if (selectedGroup.value !== 'default') {
      await loadGroupConfig(selectedGroup.value)
      return
    }
    
    // 默认模式：使用新的 openapi
    // 1. 分页获取所有市场数据
    showToast('正在获取市场数据...', 'info')
    const allMarkets = await fetchAllMarkets()
    
    // 2. 处理市场数据，转换为完整主题列表
    const fullTopics = processMarketsToFullTopics(allMarkets)
    console.log(`处理后的完整主题数量: ${fullTopics.length}`)
    
    // 3. 获取现有配置
    const configResponse = await axios.get('https://sg.bicoin.com.cn/99l/mission/exchangeConfig')
    
    if (configResponse.data?.code !== 0) {
      throw new Error('获取配置数据失败')
    }
    
    const existingConfigs = configResponse.data.data.configList || []
    
    // 4. 创建 marketId 到 fullTopic 的映射
    const topicMap = new Map()
    fullTopics.forEach(topic => {
      topicMap.set(String(topic.marketId), topic)
    })
    
    // 5. 创建 opTopicId 到 config 的映射
    const configMap = new Map()
    existingConfigs.forEach(config => {
      if (config.opTopicId) {
        configMap.set(String(config.opTopicId), config)
      }
    })
    
    // 6. 更新现有配置
    const updatedConfigs = []
    let matchedCount = 0
    let unmatchedCount = 0
    
    for (const config of existingConfigs) {
      const opTopicId = String(config.opTopicId || '')
      const topic = topicMap.get(opTopicId)
      
      if (topic) {
        // 找到匹配的 topic，更新配置
        matchedCount++
        console.log(`✅ 匹配成功: opTopicId=${opTopicId} -> ${topic.trending}`)
        updatedConfigs.push({
          id: config.id,
          trending: topic.trending,
          trendingPart1: topic.yesTokenId,
          trendingPart2: topic.noTokenId,
          trendingPart3: config.trendingPart3,
          opUrl: `https://app.opinion.trade/detail?topicId=${topic.marketId}`,
          polyUrl: `https://app.opinion.trade/detail?topicId=${topic.marketId}`,
          opTopicId: String(topic.marketId),
          weight: config.weight || 2,
          isOpen: config.isOpen || 0
        })
        // 从 map 中移除已处理的
        topicMap.delete(opTopicId)
      } else {
        // 没有匹配的 topic，在 trending 后添加 ###undefined，其他字段置空
        unmatchedCount++
        if (unmatchedCount <= 5) {
          console.log(`❌ 未匹配: opTopicId=${opTopicId}, trending=${config.trending}`)
        }
        updatedConfigs.push({
          id: config.id,
          trending: config.trending ? `${config.trending}###undefined` : '###undefined',
          trendingPart1: '',
          trendingPart2: '',
          trendingPart3: config.trendingPart3,
          opUrl: '',
          polyUrl: '',
          opTopicId: '',
          weight: config.weight || 2,
          isOpen: config.isOpen || 0
        })
      }
    }
    
    console.log(`配置匹配结果: 匹配 ${matchedCount} 个，未匹配 ${unmatchedCount} 个`)
    
    // 7. 添加新配置（openapi 中有但 exchangeConfig 中没有的）
    const newConfigs = []
    for (const [marketId, topic] of topicMap) {
      newConfigs.push({
        trending: topic.trending,
        trendingPart1: topic.yesTokenId,
        trendingPart2: topic.noTokenId,
        trendingPart3: null,
        opUrl: `https://app.opinion.trade/detail?topicId=${topic.marketId}`,
        polyUrl: `https://app.opinion.trade/detail?topicId=${topic.marketId}`,
        opTopicId: String(topic.marketId),
        weight: 2,
        isOpen: 0
      })
    }
    
    // 8. 合并更新的配置和新配置
    const allConfigs = [...updatedConfigs, ...newConfigs]
    
    // 9. 提交到服务器
    const submitData = {
      list: allConfigs
    }
    
    console.log('同步配置数据:', {
      更新数量: updatedConfigs.length,
      新增数量: newConfigs.length,
      总数量: allConfigs.length
    })
    
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
      console.log('配置同步成功:', response.data)
      showToast(`配置同步成功！更新 ${updatedConfigs.length} 条，新增 ${newConfigs.length} 条`, 'success')
      // 重新加载配置
      updateActiveConfigs()
      fetchExchangeConfig()
    }
  } catch (error) {
    console.error('配置同步失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showToast(`配置同步失败: ${errorMsg}`, 'error')
  }
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
  
  // 初始化订单薄信息字段和最大开单量编辑字段
  editConfigList.value.forEach(config => {
    config.orderbookInfo = null
    // 初始化editMaxDailyAmount字段，如果有c字段则使用c字段的值，否则为空
    config.editMaxDailyAmount = (config.c !== undefined && config.c !== null && config.c !== '') ? config.c : ''
  })
  
  // 加载评分数据
  loadConfigRatings()
  
  // 加载拉黑状态（从本地存储获取）
  loadConfigBlacklist()
  
  // 保存原始配置数据的副本，用于比较是否修改
  originalConfigList.value = JSON.parse(JSON.stringify(editConfigList.value))
  
  showEditConfig.value = true
}

/**
 * 关闭修改配置弹窗
 */
const closeEditConfigDialog = () => {
  showEditConfig.value = false
  // 关闭时清空筛选
  editConfigFilter.value = ''
  editConfigStatusFilter.value = ''
  editConfigBatchFilter.value = ''
  showOnlyValid.value = false
  quickBlacklistInput.value = ''  // 清空快速拉黑输入框
  bulkMaxDailyAmount.value = null  // 清空批量最大开单量输入框
  // 清空原始配置数据
  originalConfigList.value = []
}

/**
 * 一键填入最大开单量
 */
const applyBulkMaxDailyAmount = () => {
  if (bulkMaxDailyAmount.value === null || bulkMaxDailyAmount.value === undefined || bulkMaxDailyAmount.value === '') {
    showToast('请输入最大开单量', 'warning')
    return
  }
  
  // 将顶部输入框的值填入所有配置的最大开单量输入框
  editConfigList.value.forEach(config => {
    config.editMaxDailyAmount = String(bulkMaxDailyAmount.value)
  })
  
  showToast(`已将最大开单量 ${bulkMaxDailyAmount.value} 填入所有配置`, 'success')
}

/**
 * 全部禁用配置
 */
const disableAllConfigs = () => {
  editConfigList.value.forEach(config => {
    config.enabled = false
  })
}

/**
 * 全部启用配置
 */
const enableAllConfigs = () => {
  editConfigList.value.forEach(config => {
    config.enabled = true
  })
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
 * 取消所有拉黑
 */
const cancelAllBlacklist = async () => {
  if (confirm('确定要取消所有配置的拉黑状态吗？')) {
    try {
      // 找出所有已拉黑的配置
      const blacklistedConfigs = editConfigList.value.filter(config => 
        config.isBlacklisted || config.a === "1" || config.a === 1
      )
      
      if (blacklistedConfigs.length === 0) {
        alert('没有已拉黑的配置')
        return
      }
      
      // 构建提交数据，将所有拉黑的配置的a字段设置为"0"
      const submitData = {
        list: blacklistedConfigs.map(config => ({
          id: config.id,
          trending: config.trending,
          trendingPart1: config.trendingPart1 || null,
          trendingPart2: config.trendingPart2 || null,
          trendingPart3: config.trendingPart3 || null,
          opUrl: config.opUrl || '',
          polyUrl: config.polyUrl || '',
          opTopicId: config.opTopicId || '',
          weight: config.weight || 0,
          isOpen: config.isOpen || (config.enabled ? 1 : 0),
          a: "0"  // 取消拉黑
        }))
      }
      
      // 调用保存接口
      const response = await axios.post(
        'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
        submitData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.data && response.data.code === 0) {
        // 更新本地状态
        blacklistedConfigs.forEach(config => {
          config.isBlacklisted = false
          config.a = "0"
        })
        
        // 更新活动配置列表
        updateActiveConfigs()
        
        alert(`已成功取消 ${blacklistedConfigs.length} 个配置的拉黑状态`)
      } else {
        throw new Error(response.data?.msg || '取消拉黑失败')
      }
    } catch (error) {
      console.error('取消所有拉黑失败:', error)
      alert('取消所有拉黑失败: ' + (error.response?.data?.msg || error.message))
    }
  }
}

/**
 * 只显示符合对冲条件的配置
 */
const showOnlyValidOrderbooks = () => {
  showOnlyValid.value = !showOnlyValid.value
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
 * 加载配置评分数据
 */
const loadConfigRatings = () => {
  try {
    const ratingsStr = localStorage.getItem('configRatings')
    if (ratingsStr) {
      const ratings = JSON.parse(ratingsStr)
      editConfigList.value.forEach(config => {
        if (ratings[config.trending]) {
          config.rating = ratings[config.trending]
        }
      })
    }
  } catch (error) {
    console.error('加载评分数据失败:', error)
  }
}

/**
 * 保存配置评分
 */
const saveConfigRating = (config) => {
  try {
    const ratingsStr = localStorage.getItem('configRatings')
    const ratings = ratingsStr ? JSON.parse(ratingsStr) : {}
    
    if (config.rating !== undefined && config.rating !== null && config.rating !== '') {
      ratings[config.trending] = config.rating
    } else {
      delete ratings[config.trending]
    }
    
    localStorage.setItem('configRatings', JSON.stringify(ratings))
  } catch (error) {
    console.error('保存评分数据失败:', error)
  }
}

/**
 * 加载配置拉黑状态（从服务器数据读取字段a）
 */
const loadConfigBlacklist = () => {
  try {
    editConfigList.value.forEach(config => {
      // 从服务器返回的数据中读取字段a，a === "1" 表示拉黑
      config.isBlacklisted = config.a === "1" || config.a === 1
    })
  } catch (error) {
    console.error('加载拉黑状态失败:', error)
    editConfigList.value.forEach(config => {
      config.isBlacklisted = false
    })
  }
}

/**
 * 保存配置拉黑状态（保存到服务器）
 */
const saveConfigBlacklist = async (config) => {
  try {
    // 更新本地状态
    config.a = config.isBlacklisted ? "1" : "0"
    
    // 构建提交数据
    const submitData = {
      list: [{
        id: config.id,
        trending: config.trending,
        trendingPart1: config.trendingPart1 || null,
        trendingPart2: config.trendingPart2 || null,
        trendingPart3: config.trendingPart3 || null,
        opUrl: config.opUrl || '',
        polyUrl: config.polyUrl || '',
        opTopicId: config.opTopicId || '',
        weight: config.weight || 0,
        isOpen: config.isOpen || (config.enabled ? 1 : 0),
        a: config.a  // 拉黑状态：1=拉黑，0=未拉黑
      }]
    }
    
    // 调用保存接口
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.code === 0) {
      // 如果被拉黑，需要关闭该主题的所有运行中的对冲任务
      if (config.isBlacklisted) {
        // 在 activeConfigs 中查找对应的配置（可能还在列表中）
        const activeConfig = activeConfigs.value.find(c => c.id === config.id)
        if (activeConfig && activeConfig.currentHedges) {
          const runningHedges = activeConfig.currentHedges.filter(h => h.finalStatus === 'running')
          if (runningHedges.length > 0) {
            console.log(`[拉黑] 配置 ${config.trending} 有 ${runningHedges.length} 个运行中的对冲任务，开始关闭...`)
            // 关闭所有运行中的对冲任务
            runningHedges.forEach(hedge => {
              hedge.finalStatus = 'blacklisted'
              finishHedge(activeConfig, hedge)
            })
            console.log(`[拉黑] 配置 ${config.trending} 的所有对冲任务已关闭`)
          }
        }
      }
      
      // 更新活动配置列表，确保拉黑的主题立即从自动分配中移除
      updateActiveConfigs()
      
      console.log(`配置 ${config.trending} ${config.isBlacklisted ? '已拉黑' : '已解除拉黑'}`)
    } else {
      // 保存失败，恢复状态
      config.isBlacklisted = !config.isBlacklisted
      config.a = config.isBlacklisted ? "1" : "0"
      throw new Error(response.data?.msg || '保存拉黑状态失败')
    }
  } catch (error) {
    console.error('保存拉黑状态失败:', error)
    alert('保存拉黑状态失败: ' + (error.response?.data?.msg || error.message))
  }
}

/**
 * 快速拉黑功能
 * 将输入框中的主题（按分号分隔）都设置为拉黑状态，并保存到服务器
 */
const quickBlacklist = async () => {
  if (!quickBlacklistInput.value || !quickBlacklistInput.value.trim()) {
    alert('请输入要拉黑的主题，用分号(;)分隔')
    return
  }
  
  // 按分号分割，去除空字符串和首尾空格
  const topics = quickBlacklistInput.value
    .split(';')
    .map(t => t.trim())
    .filter(t => t.length > 0)
  
  if (topics.length === 0) {
    alert('未找到有效的主题')
    return
  }
  
  try {
    let matchedCount = 0
    let notFoundTopics = []
    let newBlacklistedConfigs = []
    
    // 遍历所有配置，匹配主题并设置为拉黑（只进行完全匹配）
    editConfigList.value.forEach(config => {
      // 只进行完全匹配，包括###后面的部分
      const configTrending = config.trending ? config.trending.trim() : ''
      
      for (const topic of topics) {
        const topicTrimmed = topic.trim()
        
        // 完全匹配：去除首尾空格后完全相同
        if (configTrending === topicTrimmed) {
          // 检查是否已经拉黑
          const isAlreadyBlacklisted = config.a === "1" || config.a === 1
          if (!isAlreadyBlacklisted) {
            // 设置为拉黑
            config.isBlacklisted = true
            config.a = "1"
            newBlacklistedConfigs.push(config)
          } else {
            // 已经拉黑了，只更新界面状态
            config.isBlacklisted = true
          }
          matchedCount++
          break
        }
      }
    })
    
    // 检查哪些主题没有匹配到
    topics.forEach(topic => {
      const topicTrimmed = topic.trim()
      let found = false
      
      for (const config of editConfigList.value) {
        const configTrending = config.trending ? config.trending.trim() : ''
        
        // 只进行完全匹配
        if (configTrending === topicTrimmed) {
          found = true
          break
        }
      }
      
      if (!found) {
        notFoundTopics.push(topicTrimmed)
      }
    })
    
    // 如果有新拉黑的配置，调用保存接口
    if (newBlacklistedConfigs.length > 0) {
      const submitData = {
        list: newBlacklistedConfigs.map(config => ({
          id: config.id,
          trending: config.trending,
          trendingPart1: config.trendingPart1 || null,
          trendingPart2: config.trendingPart2 || null,
          trendingPart3: config.trendingPart3 || null,
          opUrl: config.opUrl || '',
          polyUrl: config.polyUrl || '',
          opTopicId: config.opTopicId || '',
          weight: config.weight || 0,
          isOpen: config.isOpen || (config.enabled ? 1 : 0),
          a: "1"  // 拉黑状态
        }))
      }
      
      const response = await axios.post(
        'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
        submitData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.data && response.data.code !== 0) {
        throw new Error(response.data?.msg || '保存拉黑状态失败')
      }
      
      // 更新活动配置列表
      updateActiveConfigs()
      
      // 显示结果
      let message = `已成功拉黑 ${matchedCount} 个主题（其中 ${newBlacklistedConfigs.length} 个新拉黑）`
      if (notFoundTopics.length > 0) {
        message += `\n\n未找到以下主题（${notFoundTopics.length} 个）:\n${notFoundTopics.slice(0, 10).join('\n')}`
        if (notFoundTopics.length > 10) {
          message += `\n... 还有 ${notFoundTopics.length - 10} 个未显示`
        }
      }
      alert(message)
      
      console.log('[快速拉黑] 匹配的主题数量:', matchedCount)
      console.log('[快速拉黑] 新拉黑的配置数量:', newBlacklistedConfigs.length)
      console.log('[快速拉黑] 未找到的主题:', notFoundTopics)
    } else {
      // 没有需要更新的配置，只显示结果
      let message = `已找到 ${matchedCount} 个主题（均已拉黑，无需更新）`
      if (notFoundTopics.length > 0) {
        message += `\n\n未找到以下主题（${notFoundTopics.length} 个）:\n${notFoundTopics.slice(0, 10).join('\n')}`
        if (notFoundTopics.length > 10) {
          message += `\n... 还有 ${notFoundTopics.length - 10} 个未显示`
        }
      }
      alert(message)
    }
  } catch (error) {
    console.error('快速拉黑失败:', error)
    alert('快速拉黑失败: ' + (error.response?.data?.msg || error.message))
  }
}

/**
 * 根据订单薄数据计算评分
 */
const calculateRating = (orderbookInfo) => {
  if (!orderbookInfo) {
    return null
  }
  
  const diff = orderbookInfo.diff
  
  let baseRating
  
  // 价差 >= 0.3：10分
  if (diff >= 0.3) {
    baseRating = 10
  }
  // 价差 = 0.2：9分
  else if (Math.abs(diff - 0.2) < 0.01) {
    baseRating = 9
  }
  // 价差 <= 0.11：根据深度评分
  else if (diff <= 0.11) {
    // 使用先挂方的深度（开仓用卖一深度depth2，平仓用买一深度depth1）
    // 为了简化，使用depth1（买一深度）
    const depth = orderbookInfo.depth1
    
    if (depth < 100) {
      baseRating = 7
    } else if (depth < 500) {
      baseRating = 6
    } else if (depth < 1000) {
      baseRating = 5
    } else if (depth < 2000) {
      baseRating = 4
    } else if (depth < 5000) {
      baseRating = 3
    } else if (depth < 10000) {
      baseRating = 2
    } else {
      baseRating = 1
    }
  }
  // 其他情况（0.11 < diff < 0.2）：根据深度评分
  else {
    const depth = orderbookInfo.depth1
    
    if (depth < 100) {
      baseRating = 7
    } else if (depth < 500) {
      baseRating = 6
    } else if (depth < 1000) {
      baseRating = 5
    } else if (depth < 2000) {
      baseRating = 4
    } else if (depth < 5000) {
      baseRating = 3
    } else if (depth < 10000) {
      baseRating = 2
    } else {
      baseRating = 1
    }
  }
  
  // 检查订单薄的数量：如果两边都小于3组，则扣4分
  const yesBidsCount = orderbookInfo.yesBidsCount || 0
  const yesAsksCount = orderbookInfo.yesAsksCount || 0
  const noBidsCount = orderbookInfo.noBidsCount || 0
  const noAsksCount = orderbookInfo.noAsksCount || 0
  
  // 判断YES方和NO方是否都小于3组
  const yesLessThan3 = yesBidsCount < 3 && yesAsksCount < 3
  const noLessThan3 = noBidsCount < 3 && noAsksCount < 3
  
  // 如果两边都小于3组，扣4分
  if (yesLessThan3 && noLessThan3) {
    baseRating = Math.max(1, baseRating - 4)  // 最低为1
  }
  
  return baseRating
}

/**
 * 计算配置所属批次
 */
const getConfigBatch = (config) => {
  // 只有启用和显示都开启的配置才会在任务列表中
  if (!config.enabled || !config.visible) {
    return null
  }
  
  // 需要检查是否有tokenId
  if (!config.trendingPart1 || !config.trendingPart2) {
    return null
  }
  
  // 获取所有符合条件的配置（与activeConfigs逻辑一致）
  const validConfigs = activeConfigs.value.filter(c => 
    c.trendingPart1 && c.trendingPart2
  )
  
  // 找到当前配置在列表中的索引
  const configIndex = validConfigs.findIndex(c => c.id === config.id || c.trending === config.trending)
  
  if (configIndex === -1) {
    return null
  }
  
  // 计算批次（从1开始）
  const batch = Math.floor(configIndex / batchSize.value) + 1
  const totalBatches = Math.ceil(validConfigs.length / batchSize.value)
  
  return `${batch}/${totalBatches}`
}

/**
 * 获取配置状态
 */
const getConfigStatus = (config) => {
  // 已拉黑：从服务器数据字段a判断
  if (config.a === "1" || config.a === 1) {
    return '已拉黑'
  }
  
  // 未添加：启用和显示有任意一个没有开启
  if (!config.enabled || !config.visible) {
    return '未添加'
  }
  
  // 需要检查是否有tokenId
  if (!config.trendingPart1 || !config.trendingPart2) {
    return '未添加'
  }
  
  // 检查是否在任务列表中
  const validConfigs = activeConfigs.value.filter(c => 
    c.trendingPart1 && c.trendingPart2
  )
  
  const configIndex = validConfigs.findIndex(c => c.id === config.id || c.trending === config.trending)
  
  if (configIndex === -1) {
    return '未添加'
  }
  
  // 计算批次索引（从0开始）
  const batchIndex = Math.floor(configIndex / batchSize.value)
  
  // 如果自动分配没有运行，返回待执行
  if (!autoHedgeRunning.value) {
    return '待执行'
  }
  
  // 检查是否是当前运行的批次
  if (batchIndex === currentBatchIndex.value) {
    return '进行中'
  }
  
  return '待执行'
}

/**
 * 获取配置状态样式类
 */
const getConfigStatusClass = (config) => {
  const status = getConfigStatus(config)
  const classMap = {
    '未添加': 'status-pending',
    '待执行': 'status-waiting',
    '进行中': 'status-running',
    '已拉黑': 'status-blacklisted'
  }
  return classMap[status] || ''
}

/**
 * 获取所有主题的订单薄数据
 */
const fetchAllOrderbooks = async () => {
  if (isFetchingOrderbooks.value) return
  
  isFetchingOrderbooks.value = true
  showToast('开始获取所有主题的订单薄数据...', 'info')
  
  try {
    // 筛选出有tokenId的配置
    const validConfigs = filteredEditConfigList.value.filter(c => c.trendingPart1 && c.trendingPart2)
    
    if (validConfigs.length === 0) {
      showToast('没有配置tokenId的主题', 'warning')
      return
    }
    
    console.log(`开始获取 ${validConfigs.length} 个主题的订单薄数据`)
    
    let successCount = 0
    let failCount = 0
    
    for (let i = 0; i < validConfigs.length; i++) {
      const config = validConfigs[i]
      
      try {
        showToast(`正在获取 ${i + 1}/${validConfigs.length}: ${config.trending.substring(0, 30)}...`, 'info')
        
        // 使用fetchOrderbookBasic获取基本订单薄数据（不进行条件检查）
        const basicInfo = await fetchOrderbookBasic(config, hedgeMode.isClose)
        
        if (basicInfo) {
          // 尝试使用parseOrderbookData进行完整检查，判断是否符合条件
          let meetsCondition = false
          try {
            const priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
            if (priceInfo) {
              meetsCondition = checkOrderbookHedgeCondition(priceInfo, config)
            }
          } catch (error) {
            // 如果parseOrderbookData失败，说明不符合条件，但依然显示基本数据
            meetsCondition = false
            console.log(`⚠️ ${config.trending}: 不符合完整条件，但显示基本数据`)
          }
          
          // 计算自动评分
          const rating = calculateRating(basicInfo)
          
          // 保存订单薄信息到config（无论是否符合条件都显示）
          config.orderbookInfo = {
            firstSide: basicInfo.firstSide,
            price1: basicInfo.price1,
            price2: basicInfo.price2,
            depth1: basicInfo.depth1,
            depth2: basicInfo.depth2,
            diff: basicInfo.diff,
            meetsCondition: meetsCondition,
            yesBidsCount: basicInfo.yesBidsCount,
            yesAsksCount: basicInfo.yesAsksCount,
            noBidsCount: basicInfo.noBidsCount,
            noAsksCount: basicInfo.noAsksCount
          }
          
          // 保存自动计算的评分
          if (rating !== null) {
            config.rating = rating
            saveConfigRating(config)
          }
          
          successCount++
          console.log(`✅ ${config.trending}: 获取成功，符合条件: ${meetsCondition}, 评分: ${rating}`)
        } else {
          config.orderbookInfo = null
          failCount++
          console.log(`❌ ${config.trending}: 获取失败`)
        }
      } catch (error) {
        config.orderbookInfo = null
        failCount++
        console.error(`获取 ${config.trending} 订单薄失败:`, error)
      }
      
      // 添加延迟，避免请求过快
      if (i < validConfigs.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    }
    
    showToast(`订单薄获取完成: 成功 ${successCount} 个，失败 ${failCount} 个`, 'success')
  } catch (error) {
    console.error('获取订单薄数据失败:', error)
    showToast(`获取失败: ${error.message}`, 'error')
  } finally {
    isFetchingOrderbooks.value = false
  }
}

/**
 * 提交修改配置（只上传修改过的主题）
 */
const submitEditConfig = async () => {
  isSubmittingConfig.value = true
  
  try {
    // 先检查是否有任何修改（包括 visible 字段）
    let hasAnyChange = false
    let hasVisibleChange = false
    const modifiedConfigs = []
    
    for (let i = 0; i < editConfigList.value.length; i++) {
      const currentConfig = editConfigList.value[i]
      const originalConfig = originalConfigList.value[i]
      
      // 检查 visible 字段是否变化
      if (currentConfig.visible !== originalConfig.visible) {
        hasVisibleChange = true
        hasAnyChange = true
      }
      
      // 比较需要提交到服务器的字段是否发生变化（包括拉黑状态a字段和最大开单量c字段）
      const currentA = currentConfig.a === "1" || currentConfig.a === 1 ? "1" : (currentConfig.a || "0")
      const originalA = originalConfig.a === "1" || originalConfig.a === 1 ? "1" : (originalConfig.a || "0")
      
      // 检查最大开单量（c字段）是否变化
      const currentC = (currentConfig.editMaxDailyAmount !== undefined && currentConfig.editMaxDailyAmount !== null && currentConfig.editMaxDailyAmount !== '') ? String(currentConfig.editMaxDailyAmount) : null
      const originalC = (originalConfig.c !== undefined && originalConfig.c !== null && originalConfig.c !== '') ? String(originalConfig.c) : null
      const cChanged = currentC !== originalC
      
      const isServerFieldModified = 
        currentConfig.trending !== originalConfig.trending ||
        currentConfig.opUrl !== originalConfig.opUrl ||
        currentConfig.polyUrl !== originalConfig.polyUrl ||
        currentConfig.opTopicId !== originalConfig.opTopicId ||
        currentConfig.weight !== originalConfig.weight ||
        currentConfig.enabled !== originalConfig.enabled ||
        currentConfig.group !== originalConfig.group ||
        currentA !== originalA ||
        cChanged
      
      if (isServerFieldModified) {
        hasAnyChange = true
        modifiedConfigs.push(currentConfig)
      }
    }
    
    // 如果没有任何修改，提示并返回
    if (!hasAnyChange) {
      alert('没有修改任何配置')
      isSubmittingConfig.value = false
      return
    }
    
    // 保存显示状态到本地存储（不提交到服务器）
    saveConfigVisibleStatus(editConfigList.value)
    
    // 如果只修改了显示/隐藏状态，不需要提交到服务器
    if (hasVisibleChange && modifiedConfigs.length === 0) {
      alert('显示/隐藏状态已保存到本地')
      // 更新活动配置列表，使显示/隐藏状态生效
      updateActiveConfigs()
      closeEditConfigDialog()
      isSubmittingConfig.value = false
      return
    }
    
    // 构建提交数据，保持 trendingPart1、trendingPart2、trendingPart3 不变
    const submitData = {
      list: modifiedConfigs.map(config => {
        // 处理最大开单量（c字段）：如果editMaxDailyAmount有值则使用，否则为null
        const cValue = (config.editMaxDailyAmount !== undefined && config.editMaxDailyAmount !== null && config.editMaxDailyAmount !== '') ? String(config.editMaxDailyAmount) : null
        
        return {
          id: config.id,  // 带上id表示更新
          trending: config.trending,
          trendingPart1: config.trendingPart1 || null,
          trendingPart2: config.trendingPart2 || null,
          trendingPart3: config.trendingPart3 || null,
          opUrl: config.opUrl,
          polyUrl: config.polyUrl,
          opTopicId: config.opTopicId,
          weight: config.weight || 0,
          isOpen: config.enabled ? 1 : 0,  // enabled 映射为 isOpen (true->1, false->0)
          group: config.group || null,  // 添加group字段
          a: config.a === "1" || config.a === 1 ? "1" : (config.a || "0"),  // 拉黑状态：1=拉黑，0=未拉黑
          c: cValue  // 今日最大开单量
          // 注意：visible 字段不提交到服务器
        }
      })
    }
    
    console.log(`提交修改配置（共 ${modifiedConfigs.length} 个）:`, submitData)
    
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
      alert(`配置更新成功！共更新 ${modifiedConfigs.length} 个主题`)
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
  let result = activeConfigs.value
  
  // 根据排序方式排序
  result = [...result].sort((a, b) => {
    if (hedgeSortBy.value === 'yesAmt') {
      // 按YES金额排序（降序，大的在前）
      const yesAmtA = a.yesAmt || 0
      const yesAmtB = b.yesAmt || 0
      return yesAmtB - yesAmtA
    } else if (hedgeSortBy.value === 'weightedAvgTime') {
      // 按创建时间加权平均值排序（降序，大的在前）
      const weightedAvgTimeA = a.weightedAvgTime || 0
      const weightedAvgTimeB = b.weightedAvgTime || 0
      return weightedAvgTimeB - weightedAvgTimeA
    } else if (hedgeSortBy.value === 'volume24h') {
      // 按24h量排序（降序，大的在前）
      const volume24hA = a.volume24h || 0
      const volume24hB = b.volume24h || 0
      return volume24hB - volume24hA
    } else if (hedgeSortBy.value === 'volume7dAvg') {
      // 按7天平均量排序（降序，大的在前）
      const volume7dAvgA = a.volume7dAvg || 0
      const volume7dAvgB = b.volume7dAvg || 0
      return volume7dAvgB - volume7dAvgA
    } else {
      // 默认按持仓yes大小排序，持仓大的排最上方
      const positionDataA = positionDataMap.value.get(a.trending?.trim())
      const positionDataB = positionDataMap.value.get(b.trending?.trim())
      
      const yesPositionA = positionDataA?.yesPosition || 0
      const yesPositionB = positionDataB?.yesPosition || 0
      
      // 按持仓yes大小降序排序（大的在前）
      return yesPositionB - yesPositionA
    }
  })
  
  // 应用筛选
  if (autoHedgeFilter.value && autoHedgeFilter.value.trim()) {
    const keyword = autoHedgeFilter.value.trim().toLowerCase()
    result = result.filter(config => {
      const trending = (config.trending || '').toLowerCase()
      return trending.includes(keyword)
    })
  }
  
  return result
})

/**
 * 获取所有可用的批次列表（用于下拉选择）
 */
const availableBatches = computed(() => {
  const batches = new Set()
  editConfigList.value.forEach(config => {
    const batch = getConfigBatch(config)
    if (batch) {
      batches.add(batch)
    }
  })
  return Array.from(batches).sort((a, b) => {
    // 按批次排序，例如 "1/5" < "2/5"
    const [aNum] = a.split('/').map(Number)
    const [bNum] = b.split('/').map(Number)
    return aNum - bNum
  })
})

/**
 * 筛选后的编辑配置列表（用于修改配置弹窗显示）
 */
const filteredEditConfigList = computed(() => {
  let result = editConfigList.value
  
  // 先根据关键词筛选
  if (editConfigFilter.value && editConfigFilter.value.trim()) {
    const keyword = editConfigFilter.value.trim().toLowerCase()
    result = result.filter(config => {
      const trending = (config.trending || '').toLowerCase()
      return trending.includes(keyword)
    })
  }
  
  // 根据当前状态筛选
  if (editConfigStatusFilter.value) {
    result = result.filter(config => {
      return getConfigStatus(config) === editConfigStatusFilter.value
    })
  }
  
  // 根据所属批次筛选
  if (editConfigBatchFilter.value) {
    result = result.filter(config => {
      return getConfigBatch(config) === editConfigBatchFilter.value
    })
  }
  
  // 如果开启了"只显示符合对冲条件的"筛选
  if (showOnlyValid.value) {
    result = result.filter(config => {
      return config.orderbookInfo && config.orderbookInfo.meetsCondition === true
    })
  }
  
  return result
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
  // 先保存当前活动配置的对冲信息和订单薄信息（避免被清空）
  const hedgeInfoMap = new Map()
  for (const config of activeConfigs.value) {
    if (config.currentHedges || config.currentHedge || config.orderbookData) {
      hedgeInfoMap.set(config.id, {
        currentHedges: config.currentHedges || [],
        currentHedge: config.currentHedge || null,
        orderbookData: config.orderbookData || null,  // 保存订单薄数据
      })
    }
  }
  
  // 先加载显示状态
  const configsWithVisible = loadConfigVisibleStatus(configList.value)
  
  // 加载主题设置
  const topicSettings = loadTopicSettings()
  
  // 过滤配置：启用状态(isOpen=1)、未拉黑(a !== "1")、且本地显示是打开的
  activeConfigs.value = configsWithVisible
    .filter(config => config.isOpen === 1 || config.enabled === true)  // 启用的配置
    .filter(config => config.visible !== false)  // 显示开关打开的配置
    .filter(config => config.a !== "1" && config.a !== 1)  // 过滤掉拉黑的配置（a !== "1" 表示未拉黑）
    .map(config => {
      // 恢复保存的对冲信息和订单薄信息
      const savedInfo = hedgeInfoMap.get(config.id)
      
      // 加载该主题的保存设置
      const configId = String(config.id)
      const savedTopicSetting = topicSettings[configId] || {}
      
      return {
        ...config,
        // 优先使用保存的订单薄数据，如果没有保存的则使用原配置中的数据，最后才为null
        orderbookData: savedInfo ? (savedInfo.orderbookData || config.orderbookData || null) : (config.orderbookData || null),
        weight: config.weight || 0,
        // 优先使用保存的对冲任务数组，如果没有保存的则使用原配置中的数据
        currentHedges: savedInfo ? (savedInfo.currentHedges.length > 0 ? savedInfo.currentHedges : (config.currentHedges || [])) : (config.currentHedges || []),
        currentHedge: savedInfo ? (savedInfo.currentHedge || config.currentHedge || null) : (config.currentHedge || null),  // 当前对冲任务
        lastRequestTime: config.lastRequestTime || null,  // 上次请求时间
        lastHedgeTime: config.lastHedgeTime || null,  // 上次对冲时间
        noHedgeSince: config.noHedgeSince || null,  // 开始无法对冲的时间
        isFetching: config.isFetching || false,  // 是否正在请求中
        retryCount: config.retryCount || 0,  // 重试次数
        errorMessage: config.errorMessage || null,  // 错误信息
        // 加载保存的主题设置
        savedTasksPerTopic: savedTopicSetting.tasksPerTopic !== undefined ? savedTopicSetting.tasksPerTopic : (config.savedTasksPerTopic || undefined),
        savedMaxDepth: savedTopicSetting.maxDepth !== undefined ? savedTopicSetting.maxDepth : (config.savedMaxDepth || undefined),
        // 将保存的值也赋值给输入框绑定的字段，这样刷新后输入框能显示保存的值
        tasksPerTopic: savedTopicSetting.tasksPerTopic !== undefined ? savedTopicSetting.tasksPerTopic : (config.tasksPerTopic || undefined),
        maxDepth: savedTopicSetting.maxDepth !== undefined ? savedTopicSetting.maxDepth : (config.maxDepth || undefined)
      }
    })
}

/**
 * 切换自动对冲状态
 */
const toggleAutoHedge = () => {
  if (autoHedgeRunning.value) {
    stopAutoHedge()
  } else {
    // 在开始自动分配时保存所有对冲模块的输入框数据
    saveHedgeSettings()
    startAutoHedge()
  }
}

/**
 * 开始自动对冲
 */
const startAutoHedge = () => {
  // 在开始自动分配时，先更新活动配置列表，过滤掉拉黑的主题
  updateActiveConfigs()
  
  if (activeConfigs.value.length === 0) {
    alert('没有启用的主题配置')
    return
  }
  
  // 检查是否有配置了tokenId的主题
  const hasValidConfig = activeConfigs.value.some(c => c.trendingPart1 && c.trendingPart2)
  if (!hasValidConfig) {
    alert('请至少为一个主题配置tokenId（需要先更新配置）')
    return
  }
  
  // 检查对冲数量状态
  if (hedgeStatus.amt === 0) {
    alert('对冲总数量为0，无法开始自动对冲。请先在"总数量"输入框中设置一个大于0的数量，然后点击"更新对冲数量"按钮。')
    return
  }
  
  if (hedgeStatus.amtSum >= hedgeStatus.amt) {
    alert(`对冲数量已满！累计对冲数量(${hedgeStatus.amtSum})已达到或超过总数量(${hedgeStatus.amt})。如需继续对冲，请先点击"清空当前已开"按钮，或增加总数量。`)
    return
  }
  
  autoHedgeRunning.value = true
  currentBatchIndex.value = 0  // 重置批次索引
  
  // 如果启用了分批模式
  if (enableBatchMode.value) {
    // 验证批次设置
    if (batchSize.value < 1) {
      alert('每一批的个数必须大于0')
      autoHedgeRunning.value = false
      return
    }
    if (batchExecutionTime.value < 1) {
      alert('每一批的执行时间必须大于0')
      autoHedgeRunning.value = false
      return
    }
    
    console.log('开始自动对冲（分批执行模式）')
    // 立即执行第一批
    executeBatch()
  } else {
    // 不分批，直接执行所有主题
    console.log('开始自动对冲（全部同时执行模式）')
    executeAllTopics()
  }
}

/**
 * 停止自动对冲
 */
const stopAutoHedge = () => {
  autoHedgeRunning.value = false
  
  // 清除定时器
  if (autoHedgeInterval.value) {
    clearInterval(autoHedgeInterval.value)
    autoHedgeInterval.value = null
  }
  if (batchTimer.value) {
    clearTimeout(batchTimer.value)
    batchTimer.value = null
  }
  
  // 清除所有配置的状态
  for (const config of activeConfigs.value) {
    config.isFetching = false
    config.retryCount = 0
    config.errorMessage = null
    config.noHedgeSince = null
    console.log(`配置 ${config.id} - 清除状态`)
  }
  
  currentBatchIndex.value = 0
  console.log('停止自动对冲')
}

/**
 * 切换分组执行状态
 */
const toggleGroupExecution = () => {
  if (groupExecution.isRunning) {
    stopGroupExecution()
  } else {
    startGroupExecution()
  }
}

/**
 * 开始分组执行
 */
const startGroupExecution = () => {
  // 验证输入
  if (!groupExecution.roundTimeHours || groupExecution.roundTimeHours <= 0) {
    alert('每轮时间必须大于0')
    return
  }
  if (groupExecution.intervalMinutes < 0) {
    alert('每轮间隔时间不能小于0')
    return
  }
  
  groupExecution.isRunning = true
  
  // 记录当前轮开始时间戳
  groupExecution.currentRoundStartTime = Date.now()
  groupExecution.previousRoundEndTime = null
  groupExecution.unrefreshedCount = 0
  groupExecution.unrefreshedBrowsers = []
  groupExecution.unrefreshedBrowserInfo = []
  
  // 如果当前是默认分组，切换到分组1
  if (selectedGroup.value === 'default') {
    selectedGroup.value = '1'
  }
  
  // 执行当前分组
  executeCurrentGroup()
}

/**
 * 执行当前分组
 */
const executeCurrentGroup = async () => {
  try {
    // 清除之前的定时器
    if (groupExecution.timer) {
      clearTimeout(groupExecution.timer)
      groupExecution.timer = null
    }
    if (groupExecution.intervalTimer) {
      clearTimeout(groupExecution.intervalTimer)
      groupExecution.intervalTimer = null
    }
    
    // 确保分组配置已加载
    if (selectedGroup.value !== 'default') {
      await loadGroupConfig(selectedGroup.value)
    }
    
    // 等待配置加载完成后，开始自动分配
    setTimeout(() => {
      if (!autoHedgeRunning.value && groupExecution.isRunning) {
        toggleAutoHedge()
      }
      
      // 设置定时器，在每轮时间后切换到另一组
      if (groupExecution.isRunning) {
        const roundTimeMs = groupExecution.roundTimeHours * 60 * 60 * 1000
        groupExecution.timer = setTimeout(() => {
          if (groupExecution.isRunning) {
            // 停止当前自动对冲
            if (autoHedgeRunning.value) {
              stopAutoHedge()
            }
            
            // 等待间隔时间
            const intervalMs = groupExecution.intervalMinutes * 60 * 1000
            if (intervalMs > 0) {
              groupExecution.intervalTimer = setTimeout(() => {
                if (groupExecution.isRunning) {
                  switchToNextGroup()
                }
              }, intervalMs)
            } else {
              switchToNextGroup()
            }
          }
        }, roundTimeMs)
        
        console.log(`开始分组执行，当前分组：${selectedGroup.value}，每轮时间：${groupExecution.roundTimeHours}小时，间隔时间：${groupExecution.intervalMinutes}分钟`)
      }
    }, 1000)
  } catch (error) {
    console.error('执行当前分组失败:', error)
    showToast('执行当前分组失败', 'error')
    groupExecution.isRunning = false
  }
}

/**
 * 切换到下一组
 */
const switchToNextGroup = () => {
  // 记录上一轮结束时间戳（即当前轮开始时间）
  if (groupExecution.currentRoundStartTime) {
    groupExecution.previousRoundEndTime = groupExecution.currentRoundStartTime
  }
  
  // 记录新的当前轮开始时间戳
  groupExecution.currentRoundStartTime = Date.now()
  
  // 重置未刷新数量（等待新的检查结果）
  groupExecution.unrefreshedCount = 0
  groupExecution.unrefreshedBrowsers = []
  groupExecution.unrefreshedBrowserInfo = []
  
  // 清除之前的检查定时器
  if (groupExecution.checkTimer) {
    clearInterval(groupExecution.checkTimer)
    groupExecution.checkTimer = null
  }
  
  // 在分组1和分组2之间切换
  if (selectedGroup.value === '1') {
    selectedGroup.value = '2'
  } else if (selectedGroup.value === '2') {
    selectedGroup.value = '1'
  } else {
    // 如果是默认分组，切换到分组1
    selectedGroup.value = '1'
  }
  
  // 等待分组切换完成后，执行当前分组
  setTimeout(() => {
    if (groupExecution.isRunning) {
      executeCurrentGroup()
      
      // 如果有上一轮结束时间，等待15分钟后开始检查
      if (groupExecution.previousRoundEndTime) {
        setTimeout(() => {
          if (groupExecution.isRunning) {
            checkPositionRefreshStatus()
            // 每隔15分钟检查一次
            groupExecution.checkTimer = setInterval(() => {
              if (groupExecution.isRunning) {
                checkPositionRefreshStatus()
              } else {
                clearInterval(groupExecution.checkTimer)
                groupExecution.checkTimer = null
              }
            }, 15 * 60 * 1000)  // 15分钟
          }
        }, 15 * 60 * 1000)  // 等待15分钟
      }
    }
  }, 1000)
}

/**
 * 停止分组执行
 */
const stopGroupExecution = () => {
  groupExecution.isRunning = false
  
  // 清除定时器
  if (groupExecution.timer) {
    clearTimeout(groupExecution.timer)
    groupExecution.timer = null
  }
  if (groupExecution.intervalTimer) {
    clearTimeout(groupExecution.intervalTimer)
    groupExecution.intervalTimer = null
  }
  if (groupExecution.checkTimer) {
    clearInterval(groupExecution.checkTimer)
    groupExecution.checkTimer = null
  }
  
  // 停止自动对冲
  if (autoHedgeRunning.value) {
    stopAutoHedge()
  }
  
  console.log('停止分组执行')
}

/**
 * 检查仓位刷新状态
 */
const checkPositionRefreshStatus = async () => {
  if (!groupExecution.previousRoundEndTime || !groupExecution.currentRoundStartTime) {
    console.log('没有上一轮时间戳，跳过检查')
    return
  }
  
  try {
    const startTime = groupExecution.previousRoundEndTime
    const endTime = groupExecution.currentRoundStartTime
    
    console.log(`开始检查仓位刷新状态，时间段：${new Date(startTime).toLocaleString()} - ${new Date(endTime).toLocaleString()}`)
    
    // 1. 调用 numberInUseList 接口获取浏览器编号列表
    const numberListResponse = await axios.get('https://sg.bicoin.com.cn/99l/hedge/numberInUseList', {
      params: {
        startTime: startTime,
        endTime: endTime
      }
    })
    
    if (numberListResponse.data?.code !== 0 || !numberListResponse.data?.data?.list) {
      console.error('获取浏览器编号列表失败:', numberListResponse.data)
      return
    }
    
    const browserNumbers = numberListResponse.data.data.list
    console.log(`获取到 ${browserNumbers.length} 个浏览器编号`)
    
    // 2. 调用 findAccountConfigCache 接口获取浏览器详细信息
    const accountConfigResponse = await axios.get('https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache')
    
    if (accountConfigResponse.data?.code !== 0 || !accountConfigResponse.data?.data) {
      console.error('获取账户配置失败:', accountConfigResponse.data)
      return
    }
    
    const accountConfigs = accountConfigResponse.data.data
    console.log(`获取到 ${accountConfigs.length} 个账户配置`)
    
    // 3. 筛选出在浏览器编号列表中的账户（需要处理字符串和数字类型的匹配）
    const relevantAccounts = accountConfigs.filter(account => {
      const fingerprintNo = String(account.fingerprintNo || '')
      return browserNumbers.some(num => String(num) === fingerprintNo)
    })
    
    console.log(`筛选出 ${relevantAccounts.length} 个相关账户`)
    
    // 4. 检查哪些账户的 d 字段时间戳小于上一轮结束时间戳
    const currentTime = Date.now()
    const fifteenMinutesAgo = currentTime - 15 * 60 * 1000
    
    const unrefreshedBrowsers = []
    const unrefreshedBrowserInfo = []
    
    for (const account of relevantAccounts) {
      const dTimestamp = parseInt(account.d) || 0
      const fTimestamp = parseInt(account.f) || 0
      
      // 如果 d 字段时间戳小于上一轮结束时间戳
      if (dTimestamp < groupExecution.previousRoundEndTime) {
        // 检查 f 字段时间戳是否小于当前时间戳15分钟
        if (fTimestamp < fifteenMinutesAgo) {
          // 调用 add 接口添加任务
          try {
            await axios.post('https://sg.bicoin.com.cn/99l/mission/add', {
              groupNo: account.computeGroup || '1',
              numberList: account.fingerprintNo,
              type: 2,
              exchangeName: 'OP'
            })
            console.log(`已为浏览器 ${account.fingerprintNo} 添加刷新任务`)
          } catch (error) {
            console.error(`为浏览器 ${account.fingerprintNo} 添加任务失败:`, error)
          }
        }
        
        // 记录未刷新的浏览器
        unrefreshedBrowsers.push(account.fingerprintNo)
        // 保存浏览器详细信息（包含电脑组）
        unrefreshedBrowserInfo.push({
          fingerprintNo: account.fingerprintNo,
          computeGroup: account.computeGroup || '1'
        })
      }
    }
    
    // 更新未刷新数量和列表
    groupExecution.unrefreshedCount = unrefreshedBrowsers.length
    groupExecution.unrefreshedBrowsers = unrefreshedBrowsers
    groupExecution.unrefreshedBrowserInfo = unrefreshedBrowserInfo
    
    console.log(`检查完成，未刷新数量：${unrefreshedBrowsers.length}`)
    
    // 如果还有未刷新的，继续等待下次检查
    if (unrefreshedBrowsers.length > 0) {
      console.log(`还有 ${unrefreshedBrowsers.length} 个浏览器未刷新，将在15分钟后再次检查`)
    } else {
      console.log('所有浏览器都已刷新')
      // 如果所有浏览器都已刷新，可以停止检查（但定时器会继续运行直到下一轮开始）
    }
    
  } catch (error) {
    console.error('检查仓位刷新状态失败:', error)
    showToast('检查仓位刷新状态失败', 'error')
  }
}

/**
 * 查询未完成type2任务的浏览器
 */
const checkUnfinishedType2Browsers = async () => {
  if (!groupExecution.previousRoundEndTime || !groupExecution.currentRoundStartTime) {
    alert('请先开始分组执行')
    return
  }
  
  isLoadingUnfinishedType2.value = true
  unfinishedType2Browsers.value = []
  
  try {
    const startTime = groupExecution.previousRoundEndTime
    const endTime = groupExecution.currentRoundStartTime
    
    console.log(`开始查询未完成type2任务，时间段：${new Date(startTime).toLocaleString()} - ${new Date(endTime).toLocaleString()}`)
    
    // 1. 调用 numberInUseList 接口获取浏览器编号列表
    const numberListResponse = await axios.get('https://sg.bicoin.com.cn/99l/hedge/numberInUseList', {
      params: {
        startTime: startTime,
        endTime: endTime
      }
    })
    
    if (numberListResponse.data?.code !== 0 || !numberListResponse.data?.data?.list) {
      console.error('获取浏览器编号列表失败:', numberListResponse.data)
      alert('获取浏览器编号列表失败')
      return
    }
    
    const browserNumbers = numberListResponse.data.data.list
    console.log(`获取到 ${browserNumbers.length} 个浏览器编号`)
    
    // 2. 调用 findAccountConfigCache 接口获取浏览器详细信息
    const accountConfigResponse = await axios.get('https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache')
    
    if (accountConfigResponse.data?.code !== 0 || !accountConfigResponse.data?.data) {
      console.error('获取账户配置失败:', accountConfigResponse.data)
      alert('获取账户配置失败')
      return
    }
    
    const accountConfigs = accountConfigResponse.data.data
    console.log(`获取到 ${accountConfigs.length} 个账户配置`)
    
    // 3. 筛选出在浏览器编号列表中的账户
    const relevantAccounts = accountConfigs.filter(account => {
      const fingerprintNo = String(account.fingerprintNo || '')
      return browserNumbers.some(num => String(num) === fingerprintNo)
    })
    
    console.log(`筛选出 ${relevantAccounts.length} 个相关账户`)
    
    // 4. 获取任务列表，查找type=2的任务
    const missionListResponse = await axios.get('https://sg.bicoin.com.cn/99l/mission/list', {
      params: {
        limit: 1000  // 获取更多任务
      }
    })
    
    if (missionListResponse.data?.code !== 0 || !missionListResponse.data?.data?.list) {
      console.error('获取任务列表失败:', missionListResponse.data)
      alert('获取任务列表失败')
      return
    }
    
    const allMissions = missionListResponse.data.data.list || []
    // 筛选出type=2的任务，且时间在上一轮范围内
    const type2Missions = allMissions.filter(mission => {
      return mission.type === 2 && 
             mission.createTime >= startTime && 
             mission.createTime <= endTime
    })
    
    console.log(`找到 ${type2Missions.length} 个type2任务`)
    
    // 5. 为每个相关账户查找对应的type2任务，检查是否完成
    const unfinishedBrowsers = []
    
    for (const account of relevantAccounts) {
      const fingerprintNo = account.fingerprintNo
      
      // 查找该浏览器的type2任务
      const browserTasks = type2Missions.filter(mission => {
        return String(mission.numberList) === String(fingerprintNo)
      })
      
      // 检查是否有未完成的任务（status !== 2 表示未成功）
      const unfinishedTasks = browserTasks.filter(task => task.status !== 2)
      
      if (unfinishedTasks.length > 0) {
        // 获取最新的未完成任务
        const latestTask = unfinishedTasks.sort((a, b) => b.createTime - a.createTime)[0]
        unfinishedBrowsers.push({
          fingerprintNo: fingerprintNo,
          computeGroup: account.computeGroup || '1',
          taskId: latestTask.id,
          status: latestTask.status
        })
      }
    }
    
    unfinishedType2Browsers.value = unfinishedBrowsers
    showUnfinishedType2Dialog.value = true
    
    console.log(`查询完成，未完成type2任务的浏览器：${unfinishedBrowsers.length} 个`)
    
    if (unfinishedBrowsers.length === 0) {
      alert('所有浏览器的type2任务都已完成')
    }
    
  } catch (error) {
    console.error('查询未完成type2任务失败:', error)
    showToast('查询未完成type2任务失败', 'error')
    alert('查询失败：' + (error.response?.data?.message || error.message || '未知错误'))
  } finally {
    isLoadingUnfinishedType2.value = false
  }
}

/**
 * 获取任务状态文本
 */
const getTaskStatusText = (status) => {
  const statusMap = {
    0: '待执行',
    1: '执行中',
    2: '成功',
    3: '失败',
    9: '进行中'
  }
  return statusMap[status] || `状态${status}`
}

/**
 * 获取总任务数（总计个数）
 * 参考browser_status.html的逻辑
 */
const getTotalTaskCount = async () => {
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/hedge/groupStatusV2')
    const result = response.data

    if (result.code === 0 && result.data) {
      // 固定的电脑组列表（与browser_status.html保持一致）
      const fixedGroupIds = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,21,22,23,24,25,26,27,901,902,903,904,905,906,907,908,909,910,911,912,913,914,915,916,921,922,923,924,925,926,927]
      
      const detail = result.data.detail || {}
      let totalSum = 0

      // 遍历每个固定的电脑组
      fixedGroupIds.forEach(groupId => {
        // 将组号转换为字符串和数字，以便匹配数据
        const groupIdStr = String(groupId)
        const groupIdNum = Number(groupId)
        
        // 尝试从detail中获取浏览器列表（支持字符串和数字key）
        const browserList = detail[groupIdStr] || detail[groupIdNum] || []
        
        // 累加总计个数
        totalSum += browserList.length
      })

      return totalSum
    } else {
      console.error('获取总任务数失败:', result.msg || '无数据')
      return null
    }
  } catch (error) {
    console.error('获取总任务数异常:', error)
    return null
  }
}

/**
 * 检查总任务数是否满足分配条件
 * @returns {Promise<boolean>} true=满足条件，可以分配；false=不满足条件，不能分配
 */
const checkTaskCountCondition = async () => {
  const totalCount = await getTotalTaskCount()
  
  if (totalCount === null) {
    // 获取失败，允许继续执行
    console.log('获取总任务数失败，允许继续执行')
    return true
  }
  
  const operator = hedgeMode.totalTaskCountOperator
  const threshold = hedgeMode.totalTaskCountThreshold
  
  let canAllocate = false
  
  if (operator === 'gt') {
    // 大于阈值才分配
    canAllocate = totalCount > threshold
    console.log(`总任务数控制检查: 当前总任务数=${totalCount}, 需要大于${threshold}, ${canAllocate ? '满足条件' : '不满足条件'}`)
  } else {
    // 小于阈值才分配
    canAllocate = totalCount < threshold
    console.log(`总任务数控制检查: 当前总任务数=${totalCount}, 需要小于${threshold}, ${canAllocate ? '满足条件' : '不满足条件'}`)
  }
  
  return canAllocate
}

/**
 * 执行所有主题（不分批模式）
 */
const executeAllTopics = async () => {
  if (!autoHedgeRunning.value) {
    return
  }
  
  // 获取所有有效的主题列表
  let validConfigs = filteredActiveConfigs.value.filter(c => c.trendingPart1 && c.trendingPart2)
  
  if (validConfigs.length === 0) {
    console.log('没有有效的主题配置')
    return
  }
  
  // 打乱主题顺序
  validConfigs = [...validConfigs].sort(() => Math.random() - 0.5)
  
  console.log(`开始执行所有 ${validConfigs.length} 个主题（不分批模式）`)
  
  // 执行所有主题的任务
  await executeAutoHedgeTasksForBatch(validConfigs)
  
  // 设置定时器，定期执行（每20秒执行一次）
  if (autoHedgeRunning.value) {
    autoHedgeInterval.value = setInterval(async () => {
      if (!autoHedgeRunning.value) {
        return
      }
      
      // 重新获取有效的主题列表（因为可能有替换）
      let currentValidConfigs = filteredActiveConfigs.value.filter(c => c.trendingPart1 && c.trendingPart2)
      
      // 打乱主题顺序
      currentValidConfigs = [...currentValidConfigs].sort(() => Math.random() - 0.5)
      
      if (currentValidConfigs.length > 0) {
        await executeAutoHedgeTasksForBatch(currentValidConfigs)
      }
    }, 30000)  // 20秒执行一次
  }
}

/**
 * 执行当前批次
 */
const executeBatch = async () => {
  if (!autoHedgeRunning.value) {
    return
  }
  
  // 获取当前批次的主题列表
  const validConfigs = filteredActiveConfigs.value.filter(c => c.trendingPart1 && c.trendingPart2)
  const totalBatches = Math.ceil(validConfigs.length / batchSize.value)
  
  if (totalBatches === 0) {
    console.log('没有有效的主题配置')
    return
  }
  
  // 计算当前批次的起始和结束索引
  const startIndex = currentBatchIndex.value * batchSize.value
  const endIndex = Math.min(startIndex + batchSize.value, validConfigs.length)
  const currentBatchConfigs = validConfigs.slice(startIndex, endIndex)
  
  console.log(`开始执行第 ${currentBatchIndex.value + 1}/${totalBatches} 批，包含 ${currentBatchConfigs.length} 个主题`)
  
  // 记录批次开始时间
  const batchStartTime = Date.now()
  
  // 执行当前批次的任务
  await executeAutoHedgeTasksForBatch(currentBatchConfigs)
  
  // 计算剩余时间（将分钟转换为毫秒）
  const elapsed = Date.now() - batchStartTime
  const remainingTime = Math.max(0, batchExecutionTime.value * 60 * 1000 - elapsed)
  
  if (remainingTime > 0) {
    console.log(`批次执行完成，等待 ${remainingTime}ms 后切换到下一批`)
    batchTimer.value = setTimeout(() => {
      moveToNextBatch()
    }, remainingTime)
  } else {
    // 如果已经超时，立即切换到下一批
    moveToNextBatch()
  }
}

/**
 * 切换到下一批
 */
const moveToNextBatch = () => {
  if (!autoHedgeRunning.value) {
    return
  }
  
  const validConfigs = filteredActiveConfigs.value.filter(c => c.trendingPart1 && c.trendingPart2)
  const totalBatches = Math.ceil(validConfigs.length / batchSize.value)
  
  if (totalBatches === 0) {
    console.log('没有有效的主题配置，停止执行')
    return
  }
  
  // 移动到下一批（循环执行）
  currentBatchIndex.value = (currentBatchIndex.value + 1) % totalBatches
  
  console.log(`切换到第 ${currentBatchIndex.value + 1}/${totalBatches} 批`)
  
  // 执行下一批
  executeBatch()
}

/**
 * 执行指定批次的主题任务
 */
const executeAutoHedgeTasksForBatch = async (batchConfigs) => {
  console.log(`执行批次任务，包含 ${batchConfigs.length} 个主题`)
  
  // 检查总任务数是否满足分配条件
  const canAllocateByTaskCount = await checkTaskCountCondition()
  if (!canAllocateByTaskCount) {
    console.log('总任务数不满足分配条件，跳过本次任务分配')
    return
  }
  
  // 检查是否可以下发新的对冲任务
  const canStartNewHedge = !(hedgeStatus.amtSum >= hedgeStatus.amt || hedgeStatus.amt === 0)
  if (!canStartNewHedge) {
    if (hedgeStatus.amt === 0) {
      console.log('对冲总数量为0，不下发新对冲任务')
      showToast('对冲总数量为0，无法对冲。请设置总数量并更新。', 'warning')
    } else {
      console.log(`对冲数量已满（${hedgeStatus.amtSum}/${hedgeStatus.amt}），不下发新对冲任务`)
      showToast(`对冲数量已满（${hedgeStatus.amtSum}/${hedgeStatus.amt}），无法继续对冲`, 'warning')
    }
  }
  
  // 统计这一轮开出的任务总数
  let roundTaskCount = 0
  
  for (let i = 0; i < batchConfigs.length; i++) {
    const config = batchConfigs[i]
    
    // 每个主题之间间隔0.5秒（第一个主题不需要延迟）
    if (i > 0) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    try {
      // 检查该主题是否正在执行对冲
      const currentHedges = config.currentHedges || []
      const runningHedges = currentHedges.filter(h => h.finalStatus === 'running')
      
      if (runningHedges.length > 0) {
        // 检查是否有超时的任务
        const now = new Date()
        let hasTimeout = false
        for (const hedge of runningHedges) {
          const startTime = new Date(hedge.startTime)
          const elapsed = (now - startTime) / 1000 / 60
          if (elapsed >= 20) {
            console.log(`配置 ${config.id} 对冲任务 ${hedge.id} 超时（${elapsed.toFixed(1)}分钟），强制结束`)
            hedge.finalStatus = 'timeout'
            finishHedge(config, hedge)
            hasTimeout = true
          }
        }
        
        if (hasTimeout) {
          // 清空错误信息和无法对冲时间
          config.errorMessage = null
          config.noHedgeSince = null
        }
        
        // 检查是否还有运行中的任务，如果有且未达到最大任务数，可以继续
        const remainingRunning = (config.currentHedges || []).filter(h => h.finalStatus === 'running').length
        const maxTasks = getTasksPerTopic(config)
        
        if (remainingRunning >= maxTasks) {
          console.log(`配置 ${config.id} 正在执行 ${remainingRunning} 个对冲任务（已达最大 ${maxTasks}），跳过订单薄请求`)
          continue
        }
      } else {
        // 没有运行中的任务，检查任务间隔
        if (config.lastGroupFinishTime && hedgeTaskInterval.value > 0) {
          const now = Date.now()
          const elapsed = (now - config.lastGroupFinishTime) / 1000 / 60  // 转换为分钟
          const intervalMinutes = hedgeTaskInterval.value
          
          if (elapsed < intervalMinutes) {
            const remaining = Math.ceil((intervalMinutes - elapsed) * 60)
            console.log(`配置 ${config.id} - 任务组刚结束，等待间隔时间（还需等待 ${remaining} 秒）`)
            continue
          } else {
            // 间隔时间已过，清除记录
            config.lastGroupFinishTime = null
            console.log(`配置 ${config.id} - 任务间隔时间已过，可以开始新的任务分配`)
          }
        }
      }
      
      // 检查是否正在请求中
      if (config.isFetching) {
        console.log(`配置 ${config.id} - 正在请求订单薄中，跳过`)
        continue
      }
      
      // 检查是否需要请求订单薄
      const now = Date.now()
      
      // 先检查是否有延迟请求时间（10分钟延迟）
      if (config.nextRequestTime && now < config.nextRequestTime) {
        const remaining = Math.ceil((config.nextRequestTime - now) / 1000)
        console.log(`配置 ${config.id} - 订单薄不满足条件，距离下次请求还有 ${remaining} 秒（${Math.ceil(remaining / 60)} 分钟）`)
        continue
      }
      
      // 清除延迟请求时间（如果已过期）
      if (config.nextRequestTime && now >= config.nextRequestTime) {
        config.nextRequestTime = null
      }
      
      // 根据上一轮任务数调整轮询间隔
      // 如果上一轮任务数大于阈值，使用配置的等待时间；否则使用配置的等待时间
      const maxWaitTime = Math.max(
        (hedgeMode.waitTimeLessThanThreshold || 300) * 1000,
        (hedgeMode.waitTimeGreaterThanThreshold || 60) * 1000
      )
      if (lastRoundEndTime.value && now - lastRoundEndTime.value < maxWaitTime) {
        // 上一轮刚结束，根据任务数设置等待时间
        const taskCountThreshold = hedgeMode.taskCountThreshold || 5
        const waitSeconds = lastRoundTaskCount.value > taskCountThreshold 
          ? (hedgeMode.waitTimeGreaterThanThreshold || 60)
          : (hedgeMode.waitTimeLessThanThreshold || 300)
        const waitTime = waitSeconds * 1000
        
        if (now - lastRoundEndTime.value < waitTime) {
          const remaining = Math.ceil((waitTime - (now - lastRoundEndTime.value)) / 1000)
          console.log(`配置 ${config.id} - 上一轮任务数 ${lastRoundTaskCount.value}，等待 ${waitSeconds} 秒后轮询（还需等待 ${remaining} 秒）`)
          continue
        }
      }
      
      // 检查常规请求间隔（20秒）
      const shouldFetch = !config.lastRequestTime || (now - config.lastRequestTime) >= 20000  // 20秒
      
      if (!shouldFetch) {
        const remaining = Math.ceil((20000 - (now - config.lastRequestTime)) / 1000)
        console.log(`配置 ${config.id} - 距离下次请求还有 ${remaining} 秒`)
        continue
      }
      
      // 检查yes持仓是否满足条件（才交易）
      const positionData = positionDataMap.value.get(config.trending?.trim())
      if (positionData) {
        const thresholdPosition = hedgeMode.yesPositionThreshold * 10000  // 转换为实际数量（万转数量）
        const yesPosition = positionData.yesPosition || 0
        const yesPositionWan = yesPosition / 10000  // 转换为万
        
        let shouldTrade = false
        if (hedgeMode.yesPositionCompareType === 'less') {
          shouldTrade = yesPosition < thresholdPosition
        } else {
          shouldTrade = yesPosition > thresholdPosition
        }
        
        if (!shouldTrade) {
          const compareText = hedgeMode.yesPositionCompareType === 'less' ? '小于' : '大于'
          const positionReason = `yes持仓${compareText}${hedgeMode.yesPositionThreshold}万时才交易 (YES: ${yesPositionWan.toFixed(2)}万, 要求: ${compareText} ${hedgeMode.yesPositionThreshold}万)`
          console.log(`配置 ${config.id} - ${positionReason}，跳过本次请求`)
          // 设置订单薄数据以显示原因
          config.orderbookData = {
            pollTime: Date.now(),
            updateTime: null,
            reason: positionReason,
            firstSide: null,
            price1: null,
            price2: null,
            depth1: null,
            depth2: null,
            diff: null
          }
          config.isFetching = false
          continue
        }
      } else {
        console.log(`配置 ${config.id} - 未获取到持仓数据，跳过本次请求`)
        config.isFetching = false
        continue
      }
      
      // 检查加权时间和yes持仓组合条件（不交易）- 适用于开仓和平仓模式
      // 如果加权时间满足条件 且 yes持仓满足条件，则不交易
      if (hedgeMode.weightedTimeHourOpen > 0 && hedgeMode.weightedTimeYesPositionThreshold > 0) {
        const weightedAvgTime = config.weightedAvgTime || 0
        const weightedTimeHour = weightedAvgTime / 3600000  // 转换为小时
        const thresholdTimeMs = hedgeMode.weightedTimeHourOpen * 3600000  // 小时转毫秒
        
        // 检查加权时间条件
        let weightedTimeMatch = false
        if (hedgeMode.weightedTimeCompareType === 'less') {
          weightedTimeMatch = weightedAvgTime < thresholdTimeMs
        } else {
          weightedTimeMatch = weightedAvgTime > thresholdTimeMs
        }
        
        // 检查yes持仓条件
        const positionData = positionDataMap.value.get(config.trending?.trim())
        let yesPositionMatch = false
        if (positionData) {
          const yesPosition = positionData.yesPosition || 0
          const yesPositionWan = yesPosition / 10000  // 转换为万
          const thresholdPosition = hedgeMode.weightedTimeYesPositionThreshold * 10000  // 转换为实际数量
          
          if (hedgeMode.weightedTimeYesPositionCompareType === 'less') {
            yesPositionMatch = yesPosition < thresholdPosition
          } else {
            yesPositionMatch = yesPosition > thresholdPosition
          }
        }
        
        // 如果两个条件都满足，则不交易
        if (weightedTimeMatch && yesPositionMatch) {
          const timeCompareText = hedgeMode.weightedTimeCompareType === 'less' ? '小于' : '大于'
          const positionCompareText = hedgeMode.weightedTimeYesPositionCompareType === 'less' ? '小于' : '大于'
          const yesPositionWan = positionData ? (positionData.yesPosition || 0) / 10000 : 0
          const weightedTimeReason = `加权时间${timeCompareText}${hedgeMode.weightedTimeHourOpen}小时且事件yes持仓${positionCompareText}${hedgeMode.weightedTimeYesPositionThreshold}万不交易 (加权时间: ${weightedTimeHour.toFixed(2)}h, yes持仓: ${yesPositionWan.toFixed(2)}万)`
          console.log(`配置 ${config.id} - ${weightedTimeReason}，跳过本次请求`)
          // 设置订单薄数据以显示原因
          config.orderbookData = {
            pollTime: Date.now(),
            updateTime: null,
            reason: weightedTimeReason,
            firstSide: null,
            price1: null,
            price2: null,
            depth1: null,
            depth2: null,
            diff: null
          }
          config.isFetching = false
          continue
        }
      }
      
      // 检查24小时交易量和7天平均交易量
      const volume24h = config.volume24h || 0
      const volume7dAvg = config.volume7dAvg || 0
      const maxVolume24h = hedgeMode.maxVolume24hOpen * 10000  // 转换为实际数量（万转数量）
      const maxVolume7dAvg = hedgeMode.maxVolume7dAvgOpen * 10000  // 转换为实际数量（万转数量）
      
      // 24h交易量大于XX万 或 7天平均交易量大于XX万 时不交易
      if (volume24h > maxVolume24h || volume7dAvg > maxVolume7dAvg) {
        const volumeReason = `交易量过大：24h量 ${(volume24h/10000).toFixed(2)}万 > ${hedgeMode.maxVolume24hOpen}万 或 7d均量 ${(volume7dAvg/10000).toFixed(2)}万 > ${hedgeMode.maxVolume7dAvgOpen}万`
        console.log(`配置 ${config.id} - ${volumeReason}，跳过本次请求`)
        // 设置订单薄数据以显示原因
        config.orderbookData = {
          pollTime: Date.now(),
          updateTime: null,
          reason: volumeReason,
          firstSide: null,
          price1: null,
          price2: null,
          depth1: null,
          depth2: null,
          diff: null
        }
        config.isFetching = false
        continue
      }
      
      // 开始请求订单薄
      config.isFetching = true
      config.lastRequestTime = now
      
      // 记录轮询时间（每次请求的时间）
      const pollTime = now
      config.pollTime = pollTime
      
      try {
        console.log(`配置 ${config.id} - 开始请求订单薄...`)
        
        let priceInfo = null
        let orderbookReason = null  // 不满足原因
        
        // 判断是否为平仓且模式1
        const currentMode = hedgeMode.isClose ? hedgeMode.hedgeMode : 1
        const isCloseMode1 = hedgeMode.isClose && currentMode === 1
        
        // 如果是平仓且模式1，先请求 calReadyToHedgeCanClose 接口
        if (isCloseMode1) {
          try {
            console.log(`配置 ${config.id} - 平仓模式1，先请求 calReadyToHedgeCanClose 接口...`)
            
            // 构建请求参数（与 calReadyToHedgeV4 一样，除了 currentPrice 不传）
            const canCloseRequestData = {
              trendingId: config.id,
              isClose: hedgeMode.isClose,
              // currentPrice 不传
              priceOutCome: 'YES',  // 先挂方，随便传一个值
              timePassMin: hedgeMode.timePassMin,
              minUAmt: hedgeMode.minUAmt,  // 最小开单
              maxUAmt: hedgeMode.maxUAmt,   // 最大开单
              minCloseAmt: hedgeMode.minCloseAmt,  // 平仓最小数量（参数1）
              maxOpenHour: hedgeMode.maxOpenHour,  // 可加仓时间（小时）
              closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
              numberType: parseInt(selectedNumberType.value)  // 账号类型：1-全部账户, 2-1000个账户, 3-1000个账户中未达标的
            }
            // 如果 maxIpDelay 有值，则添加到请求参数中
            if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
              canCloseRequestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
            }
            // 添加 needJudgeDF 和 maxDHour 字段
            canCloseRequestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
            canCloseRequestData.maxDHour = Number(hedgeMode.maxDHour) || 12
            // 添加 minCloseMin 字段
            canCloseRequestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
            // 添加资产优先级校验字段
            canCloseRequestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
            canCloseRequestData.balancePriority = hedgeMode.balancePriority
            
            const canCloseResponse = await axios.post(
              'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeCanClose',
              canCloseRequestData,
              {
                headers: {
                  'Content-Type': 'application/json'
                }
              }
            )
            
            // 处理返回结果，与 calReadyToHedgeV4 一样
            if (canCloseResponse.data && canCloseResponse.data.data) {
              const canCloseData = canCloseResponse.data.data
              if (canCloseData.yesNumber) {
                console.log(`配置 ${config.id} - calReadyToHedgeCanClose 返回 yesNumber，可以开，继续请求订单薄`)
              } else {
                console.log(`配置 ${config.id} - calReadyToHedgeCanClose 未返回 yesNumber，不能开，跳过本次请求`)
                // 不能开，跳过本次请求
                config.isFetching = false
                continue
              }
            } else if (canCloseResponse.data && canCloseResponse.data.msg) {
              // 服务器返回错误消息，添加到对冲信息中（与 calReadyToHedgeV4 一样）
              console.warn(`配置 ${config.id} - calReadyToHedgeCanClose 服务器返回错误:`, canCloseResponse.data.msg)
              
              // 初始化 currentHedges 数组（如果不存在）
              if (!config.currentHedges) {
                config.currentHedges = []
              }
              
              // 创建一个错误记录
              const errorRecord = {
                id: Date.now(),
                trendingId: config.id,
                trendingName: config.trending,
                startTime: new Date().toISOString(),
                endTime: new Date().toISOString(),
                finalStatus: 'failed',
                errorMsg: canCloseResponse.data.msg
              }
              config.currentHedges.push(errorRecord)
              
              // 跳过本次请求
              config.isFetching = false
              continue
            } else {
              console.log(`配置 ${config.id} - calReadyToHedgeCanClose 返回数据异常，跳过本次请求`)
              config.isFetching = false
              continue
            }
          } catch (canCloseError) {
            console.error(`配置 ${config.id} - 请求 calReadyToHedgeCanClose 失败:`, canCloseError)
            // 请求失败，提取错误消息并添加到对冲信息中
            let errorMessage = '请求 calReadyToHedgeCanClose 失败'
            if (canCloseError.response?.data?.msg) {
              errorMessage = canCloseError.response.data.msg
            } else if (canCloseError.message) {
              errorMessage = canCloseError.message
            }
            
            // 初始化 currentHedges 数组（如果不存在）
            if (!config.currentHedges) {
              config.currentHedges = []
            }
            
            // 创建一个错误记录
            const errorRecord = {
              id: Date.now(),
              trendingId: config.id,
              trendingName: config.trending,
              startTime: new Date().toISOString(),
              endTime: new Date().toISOString(),
              finalStatus: 'failed',
              errorMsg: errorMessage
            }
            config.currentHedges.push(errorRecord)
            
            // 跳过本次请求
            config.isFetching = false
            continue
          }
        }
        
        try {
          // 尝试解析订单薄数据（包含完整检查）
          // 如果是平仓且模式1，需要重试5次
          let orderbookSuccess = false
          let lastOrderbookError = null
          
          if (isCloseMode1) {
            // 平仓模式1：重试5次（只对接口请求失败进行重试，不对数据处理失败重试）
            for (let retryCount = 0; retryCount < 5; retryCount++) {
              try {
                priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
                if (priceInfo) {
                  orderbookSuccess = true
                  break
                }
              } catch (orderbookError) {
                lastOrderbookError = orderbookError
                const errorMsg = orderbookError.message || ''
                
                // 判断是否为接口请求失败（需要重试）
                // 如果是数据处理失败（深度不足、价差过大等），不需要重试
                const isInterfaceError = errorMsg.includes('订单薄接口错误') || 
                                         errorMsg.includes('errno') ||
                                         errorMsg.includes('网络') ||
                                         errorMsg.includes('timeout') ||
                                         errorMsg.includes('ECONNREFUSED') ||
                                         errorMsg.includes('ENOTFOUND')
                
                if (isInterfaceError) {
                  // 接口请求失败，需要重试
                  console.warn(`配置 ${config.id} - 请求订单薄接口失败 (第 ${retryCount + 1}/5 次):`, errorMsg)
                  if (retryCount < 4) {
                    // 等待一小段时间后重试
                    await new Promise(resolve => setTimeout(resolve, 500))
                  }
                } else {
                  // 数据处理失败（深度不足、价差过大等），不需要重试，直接抛出错误
                  console.warn(`配置 ${config.id} - 订单薄数据处理失败（不重试）:`, errorMsg)
                  throw orderbookError
                }
              }
            }
            
            if (!orderbookSuccess) {
              throw lastOrderbookError || new Error('请求订单薄失败（重试5次后仍失败）')
            }
          } else {
            // 非平仓模式1：使用原来的逻辑
            priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
          }
          
          if (!priceInfo) {
            throw new Error('解析订单薄数据失败')
          }
          
          // 检查是否满足对冲条件
          const meetsCondition = checkOrderbookHedgeCondition(priceInfo, config)
          
          if (!meetsCondition) {
            // 不满足条件，获取不满足的原因
            const maxDepth = getMaxDepth(config)
            if (priceInfo.diff <= 0.15) {
              if (!hedgeMode.isClose) {
                // 开仓模式：检查买一价值（买一价 × 买一深度 / 100）
                const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
                if (bidValue >= maxDepth) {
                  orderbookReason = `先挂方买一价值 ${bidValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
                } else {
                  orderbookReason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
                }
              } else {
                // 平仓模式：检查卖一价值（卖一价 × 卖一深度 / 100）
                const askValue = priceInfo.price2 * priceInfo.depth2 / 100
                if (askValue >= maxDepth) {
                  orderbookReason = `先挂方卖一价值 ${askValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
                } else {
                  orderbookReason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
                }
              }
            } else {
              orderbookReason = '不符合对冲条件'
            }
          }
          
          // 记录更新时间（成功获取订单薄的时间）
          priceInfo.updateTime = Date.now()
          priceInfo.pollTime = pollTime
          priceInfo.reason = orderbookReason
          
        } catch (error) {
          // 如果是深度区间开关未开启的错误，直接抛出，不回退到基本数据
          if (error.message && error.message.includes('深度区间开关未开启')) {
            console.error(`配置 ${config.id} - 深度区间开关未开启，直接失败:`, error.message)
            throw error
          }
          
          // parseOrderbookData失败，尝试获取基本订单薄数据
          console.warn(`配置 ${config.id} - 完整订单薄检查失败，尝试获取基本数据:`, error.message)
          
          try {
            const basicInfo = await fetchOrderbookBasic(config, hedgeMode.isClose)
            
            if (basicInfo) {
              // 使用基本数据
              priceInfo = {
                ...basicInfo,
                updateTime: Date.now(),  // 记录更新时间
                pollTime: pollTime,      // 记录轮询时间
                reason: error.message || '订单薄数据不满足条件'  // 记录不满足原因
              }
              orderbookReason = priceInfo.reason
            } else {
              throw new Error('获取基本订单薄数据失败')
            }
          } catch (basicError) {
            // 基本数据也获取失败
            console.error(`配置 ${config.id} - 获取基本订单薄数据也失败:`, basicError)
            throw error  // 抛出原始错误
          }
        }
        
        // 保存订单薄数据（无论是否满足条件都保存）
        config.orderbookData = priceInfo
        config.retryCount = 0  // 重置重试次数
        
        // 如果订单薄成功获取到了数据，且不满足条件，设置下次请求时间为配置的间隔时间后
        if (priceInfo && priceInfo.updateTime && orderbookReason) {
          // 成功获取但不满足条件，设置配置的间隔时间后才能再次请求
          const intervalMinutes = hedgeMode.orderbookMismatchInterval || 10
          config.nextRequestTime = now + intervalMinutes * 60 * 1000
          console.log(`配置 ${config.id} - 订单薄获取成功但不满足条件，下次请求将在 ${intervalMinutes} 分钟后`)
        } else {
          // 获取失败或满足条件，清除延迟请求时间，使用原来的20秒逻辑
          config.nextRequestTime = null
        }
        
        console.log(`配置 ${config.id} - 订单薄数据:`, {
          先挂方: priceInfo.firstSide,
          先挂价格: priceInfo.price1,
          后挂价格: priceInfo.price2,
          价差: priceInfo.diff,
          不满足原因: orderbookReason
        })
        
        // 只有在可以开始新对冲时才判断是否执行对冲
        if (canStartNewHedge && !orderbookReason) {
          // 检查是否满足对冲条件
          if (checkOrderbookHedgeCondition(priceInfo, config)) {
            console.log(`配置 ${config.id} - 满足对冲条件，开始执行对冲`)
            
            // 清空无法对冲时间和标记
            config.noHedgeSince = null
            
            // 执行对冲，并统计任务数
            const taskCount = await executeHedgeFromOrderbook(config, priceInfo)
            roundTaskCount += taskCount || 0
            
            // 记录对冲时间
            config.lastHedgeTime = Date.now()
          } else {
            console.log(`配置 ${config.id} - 不满足对冲条件`)
            
            // 记录开始无法对冲的时间
            if (!config.noHedgeSince) {
              config.noHedgeSince = Date.now()
            } else {
              // 检查是否超过5分钟都无法对冲
              const noHedgeElapsed = (Date.now() - config.noHedgeSince) / 1000 / 60
              if (noHedgeElapsed >= 5) {
                config.errorMessage = `已连续 ${Math.floor(noHedgeElapsed)} 分钟无法对冲`
                console.warn(`配置 ${config.id} - ${config.errorMessage}`)
              }
            }
            
          }
        }
        
      } catch (error) {
        console.error(`配置 ${config.id} - 请求订单薄失败:`, error)
        config.retryCount++
        
        // 获取失败，清除延迟请求时间，使用原来的逻辑
        config.nextRequestTime = null
        
        // 提取错误消息
        let errorMessage = '获取深度失败'
        if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error.message) {
          errorMessage = error.message
        }
        
        // 即使请求失败，也保存轮询时间和错误信息
        config.orderbookData = {
          pollTime: pollTime,
          updateTime: null,  // 请求失败，没有更新时间
          reason: errorMessage,
          firstSide: null,
          price1: null,
          price2: null,
          depth1: null,
          depth2: null,
          diff: null
        }
        
        // 随机1-3秒后重试
        const retryDelay = Math.floor(Math.random() * 2000) + 1000  // 1000-3000ms
        console.log(`配置 ${config.id} - 将在 ${retryDelay}ms 后重试（第 ${config.retryCount} 次）`)
        
        setTimeout(() => {
          config.isFetching = false
          config.lastRequestTime = Date.now() - 20000  // 立即允许重试
        }, retryDelay)
        
        continue
      } finally {
        config.isFetching = false
      }
      
    } catch (error) {
      console.error(`配置 ${config.id} - 处理失败:`, error)
    }
  }
}

/**
 * 请求订单薄数据
 */
const fetchOrderbook = async (tokenId) => {
  try {
    const response = await axios.get(ORDERBOOK_API_URL, {
      params: {
        token_id: tokenId
      },
      headers: {
        'apikey': ORDERBOOK_API_KEY
      }
    })
    
    // 检查是否是 API rate limit exceeded 错误
    const errorMsg = response.data?.errmsg || response.data?.msg || response.data?.message || ''
    if (errorMsg === 'API rate limit exceeded') {
      const rateLimitError = new Error('API rate limit exceeded')
      rateLimitError.isRateLimit = true
      throw rateLimitError
    }
    
    // errno = 0 表示请求成功，即使 result 为空也应该返回
    if (response.data && response.data.errno === 0) {
      return response.data.result || {}
    }
    
    // errno !== 0 表示接口返回错误，需要重试
    const finalErrorMsg = errorMsg || '订单薄接口返回错误'
    throw new Error(`订单薄接口错误: ${finalErrorMsg} (errno: ${response.data?.errno})`)
  } catch (error) {
    // 如果是 axios 错误（网络错误等），需要重试
    if (error.response) {
      // HTTP 错误响应
      const errorMsg = error.response.data?.errmsg || error.response.data?.msg || error.response.data?.message || ''
      
      // 检查是否是 API rate limit exceeded 错误
      if (errorMsg === 'API rate limit exceeded') {
        const rateLimitError = new Error('API rate limit exceeded')
        rateLimitError.isRateLimit = true
        throw rateLimitError
      }
      
      const errno = error.response.data?.errno
      if (errno !== undefined && errno !== 0) {
        // 接口返回 errno !== 0，需要重试
        const finalErrorMsg = errorMsg || '订单薄接口返回错误'
        throw new Error(`订单薄接口错误: ${finalErrorMsg} (errno: ${errno})`)
      }
    }
    
    // 如果已经是 rate limit 错误，直接抛出
    if (error.isRateLimit) {
      throw error
    }
    
    console.error('获取订单薄失败:', error)
    throw error
  }
}

/**
 * 获取订单薄基本数据（不进行条件检查，用于显示）
 */
const fetchOrderbookBasic = async (config, isClose) => {
  try {
    // 获取yes和no的订单薄数据
    const [yesOrderbook, noOrderbook] = await Promise.all([
      fetchOrderbook(config.trendingPart1),
      fetchOrderbook(config.trendingPart2)
    ])
    
    // 获取YES的买一价和卖一价
    const yesBids = yesOrderbook.bids || []
    const yesAsks = yesOrderbook.asks || []
    const noBids = noOrderbook.bids || []
    const noAsks = noOrderbook.asks || []
    
    // 基本数据检查
    if (yesBids.length === 0 || yesAsks.length === 0 || 
        noBids.length === 0 || noAsks.length === 0) {
      return null
    }
    
    // 对 bids 和 asks 进行排序（确保顺序正确）
    yesBids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
    noBids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
    yesAsks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
    noAsks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
    
    // 获取YES方的买一和卖一
    const yesBid = yesBids[0]
    const yesAsk = yesAsks[0]
    
    // 获取NO方的买一和卖一  
    const noBid = noBids[0]
    const noAsk = noAsks[0]
    
    // 转换为百分比格式（API返回的是小数，需要乘以100）
    const yesBidPrice = parseFloat(yesBid.price) * 100
    const yesAskPrice = parseFloat(yesAsk.price) * 100
    const noBidPrice = parseFloat(noBid.price) * 100
    const noAskPrice = parseFloat(noAsk.price) * 100
    
    const yesBidDepth = parseFloat(yesBid.size)
    const yesAskDepth = parseFloat(yesAsk.size)
    const noBidDepth = parseFloat(noBid.size)
    const noAskDepth = parseFloat(noAsk.size)
    
    // 确定先挂方：根据开仓/平仓判断
    let firstSide, price1, price2, depth1, depth2
    
    if (isClose) {
      // 平仓：买一价更高的为先挂方
      firstSide = yesBidPrice > noBidPrice ? 'YES' : 'NO'
    } else {
      // 开仓：卖一价更高的为先挂方
      firstSide = yesAskPrice > noAskPrice ? 'YES' : 'NO'
    }
    
    // 获取先挂方的买一价和卖一价
    if (firstSide === 'YES') {
      price1 = yesBidPrice  // 先挂方的买一价
      price2 = yesAskPrice  // 先挂方的卖一价
      depth1 = yesBidDepth  // 先挂方的买一深度
      depth2 = yesAskDepth  // 先挂方的卖一深度
    } else {
      price1 = noBidPrice   // 先挂方的买一价
      price2 = noAskPrice   // 先挂方的卖一价
      depth1 = noBidDepth   // 先挂方的买一深度
      depth2 = noAskDepth   // 先挂方的卖一深度
    }
    
    return {
      firstSide,
      price1,           // 先挂方的买一价
      price2,           // 先挂方的卖一价
      depth1,           // 先挂方的买一深度
      depth2,           // 先挂方的卖一深度
      diff: Math.abs(price1 - price2),  // 先挂方买卖价差
      yesBidsCount: yesBids.length,     // YES方的买单组数
      yesAsksCount: yesAsks.length,     // YES方的卖单组数
      noBidsCount: noBids.length,        // NO方的买单组数
      noAsksCount: noAsks.length         // NO方的卖单组数
    }
  } catch (error) {
    console.error('获取订单薄基本数据失败:', error)
    return null
  }
}

/**
 * 解析订单薄数据，判断先挂方和价格
 */
/**
 * 请求 calLimitOrder API 获取挂单数据
 */
const fetchCalLimitOrder = async (trendingId) => {
  try {
    const response = await axios.post('https://sg.bicoin.com.cn/99l/hedge/calLimitOrder', {
      trendingId: trendingId
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data && response.data.code === 0 && response.data.data) {
      return response.data.data
    }
    
    throw new Error(response.data?.msg || '获取挂单数据失败')
  } catch (error) {
    console.error('请求 calLimitOrder 失败:', error)
    throw error
  }
}

/**
 * 转换挂单数据（开仓模式：将卖出转换为买入）
 * 卖出Yes价格为x，数量为y → 买入No价格为1-x，数量为y
 * 卖出No价格为x，数量为y → 买入Yes价格为1-x，数量为y
 */
const convertLimitOrdersForOpen = (limitOrderData) => {
  const convertedBids = {
    yes: [],
    no: []
  }
  
  // 转换 yesSellLimitOrder: 卖出Yes → 买入No
  if (limitOrderData.yesSellLimitOrder && Array.isArray(limitOrderData.yesSellLimitOrder)) {
    limitOrderData.yesSellLimitOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedBids.no.push({
          price: (1 - price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  // 转换 noSellOrder: 卖出No → 买入Yes
  if (limitOrderData.noSellOrder && Array.isArray(limitOrderData.noSellOrder)) {
    limitOrderData.noSellOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedBids.yes.push({
          price: (1 - price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  // 合并原有的买入挂单
  if (limitOrderData.yesBuyLimitOrder && Array.isArray(limitOrderData.yesBuyLimitOrder)) {
    limitOrderData.yesBuyLimitOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedBids.yes.push({
          price: (price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  if (limitOrderData.noBuyOrder && Array.isArray(limitOrderData.noBuyOrder)) {
    limitOrderData.noBuyOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedBids.no.push({
          price: (price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  return convertedBids
}

/**
 * 转换挂单数据（平仓模式：将买入转换为卖出）
 * 买入Yes价格为x，数量为y → 卖出No价格为1-x，数量为y
 * 买入No价格为x，数量为y → 卖出Yes价格为1-x，数量为y
 */
const convertLimitOrdersForClose = (limitOrderData) => {
  const convertedAsks = {
    yes: [],
    no: []
  }
  
  // 转换 yesBuyLimitOrder: 买入Yes → 卖出No
  if (limitOrderData.yesBuyLimitOrder && Array.isArray(limitOrderData.yesBuyLimitOrder)) {
    limitOrderData.yesBuyLimitOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedAsks.no.push({
          price: (1 - price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  // 转换 noBuyOrder: 买入No → 卖出Yes
  if (limitOrderData.noBuyOrder && Array.isArray(limitOrderData.noBuyOrder)) {
    limitOrderData.noBuyOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedAsks.yes.push({
          price: (1 - price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  // 合并原有的卖出挂单
  if (limitOrderData.yesSellLimitOrder && Array.isArray(limitOrderData.yesSellLimitOrder)) {
    limitOrderData.yesSellLimitOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedAsks.yes.push({
          price: (price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  if (limitOrderData.noSellOrder && Array.isArray(limitOrderData.noSellOrder)) {
    limitOrderData.noSellOrder.forEach(order => {
      const price = parseFloat(order.price)
      const restAmt = parseFloat(order.restAmt)
      if (price > 0 && restAmt > 0) {
        convertedAsks.no.push({
          price: (price / 100).toFixed(4), // 转换为小数格式
          size: restAmt
        })
      }
    })
  }
  
  return convertedAsks
}

/**
 * 从订单薄中减去挂单数量
 * @param {Array} orderbook - 订单薄数组（bids 或 asks）
 * @param {Array} limitOrders - 需要减去的挂单数组
 * @returns {Array} - 处理后的订单薄数组
 */
const subtractLimitOrdersFromOrderbook = (orderbook, limitOrders) => {
  if (!limitOrders || limitOrders.length === 0) {
    return orderbook
  }
  
  // 创建价格到数量的映射（使用更精确的价格匹配，允许小的浮点误差）
  const limitOrderMap = new Map()
  limitOrders.forEach(order => {
    const price = parseFloat(order.price)
    const size = parseFloat(order.size)
    // 使用价格作为key，允许浮点数匹配
    const priceKey = price.toFixed(6) // 使用更高精度进行匹配
    if (limitOrderMap.has(priceKey)) {
      limitOrderMap.set(priceKey, limitOrderMap.get(priceKey) + size)
    } else {
      limitOrderMap.set(priceKey, size)
    }
  })
  
  // 从订单薄中减去对应价格的数量
  const result = orderbook.map(item => {
    const itemPrice = parseFloat(item.price)
    const priceKey = itemPrice.toFixed(6) // 使用相同精度进行匹配
    const originalSize = parseFloat(item.size)
    const subtractSize = limitOrderMap.get(priceKey) || 0
    const newSize = originalSize - subtractSize
    
    return {
      ...item,
      size: newSize > 0 ? newSize : 0
    }
  }).filter(item => {
    // 过滤掉数量小于等于0的订单
    return parseFloat(item.size) > 0
  })
  
  return result
}

/**
 * 解析订单薄数据，获取先挂方的买一价和卖一价
 * 类似 parseType3Message 的处理方式，直接返回先挂方的数据
 * 增加深度和价差判断
 * 新增：从订单薄中减去 calLimitOrder 返回的挂单数量
 */
const parseOrderbookData = async (config, isClose) => {
  try {
    // 获取yes和no的订单薄数据
    let yesOrderbook, noOrderbook
    try {
      yesOrderbook = await fetchOrderbook(config.trendingPart1)
    } catch (error) {
      // 如果是 rate limit 错误，直接抛出
      if (error.isRateLimit) {
        throw error
      }
      throw error
    }
    
    try {
      noOrderbook = await fetchOrderbook(config.trendingPart2)
    } catch (error) {
      // 如果是 rate limit 错误，直接抛出
      if (error.isRateLimit) {
        throw error
      }
      throw error
    }
    
    // 获取YES的买一价和卖一价
    let yesBids = yesOrderbook.bids || []
    let yesAsks = yesOrderbook.asks || []
    let noBids = noOrderbook.bids || []
    let noAsks = noOrderbook.asks || []
    
    // 保存原始订单薄数据（不剔除挂单），用于深度差计算
    const yesBidsRaw = JSON.parse(JSON.stringify(yesBids))
    const yesAsksRaw = JSON.parse(JSON.stringify(yesAsks))
    const noBidsRaw = JSON.parse(JSON.stringify(noBids))
    const noAsksRaw = JSON.parse(JSON.stringify(noAsks))
    
    // // 请求 calLimitOrder API 获取挂单数据
    // try {
    //   const limitOrderData = await fetchCalLimitOrder(config.id)
    //   console.log(`配置 ${config.id} - 获取到挂单数据:`, limitOrderData)
      
    //   if (isClose) {
    //     // 平仓模式：将买入转换为卖出，汇合卖出挂单
    //     const convertedAsks = convertLimitOrdersForClose(limitOrderData)
        
    //     // 从订单薄中减去对应的卖出挂单
    //     if (convertedAsks.yes.length > 0) {
    //       yesAsks = subtractLimitOrdersFromOrderbook(yesAsks, convertedAsks.yes)
    //       console.log(`配置 ${config.id} - 从YES卖单中减去 ${convertedAsks.yes.length} 个挂单`)
    //     }
    //     if (convertedAsks.no.length > 0) {
    //       noAsks = subtractLimitOrdersFromOrderbook(noAsks, convertedAsks.no)
    //       console.log(`配置 ${config.id} - 从NO卖单中减去 ${convertedAsks.no.length} 个挂单`)
    //     }
    //   } else {
    //     // 开仓模式：将卖出转换为买入，汇合买入挂单
    //     const convertedBids = convertLimitOrdersForOpen(limitOrderData)
        
    //     // 从订单薄中减去对应的买入挂单
    //     if (convertedBids.yes.length > 0) {
    //       yesBids = subtractLimitOrdersFromOrderbook(yesBids, convertedBids.yes)
    //       console.log(`配置 ${config.id} - 从YES买单中减去 ${convertedBids.yes.length} 个挂单`)
    //     }
    //     if (convertedBids.no.length > 0) {
    //       noBids = subtractLimitOrdersFromOrderbook(noBids, convertedBids.no)
    //       console.log(`配置 ${config.id} - 从NO买单中减去 ${convertedBids.no.length} 个挂单`)
    //     }
    //   }
    // } catch (error) {
    //   console.warn(`配置 ${config.id} - 获取挂单数据失败，继续使用原始订单薄:`, error.message)
    //   // 如果获取挂单数据失败，继续使用原始订单薄数据
    // }
    
    // 基本数据检查
    if (yesBids.length === 0 || yesAsks.length === 0 || 
        noBids.length === 0 || noAsks.length === 0) {
      throw new Error('订单薄数据不足')
    }
    
    // 检查数据数量：asks和bids每个都至少要有指定组数据
    const minDepth = hedgeMode.minOrderbookDepth
    if (yesBids.length < minDepth || yesAsks.length < minDepth || 
        noBids.length < minDepth || noAsks.length < minDepth) {
      throw new Error(`订单薄数据不足${minDepth}组`)
    }
    
    // 对 bids 和 asks 进行排序（确保顺序正确）
    // bids 按价格从高到低排序
    yesBids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
    noBids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
    // asks 按价格从低到高排序
    yesAsks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
    noAsks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
    
    // 获取YES方的买一和卖一
    const yesBid = yesBids[0]
    const yesAsk = yesAsks[0]
    
    // 获取NO方的买一和卖一  
    const noBid = noBids[0]
    const noAsk = noAsks[0]
    
    // 转换为百分比格式（API返回的是小数，需要乘以100）
    const yesBidPrice = parseFloat(yesBid.price) * 100
    const yesAskPrice = parseFloat(yesAsk.price) * 100
    const noBidPrice = parseFloat(noBid.price) * 100
    const noAskPrice = parseFloat(noAsk.price) * 100
    
    const yesBidDepth = parseFloat(yesBid.size)
    const yesAskDepth = parseFloat(yesAsk.size)
    const noBidDepth = parseFloat(noBid.size)
    const noAskDepth = parseFloat(noAsk.size)
    
    // 确定先挂方：根据开仓/平仓判断
    let firstSide, price1, price2, depth1, depth2
    let firstBids, firstAsks
    
    if (isClose) {
      // 平仓：买一价更高的为先挂方
      firstSide = yesBidPrice > noBidPrice ? 'YES' : 'NO'
      firstBids = firstSide === 'YES' ? yesBids : noBids
      firstAsks = firstSide === 'YES' ? yesAsks : noAsks
    } else {
      // 开仓：卖一价更高的为先挂方
      firstSide = yesAskPrice > noAskPrice ? 'YES' : 'NO'
      firstBids = firstSide === 'YES' ? yesBids : noBids
      firstAsks = firstSide === 'YES' ? yesAsks : noAsks
    }
    
    // 获取先挂方的买一价和卖一价
    if (firstSide === 'YES') {
      price1 = yesBidPrice  // 先挂方的买一价
      price2 = yesAskPrice  // 先挂方的卖一价
      depth1 = yesBidDepth  // 先挂方的买一深度
      depth2 = yesAskDepth  // 先挂方的卖一深度
    } else {
      price1 = noBidPrice   // 先挂方的买一价
      price2 = noAskPrice   // 先挂方的卖一价
      depth1 = noBidDepth   // 先挂方的买一深度
      depth2 = noAskDepth   // 先挂方的卖一深度
    }
    
    // === 新增判断：深度检查 ===
    // 累加 bids 价格最高的N组数据的 size
    const depthCount = hedgeMode.minOrderbookDepth
    const topNBidsDepth = firstBids.slice(0, depthCount).reduce((sum, bid) => sum + parseFloat(bid.size), 0)
    // 累加 asks 价格最低的N组数据的 size
    const topNAsksDepth = firstAsks.slice(0, depthCount).reduce((sum, ask) => sum + parseFloat(ask.size), 0)
    
    console.log(`先挂方 ${firstSide} - 买1-${depthCount}深度累计: ${topNBidsDepth.toFixed(2)}, 卖1-${depthCount}深度累计: ${topNAsksDepth.toFixed(2)}`)
    
    const minTotalDepth = hedgeMode.minTotalDepth
    if (topNBidsDepth < minTotalDepth || topNAsksDepth < minTotalDepth) {
      throw new Error(`深度不足：买1-${depthCount}累计=${topNBidsDepth.toFixed(2)}, 卖1-${depthCount}累计=${topNAsksDepth.toFixed(2)}, 要求>=${minTotalDepth}`)
    }
    
    // === 新增判断：价差检查 ===
    const maxPriceDiff = hedgeMode.maxPriceDiff
    const depthIndex = hedgeMode.minOrderbookDepth - 1  // 转为索引（0-based）
    
    if (isClose) {
      // 平仓：检查先挂方 bids 中买1和买N的价差
      const bid1Price = parseFloat(firstBids[0].price) * 100
      const bidNPrice = parseFloat(firstBids[depthIndex].price) * 100
      const bidsPriceDiff = bid1Price - bidNPrice
      
      console.log(`平仓模式 - 先挂方买1价格: ${bid1Price.toFixed(2)}, 买${hedgeMode.minOrderbookDepth}价格: ${bidNPrice.toFixed(2)}, 差值: ${bidsPriceDiff.toFixed(2)}`)
      
      if (bidsPriceDiff >= maxPriceDiff) {
        throw new Error(`买1-买${hedgeMode.minOrderbookDepth}价差过大: ${bidsPriceDiff.toFixed(2)} >= ${maxPriceDiff}`)
      }
    } else {
      // 开仓：检查先挂方 asks 中卖1和卖N的价差
      const ask1Price = parseFloat(firstAsks[0].price) * 100
      const askNPrice = parseFloat(firstAsks[depthIndex].price) * 100
      const asksPriceDiff = askNPrice - ask1Price
      
      console.log(`开仓模式 - 先挂方卖1价格: ${ask1Price.toFixed(2)}, 卖${hedgeMode.minOrderbookDepth}价格: ${askNPrice.toFixed(2)}, 差值: ${asksPriceDiff.toFixed(2)}`)
      
      if (asksPriceDiff >= maxPriceDiff) {
        throw new Error(`卖1-卖${hedgeMode.minOrderbookDepth}价差过大: ${asksPriceDiff.toFixed(2)} >= ${maxPriceDiff}`)
      }
    }
    
    // === 新增判断：先挂方价格区间检查 ===
    const priceMin = hedgeMode.priceRangeMin
    const priceMax = hedgeMode.priceRangeMax
    const avgPrice = (price1 + price2) / 2  // 买一价和卖一价的平均值
    
    // 平仓和开仓模式都需要检查平均价格是否在区间内（大于最小值且小于最大值）
    if (isClose) {
      // 平仓模式：检查平均价格是否在区间内
      console.log(`平仓模式 - 平均价格: ${avgPrice.toFixed(2)}, 价格区间要求: ${priceMin}-${priceMax}`)
    } else {
      // 开仓模式：检查平均价格是否在区间内
      console.log(`开仓模式 - 平均价格: ${avgPrice.toFixed(2)}, 价格区间要求: ${priceMin}-${priceMax}`)
    }
    
    // 统一检查：平均价格必须在区间内
    if (avgPrice <= priceMin) {
      const mode = isClose ? '平仓' : '开仓'
      throw new Error(`${mode}模式，平均价格 ${avgPrice.toFixed(2)} 不大于最小价格 ${priceMin}`)
    }
    
    if (avgPrice >= priceMax) {
      const mode = isClose ? '平仓' : '开仓'
      throw new Error(`${mode}模式，平均价格 ${avgPrice.toFixed(2)} 不小于最大价格 ${priceMax}`)
    }
    
    // === 深度差计算和价格计算逻辑 ===
    // 计算深度差（卖一减去买一的绝对值）
    const depthDiff = Math.abs(price2 - price1)
    console.log(`深度差: ${depthDiff.toFixed(2)}`)
    
    // 获取原始数据的买一和卖一价格（不剔除挂单）
    const firstBidsRaw = firstSide === 'YES' ? yesBidsRaw : noBidsRaw
    const firstAsksRaw = firstSide === 'YES' ? yesAsksRaw : noAsksRaw
    
    // 对原始数据进行排序
    firstBidsRaw.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
    firstAsksRaw.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
    
    const rawBid1 = parseFloat(firstBidsRaw[0].price) * 100
    const rawAsk1 = parseFloat(firstAsksRaw[0].price) * 100
    const rawBid1Depth = parseFloat(firstBidsRaw[0].size)
    const rawAsk1Depth = parseFloat(firstAsksRaw[0].size)
    
    // 根据深度差范围计算价格和 tp2
    let finalPrice = null
    let tp2 = null
    let firstShareReduction = 0  // 深度差0.1时，先挂方数量需要减少的量
    
    // 获取配置的深度差阈值
    const threshold1 = hedgeMode.depthThreshold1  // 默认15
    const threshold2 = hedgeMode.depthThreshold2  // 默认2
    const threshold3 = hedgeMode.depthThreshold3  // 默认0.2
    
    // 辅助函数：从范围字符串中获取随机值（秒）
    const getRandomFromRange = (rangeStr) => {
      const [min, max] = rangeStr.split(',').map(v => parseFloat(v.trim()))
      return Math.random() * (max - min) + min
    }
    
    // 辅助函数：计算价格调整值（根据配置的最小值和最大值）
    // 先在minPercent到maxPercent之间随机选一个百分比，再乘以深度差，最后确保结果至少为0.1
    const calculatePriceAdjustment = (diff, minPercent, maxPercent) => {
      // 在minPercent到maxPercent之间随机选一个百分比
      const randomPercent = Math.random() * (maxPercent - minPercent) + minPercent
      // 深度差乘以随机百分比
      const adjustment = diff * (randomPercent / 100)
      // 确保结果至少为0.1
      return Math.max(0.1, adjustment)
    }
    
    if (depthDiff > threshold1) {
      // 深度差 > 阈值1：检查开关是否打开
      if (!hedgeMode.enableDepthDiffParamsGt15) {
        throw new Error(`深度差>${threshold1}时，该深度区间开关未开启，订单薄不符合条件（当前深度差: ${depthDiff.toFixed(2)}）`)
      }
      // 使用原始数据计算价格，使用该区间的价格波动配置
      const minVolatility = hedgeMode.priceVolatilityGt15Min
      const maxVolatility = hedgeMode.priceVolatilityGt15Max
      
      if (isClose) {
        // 平仓：原始数据的卖一价 - 深度差的配置范围内取随机值
        const adjustment = calculatePriceAdjustment(depthDiff, minVolatility, maxVolatility)
        finalPrice = rawAsk1 - adjustment
        
        // 深度差>阈值1时，平仓模式：最终价格需要小于 最大区间+3
        if (finalPrice >= priceMax + 3) {
          throw new Error(`深度差>${threshold1}时，平仓模式最终价格 ${finalPrice.toFixed(2)} 不小于最大区间+3 (${priceMax + 3})`)
        }
        console.log(`深度差 > ${threshold1} - 平仓模式，最终价格: ${finalPrice.toFixed(2)}, 最大区间+3: ${priceMax + 3}`)
      } else {
        // 开仓：原始数据的买一价 + 深度差的配置范围内取随机值
        const adjustment = calculatePriceAdjustment(depthDiff, minVolatility, maxVolatility)
        finalPrice = rawBid1 + adjustment
        
        // 深度差>阈值1时，开仓模式：最终价格需要大于 最小区间-5
        if (finalPrice <= priceMin - 5) {
          throw new Error(`深度差>${threshold1}时，开仓模式最终价格 ${finalPrice.toFixed(2)} 不大于最小区间-5 (${priceMin - 5})`)
        }
        console.log(`深度差 > ${threshold1} - 开仓模式，最终价格: ${finalPrice.toFixed(2)}, 最小区间-5: ${priceMin - 5}`)
      }
      
      // tp2 为深度差阈值1以上挂单后延时检测时间的随机值（秒）
      const delayRange = hedgeMode.delayTimeGt15
      tp2 = getRandomFromRange(delayRange)
      
      console.log(`深度差 > ${threshold1} - 计算价格: ${finalPrice.toFixed(2)}, tp2: ${tp2.toFixed(2)}秒`)
      
    } else if (depthDiff >= threshold2) {
      // 深度差 阈值2-阈值1：检查开关是否打开
      if (!hedgeMode.enableDepthDiffParams2To15) {
        throw new Error(`深度差在${threshold2}-${threshold1}区间时，该深度区间开关未开启，订单薄不符合条件（当前深度差: ${depthDiff.toFixed(2)}）`)
      }
      const minVolatility = hedgeMode.priceVolatility2To15Min
      const maxVolatility = hedgeMode.priceVolatility2To15Max
      
      if (isClose) {
        // 平仓：原始数据的卖一价 - 深度差的配置范围内取随机值
        const adjustment = calculatePriceAdjustment(depthDiff, minVolatility, maxVolatility)
        finalPrice = rawAsk1 - adjustment
      } else {
        // 开仓：原始数据的买一价 + 深度差的配置范围内取随机值
        const adjustment = calculatePriceAdjustment(depthDiff, minVolatility, maxVolatility)
        finalPrice = rawBid1 + adjustment
      }
      
      // tp2 为深度差阈值2-阈值1挂单后延时检测时间的随机值（秒）
      const delayRange = hedgeMode.delayTime2To15
      tp2 = getRandomFromRange(delayRange)
      
      console.log(`深度差 ${threshold2}-${threshold1} - 计算价格: ${finalPrice.toFixed(2)}, tp2: ${tp2.toFixed(2)}秒`)
      
    } else if (depthDiff >= threshold3) {
      // 深度差 阈值3-阈值2：检查开关是否打开
      if (!hedgeMode.enableDepthDiffParams02To2) {
        throw new Error(`深度差在${threshold3}-${threshold2}区间时，该深度区间开关未开启，订单薄不符合条件（当前深度差: ${depthDiff.toFixed(2)}）`)
      }
      const minVolatility = hedgeMode.priceVolatility02To2Min
      const maxVolatility = hedgeMode.priceVolatility02To2Max
      
      if (isClose) {
        // 平仓：原始数据的卖一价 - 深度差的配置范围内取随机值
        const adjustment = calculatePriceAdjustment(depthDiff, minVolatility, maxVolatility)
        finalPrice = rawAsk1 - adjustment
      } else {
        // 开仓：原始数据的买一价 + 深度差的配置范围内取随机值
        const adjustment = calculatePriceAdjustment(depthDiff, minVolatility, maxVolatility)
        finalPrice = rawBid1 + adjustment
      }
      
      // tp2 为深度差阈值3-阈值2挂单后延时检测时间的随机值（秒）
      const delayRange = hedgeMode.delayTime02To2
      tp2 = getRandomFromRange(delayRange)
      
      console.log(`深度差 ${threshold3}-${threshold2} - 计算价格: ${finalPrice.toFixed(2)}, tp2: ${tp2.toFixed(2)}秒`)
      
    } else if (Math.abs(depthDiff - 0.1) < 0.01) {
      // 深度差 0.1（允许0.09-0.11的误差）：检查开关是否打开
      if (!hedgeMode.enableDepthDiffParams01) {
        throw new Error(`深度差0.1时，该深度区间开关未开启，订单薄不符合条件（当前深度差: ${depthDiff.toFixed(2)}）`)
      } else {
        // 开关打开，执行逻辑C
        const maxEatValue = hedgeMode.maxEatValue01  // 深度差0.1最大多吃价值(U)
        const maxDepth = hedgeMode.maxDepth  // 最大允许深度(U)
        
        if (isClose) {
          // 【平仓逻辑】
          // 先计算 卖一价深度*卖一价/100 得到 卖一价的价值（美元）
          const askValue = rawAsk1 * rawAsk1Depth / 100
          
          if (askValue < maxDepth) {
            // 卖一价的价值 < 最大允许深度，价格取卖一价，数量正常（先挂方=后挂方）
            finalPrice = rawAsk1
            console.log(`深度差 0.1 - 平仓模式，卖一价值 ${askValue.toFixed(2)}U < 最大允许深度 ${maxDepth}U，使用卖一价: ${finalPrice.toFixed(2)}`)
          } else {
            // 卖一价的价值 >= 最大允许深度，查看买一价的价值
            const bidValue = rawBid1 * rawBid1Depth / 100
            
            if (bidValue >= maxEatValue) {
              // 买一价的价值 >= 深度差0.1最大多吃价值，订单薄不符合条件
              throw new Error(`深度差0.1时，平仓模式不满足条件：卖一价值 ${askValue.toFixed(2)}U >= 最大允许深度 ${maxDepth}U，且买一价值 ${bidValue.toFixed(2)}U >= 最大多吃价值 ${maxEatValue}U`)
            } else {
              // 买一价的价值 < 深度差0.1最大多吃价值
              // 价格取买一价，后挂方数量=服务器下发数量，先挂方数量需要减少
              finalPrice = rawBid1
              // 先挂方数量 = 服务器下发数量 - 深度差0.1最大多吃价值 / 买一价
              firstShareReduction = (maxEatValue / rawBid1)*100
              console.log(`深度差 0.1 - 平仓模式，卖一价值 ${askValue.toFixed(2)}U >= 最大允许深度 ${maxDepth}U，但买一价值 ${bidValue.toFixed(2)}U < 最大多吃价值 ${maxEatValue}U，使用买一价: ${finalPrice.toFixed(2)}，先挂方数量减少: ${firstShareReduction.toFixed(2)}`)
            }
          }
        } else {
          // 【开仓逻辑】
          // 先计算 买一价深度*买一价/100 得到 买一价的价值（美元）
          const bidValue = rawBid1 * rawBid1Depth / 100
          
          if (bidValue < maxDepth) {
            // 买一价的价值 < 最大允许深度，价格取买一价，数量正常（先挂方=后挂方）
            finalPrice = rawBid1
            console.log(`深度差 0.1 - 开仓模式，买一价值 ${bidValue.toFixed(2)}U < 最大允许深度 ${maxDepth}U，使用买一价: ${finalPrice.toFixed(2)}`)
          } else {
            // 买一价的价值 >= 最大允许深度，查看卖一价的价值
            const askValue = rawAsk1 * rawAsk1Depth / 100
            
            if (askValue >= maxEatValue) {
              // 卖一价的价值 >= 深度差0.1最大多吃价值，订单薄不符合条件
              throw new Error(`深度差0.1时，开仓模式不满足条件：买一价值 ${bidValue.toFixed(2)}U >= 最大允许深度 ${maxDepth}U，且卖一价值 ${askValue.toFixed(2)}U >= 最大多吃价值 ${maxEatValue}U`)
            } else {
              // 卖一价的价值 < 深度差0.1最大多吃价值
              // 价格取卖一价，后挂方数量=服务器下发数量，先挂方数量需要减少
              finalPrice = rawAsk1
              // 先挂方数量 = 服务器下发数量 - 深度差0.1最大多吃价值 / 卖一价
              firstShareReduction = (maxEatValue / rawAsk1)*100
              console.log(`深度差 0.1 - 开仓模式，买一价值 ${bidValue.toFixed(2)}U >= 最大允许深度 ${maxDepth}U，但卖一价值 ${askValue.toFixed(2)}U < 最大多吃价值 ${maxEatValue}U，使用卖一价: ${finalPrice.toFixed(2)}，先挂方数量减少: ${firstShareReduction.toFixed(2)}`)
            }
          }
        }
      }
      
      // 深度差0.1时，不传tp2（tp4会在后面添加，固定为1）
      tp2 = null
      
      console.log(`深度差 0.1 - 最终价格: ${finalPrice.toFixed(2)}`)
      
    } else {
      throw new Error(`该深度区间开关未开启，订单薄不符合条件（当前深度差: ${depthDiff.toFixed(2)}）`)
    }
    
    // 确定深度差范围标识（用于判断使用哪个开关）
    let depthDiffRange = null
    if (depthDiff > threshold1) {
      depthDiffRange = 'gt15'
    } else if (depthDiff >= threshold2) {
      depthDiffRange = '2to15'
    } else if (depthDiff >= threshold3) {
      depthDiffRange = '02to2'
    } else if (Math.abs(depthDiff - 0.1) < 0.01) {
      depthDiffRange = '01'
    }
    
    return {
      firstSide,
      price1,           // 先挂方的买一价（剔除挂单后）
      price2,           // 先挂方的卖一价（剔除挂单后）
      depth1,           // 先挂方的买一深度
      depth2,           // 先挂方的卖一深度
      depthDiffRange,   // 深度差范围标识：'gt15', '2to15', '02to2', '01'
      diff: depthDiff,  // 先挂方买卖价差（深度差）
      minPrice: Math.min(price1, price2),
      maxPrice: Math.max(price1, price2),
      topNBidsDepth,    // 买1-N深度累计
      topNAsksDepth,    // 卖1-N深度累计
      finalPrice,       // 计算出的最终价格
      tp2,              // 延时检测时间（秒）
      firstShareReduction  // 深度差0.1时，先挂方数量需要减少的量
    }
  } catch (error) {
    console.error('解析订单薄数据失败:', error)
    throw error
  }
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
 * 检查订单薄数据是否满足对冲条件
 * 类似 App_old.vue 中的判断逻辑：
 * 1. 先挂方的买一和卖一价差值 > 0.15
 * 2. 或者根据开仓/平仓判断先挂方的深度
 * 3. 深度差0.1时，如果开关打开，使用特殊的"多吃价值"逻辑
 * @param {Object} priceInfo - 订单薄价格信息
 * @param {Object} config - 主题配置（可选，用于获取主题单独设置的最大允许深度）
 */
const checkOrderbookHedgeCondition = (priceInfo, config = null) => {
  if (!priceInfo) return false
  
  // 获取该主题的最大允许深度（优先使用主题单独设置）
  const maxDepth = getMaxDepth(config)
  
  let canHedge = false
  
  // price1: 先挂方的买一价
  // price2: 先挂方的卖一价
  // depth1: 先挂方的买一深度
  // depth2: 先挂方的卖一深度
  
  if (priceInfo.diff > 0.15) {
    // 先挂方的买卖价差大于0.15，可以对冲
    canHedge = true
    console.log(`✅ 先挂方买卖价差充足 (${priceInfo.diff.toFixed(2)})，满足对冲条件`)
  } else if (priceInfo.depthDiffRange === '01' && hedgeMode.enableDepthDiffParams01) {
    // 深度差0.1且开关打开，使用特殊的"多吃价值"逻辑
    // 如果 parseOrderbookData 已经通过了检查并返回了 finalPrice，说明满足条件
    console.log(`⚠️ 深度差0.1，检查多吃价值条件`)
    
    const maxEatValue = hedgeMode.maxEatValue01  // 深度差0.1最大多吃价值(U)
    
    if (!hedgeMode.isClose) {
      // 开仓模式：
      // 1. 买一价值 < 最大允许深度 → 允许对冲
      // 2. 买一价值 >= 最大允许深度，但卖一价值 < 最大多吃价值 → 也允许对冲
      const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
      const askValue = priceInfo.price2 * priceInfo.depth2 / 100
      console.log(`开仓模式，买一价值: ${bidValue.toFixed(2)}U, 卖一价值: ${askValue.toFixed(2)}U, 最大允许深度: ${maxDepth}U, 最大多吃价值: ${maxEatValue}U`)
      
      if (bidValue < maxDepth) {
        canHedge = true
        console.log(`✅ 买一价值满足条件 (${bidValue.toFixed(2)}U < ${maxDepth}U)，允许对冲`)
      } else if (askValue < maxEatValue) {
        canHedge = true
        console.log(`✅ 买一价值超限但卖一价值满足多吃条件 (${askValue.toFixed(2)}U < ${maxEatValue}U)，允许对冲`)
      } else {
        console.log(`❌ 买一价值超限 (${bidValue.toFixed(2)}U >= ${maxDepth}U) 且卖一价值也超限 (${askValue.toFixed(2)}U >= ${maxEatValue}U)，不对冲`)
      }
    } else {
      // 平仓模式：
      // 1. 卖一价值 < 最大允许深度 → 允许对冲
      // 2. 卖一价值 >= 最大允许深度，但买一价值 < 最大多吃价值 → 也允许对冲
      const askValue = priceInfo.price2 * priceInfo.depth2 / 100
      const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
      console.log(`平仓模式，卖一价值: ${askValue.toFixed(2)}U, 买一价值: ${bidValue.toFixed(2)}U, 最大允许深度: ${maxDepth}U, 最大多吃价值: ${maxEatValue}U`)
      
      if (askValue < maxDepth) {
        canHedge = true
        console.log(`✅ 卖一价值满足条件 (${askValue.toFixed(2)}U < ${maxDepth}U)，允许对冲`)
      } else if (bidValue < maxEatValue) {
        canHedge = true
        console.log(`✅ 卖一价值超限但买一价值满足多吃条件 (${bidValue.toFixed(2)}U < ${maxEatValue}U)，允许对冲`)
      } else {
        console.log(`❌ 卖一价值超限 (${askValue.toFixed(2)}U >= ${maxDepth}U) 且买一价值也超限 (${bidValue.toFixed(2)}U >= ${maxEatValue}U)，不对冲`)
      }
    }
  } else {
    // 其他情况（差值小于等于0.15且不是深度差0.1特殊逻辑），根据开仓/平仓判断先挂方的价值
    console.log(`⚠️ 先挂方买卖价差不足 (${priceInfo.diff.toFixed(2)})，检查价值条件`)
    
    if (!hedgeMode.isClose) {
      // 开仓模式：判断先挂方买一价值（买一价 × 买一深度 / 100）
      const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
      console.log(`开仓模式，先挂方买一价值: ${bidValue.toFixed(2)}U, 最大允许深度: ${maxDepth}U`)
      
      if (bidValue < maxDepth) {
        canHedge = true
        console.log(`✅ 价值满足条件 (${bidValue.toFixed(2)}U < ${maxDepth}U)，允许对冲`)
      } else {
        console.log(`❌ 价值超过限制 (${bidValue.toFixed(2)}U >= ${maxDepth}U)，不对冲`)
      }
    } else {
      // 平仓模式：判断先挂方卖一价值（卖一价 × 卖一深度 / 100）
      const askValue = priceInfo.price2 * priceInfo.depth2 / 100
      console.log(`平仓模式，先挂方卖一价值: ${askValue.toFixed(2)}U, 最大允许深度: ${maxDepth}U`)
      
      if (askValue < maxDepth) {
        canHedge = true
        console.log(`✅ 价值满足条件 (${askValue.toFixed(2)}U < ${maxDepth}U)，允许对冲`)
      } else {
        console.log(`❌ 价值超过限制 (${askValue.toFixed(2)}U >= ${maxDepth}U)，不对冲`)
      }
    }
  }
  
  return canHedge
}

/**
 * 从订单薄数据执行对冲
 * price1: 先挂方的买一价
 * price2: 先挂方的卖一价
 * 支持同时执行多个对冲任务
 */
const executeHedgeFromOrderbook = async (config, priceInfo) => {
  try {
    console.log(`配置 ${config.id} - 符合对冲条件，准备执行对冲`, priceInfo)
    
    // 使用计算出的最终价格，如果没有则使用原来的逻辑
    let orderPrice
    if (priceInfo.finalPrice !== null && priceInfo.finalPrice !== undefined) {
      orderPrice = priceInfo.finalPrice.toFixed(1)
      console.log(`使用计算出的最终价格: ${orderPrice}`)
    } else {
      // 兼容旧逻辑
      if (priceInfo.diff > 0.15) {
        // 先挂方买卖价差大于0.15，取平均价
        orderPrice = ((priceInfo.price1 + priceInfo.price2) / 2).toFixed(1)
        console.log(`差值充足，订单价格（买卖均价）: ${orderPrice}`)
      } else {
        // 差值小于等于0.15，根据开仓/平仓取价格
        if (!hedgeMode.isClose) {
          // 开仓模式：取较小的价格（买一价）
          orderPrice = priceInfo.minPrice.toFixed(1)
          console.log(`开仓模式，订单价格（买一价）: ${orderPrice}`)
        } else {
          // 平仓模式：取较大的价格（卖一价）
          orderPrice = priceInfo.maxPrice.toFixed(1)
          console.log(`平仓模式，订单价格（卖一价）: ${orderPrice}`)
        }
      }
    }
    
    // 获取当前打开显示的所有主题ID
    const trendingIds = activeConfigs.value.map(c => c.id).join(',')
    console.log(`当前打开显示的主题: ${trendingIds}`)
    
    // 获取需要执行的任务数量（优先使用主题单独设置）
    const taskCount = getTasksPerTopic(config)
    
    // 检查当前正在执行的对冲任务数量
    const currentHedges = config.currentHedges || []
    const runningHedges = currentHedges.filter(h => h.finalStatus === 'running')
    const totalAvailableSlots = taskCount - runningHedges.length
    
    if (totalAvailableSlots <= 0) {
      console.log(`配置 ${config.id} - 已达到最大任务数 ${taskCount}，跳过`)
      return
    }
    
    // 每一轮最多任务数限制
    const maxPerRound = hedgeMaxTasksPerRound.value || 10
    const availableSlots = Math.min(totalAvailableSlots, maxPerRound)
    
    console.log(`配置 ${config.id} - 需要执行 ${availableSlots} 个对冲任务（总上限: ${taskCount}, 当前运行: ${runningHedges.length}, 本轮上限: ${maxPerRound}）`)
    
    // 顺序请求多个对冲任务（避免同时请求导致的问题）
    const hedgeResults = []
    for (let i = 0; i < availableSlots; i++) {
      try {
        console.log(`配置 ${config.id} - 开始请求第 ${i + 1}/${availableSlots} 个对冲任务...`)
        
        // 根据模式选择不同的接口
        const currentMode = hedgeMode.isClose ? hedgeMode.hedgeMode : 1
        let apiUrl, requestData
        
        if (currentMode === 2) {
          // 模式2：使用 calReadyToHedgeToCloseV2 接口
          apiUrl = 'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeToCloseV2'
          requestData = {
            trendingId: config.id,
            currentPrice: orderPrice,
            priceOutCome: priceInfo.firstSide,  // 先挂方 (yes/no)
            singleCloseAmtMax: hedgeMode.minCloseAmt,  // 参数1：平仓最小数量
            closeAmtSumMin: hedgeMode.minTotalCloseAmt,  // 参数2：合计最小平仓值
            closeAmtSumMax: hedgeMode.maxTotalCloseAmt,  // 参数3：合计最大平仓值
            takerMinAmt: hedgeMode.takerMinAmt,  // 参数4：taker最小数量
            numberType: parseInt(selectedNumberType.value),  // 账号类型：1-全部账户, 2-1000个账户,
            //  3-1000个账户中未达标的
            // closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
          }
          // 如果 maxIpDelay 有值，则添加到请求参数中
          if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
            requestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
          }
          // 添加 needJudgeDF 和 maxDHour 字段
          requestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
          requestData.maxDHour = Number(hedgeMode.maxDHour) || 12
          // 添加 minCloseMin 字段
          requestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
          // 添加资产优先级校验字段
          requestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
          requestData.balancePriority = hedgeMode.balancePriority
        } else if (currentMode === 3) {
          // 模式3：使用 quickCalReadyToHedgeToClose 接口
          apiUrl = 'https://sg.bicoin.com.cn/99l/hedge/quickCalReadyToHedgeToClose'
          requestData = {
            trendingId: config.id,
            currentPrice: orderPrice,
            priceOutCome: priceInfo.firstSide,  // 先挂方 (yes/no)
            singleCloseAmtMax: hedgeMode.minCloseAmt,  // 参数1：平仓最小数量
            closeAmtSumMin: hedgeMode.minTotalCloseAmt,  // 参数2：合计最小平仓值
            closeAmtSumMax: hedgeMode.maxTotalCloseAmt,  // 参数3：合计最大平仓值
            takerMinAmt: hedgeMode.takerMinAmt,  // 参数4：taker最小数量
            // closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
            // 模式3不传 numberType
          }
          // 如果 maxIpDelay 有值，则添加到请求参数中
          if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
            requestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
          }
          // 添加 needJudgeDF 和 maxDHour 字段
          requestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
          requestData.maxDHour = Number(hedgeMode.maxDHour) || 12
          // 添加 minCloseMin 字段
          requestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
          // 添加资产优先级校验字段
          requestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
          requestData.balancePriority = hedgeMode.balancePriority
        } else {
          // 模式1：使用原有接口
          apiUrl = 'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeV4'
          requestData = {
            trendingId: config.id,
            isClose: hedgeMode.isClose,
            currentPrice: orderPrice,
            priceOutCome: priceInfo.firstSide,  // 先挂方 (YES/NO)
            timePassMin: hedgeMode.timePassMin,
            minUAmt: hedgeMode.minUAmt,  // 最小开单
            maxUAmt: hedgeMode.maxUAmt,   // 最大开单
            minCloseAmt: hedgeMode.minCloseAmt,  // 平仓最小数量（参数1）
            maxOpenHour: hedgeMode.maxOpenHour,  // 可加仓时间（小时）
            closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
            numberType: parseInt(selectedNumberType.value)  // 账号类型：1-全部账户, 2-1000个账户, 3-1000个账户中未达标的
          }
          // 如果 maxIpDelay 有值，则添加到请求参数中
          if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
            requestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
          }
          // 添加 needJudgeDF 和 maxDHour 字段
          requestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
          requestData.maxDHour = Number(hedgeMode.maxDHour) || 12
          // 添加 minCloseMin 字段
          requestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
          // 添加资产优先级校验字段
          requestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
          requestData.balancePriority = hedgeMode.balancePriority
          // 添加账号随机8小时不交易参数
          requestData.needJudgeTimeRandom = hedgeMode.needJudgeTimeRandom || 0
          // 添加交易量和仓位价值限制参数（单位：万转10000）
          if (hedgeMode.maxVolume24hOpen !== undefined && hedgeMode.maxVolume24hOpen !== null && hedgeMode.maxVolume24hOpen !== '') {
            requestData.maxVolume24hOpen = Number(hedgeMode.maxVolume24hOpen) * 10000
          }
          if (hedgeMode.maxVolume7dAvgOpen !== undefined && hedgeMode.maxVolume7dAvgOpen !== null && hedgeMode.maxVolume7dAvgOpen !== '') {
            requestData.maxVolume7dAvgOpen = Number(hedgeMode.maxVolume7dAvgOpen) * 10000
          }
          if (hedgeMode.maxPosWorthOpen !== undefined && hedgeMode.maxPosWorthOpen !== null && hedgeMode.maxPosWorthOpen !== '' && hedgeMode.maxPosWorthOpen > 0) {
            requestData.maxPosWorthOpen = Number(hedgeMode.maxPosWorthOpen) * 10000
          }
          // 如果是开仓模式，添加模式一专属设置
          if (!hedgeMode.isClose) {
            if (hedgeMode.posPriorityArea && hedgeMode.posPriorityArea !== '') {
              requestData.posPriorityArea = hedgeMode.posPriorityArea
            }
            if (hedgeMode.maxPosLimit !== undefined && hedgeMode.maxPosLimit !== null && hedgeMode.maxPosLimit !== '') {
              requestData.maxPosLimit = Number(hedgeMode.maxPosLimit)
            }
          }
        }
        
        const response = await axios.post(
          apiUrl,
          requestData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data && response.data.data) {
          const hedgeData = response.data.data
          console.log(`配置 ${config.id} - 获取对冲双方成功 (任务 ${i + 1}/${availableSlots}):`, hedgeData)
          
          // 获取 missionId（组任务的任务id）
          const missionId = hedgeData.missionId
          
          // 根据模式执行不同的对冲任务
          // 根据深度差范围和开关决定是否传递tp2和tp4
          let shouldPassTp2Tp4 = false
          let shouldPassTp4For01 = false  // 深度差0.1时只传tp4（固定为1），不传tp2
          if (priceInfo.depthDiffRange === 'gt15' && hedgeMode.enableDepthDiffParamsGt15) {
            shouldPassTp2Tp4 = true
          } else if (priceInfo.depthDiffRange === '2to15' && hedgeMode.enableDepthDiffParams2To15) {
            shouldPassTp2Tp4 = true
          } else if (priceInfo.depthDiffRange === '02to2' && hedgeMode.enableDepthDiffParams02To2) {
            shouldPassTp2Tp4 = true
          } else if (priceInfo.depthDiffRange === '01' && hedgeMode.enableDepthDiffParams01) {
            shouldPassTp4For01 = true  // 深度差0.1时只传tp4，固定为1
          }
          
          if (currentMode === 2 || currentMode === 3) {
            // 模式2和模式3：使用新的多任务逻辑
            await executeHedgeTaskV2(config, {
              ...hedgeData,
              currentPrice: orderPrice,
              firstSide: priceInfo.firstSide,
              missionId: missionId,  // 传递组任务id
              priceInfo: priceInfo,   // 传递订单薄数据，用于构建 depthStr
              tp2: shouldPassTp2Tp4 ? priceInfo.tp2 : null,  // 根据开关决定是否传递 tp2
              depthDiffRange: priceInfo.depthDiffRange  // 传递深度差范围标识
            })
          } else {
            // 模式1：使用原有逻辑
            await executeHedgeTask(config, {
              ...hedgeData,
              currentPrice: orderPrice,
              firstSide: priceInfo.firstSide,
              missionId: missionId,  // 传递组任务id
              priceInfo: priceInfo,   // 传递订单薄数据，用于构建 depthStr
              tp2: shouldPassTp2Tp4 ? priceInfo.tp2 : null,  // 根据开关决定是否传递 tp2
              firstShareReduction: priceInfo.firstShareReduction || 0,  // 传递深度差0.1时先挂方数量需要减少的量
              depthDiffRange: priceInfo.depthDiffRange  // 传递深度差范围标识
            })
          }
          
          hedgeResults.push(true)
          console.log(`配置 ${config.id} - 第 ${i + 1} 个对冲任务已提交成功`)
        } else if (response.data && response.data.msg) {
          // 服务器返回错误消息，添加到对冲信息中
          console.warn(`配置 ${config.id} - 对冲任务 ${i + 1} 服务器返回错误:`, response.data.msg)
          
          // 初始化 currentHedges 数组（如果不存在）
          if (!config.currentHedges) {
            config.currentHedges = []
          }
          
          // 创建一个错误记录
          const errorRecord = {
            id: Date.now(),
            trendingId: config.id,
            trendingName: config.trending,
            startTime: new Date().toISOString(),
            endTime: new Date().toISOString(),
            finalStatus: 'failed',
            errorMsg: response.data.msg
          }
          config.currentHedges.push(errorRecord)
          
          hedgeResults.push(false)
        } else {
          throw new Error('获取对冲双方失败')
        }
      } catch (error) {
        console.error(`配置 ${config.id} - 执行对冲任务 ${i + 1} 失败:`, error)
        hedgeResults.push(false)
      }
      
      // 添加小延迟，避免请求过快（最后一个不需要延迟）
      if (i < availableSlots - 1) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    }
    
    const successCount = hedgeResults.filter(r => r === true).length
    console.log(`配置 ${config.id} - 已提交 ${successCount}/${availableSlots} 个对冲任务`)
    
    // 返回成功提交的任务数
    return successCount
  } catch (error) {
    console.error(`配置 ${config.id} - 执行对冲失败:`, error)
    return 0
  }
}

/**
 * 打开主题链接（在新标签页打开）
 */
const openOpUrl = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
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
 * 检查配置是否正在更新订单薄
 */
const isUpdatingOrderbook = (config) => {
  if (!config || !config.id) {
    return false
  }
  return updatingOrderbookConfigIds.value.has(String(config.id))
}

/**
 * 手动更新指定配置的订单薄
 */
const updateOrderbookForConfig = async (config) => {
  if (!config || !config.id) {
    showToast('配置不存在', 'warning')
    return
  }
  
  const configId = String(config.id)
  
  // 如果正在更新，直接返回
  if (updatingOrderbookConfigIds.value.has(configId)) {
    return
  }
  
  // 标记为正在更新
  updatingOrderbookConfigIds.value.add(configId)
  
  const pollTime = Date.now()
  let priceInfo = null
  let orderbookReason = null
  
  try {
    showToast(`正在更新 ${config.trending} 的订单薄...`, 'info')
    
    // 尝试使用parseOrderbookData进行完整检查
    try {
      priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
      
      if (priceInfo) {
        // 检查是否满足对冲条件
        const meetsCondition = checkOrderbookHedgeCondition(priceInfo, config)
        
        if (!meetsCondition) {
          // 不满足条件，获取不满足的原因
          const maxDepth = getMaxDepth(config)
          if (priceInfo.diff <= 0.15) {
            if (!hedgeMode.isClose) {
              // 开仓模式：检查买一价值（买一价 × 买一深度 / 100）
              const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
              if (bidValue >= maxDepth) {
                orderbookReason = `先挂方买一价值 ${bidValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
              } else {
                orderbookReason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
              }
            } else {
              // 平仓模式：检查卖一价值（卖一价 × 卖一深度 / 100）
              const askValue = priceInfo.price2 * priceInfo.depth2 / 100
              if (askValue >= maxDepth) {
                orderbookReason = `先挂方卖一价值 ${askValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
              } else {
                orderbookReason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
              }
            }
          } else {
            orderbookReason = '不符合对冲条件'
          }
        }
        
        // 记录更新时间（成功获取订单薄的时间）
        priceInfo.updateTime = Date.now()
        priceInfo.pollTime = pollTime
        priceInfo.reason = orderbookReason
      }
    } catch (error) {
      // 如果是深度区间开关未开启的错误，直接抛出，不回退到基本数据
      if (error.message && error.message.includes('深度区间开关未开启')) {
        console.error(`配置 ${config.id} - 深度区间开关未开启，直接失败:`, error.message)
        throw error
      }
      
      // parseOrderbookData失败，尝试获取基本订单薄数据
      console.warn(`配置 ${config.id} - 完整订单薄检查失败，尝试获取基本数据:`, error.message)
      
      try {
        const basicInfo = await fetchOrderbookBasic(config, hedgeMode.isClose)
        
        if (basicInfo) {
          // 使用基本数据
          priceInfo = {
            ...basicInfo,
            updateTime: Date.now(),  // 记录更新时间
            pollTime: pollTime,      // 记录轮询时间
            reason: error.message || '订单薄数据不满足条件'  // 记录不满足原因
          }
          orderbookReason = priceInfo.reason
        } else {
          throw new Error('获取基本订单薄数据失败')
        }
      } catch (basicError) {
        // 基本数据也获取失败
        console.error(`配置 ${config.id} - 获取基本订单薄数据也失败:`, basicError)
        throw error  // 抛出原始错误
      }
    }
    
    if (priceInfo) {
      // 保存订单薄数据到config.orderbookData（与自动分配时保存的位置一致）
      config.orderbookData = priceInfo
      
      // 同时更新orderbookInfo（用于配置列表显示）
      const meetsCondition = !orderbookReason
      
      // 获取basicInfo用于计算评分和显示统计信息
      const basicInfo = await fetchOrderbookBasic(config, hedgeMode.isClose)
      if (basicInfo) {
        config.orderbookInfo = {
          firstSide: basicInfo.firstSide,
          price1: basicInfo.price1,
          price2: basicInfo.price2,
          depth1: basicInfo.depth1,
          depth2: basicInfo.depth2,
          diff: basicInfo.diff,
          meetsCondition: meetsCondition,
          yesBidsCount: basicInfo.yesBidsCount,
          yesAsksCount: basicInfo.yesAsksCount,
          noBidsCount: basicInfo.noBidsCount,
          noAsksCount: basicInfo.noAsksCount
        }
        
        // 计算自动评分
        const rating = calculateRating(basicInfo)
        if (rating !== null) {
          config.rating = rating
          saveConfigRating(config)
        }
      } else {
        // 如果获取basicInfo失败，至少使用priceInfo的基本信息
        config.orderbookInfo = {
          firstSide: priceInfo.firstSide,
          price1: priceInfo.price1,
          price2: priceInfo.price2,
          depth1: priceInfo.depth1,
          depth2: priceInfo.depth2,
          diff: priceInfo.diff,
          meetsCondition: meetsCondition
        }
      }
      
      showToast(`${config.trending} 订单薄更新成功`, 'success')
      console.log(`✅ ${config.trending}: 订单薄更新成功`, {
        先挂方: priceInfo.firstSide,
        先挂价格: priceInfo.price1,
        后挂价格: priceInfo.price2,
        价差: priceInfo.diff,
        不满足原因: orderbookReason
      })
    } else {
      config.orderbookData = null
      showToast(`${config.trending} 订单薄更新失败：数据不足`, 'error')
      console.log(`❌ ${config.trending}: 订单薄更新失败`)
    }
  } catch (error) {
    // 即使请求失败，也保存轮询时间和错误信息
    const errorMessage = error.response?.data?.message || error.message || '获取深度失败'
    config.orderbookData = {
      pollTime: pollTime,
      updateTime: null,  // 请求失败，没有更新时间
      reason: errorMessage,
      firstSide: null,
      price1: null,
      price2: null,
      depth1: null,
      depth2: null,
      diff: null
    }
    
    showToast(`${config.trending} 订单薄更新失败: ${errorMessage}`, 'error')
    console.error(`更新 ${config.trending} 订单薄失败:`, error)
  } finally {
    // 移除更新标记
    updatingOrderbookConfigIds.value.delete(configId)
    
    // 5秒后跳转到任务异常界面，传递 trendingId 参数
    setTimeout(() => {
      const trendingId = config.id
      const taskAnomalyUrl = `https://oss.w3id.info/Opanomaly/index.html#/task-anomaly?trendingId=${trendingId}`
      window.open(taskAnomalyUrl, '_blank')
    }, 5000)
  }
}

/**
 * 打开持仓详情页面
 */
const openPositionDetail = (config) => {
  if (!config || !config.id) {
    showToast('配置不存在', 'warning')
    return
  }
  
  const trendingId = config.id
  const positionDetailUrl = `https://oss.w3id.info/Opanomaly/index.html#/position-detail?id=${trendingId}`
  window.open(positionDetailUrl, '_blank')
}

/**
 * 打开挂单详情页面
 */
const openOpenOrderDetail = (config) => {
  if (!config || !config.id) {
    showToast('配置不存在', 'warning')
    return
  }
  
  const trendingId = config.id
  const openOrderDetailUrl = `https://oss.w3id.info/Opanomaly/index.html#/open-order-detail?id=${trendingId}`
  window.open(openOrderDetailUrl, '_blank')
}

/**
 * 关闭配置任务
 */
const closeConfigTask = async (config) => {
  if (!confirm(`确定要关闭任务"${config.trending}"吗？`)) {
    return
  }
  
  try {
    // 1. 更新本地显示状态（只更新这一个主题，不影响其他主题）
    try {
      const visibleData = JSON.parse(localStorage.getItem(CONFIG_VISIBLE_KEY) || '{}')
      visibleData[config.id] = false
      localStorage.setItem(CONFIG_VISIBLE_KEY, JSON.stringify(visibleData))
      console.log(`主题 ${config.id} 的显示状态已设置为 false`)
    } catch (e) {
      console.error('更新显示状态失败:', e)
    }
    
    // 2. 更新服务器配置，将isOpen设为0
    const updateData = {
      list: [{
        id: config.id,
        trending: config.trending,
        trendingPart1: config.trendingPart1,
        trendingPart2: config.trendingPart2,
        trendingPart3: config.trendingPart3,
        opUrl: config.opUrl,
        polyUrl: config.polyUrl,
        opTopicId: config.opTopicId,
        weight: config.weight,
        isOpen: 0  // 关闭任务
      }]
    }
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      updateData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log(`配置 ${config.id} 已关闭`)
      showToast(`任务"${config.trending}"已关闭`, 'success')
      
      // 3. 更新本地配置列表中这个配置的状态（避免重新加载所有配置）
      const configInList = configList.value.find(c => c.id === config.id)
      if (configInList) {
        configInList.isOpen = 0
        configInList.enabled = false
      }
      
      // 4. 更新活动配置列表
      updateActiveConfigs()
    }
  } catch (error) {
    console.error('关闭任务失败:', error)
    showToast(`关闭任务失败: ${error.message}`, 'error')
  }
}

/**
 * 随机获取可用主题
 * @param {Array} useFailedTopics - 是否使用失败的主题列表，如果为true，则从失败列表中获取
 */
const randomGetAvailableTopic = async (useFailedTopics = false) => {
  if (isRandomGetting.value) return
  
  // 获取目标数量，确保至少为1
  const targetCount = Math.max(1, Math.floor(randomGetCount.value) || 1)
  
  isRandomGetting.value = true
  
  // 清空当前轮次的失败主题列表（如果是从失败列表获取，则不清空，而是更新）
  const currentRoundFailedTopics = []
  
  if (useFailedTopics) {
    if (failedTopics.value.length === 0) {
      showToast('没有失败的主题可以重试', 'warning')
      isRandomGetting.value = false
      return
    }
    showToast(`正在从失败列表中获取 ${targetCount} 个可用主题（共 ${failedTopics.value.length} 个失败主题）...`, 'info')
  } else {
    showToast(`正在随机获取 ${targetCount} 个可用主题...`, 'info')
  }
  
  try {
    // 如果是平仓模式，先获取持仓数据
    if (hedgeMode.isClose) {
      console.log('平仓模式：先获取持仓数据...')
      await fetchPositionTopics()
      console.log(`当前持仓主题数量: ${positionTopics.value.size}`)
      
      if (positionTopics.value.size === 0) {
        showToast('当前没有任何持仓，无法进行平仓操作', 'warning')
        isRandomGetting.value = false
        return
      }
    }
    
    let closedConfigs = []
    
    if (useFailedTopics) {
      // 从失败的主题列表中获取
      closedConfigs = failedTopics.value.filter(config => {
        // 确保配置仍然有效
        return config.trendingPart1 && 
               config.trendingPart2 &&
               config.trending && 
               !config.trending.includes('undefined')
      })
      
      if (closedConfigs.length === 0) {
        showToast('失败的主题列表中没有有效主题', 'warning')
        return
      }
      
      console.log(`从失败列表中获取到 ${closedConfigs.length} 个主题`)
    } else {
      // 1. 请求配置列表
      const configResponse = await axios.get('https://sg.bicoin.com.cn/99l/mission/exchangeConfig')
      
      if (configResponse.data?.code !== 0) {
        throw new Error('获取配置数据失败')
      }
      
      const allConfigs = configResponse.data.data.configList || []
      
      // 加载本地的显示/隐藏状态
      const allConfigsWithVisible = loadConfigVisibleStatus(allConfigs)
      
      console.log(`获取到 ${allConfigsWithVisible.length} 个配置`)
      
      // 统计各种状态
      const openCount = allConfigsWithVisible.filter(c => c.isOpen === 1).length
      const closedCount = allConfigsWithVisible.filter(c => c.isOpen === 0).length
      const hasTokenCount = allConfigsWithVisible.filter(c => c.trendingPart1 && c.trendingPart2).length
      const hiddenCount = allConfigsWithVisible.filter(c => c.visible === false).length
      
      console.log(`- isOpen=1 (打开): ${openCount} 个`)
      console.log(`- isOpen=0 (关闭): ${closedCount} 个`)
      console.log(`- visible=false (隐藏): ${hiddenCount} 个`)
      console.log(`- 有tokenId: ${hasTokenCount} 个`)
      
      // 2. 筛选出(isOpen=0或visible=false)且有tokenId的主题，且trending不包含"undefined"
      closedConfigs = allConfigsWithVisible.filter(config => 
        (config.isOpen === 0 || config.visible === false) && 
        config.trendingPart1 && 
        config.trendingPart2 &&
        config.trending && 
        !config.trending.includes('undefined')
      )
      
      console.log(`符合条件的主题: ${closedConfigs.length} 个`)
      
      if (closedConfigs.length === 0) {
        showToast(`没有可用的主题 (总配置:${allConfigsWithVisible.length}, 关闭:${closedCount}, 隐藏:${hiddenCount}, 有token:${hasTokenCount})`, 'warning')
        return
      }
    }
    
    console.log(`找到 ${closedConfigs.length} 个主题，开始测试...`)
    
    // 3. 打乱顺序（测试所有主题，直到找到指定数量的符合条件的）
    const shuffled = [...closedConfigs].sort(() => Math.random() - 0.5)
    
    console.log(`将测试所有 ${shuffled.length} 个主题，直到找到 ${targetCount} 个符合条件的`)
    
    // 4. 遍历测试每个主题，收集符合条件的主题
    let testedCount = 0
    let foundCount = 0
    const foundConfigs = []
    
    for (const config of shuffled) {
      // 如果已经找到足够数量的主题，停止查找
      if (foundCount >= targetCount) {
        break
      }
      
      testedCount++
      try {
        console.log(`[${testedCount}/${shuffled.length}] 测试主题: ${config.trending} (已找到: ${foundCount}/${targetCount})`)
        showToast(`正在测试 ${testedCount}/${shuffled.length} (已找到: ${foundCount}/${targetCount}): ${config.trending.substring(0, 30)}...`, 'info')
        
        // 请求订单薄数据
        const priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
        
        if (!priceInfo) {
          console.log(`主题 ${config.trending} 订单薄数据不足，跳过`)
          continue
        }
        
        // 检查是否满足对冲条件
        if (checkOrderbookHedgeCondition(priceInfo, config)) {
          // 如果是平仓模式，需要检查主题是否在持仓列表中
          if (hedgeMode.isClose) {
            const isInPosition = positionTopics.value.has(config.trending)
            console.log(`平仓检查: 主题 "${config.trending}" ${isInPosition ? '在' : '不在'}持仓列表中`)
            
            if (!isInPosition) {
              console.log(`❌ 主题 ${config.trending} 不在持仓列表中，跳过`)
              continue
            }
          }
          
          console.log(`✅ 主题 ${config.trending} 满足对冲条件！ (${foundCount + 1}/${targetCount})`)
          foundConfigs.push(config)
          foundCount++
          
          // 打开这个主题
          await openConfigTask(config)
          
          if (foundCount < targetCount) {
            showToast(`✅ 已找到 ${foundCount}/${targetCount} 个可用主题，继续查找...`, 'success')
          }
        } else {
          console.log(`❌ 主题 ${config.trending} 不满足对冲条件，继续寻找...`)
        }
      } catch (error) {
        console.error(`测试主题 ${config.trending} 失败:`, error)
        
        // 检查是否是 API rate limit exceeded 错误
        if (error.isRateLimit || error.message === 'API rate limit exceeded') {
          console.log(`⚠️ 主题 ${config.trending} 遇到 API rate limit exceeded，记录到失败列表`)
          // 记录到当前轮次的失败主题列表
          if (!currentRoundFailedTopics.find(c => c.id === config.id)) {
            currentRoundFailedTopics.push(config)
          }
        }
        // 继续测试下一个
      }
      
      // 每个主题之间间隔5秒钟
      if (testedCount < shuffled.length && foundCount < targetCount) {
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
    }
    
    // 更新失败主题列表
    if (useFailedTopics) {
      // 如果是从失败列表获取，则更新为当前轮次失败的主题
      failedTopics.value = currentRoundFailedTopics
      console.log(`更新失败主题列表，当前有 ${failedTopics.value.length} 个失败主题`)
    } else {
      // 如果是随机获取，则添加当前轮次失败的主题到列表
      currentRoundFailedTopics.forEach(config => {
        if (!failedTopics.value.find(c => c.id === config.id)) {
          failedTopics.value.push(config)
        }
      })
      console.log(`当前轮次有 ${currentRoundFailedTopics.length} 个失败主题，总失败主题数: ${failedTopics.value.length}`)
    }
    
    // 显示最终结果
    if (foundCount > 0) {
      showToast(`✅ 成功获取 ${foundCount}/${targetCount} 个可用主题`, 'success')
    } else {
      showToast(`测试了所有 ${testedCount} 个主题，未找到满足对冲条件的主题`, 'warning')
    }
    
    if (currentRoundFailedTopics.length > 0) {
      showToast(`⚠️ 本轮有 ${currentRoundFailedTopics.length} 个主题因 API rate limit 失败，已记录`, 'warning')
    }
    
  } catch (error) {
    console.error('随机获取主题失败:', error)
    showToast(`获取失败: ${error.message}`, 'error')
  } finally {
    isRandomGetting.value = false
  }
}

/**
 * 打开配置任务
 */
const openConfigTask = async (config) => {
  try {
    // 1. 更新服务器配置，将isOpen设为1
    const updateData = {
      list: [{
        id: config.id,
        trending: config.trending,
        trendingPart1: config.trendingPart1,
        trendingPart2: config.trendingPart2,
        trendingPart3: config.trendingPart3,
        opUrl: config.opUrl,
        polyUrl: config.polyUrl,
        opTopicId: config.opTopicId,
        weight: config.weight,
        isOpen: 1  // 打开任务
      }]
    }
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/exchangeConfig',
      updateData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log(`配置 ${config.id} 已打开`)
      
      // 2. 更新本地显示状态（只更新这一个主题，不影响其他主题）
      try {
        const visibleData = JSON.parse(localStorage.getItem(CONFIG_VISIBLE_KEY) || '{}')
        visibleData[config.id] = true
        localStorage.setItem(CONFIG_VISIBLE_KEY, JSON.stringify(visibleData))
        console.log(`主题 ${config.id} 的显示状态已设置为 true`)
      } catch (e) {
        console.error('更新显示状态失败:', e)
      }
      
      // 3. 更新本地配置列表中这个配置的状态（避免重新加载所有配置）
      let configInList = configList.value.find(c => c.id === config.id)
      if (configInList) {
        configInList.isOpen = 1
        configInList.enabled = true
      } else {
        // 如果本地列表中没有这个配置（例如随机获取的新主题），添加到列表
        configList.value.push({
          ...config,
          isOpen: 1,
          enabled: true
        })
      }
      
      // 4. 更新活动配置列表
      updateActiveConfigs()
      
      showToast(`主题"${config.trending}"已打开`, 'success')
    }
  } catch (error) {
    console.error('打开任务失败:', error)
    showToast(`打开任务失败: ${error.message}`, 'error')
  }
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
 * 获取链上余额
 */
const getOnChainBalance = async (fingerprintNo, title, psSide) => {
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
}

/**
 * 加载当前页的任务状态
 */
const loadCurrentPageTaskStatus = async () => {
  const start = (allHedgeLogsCurrentPage.value - 1) * allHedgeLogsPageSize.value
  const end = start + allHedgeLogsPageSize.value
  const currentPageLogs = allHedgeLogs.value.slice(start, end)
  
  // 先初始化链上余额字段，显示"加载中..."
  currentPageLogs.forEach((log, pageIndex) => {
    const actualIndex = start + pageIndex
    if (log.yesNumber && log.trendingName && allHedgeLogs.value[actualIndex].yesOnChainBalance === undefined) {
      allHedgeLogs.value[actualIndex].yesOnChainBalance = '' // 空字符串表示加载中
    }
    if (log.noNumber && log.trendingName && allHedgeLogs.value[actualIndex].noOnChainBalance === undefined) {
      allHedgeLogs.value[actualIndex].noOnChainBalance = '' // 空字符串表示加载中
    }
  })
  
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
    
    // 模式2：获取所有任务的详情
    if (log.isMode2) {
      // 更新YES任务
      if (log.yesTasks && log.yesTasks.length > 0) {
        for (let i = 0; i < log.yesTasks.length; i++) {
          const task = log.yesTasks[i]
          if (task.taskId) {
            try {
              const taskData = await fetchMissionStatus(task.taskId)
              if (taskData) {
                allHedgeLogs.value[actualIndex].yesTasks[i].status = taskData.status
                allHedgeLogs.value[actualIndex].yesTasks[i].msg = taskData.msg || ''
              }
            } catch (e) {
              console.error(`获取YES任务 ${task.taskId} 详情失败:`, e)
            }
          }
        }
      }
      
      // 更新NO任务
      if (log.noTasks && log.noTasks.length > 0) {
        for (let i = 0; i < log.noTasks.length; i++) {
          const task = log.noTasks[i]
          if (task.taskId) {
            try {
              const taskData = await fetchMissionStatus(task.taskId)
              if (taskData) {
                allHedgeLogs.value[actualIndex].noTasks[i].status = taskData.status
                allHedgeLogs.value[actualIndex].noTasks[i].msg = taskData.msg || ''
              }
            } catch (e) {
              console.error(`获取NO任务 ${task.taskId} 详情失败:`, e)
            }
          }
        }
      }
      
      // 重新判断整组任务是否成功（使用新的判断逻辑）
      const allTasks = [...(allHedgeLogs.value[actualIndex].yesTasks || []), ...(allHedgeLogs.value[actualIndex].noTasks || [])]
      if (allTasks.length > 0) {
        const allSuccess = allTasks.every(t => isTaskSuccess(t.status, t.msg))
        if (allSuccess) {
          allHedgeLogs.value[actualIndex].finalStatus = 'success'
        }
      }
    } else {
      // 模式1：重新判断整组任务是否成功（使用新的判断逻辑）
      const yesSuccess = allHedgeLogs.value[actualIndex].yesStatus === 2 || isTaskSuccess(allHedgeLogs.value[actualIndex].yesStatus, allHedgeLogs.value[actualIndex].yesTaskMsg)
      const noSuccess = allHedgeLogs.value[actualIndex].noStatus === 2 || isTaskSuccess(allHedgeLogs.value[actualIndex].noStatus, allHedgeLogs.value[actualIndex].noTaskMsg)
      if (yesSuccess && noSuccess) {
        allHedgeLogs.value[actualIndex].finalStatus = 'success'
      }
    }
    
    // 获取YES任务的链上余额
    if (log.yesNumber && log.trendingName) {
      try {
        const yesBalance = await getOnChainBalance(log.yesNumber, log.trendingName, 1) // YES 的 psSide 是 1
        allHedgeLogs.value[actualIndex].yesOnChainBalance = yesBalance
      } catch (e) {
        console.error(`获取YES任务链上余额失败:`, e)
        allHedgeLogs.value[actualIndex].yesOnChainBalance = '获取失败'
      }
    }
    
    // 获取NO任务的链上余额
    if (log.noNumber && log.trendingName) {
      try {
        const noBalance = await getOnChainBalance(log.noNumber, log.trendingName, 2) // NO 的 psSide 是 2
        allHedgeLogs.value[actualIndex].noOnChainBalance = noBalance
      } catch (e) {
        console.error(`获取NO任务链上余额失败:`, e)
        allHedgeLogs.value[actualIndex].noOnChainBalance = '获取失败'
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
 * 检查是否正在获取服务器数据
 */
const isFetchingServerData = (log) => {
  return fetchingServerDataLogs.value.has(log.id)
}

/**
 * 获取服务器数据
 */
const fetchServerData = async (log) => {
  console.log('fetchServerData', log)
  if (isFetchingServerData(log)) {
    return
  }
  
  // 确定先挂方和后挂方的number参数
  let firstSideNumber = null  // 先挂方的number
  let secondSideNumber = null  // 后挂方的number
  
  if (!log.isMode2) {
    // 模式1：根据firstSide确定先挂方和后挂方
    if (log.firstSide === 'YES') {
      firstSideNumber = log.yesNumber
      secondSideNumber = log.noNumber
    } else if (log.firstSide === 'NO') {
      firstSideNumber = log.noNumber
      secondSideNumber = log.yesNumber
    } else {
      // 如果无法确定，使用可用的number
      firstSideNumber = log.yesNumber || log.noNumber
      secondSideNumber = log.yesNumber && log.noNumber ? 
        (firstSideNumber === log.yesNumber ? log.noNumber : log.yesNumber) : null
    }
  } else {
    // 模式2：使用第一个任务的number
    if (log.firstSide === 'YES') {
      if (log.yesTasks && log.yesTasks.length > 0) {
        firstSideNumber = log.yesTasks[0].number
      } else if (log.yesList && log.yesList.length > 0) {
        firstSideNumber = log.yesList[0].number
      }
      if (log.noTasks && log.noTasks.length > 0) {
        secondSideNumber = log.noTasks[0].number
      } else if (log.noList && log.noList.length > 0) {
        secondSideNumber = log.noList[0].number
      }
    } else if (log.firstSide === 'NO') {
      if (log.noTasks && log.noTasks.length > 0) {
        firstSideNumber = log.noTasks[0].number
      } else if (log.noList && log.noList.length > 0) {
        firstSideNumber = log.noList[0].number
      }
      if (log.yesTasks && log.yesTasks.length > 0) {
        secondSideNumber = log.yesTasks[0].number
      } else if (log.yesList && log.yesList.length > 0) {
        secondSideNumber = log.yesList[0].number
      }
    }
  }
  
  if (!firstSideNumber) {
    showToast('无法获取先挂方浏览器编号', 'error')
    return
  }
  
  // 确定side参数：1=开仓（买入），2=平仓（卖出）
  const side = log.side || (log.isClose ? 2 : 1)
  
  // 确定价格：先挂方使用log.price，后挂方使用100-log.price，保留两位小数并四舍五入
  const firstSidePrice = Math.round(parseFloat(log.price) * 100) / 100
  const secondSidePrice = Math.round((100 - parseFloat(log.price)) * 100) / 100
  
  // 标记为正在获取
  fetchingServerDataLogs.value.add(log.id)
  
  try {
    // 获取任务的updateTime（用于time字段）
    let firstSideTime = null
    let secondSideTime = null
    
    // 获取先挂方任务的updateTime
    if (!log.isMode2) {
      // 模式1：根据firstSide确定任务ID
      let firstSideTaskId = null
      if (log.firstSide === 'YES') {
        firstSideTaskId = log.yesTaskId
      } else if (log.firstSide === 'NO') {
        firstSideTaskId = log.noTaskId
      }
      
      if (firstSideTaskId) {
        try {
          const taskData = await fetchMissionStatus(firstSideTaskId)
          if (taskData && taskData.updateTime) {
            firstSideTime = new Date(taskData.updateTime).getTime()
          }
        } catch (e) {
          console.error(`获取先挂方任务 ${firstSideTaskId} 详情失败:`, e)
        }
      }
      
      // 获取后挂方任务的updateTime
      let secondSideTaskId = null
      if (log.firstSide === 'YES') {
        secondSideTaskId = log.noTaskId
      } else if (log.firstSide === 'NO') {
        secondSideTaskId = log.yesTaskId
      }
      
      if (secondSideTaskId) {
        try {
          const taskData = await fetchMissionStatus(secondSideTaskId)
          if (taskData && taskData.updateTime) {
            secondSideTime = new Date(taskData.updateTime).getTime()
          }
        } catch (e) {
          console.error(`获取后挂方任务 ${secondSideTaskId} 详情失败:`, e)
        }
      }
    } else {
      // 模式2：从任务列表中获取updateTime
      if (log.firstSide === 'YES') {
        if (log.yesTasks && log.yesTasks.length > 0 && log.yesTasks[0].taskId) {
          try {
            const taskData = await fetchMissionStatus(log.yesTasks[0].taskId)
            if (taskData && taskData.updateTime) {
              firstSideTime = new Date(taskData.updateTime).getTime()
            }
          } catch (e) {
            console.error(`获取先挂方任务 ${log.yesTasks[0].taskId} 详情失败:`, e)
          }
        }
        if (log.noTasks && log.noTasks.length > 0 && log.noTasks[0].taskId) {
          try {
            const taskData = await fetchMissionStatus(log.noTasks[0].taskId)
            if (taskData && taskData.updateTime) {
              secondSideTime = new Date(taskData.updateTime).getTime()
            }
          } catch (e) {
            console.error(`获取后挂方任务 ${log.noTasks[0].taskId} 详情失败:`, e)
          }
        }
      } else if (log.firstSide === 'NO') {
        if (log.noTasks && log.noTasks.length > 0 && log.noTasks[0].taskId) {
          try {
            const taskData = await fetchMissionStatus(log.noTasks[0].taskId)
            if (taskData && taskData.updateTime) {
              firstSideTime = new Date(taskData.updateTime).getTime()
            }
          } catch (e) {
            console.error(`获取先挂方任务 ${log.noTasks[0].taskId} 详情失败:`, e)
          }
        }
        if (log.yesTasks && log.yesTasks.length > 0 && log.yesTasks[0].taskId) {
          try {
            const taskData = await fetchMissionStatus(log.yesTasks[0].taskId)
            if (taskData && taskData.updateTime) {
              secondSideTime = new Date(taskData.updateTime).getTime()
            }
          } catch (e) {
            console.error(`获取后挂方任务 ${log.yesTasks[0].taskId} 详情失败:`, e)
          }
        }
      }
    }
    
    // 构建先挂方请求数据
    const firstSideRequestData = {
      number: firstSideNumber,
      trending: log.trendingName,
      side: side == 1 ? "buy":"sell",
      price: firstSidePrice,
      amt: log.share
    }
    
    // 如果有time，添加到请求数据中
    if (firstSideTime) {
      firstSideRequestData.time = firstSideTime
    }
    
    // 发送先挂方请求
    const firstSidePromise = axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/filterOrder',
      firstSideRequestData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    // 构建请求数组
    const requests = [firstSidePromise]
    
    // 如果有后挂方，也发送请求
    if (secondSideNumber) {
      const secondSideRequestData = {
        number: secondSideNumber,
        trending: log.trendingName,
        side: side == 1 ? "buy":"sell",
        price: secondSidePrice,
        amt: log.share
      }
      
      // 如果有time，添加到请求数据中
      if (secondSideTime) {
        secondSideRequestData.time = secondSideTime
      }
      
      const secondSidePromise = axios.post(
        'https://sg.bicoin.com.cn/99l/hedge/filterOrder',
        secondSideRequestData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )
      
      requests.push(secondSidePromise)
    }
    
    // 并行发送所有请求
    const responses = await Promise.all(requests)
    
    console.log('获取服务器数据成功:', responses)
    showToast(`获取服务器数据成功（${responses.length}个请求）`, 'success')
    
    // 处理返回的数据并存储到log对象中
    responses.forEach((response, index) => {
      if (response.data && response.data.code === 0 && response.data.data) {
        const requestNumber = index === 0 ? firstSideNumber : secondSideNumber
        const serverData = response.data.data.hist || {}
        
        if (!log.isMode2) {
          // 模式1：根据number匹配到YES或NO
          if (requestNumber === log.yesNumber) {
            log.yesServerData = serverData
          } else if (requestNumber === log.noNumber) {
            log.noServerData = serverData
          }
        } else {
          // 模式2：根据number匹配到对应的任务
          // 查找YES任务
          if (log.yesTasks && log.yesTasks.length > 0) {
            const yesTask = log.yesTasks.find(task => task.number === requestNumber)
            if (yesTask) {
              yesTask.serverData = serverData
            }
          }
          // 查找NO任务
          if (log.noTasks && log.noTasks.length > 0) {
            const noTask = log.noTasks.find(task => task.number === requestNumber)
            if (noTask) {
              noTask.serverData = serverData
            }
          }
        }
        
        // 保存到localStorage
        saveHedgeLogToStorage(log)
      }
    })
  } catch (error) {
    console.error('获取服务器数据失败:', error)
    showToast('获取服务器数据失败: ' + (error.response?.data?.message || error.message), 'error')
  } finally {
    // 移除标记
    fetchingServerDataLogs.value.delete(log.id)
  }
}

/**
 * 将时间戳或时间字符串转换为北京时间
 */
const timestampToBeijingTime = (timestamp, isDifferentTimezone = false) => {
  if (!timestamp) return '-'
  try {
    let date
    if (typeof timestamp === 'string') {
      // 尝试解析字符串时间（如 "Jan 07, 2026 09:46:17"）
      date = new Date(timestamp)
    } else {
      // 如果是数字时间戳
      date = new Date(timestamp)
    }
    
    // 如果标记为不同时区，需要转换（假设原时间是UTC或其他时区）
    // 否则直接使用本地时间
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
}

/**
 * 格式化side值（1=买，2=卖）
 */
const formatSide = (side) => {
  if (side === 1 || side === '1') return '买'
  if (side === 2 || side === '2') return '卖'
  if (side === 'BUY' || side === 'buy') return '买'
  if (side === 'SELL' || side === 'sell') return '卖'
  return side
}

/**
 * 格式化挂单数据为字符串
 */
const formatOpenOrderMsg = (order) => {
  const time = timestampToBeijingTime(order.ctime)
  const side = formatSide(order.side)
  const progress = ((order.amt - order.restAmt) / order.amt * 100).toFixed(2)
  return `创建时间: ${time} | 方向: ${side} | 结果: ${order.outCome} | 价格: ${order.price} | 进度: ${progress}% (${(order.amt - order.restAmt).toFixed(2)}/${order.amt})`
}

/**
 * 格式化已成交数据为字符串
 */
const formatClosedOrderMsg = (order) => {
  const time = order.convertTime ? timestampToBeijingTime(order.convertTime) : timestampToBeijingTime(order.time, true)
  const timezoneNote = !order.convertTime ? ' (不同时区)' : ''
  const side = formatSide(order.side)
  const progress = ((order.fillAmt / order.amt) * 100).toFixed(2)
  return `时间: ${time}${timezoneNote} | 方向: ${side} | 结果: ${order.outCome} | 价格: ${order.price} | 进度: ${progress}% (${order.fillAmt}/${order.amt}) | 状态: ${order.status}`
}

/**
 * 保存任务状态为成功
 */
const saveTaskAsSuccess = async (log, taskId, msg, taskType = 'single') => {
  if (!taskId) {
    showToast('任务ID不存在', 'error')
    return
  }
  
  try {
    // 调用API保存任务状态
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/mission/saveResult',
      {
        id: taskId,
        status: 2,
        msg: msg
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.code === 0) {
      // 更新本地记录
      if (!log.isMode2) {
        // 模式1：更新对应的任务状态
        if (taskType === 'yes') {
          log.yesStatus = 2
          log.yesTaskMsg = msg
        } else if (taskType === 'no') {
          log.noStatus = 2
          log.noTaskMsg = msg
        }
        
        // 检查是否两个任务都成功（使用新的判断逻辑）
        const yesSuccess = log.yesStatus === 2 || isTaskSuccess(log.yesStatus, log.yesTaskMsg)
        const noSuccess = log.noStatus === 2 || isTaskSuccess(log.noStatus, log.noTaskMsg)
        if (yesSuccess && noSuccess) {
          log.finalStatus = 'success'
        }
      } else {
        // 模式2：更新对应任务的状态
        let taskUpdated = false
        
        // 更新YES任务
        if (log.yesTasks && log.yesTasks.length > 0) {
          const yesTask = log.yesTasks.find(t => String(t.taskId) === String(taskId))
          if (yesTask) {
            yesTask.status = 2
            yesTask.msg = msg
            taskUpdated = true
          }
        }
        
        // 更新NO任务
        if (log.noTasks && log.noTasks.length > 0) {
          const noTask = log.noTasks.find(t => String(t.taskId) === String(taskId))
          if (noTask) {
            noTask.status = 2
            noTask.msg = msg
            taskUpdated = true
          }
        }
        
        // 检查所有任务是否都成功（使用新的判断逻辑）
        if (taskUpdated) {
          const yesTasks = log.yesTasks || []
          const noTasks = log.noTasks || []
          const allTasks = [...yesTasks, ...noTasks]
          
          // 检查是否所有任务都成功（使用新的判断逻辑）
          if (allTasks.length > 0) {
            const allSuccess = allTasks.every(t => isTaskSuccess(t.status, t.msg))
            if (allSuccess) {
              log.finalStatus = 'success'
            }
          }
        }
      }
      
      // 保存到localStorage
      saveHedgeLogToStorage(log)
      
      // 更新allHedgeLogs中的记录
      const index = allHedgeLogs.value.findIndex(l => l.id === log.id)
      if (index !== -1) {
        // 使用深拷贝确保响应式更新
        allHedgeLogs.value[index] = JSON.parse(JSON.stringify(log))
      }
      
      showToast('任务状态已保存为成功', 'success')
    } else {
      showToast('保存任务状态失败: ' + (response.data?.msg || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('保存任务状态失败:', error)
    showToast('保存任务状态失败: ' + (error.response?.data?.message || error.message), 'error')
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
 * 格式化毫秒时间戳为北京时间
 */
const formatBeijingTime = (timestamp) => {
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
}

/**
 * 打开浏览器日志弹窗
 */
const openBroLogDialog = async (number) => {
  if (!number) return
  currentBroNumber.value = number
  showBroLogDialog.value = true
  broLogs.value = []
  await fetchBroLogs(number)
}

/**
 * 获取浏览器日志
 */
const fetchBroLogs = async (number) => {
  if (!number) return
  isLoadingBroLogs.value = true
  try {
    const response = await axios.get('https://sg.bicoin.com.cn/99l/bro/getBroLog', {
      params: {
        number: number,
        size: 1000
      }
    })
    if (response.data?.code === 0 && response.data?.data?.list) {
      broLogs.value = response.data.data.list
    } else {
      console.error('获取浏览器日志失败:', response.data)
      broLogs.value = []
    }
  } catch (error) {
    console.error('获取浏览器日志失败:', error)
    broLogs.value = []
  } finally {
    isLoadingBroLogs.value = false
  }
}

/**
 * 关闭浏览器日志弹窗
 */
const closeBroLogDialog = () => {
  showBroLogDialog.value = false
  broLogs.value = []
  currentBroNumber.value = null
}

/**
 * 保存对冲设置到本地
 */
const saveHedgeSettings = () => {
  try {
    localStorage.setItem(HEDGE_SETTINGS_KEY, JSON.stringify({
      // 对冲模式基本设置
      isClose: hedgeMode.isClose,
      timePassMin: hedgeMode.timePassMin,
      minCloseMin: hedgeMode.minCloseMin,
      intervalType: hedgeMode.intervalType,
      intervalDelay: hedgeMode.intervalDelay,
      maxDepth: hedgeMode.maxDepth,
      minUAmt: hedgeMode.minUAmt,
      maxUAmt: hedgeMode.maxUAmt,
      minCloseAmt: hedgeMode.minCloseAmt,
      minTotalCloseAmt: hedgeMode.minTotalCloseAmt,
      maxTotalCloseAmt: hedgeMode.maxTotalCloseAmt,
      takerMinAmt: hedgeMode.takerMinAmt,
      hedgeMode: hedgeMode.hedgeMode,
      maxOpenHour: hedgeMode.maxOpenHour,
      closeOpenHourArea: hedgeMode.closeOpenHourArea,
      // 订单薄相关设置
      minOrderbookDepth: hedgeMode.minOrderbookDepth,
      maxPriceDiff: hedgeMode.maxPriceDiff,
      priceRangeMin: hedgeMode.priceRangeMin,
      priceRangeMax: hedgeMode.priceRangeMax,
      minTotalDepth: hedgeMode.minTotalDepth,
      maxIpDelay: hedgeMode.maxIpDelay,
      needJudgeDF: hedgeMode.needJudgeDF,
      maxDHour: hedgeMode.maxDHour,
      needJudgeTimeRandom: hedgeMode.needJudgeTimeRandom,
      // 资产优先级校验设置
      needJudgeBalancePriority: hedgeMode.needJudgeBalancePriority,
      balancePriority: hedgeMode.balancePriority,
      // 其他设置
      hedgeTasksPerTopic: hedgeTasksPerTopic.value,
      hedgeMaxTasksPerRound: hedgeMaxTasksPerRound.value,
      hedgeTaskInterval: hedgeTaskInterval.value,
      randomGetCount: randomGetCount.value,
      enableBatchMode: enableBatchMode.value,
      batchSize: batchSize.value,
      batchExecutionTime: batchExecutionTime.value,
      // 任务个数阈值和等待时间设置
      taskCountThreshold: hedgeMode.taskCountThreshold,
      waitTimeLessThanThreshold: hedgeMode.waitTimeLessThanThreshold,
      waitTimeGreaterThanThreshold: hedgeMode.waitTimeGreaterThanThreshold,
      // 订单薄更新设置
      yesPositionThreshold: hedgeMode.yesPositionThreshold,
      yesPositionCompareType: hedgeMode.yesPositionCompareType,
      maxVolume24hOpen: hedgeMode.maxVolume24hOpen,
      maxVolume7dAvgOpen: hedgeMode.maxVolume7dAvgOpen,
      maxPosWorthOpen: hedgeMode.maxPosWorthOpen,
      orderbookMismatchInterval: hedgeMode.orderbookMismatchInterval,
      weightedTimeHourOpen: hedgeMode.weightedTimeHourOpen,
      weightedTimeCompareType: hedgeMode.weightedTimeCompareType,
      weightedTimeYesPositionThreshold: hedgeMode.weightedTimeYesPositionThreshold,
      weightedTimeYesPositionCompareType: hedgeMode.weightedTimeYesPositionCompareType,
      // 模式一开仓专属设置
      posPriorityArea: hedgeMode.posPriorityArea,
      maxPosLimit: hedgeMode.maxPosLimit,
      // 深度差相关设置
      // 深度差阈值配置
      depthThreshold1: hedgeMode.depthThreshold1,
      depthThreshold2: hedgeMode.depthThreshold2,
      depthThreshold3: hedgeMode.depthThreshold3,
      // 各深度区间延时检测时间
      delayTimeGt15: hedgeMode.delayTimeGt15,
      delayTime2To15: hedgeMode.delayTime2To15,
      delayTime02To2: hedgeMode.delayTime02To2,
      maxEatValue01: hedgeMode.maxEatValue01,
      // 各深度区间开关
      enableDepthDiffParamsGt15: hedgeMode.enableDepthDiffParamsGt15,
      enableDepthDiffParams2To15: hedgeMode.enableDepthDiffParams2To15,
      enableDepthDiffParams02To2: hedgeMode.enableDepthDiffParams02To2,
      enableDepthDiffParams01: hedgeMode.enableDepthDiffParams01,
      // 各深度区间价格波动配置
      priceVolatilityGt15Min: hedgeMode.priceVolatilityGt15Min,
      priceVolatilityGt15Max: hedgeMode.priceVolatilityGt15Max,
      priceVolatility2To15Min: hedgeMode.priceVolatility2To15Min,
      priceVolatility2To15Max: hedgeMode.priceVolatility2To15Max,
      priceVolatility02To2Min: hedgeMode.priceVolatility02To2Min,
      priceVolatility02To2Max: hedgeMode.priceVolatility02To2Max,
      // 兼容旧配置（保留但不使用）
      maxPriceVolatility: hedgeMode.maxPriceVolatility,
      // 总任务数控制设置
      totalTaskCountOperator: hedgeMode.totalTaskCountOperator,
      totalTaskCountThreshold: hedgeMode.totalTaskCountThreshold,
      // 挂单超时撤单设置
      openOrderCancelHours: hedgeMode.openOrderCancelHours,
      // yes数量大于、模式选择、账户选择
      yesCountThreshold: yesCountThreshold.value,
      isFastMode: isFastMode.value,
      selectedNumberType: selectedNumberType.value
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
    
    // 对冲模式基本设置
    if (settings.isClose !== undefined) {
      hedgeMode.isClose = settings.isClose
    }
    if (settings.timePassMin !== undefined) {
      hedgeMode.timePassMin = settings.timePassMin
    }
    if (settings.minCloseMin !== undefined) {
      hedgeMode.minCloseMin = settings.minCloseMin
    }
    if (settings.intervalType !== undefined) {
      hedgeMode.intervalType = settings.intervalType
    }
    if (settings.intervalDelay !== undefined) {
      hedgeMode.intervalDelay = settings.intervalDelay
    }
    if (settings.maxDepth !== undefined) {
      hedgeMode.maxDepth = settings.maxDepth
    }
    if (settings.minUAmt !== undefined) {
      hedgeMode.minUAmt = settings.minUAmt
    }
    if (settings.maxUAmt !== undefined) {
      hedgeMode.maxUAmt = settings.maxUAmt
    }
    if (settings.minCloseAmt !== undefined) {
      hedgeMode.minCloseAmt = settings.minCloseAmt
    }
    if (settings.minTotalCloseAmt !== undefined) {
      hedgeMode.minTotalCloseAmt = settings.minTotalCloseAmt
    }
    if (settings.maxTotalCloseAmt !== undefined) {
      hedgeMode.maxTotalCloseAmt = settings.maxTotalCloseAmt
    }
    if (settings.takerMinAmt !== undefined) {
      hedgeMode.takerMinAmt = settings.takerMinAmt
    }
    if (settings.hedgeMode !== undefined) {
      hedgeMode.hedgeMode = settings.hedgeMode
    } else if (settings.hedgeMode2 !== undefined) {
      // 兼容旧版本：将 boolean 转换为 number
      hedgeMode.hedgeMode = settings.hedgeMode2 ? 2 : 1
    }
    if (settings.maxOpenHour !== undefined) {
      hedgeMode.maxOpenHour = settings.maxOpenHour
    }
    if (settings.closeOpenHourArea !== undefined) {
      hedgeMode.closeOpenHourArea = settings.closeOpenHourArea
    }
    
    // 订单薄相关设置
    if (settings.minOrderbookDepth !== undefined) {
      hedgeMode.minOrderbookDepth = settings.minOrderbookDepth
    }
    if (settings.maxPriceDiff !== undefined) {
      hedgeMode.maxPriceDiff = settings.maxPriceDiff
    }
    if (settings.priceRangeMin !== undefined) {
      hedgeMode.priceRangeMin = settings.priceRangeMin
    }
    if (settings.priceRangeMax !== undefined) {
      hedgeMode.priceRangeMax = settings.priceRangeMax
    }
    if (settings.minTotalDepth !== undefined) {
      hedgeMode.minTotalDepth = settings.minTotalDepth
    }
    if (settings.maxIpDelay !== undefined) {
      hedgeMode.maxIpDelay = settings.maxIpDelay
    }
    if (settings.needJudgeDF !== undefined) {
      hedgeMode.needJudgeDF = settings.needJudgeDF
    }
    if (settings.maxDHour !== undefined) {
      hedgeMode.maxDHour = settings.maxDHour
    }
    if (settings.needJudgeTimeRandom !== undefined) {
      hedgeMode.needJudgeTimeRandom = settings.needJudgeTimeRandom
    }
    
    // 资产优先级校验设置
    if (settings.needJudgeBalancePriority !== undefined) {
      hedgeMode.needJudgeBalancePriority = settings.needJudgeBalancePriority
    }
    if (settings.balancePriority !== undefined) {
      hedgeMode.balancePriority = settings.balancePriority
    }
    
    // 其他设置
    if (settings.hedgeTasksPerTopic !== undefined) {
      hedgeTasksPerTopic.value = settings.hedgeTasksPerTopic
    }
    if (settings.hedgeMaxTasksPerRound !== undefined) {
      hedgeMaxTasksPerRound.value = settings.hedgeMaxTasksPerRound
    }
    if (settings.hedgeTaskInterval !== undefined) {
      hedgeTaskInterval.value = settings.hedgeTaskInterval
    }
    if (settings.randomGetCount !== undefined) {
      randomGetCount.value = settings.randomGetCount
    }
    if (settings.enableBatchMode !== undefined) {
      enableBatchMode.value = settings.enableBatchMode
    }
    if (settings.batchSize !== undefined) {
      batchSize.value = settings.batchSize
    }
    if (settings.batchExecutionTime !== undefined) {
      batchExecutionTime.value = settings.batchExecutionTime
    }
    
    // 任务个数阈值和等待时间设置
    if (settings.taskCountThreshold !== undefined) {
      hedgeMode.taskCountThreshold = settings.taskCountThreshold
    }
    if (settings.waitTimeLessThanThreshold !== undefined) {
      hedgeMode.waitTimeLessThanThreshold = settings.waitTimeLessThanThreshold
    }
    if (settings.waitTimeGreaterThanThreshold !== undefined) {
      hedgeMode.waitTimeGreaterThanThreshold = settings.waitTimeGreaterThanThreshold
    }
    
    // 订单薄更新设置
    if (settings.yesPositionThreshold !== undefined) {
      hedgeMode.yesPositionThreshold = settings.yesPositionThreshold
    } else if (settings.minPositionForClose !== undefined) {
      // 向后兼容：如果存在旧字段，使用旧字段值
      hedgeMode.yesPositionThreshold = settings.minPositionForClose
      hedgeMode.yesPositionCompareType = 'less'
    }
    if (settings.yesPositionCompareType !== undefined) {
      hedgeMode.yesPositionCompareType = settings.yesPositionCompareType
    }
    // 优先使用新字段名，如果没有则使用旧字段名（向后兼容）
    if (settings.maxVolume24hOpen !== undefined) {
      hedgeMode.maxVolume24hOpen = settings.maxVolume24hOpen
    } else if (settings.maxVolume24h !== undefined) {位价值大于
      hedgeMode.maxVolume24hOpen = settings.maxVolume24h
    }
    if (settings.maxVolume7dAvgOpen !== undefined) {
      hedgeMode.maxVolume7dAvgOpen = settings.maxVolume7dAvgOpen
    } else if (settings.maxVolume7dAvg !== undefined) {
      hedgeMode.maxVolume7dAvgOpen = settings.maxVolume7dAvg
    }
    if (settings.maxPosWorthOpen !== undefined) {
      hedgeMode.maxPosWorthOpen = settings.maxPosWorthOpen
    }
    if (settings.orderbookMismatchInterval !== undefined) {
      hedgeMode.orderbookMismatchInterval = settings.orderbookMismatchInterval
    }
    if (settings.weightedTimeHourOpen !== undefined) {
      hedgeMode.weightedTimeHourOpen = settings.weightedTimeHourOpen
    } else if (settings.maxWeightedTimeHourOpen !== undefined) {
      // 向后兼容：如果存在旧字段，使用旧字段值
      hedgeMode.weightedTimeHourOpen = settings.maxWeightedTimeHourOpen
      hedgeMode.weightedTimeCompareType = 'greater'
    }
    if (settings.weightedTimeCompareType !== undefined) {
      hedgeMode.weightedTimeCompareType = settings.weightedTimeCompareType
    }
    if (settings.weightedTimeYesPositionThreshold !== undefined) {
      hedgeMode.weightedTimeYesPositionThreshold = settings.weightedTimeYesPositionThreshold
    }
    if (settings.weightedTimeYesPositionCompareType !== undefined) {
      hedgeMode.weightedTimeYesPositionCompareType = settings.weightedTimeYesPositionCompareType
    }
    
    // 模式一开仓专属设置
    if (settings.posPriorityArea !== undefined) {
      hedgeMode.posPriorityArea = settings.posPriorityArea
    }
    if (settings.maxPosLimit !== undefined) {
      hedgeMode.maxPosLimit = settings.maxPosLimit
    }
    
    // 深度差相关设置
    // 深度差阈值配置
    if (settings.depthThreshold1 !== undefined) {
      hedgeMode.depthThreshold1 = settings.depthThreshold1
    }
    if (settings.depthThreshold2 !== undefined) {
      hedgeMode.depthThreshold2 = settings.depthThreshold2
    }
    if (settings.depthThreshold3 !== undefined) {
      hedgeMode.depthThreshold3 = settings.depthThreshold3
    }
    // 各深度区间延时检测时间
    if (settings.delayTimeGt15 !== undefined) {
      hedgeMode.delayTimeGt15 = settings.delayTimeGt15
    }
    if (settings.delayTime2To15 !== undefined) {
      hedgeMode.delayTime2To15 = settings.delayTime2To15
    }
    if (settings.delayTime02To2 !== undefined) {
      hedgeMode.delayTime02To2 = settings.delayTime02To2
    }
    if (settings.maxEatValue01 !== undefined) {
      hedgeMode.maxEatValue01 = settings.maxEatValue01
    }
    // 各深度区间开关
    if (settings.enableDepthDiffParamsGt15 !== undefined) {
      hedgeMode.enableDepthDiffParamsGt15 = settings.enableDepthDiffParamsGt15
    }
    if (settings.enableDepthDiffParams2To15 !== undefined) {
      hedgeMode.enableDepthDiffParams2To15 = settings.enableDepthDiffParams2To15
    }
    if (settings.enableDepthDiffParams02To2 !== undefined) {
      hedgeMode.enableDepthDiffParams02To2 = settings.enableDepthDiffParams02To2
    }
    if (settings.enableDepthDiffParams01 !== undefined) {
      hedgeMode.enableDepthDiffParams01 = settings.enableDepthDiffParams01
    }
    // 各深度区间价格波动配置
    if (settings.priceVolatilityGt15Min !== undefined) {
      hedgeMode.priceVolatilityGt15Min = settings.priceVolatilityGt15Min
    }
    if (settings.priceVolatilityGt15Max !== undefined) {
      hedgeMode.priceVolatilityGt15Max = settings.priceVolatilityGt15Max
    }
    if (settings.priceVolatility2To15Min !== undefined) {
      hedgeMode.priceVolatility2To15Min = settings.priceVolatility2To15Min
    }
    if (settings.priceVolatility2To15Max !== undefined) {
      hedgeMode.priceVolatility2To15Max = settings.priceVolatility2To15Max
    }
    if (settings.priceVolatility02To2Min !== undefined) {
      hedgeMode.priceVolatility02To2Min = settings.priceVolatility02To2Min
    }
    if (settings.priceVolatility02To2Max !== undefined) {
      hedgeMode.priceVolatility02To2Max = settings.priceVolatility02To2Max
    }
    // 兼容旧配置
    if (settings.maxPriceVolatility !== undefined) {
      hedgeMode.maxPriceVolatility = settings.maxPriceVolatility
    }
    
    // 总任务数控制设置
    if (settings.totalTaskCountOperator !== undefined) {
      hedgeMode.totalTaskCountOperator = settings.totalTaskCountOperator
    }
    if (settings.totalTaskCountThreshold !== undefined) {
      hedgeMode.totalTaskCountThreshold = settings.totalTaskCountThreshold
    }
    // 兼容旧字段名
    if (settings.maxTotalTaskCount !== undefined && settings.totalTaskCountThreshold === undefined) {
      hedgeMode.totalTaskCountThreshold = settings.maxTotalTaskCount
    }
    
    // 挂单超时撤单设置
    if (settings.openOrderCancelHours !== undefined) {
      hedgeMode.openOrderCancelHours = settings.openOrderCancelHours
    }
    
    // yes数量大于、模式选择、账户选择
    if (settings.yesCountThreshold !== undefined) {
      yesCountThreshold.value = settings.yesCountThreshold
    }
    if (settings.isFastMode !== undefined) {
      isFastMode.value = settings.isFastMode
    }
    if (settings.selectedNumberType !== undefined) {
      selectedNumberType.value = settings.selectedNumberType
    }
  } catch (e) {
    console.error('加载对冲设置失败:', e)
  }
}

/**
 * 获取并解析账户持仓数据
 * 从 findAccountConfigCache 接口获取所有账户的持仓信息
 * 解析 a 字段，提取所有持仓的主题名称
 */
const fetchPositionTopics = async () => {
  try {
    console.log('开始获取持仓数据...')
    const response = await axios.get('https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache')
    
    if (response.data && response.data.data) {
      const accounts = response.data.data
      const topics = new Set()
      
      // 遍历所有账户
      accounts.forEach(account => {
        if (account.a && account.a.trim()) {
          // a 字段格式：多个持仓用 ; 分割
          const positions = account.a.split(';')
          
          positions.forEach(position => {
            if (position.trim()) {
              // 每个持仓内部用 ||| 分割，第一个字段是主题名称
              const parts = position.split('|||')
              if (parts.length > 0 && parts[0].trim()) {
                topics.add(parts[0].trim())
              }
            }
          })
        }
      })
      
      positionTopics.value = topics
      console.log(`持仓数据已更新，共 ${topics.size} 个不同的主题`)
      console.log('持仓主题列表:', Array.from(topics))
      
      return topics
    } else {
      console.warn('获取持仓数据失败: 返回数据格式错误')
      return new Set()
    }
  } catch (error) {
    console.error('获取持仓数据失败:', error)
    showToast('获取持仓数据失败', 'error')
    return new Set()
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
  
  // 检查是否有 [x] 开头的 msg，如果 x < 10，显示"失败不用管"
  if (hedge.isMode2) {
    // 模式2：检查所有任务的 msg
    const allTasks = [...(hedge.yesTasks || []), ...(hedge.noTasks || [])]
    for (const task of allTasks) {
      if (task.msg) {
        const bracketNum = extractBracketNumber(task.msg)
        if (bracketNum !== null) {
          return '失败不用管'
        }
      }
    }
  } else {
    // 模式1：检查 yesTaskMsg 和 noTaskMsg
    if (hedge.yesTaskMsg) {
      const bracketNum = extractBracketNumber(hedge.yesTaskMsg)
      if (bracketNum !== null) {
        return '失败不用管'
      }
    }
    if (hedge.noTaskMsg) {
      const bracketNum = extractBracketNumber(hedge.noTaskMsg)
      if (bracketNum !== null) {
        return '失败不用管'
      }
    }
  }
  
  // 优先使用 finalStatus（新版本）
  if (hedge.finalStatus === 'success') return '全部成功'
  if (hedge.finalStatus === 'failed') return '失败'
  if (hedge.finalStatus === 'timeout') return '超时'
  if (hedge.finalStatus === 'running') {
    // 模式2：检查任务状态（使用新的判断逻辑）
    if (hedge.isMode2) {
      const allTasks = [...(hedge.yesTasks || []), ...(hedge.noTasks || [])]
      if (allTasks.length === 0) return '等待提交'
      
      // 使用新的判断逻辑统计成功和失败
      const successCount = allTasks.filter(t => isTaskSuccess(t.status, t.msg)).length
      const failedCount = allTasks.filter(t => !isTaskSuccess(t.status, t.msg) && t.status !== 9 && t.status !== 0 && t.status !== 1).length
      if (successCount > 0 || failedCount > 0) {
        return `进行中 (成功:${successCount}, 失败:${failedCount}, 总计:${allTasks.length})`
      }
      return '进行中'
    }
    return '进行中'
  }
  
  // 兼容旧版本（没有 finalStatus 字段的记录）
  // 使用新的判断逻辑
  const yesSuccess = hedge.yesStatus === 2 || isTaskSuccess(hedge.yesStatus, hedge.yesTaskMsg)
  const noSuccess = hedge.noStatus === 2 || isTaskSuccess(hedge.noStatus, hedge.noTaskMsg)
  
  if (yesSuccess && noSuccess) return '全部成功'
  // 检查是否有 [x] 格式的失败不用管
  const yesBracketNum = extractBracketNumber(hedge.yesTaskMsg)
  const noBracketNum = extractBracketNumber(hedge.noTaskMsg)
  if (yesBracketNum !== null || noBracketNum !== null) {
    return '失败不用管'
  }
  if (hedge.yesStatus === 3 || hedge.noStatus === 3) return '部分失败'
  if (hedge.yesStatus === 9 || hedge.noStatus === 9) return '进行中'
  return '未知'
}

/**
 * 获取对冲状态样式类
 */
const getHedgeStatusClass = (hedge) => {
  if (!hedge) return ''
  
  // 检查是否有 [x] 开头的 msg，如果 x < 10，显示黄色背景
  if (hedge.isMode2) {
    // 模式2：检查所有任务的 msg
    const allTasks = [...(hedge.yesTasks || []), ...(hedge.noTasks || [])]
    for (const task of allTasks) {
      if (task.msg) {
        const bracketNum = extractBracketNumber(task.msg)
        if (bracketNum !== null) {
          return 'hedge-warning'
        }
      }
    }
  } else {
    // 模式1：检查 yesTaskMsg 和 noTaskMsg
    if (hedge.yesTaskMsg) {
      const bracketNum = extractBracketNumber(hedge.yesTaskMsg)
      if (bracketNum !== null) {
        return 'hedge-warning'
      }
    }
    if (hedge.noTaskMsg) {
      const bracketNum = extractBracketNumber(hedge.noTaskMsg)
      if (bracketNum !== null) {
        return 'hedge-warning'
      }
    }
  }
  
  // 优先使用 finalStatus（新版本）
  if (hedge.finalStatus === 'success') return 'hedge-success'
  if (hedge.finalStatus === 'failed') return 'hedge-failed'
  if (hedge.finalStatus === 'running') return 'hedge-running'
  
  // 兼容旧版本（没有 finalStatus 字段的记录）
  // 使用新的判断逻辑
  const yesSuccess = hedge.yesStatus === 2 || isTaskSuccess(hedge.yesStatus, hedge.yesTaskMsg)
  const noSuccess = hedge.noStatus === 2 || isTaskSuccess(hedge.noStatus, hedge.noTaskMsg)
  
  if (yesSuccess && noSuccess) return 'hedge-success'
  // 检查是否有 [x] 格式的失败不用管
  const yesBracketNum = extractBracketNumber(hedge.yesTaskMsg)
  const noBracketNum = extractBracketNumber(hedge.noTaskMsg)
  if (yesBracketNum !== null || noBracketNum !== null) {
    return 'hedge-warning'
  }
  if (hedge.yesStatus === 3 || hedge.noStatus === 3) return 'hedge-failed'
  if (hedge.yesStatus === 9 || hedge.noStatus === 9) return 'hedge-running'
  return ''
}

/**
 * 获取任务状态样式类
 */
const getTaskStatusClass = (status, msg = null) => {
  // 如果传入了 msg，需要根据新的逻辑判断
  if (msg !== null && msg !== undefined) {
    if (isTaskSuccess(status, msg)) {
      return 'task-success'
    }
  }
  
  const classMap = {
    0: 'task-pending',
    2: 'task-success',  // 已完成，绿色
    20: 'task-success',  // 已完成，绿色
    3: 'task-failed',   // 失败，红色
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
 * 将数量保留2位小数并向下取整
 */
const floorToTwoDecimals = (value) => {
  return Math.floor(value * 100) / 100
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
  
  // 获取电脑组ID（直接使用API返回的组号，如果API返回了组号则优先使用，否则使用映射）
  const yesGroupNo = (hedgeData.yesGroup !== undefined && hedgeData.yesGroup !== null && hedgeData.yesGroup !== '') 
    ? String(hedgeData.yesGroup) 
    : (browserToGroupMap.value[hedgeData.yesNumber] || '1')
  const noGroupNo = (hedgeData.noGroup !== undefined && hedgeData.noGroup !== null && hedgeData.noGroup !== '') 
    ? String(hedgeData.noGroup) 
    : (browserToGroupMap.value[hedgeData.noNumber] || '1')
  
  console.log(`[executeHedgeTask] API返回的组号 - yesGroup: ${hedgeData.yesGroup}, noGroup: ${hedgeData.noGroup}`)
  console.log(`[executeHedgeTask] 使用的组号 - yesGroupNo: ${yesGroupNo}, noGroupNo: ${noGroupNo}`)
  
  // 计算价格（一方是 currentPrice，另一方是 100 - currentPrice）
  const yesPrice = firstSide === 'YES' ? parseFloat(hedgeData.currentPrice) : (100 - parseFloat(hedgeData.currentPrice))
  const noPrice = firstSide === 'NO' ? parseFloat(hedgeData.currentPrice) : (100 - parseFloat(hedgeData.currentPrice))
  
  // 计算数量并保留2位小数向下取整
  let calculatedShare = hedgeMode.isClose ? hedgeData.share : (hedgeData.share * 100)
  
  const roundedShare = floorToTwoDecimals(calculatedShare)
  
  const missionId = hedgeData.missionId  // 组任务的任务id
  const priceInfo = hedgeData.priceInfo  // 订单薄数据
  
  const hedgeRecord = {
    id: Date.now(),
    trendingId: config.id,
    trendingName: config.trending,
    yesNumber: hedgeData.yesNumber,
    noNumber: hedgeData.noNumber,
    yesGroupNo: yesGroupNo,
    noGroupNo: noGroupNo,
    share: roundedShare,  // 保留2位小数向下取整
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
    finalStatus: 'running',  // running, success, failed
    missionId: missionId,  // 组任务的任务id
    priceInfo: priceInfo,  // 订单薄数据
    tp2: hedgeData.tp2,  // 保存tp2值，用于后挂方任务提交
    firstShareReduction: hedgeData.firstShareReduction || 0,  // 深度差0.1时，先挂方数量需要减少的量
    // 用于收集所有子任务的映射：{number: misId}
    subTaskMap: {},  // {浏览器编号: 子任务id}
    wasCounted: true  // 标记此任务已被计入 runningHedgeGroupsCount
  }
  
  // 初始化 currentHedges 数组（如果不存在）
  if (!config.currentHedges) {
    config.currentHedges = []
  }
  
  // 添加到数组中
  config.currentHedges.push(hedgeRecord)
  
  // 增加正在运行的任务组数
  runningHedgeGroupsCount.value++
  
  // 为了兼容旧代码，也设置 currentHedge（指向最新的）
  config.currentHedge = hedgeRecord
  
  pausedType3Tasks.value.add(config.id)
  
  console.log(`开始对冲 ${config.id}:`, hedgeRecord)
  
  try {
    // 使用已获取的组号（直接使用API返回的组号）
    const groupNo = firstSide === 'YES' ? yesGroupNo : noGroupNo
    console.log(`[executeHedgeTask] 提交第一个任务，使用组号: ${groupNo} (firstSide: ${firstSide}, yesGroupNo: ${yesGroupNo}, noGroupNo: ${noGroupNo})`)
    
    // 计算先挂方数量（如果存在 firstShareReduction，需要减去）
    let firstShare = roundedShare
    if (hedgeData.firstShareReduction && hedgeData.firstShareReduction > 0) {
      firstShare = roundedShare - hedgeData.firstShareReduction
      console.log(`深度差0.1 - 先挂方数量减少: ${hedgeData.firstShareReduction.toFixed(2)}, 原数量: ${roundedShare}, 新数量: ${firstShare.toFixed(2)}`)
    }
    
    const taskData = {
      groupNo: groupNo,
      numberList: parseInt(firstBrowser),
      type: 5,  // 自动对冲使用 type=5
      trendingId: config.id,
      exchangeName: 'OP',
      side: hedgeMode.isClose ? 2 : 1,  // 开仓=1，平仓=2
      psSide: firstPsSide,
      amt: floorToTwoDecimals(firstShare),  // 先挂方数量，保留2位小数向下取整
      price: hedgeData.currentPrice,
      tp3: isFastMode.value ? "1" : "0",  // 根据模式设置tp3
      tp5: hedgeMode.openOrderCancelHours  // 挂单超过XX小时撤单
    }
    
    // 根据深度差范围和开关决定是否传递tp2和tp4
    const depthDiffRange = hedgeData.depthDiffRange
    let shouldPassTp2Tp4 = false
    let shouldPassTp4For01 = false  // 深度差0.1时只传tp4（固定为1），不传tp2
    if (depthDiffRange === 'gt15' && hedgeMode.enableDepthDiffParamsGt15) {
      shouldPassTp2Tp4 = true
    } else if (depthDiffRange === '2to15' && hedgeMode.enableDepthDiffParams2To15) {
      shouldPassTp2Tp4 = true
    } else if (depthDiffRange === '02to2' && hedgeMode.enableDepthDiffParams02To2) {
      shouldPassTp2Tp4 = true
    } else if (depthDiffRange === '01' && hedgeMode.enableDepthDiffParams01) {
      shouldPassTp4For01 = true  // 深度差0.1时只传tp4，固定为1
    }
    
    if (shouldPassTp2Tp4 && hedgeData.tp2 !== null && hedgeData.tp2 !== undefined) {
      taskData.tp2 = Math.round(hedgeData.tp2)  // tp2转换为整数（秒）
      console.log(`添加tp2字段: ${taskData.tp2}秒`)
    }
    
    // 添加tp4字段（最大允许深度）
    if (shouldPassTp2Tp4) {
      taskData.tp4 = getMaxDepth(config)  // 最大允许深度（优先使用保存的单独设置，否则使用全局设置）
      console.log(`添加tp4字段: ${taskData.tp4}`)
    } else if (shouldPassTp4For01) {
      taskData.tp4 = getMaxDepth(config)  // 深度差0.1时tp4也传最大允许深度
      console.log(`深度差0.1添加tp4字段: ${taskData.tp4}`)
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
        // 保存子任务映射：浏览器编号 -> 子任务id
        hedgeRecord.subTaskMap[hedgeRecord.yesNumber] = taskId
      } else {
        hedgeRecord.noTaskId = taskId
        hedgeRecord.noStatus = 9
        // 保存子任务映射：浏览器编号 -> 子任务id
        hedgeRecord.subTaskMap[hedgeRecord.noNumber] = taskId
      }
      
      // 调用更新接口的函数（模式1）
      const updateHedgeMissionStatus = async (hedgeRecord) => {
        // 如果没有 missionId，则不调用更新接口
        if (!hedgeRecord.missionId) {
          console.log('模式1 - 没有 missionId，跳过更新接口调用')
          return
        }
        
        // 如果没有订单薄数据，则不调用更新接口
        if (!hedgeRecord.priceInfo) {
          console.log('模式1 - 没有订单薄数据，跳过更新接口调用')
          return
        }
        
        try {
          // 构建 depthStr：买一深度,买一价；卖一价，卖一深度
          const depth1 = hedgeRecord.priceInfo.depth1 || 0  // 买一深度
          const price1 = hedgeRecord.priceInfo.price1 || 0  // 买一价
          const price2 = hedgeRecord.priceInfo.price2 || 0  // 卖一价
          const depth2 = hedgeRecord.priceInfo.depth2 || 0  // 卖一深度
          const depthStr = `${depth1},${price1}；${price2},${depth2}`
          
          // 构建请求数据列表
          const list = []
          for (const [number, misId] of Object.entries(hedgeRecord.subTaskMap)) {
            list.push({
              missionId: hedgeRecord.missionId,
              number: parseInt(number),
              misId: parseInt(misId),
              depthStr: depthStr
            })
          }
          
          // 如果没有子任务，则不调用更新接口
          if (list.length === 0) {
            console.log('模式1 - 没有子任务，跳过更新接口调用')
            return
          }
          
          const requestData = { list: list }
          console.log('模式1 - 调用更新接口:', requestData)
          
          const response = await axios.post(
            'https://sg.bicoin.com.cn/99l/hedge/updateHedgeMissionStatus',
            requestData,
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )
          
          if (response.data) {
            console.log('模式1 - 更新接口调用成功:', response.data)
          } else {
            console.warn('模式1 - 更新接口调用返回异常:', response.data)
          }
        } catch (error) {
          console.error('模式1 - 更新接口调用失败:', error)
        }
      }
      
      // 根据事件间隔类型决定何时提交第二个任务
      if (hedgeMode.intervalType === 'delay') {
        // 延时模式：等待指定时间后直接提交第二个任务
        console.log(`[延时模式] 等待 ${hedgeMode.intervalDelay}ms 后提交第二个任务`)
        setTimeout(async () => {
          if (hedgeRecord.finalStatus === 'running' && !hedgeRecord.secondTaskSubmitted) {
            console.log(`[延时模式] 延时结束，提交第二个任务`)
            hedgeRecord.secondTaskSubmitted = true
            await submitSecondHedgeTask(config, hedgeRecord, updateHedgeMissionStatus)
            // submitSecondHedgeTask 内部会调用 updateHedgeMissionStatus
          }
        }, hedgeMode.intervalDelay)
      } else {
        // 挂单成功模式：如果只有第一个任务（没有第二个任务），也需要调用更新接口
        // 注意：模式1通常有两个任务，但为了保险起见，这里也处理
        // 实际上，挂单成功模式下，第二个任务会在 monitorHedgeStatus 中提交
        // 但第一个任务提交后，应该先调用一次更新接口（如果只有第一个任务的话）
        // 由于模式1通常有两个任务，这里暂时不调用，等第二个任务提交后再调用
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
    // 使用已存储的组号（来自API返回的组号）
    const groupNo = secondSide === 'YES' ? hedgeRecord.yesGroupNo : hedgeRecord.noGroupNo
    
    // 任务二的价格 = 100 - 任务一的价格
    const secondPrice = (100 - parseFloat(hedgeRecord.price)).toFixed(1)
    console.log(`任务二价格计算: 100 - ${hedgeRecord.price} = ${secondPrice}`)
    
    // 获取第一个任务的ID
    const firstTaskId = hedgeRecord.firstSide === 'YES' ? hedgeRecord.yesTaskId : hedgeRecord.noTaskId
    
    // 后挂方数量直接使用服务器下发的数量（深度差0.1时先挂方已经减少了）
    const secondShare = hedgeRecord.share
    
    const taskData = {
      groupNo: groupNo,
      numberList: parseInt(secondBrowser),
      type: 5,  // 自动对冲使用 type=5
      trendingId: config.id,
      exchangeName: 'OP',
      side: hedgeRecord.isClose ? 2 : 1,  // 开仓=1，平仓=2
      psSide: secondPsSide,
      amt: floorToTwoDecimals(secondShare),  // 后挂方数量，保留2位小数向下取整
      price: parseFloat(secondPrice),
      tp1: firstTaskId,  // 任务二需要传递任务一的ID
      tp3: isFastMode.value ? "1" : "0",  // 根据模式设置tp3
      tp5: hedgeMode.openOrderCancelHours  // 挂单超过XX小时撤单
    }
    
    // 根据深度差范围和开关决定是否传递tp2和tp4
    const depthDiffRange = hedgeRecord.priceInfo?.depthDiffRange
    let shouldPassTp2Tp4 = false
    let shouldPassTp4For01 = false  // 深度差0.1时只传tp4（固定为1），不传tp2
    if (depthDiffRange === 'gt15' && hedgeMode.enableDepthDiffParamsGt15) {
      shouldPassTp2Tp4 = true
    } else if (depthDiffRange === '2to15' && hedgeMode.enableDepthDiffParams2To15) {
      shouldPassTp2Tp4 = true
    } else if (depthDiffRange === '02to2' && hedgeMode.enableDepthDiffParams02To2) {
      shouldPassTp2Tp4 = true
    } else if (depthDiffRange === '01' && hedgeMode.enableDepthDiffParams01) {
      shouldPassTp4For01 = true  // 深度差0.1时只传tp4，固定为1
    }
    
    if (shouldPassTp2Tp4 && hedgeRecord.tp2 !== null && hedgeRecord.tp2 !== undefined) {
      taskData.tp2 = Math.round(hedgeRecord.tp2)  // tp2转换为整数（秒）
      console.log(`后挂方任务添加tp2字段: ${taskData.tp2}秒`)
    }
    
    // 添加tp4字段（最大允许深度）
    if (shouldPassTp2Tp4) {
      taskData.tp4 = getMaxDepth(config)  // 最大允许深度（优先使用保存的单独设置，否则使用全局设置）
      console.log(`后挂方任务添加tp4字段: ${taskData.tp4}`)
    } else if (shouldPassTp4For01) {
      taskData.tp4 = getMaxDepth(config)  // 深度差0.1时tp4也传最大允许深度
      console.log(`深度差0.1后挂方任务添加tp4字段: ${taskData.tp4}`)
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
        // 保存子任务映射：浏览器编号 -> 子任务id
        hedgeRecord.subTaskMap[hedgeRecord.yesNumber] = taskId
      } else {
        hedgeRecord.noTaskId = taskId
        hedgeRecord.noStatus = 9
        // 保存子任务映射：浏览器编号 -> 子任务id
        hedgeRecord.subTaskMap[hedgeRecord.noNumber] = taskId
      }
      
      // 所有子任务提交完成后，调用更新接口
      await updateHedgeMissionStatus(hedgeRecord)
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
 * 调用更新接口的函数（模式1）
 */
const updateHedgeMissionStatus = async (hedgeRecord) => {
  // 如果没有 missionId，则不调用更新接口
  if (!hedgeRecord.missionId) {
    console.log('模式1 - 没有 missionId，跳过更新接口调用')
    return
  }
  
  // 如果没有订单薄数据，则不调用更新接口
  if (!hedgeRecord.priceInfo) {
    console.log('模式1 - 没有订单薄数据，跳过更新接口调用')
    return
  }
  
  try {
    // 构建 depthStr：买一深度,买一价；卖一价，卖一深度
    const depth1 = hedgeRecord.priceInfo.depth1 || 0  // 买一深度
    const price1 = hedgeRecord.priceInfo.price1 || 0  // 买一价
    const price2 = hedgeRecord.priceInfo.price2 || 0  // 卖一价
    const depth2 = hedgeRecord.priceInfo.depth2 || 0  // 卖一深度
    const depthStr = `${depth1},${price1}；${price2},${depth2}`
    
    // 构建请求数据列表
    const list = []
    for (const [number, misId] of Object.entries(hedgeRecord.subTaskMap)) {
      list.push({
        missionId: hedgeRecord.missionId,
        number: parseInt(number),
        misId: parseInt(misId),
        depthStr: depthStr
      })
    }
    
    // 如果没有子任务，则不调用更新接口
    if (list.length === 0) {
      console.log('模式1 - 没有子任务，跳过更新接口调用')
      return
    }
    
    const requestData = { list: list }
    console.log('模式1 - 调用更新接口:', requestData)
    
    const response = await axios.post(
      'https://sg.bicoin.com.cn/99l/hedge/updateHedgeMissionStatus',
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data) {
      console.log('模式1 - 更新接口调用成功:', response.data)
    } else {
      console.warn('模式1 - 更新接口调用返回异常:', response.data)
    }
  } catch (error) {
    console.error('模式1 - 更新接口调用失败:', error)
  }
}

/**
 * 执行对冲任务（模式2 - 支持多个yes/no，不同share）
 */
const executeHedgeTaskV2 = async (config, hedgeData) => {
  const firstSide = hedgeData.firstSide
  const yesList = hedgeData.yesList || []
  const noList = hedgeData.noList || []
  const missionId = hedgeData.missionId  // 组任务的任务id
  const priceInfo = hedgeData.priceInfo  // 订单薄数据
  
  // 创建对冲记录
  const hedgeRecord = {
    id: Date.now(),
    trendingId: config.id,
    trendingName: config.trending,
    price: hedgeData.currentPrice,
    firstSide: firstSide,
    side: hedgeMode.isClose ? 2 : 1,  // 开仓=买入(1)，平仓=卖出(2)
    isClose: hedgeMode.isClose,
    startTime: new Date().toISOString(),
    endTime: null,
    duration: null,
    finalStatus: 'running',  // running, success, failed
    isMode2: true,  // 标记为模式2
    // 模式2的数据结构：多个任务
    yesTasks: [],  // [{number, share, taskId, status, groupNo, price}]
    noTasks: [],   // [{number, share, taskId, status, groupNo, price}]
    allTaskIds: [],  // 所有任务ID的数组
    // 保存原始数据，用于显示所有计划任务（包括未提交的）
    yesList: yesList,  // 原始YES任务列表
    noList: noList,    // 原始NO任务列表
    missionId: missionId,  // 组任务的任务id
    priceInfo: priceInfo,  // 订单薄数据
    // 用于收集所有子任务的映射：{number: misId}
    subTaskMap: {},  // {浏览器编号: 子任务id}
    wasCounted: true  // 标记此任务已被计入 runningHedgeGroupsCount
  }
  
  // 初始化 currentHedges 数组（如果不存在）
  if (!config.currentHedges) {
    config.currentHedges = []
  }
  
  // 添加到数组中
  config.currentHedges.push(hedgeRecord)
  
  // 增加正在运行的任务组数
  runningHedgeGroupsCount.value++
  
  // 为了兼容旧代码，也设置 currentHedge（指向最新的）
  config.currentHedge = hedgeRecord
  
  pausedType3Tasks.value.add(config.id)
  
  console.log(`开始对冲（模式2） ${config.id}:`, hedgeRecord)
  
  try {
    // 先为所有先挂方的任务添加type=1的任务
    const firstSideList = firstSide === 'YES' ? yesList : noList
    const firstPsSide = firstSide === 'YES' ? 1 : 2
    
    console.log(`模式2 - 开始提交先挂方（${firstSide}）任务，共 ${firstSideList.length} 个`)
    
    let firstSideSuccessCount = 0
    // 获取组号（优先使用API返回的group字段，如果API返回了group则优先使用，否则使用browserToGroupMap）
    const defaultGroup = (hedgeData.group !== undefined && hedgeData.group !== null && hedgeData.group !== '') 
      ? String(hedgeData.group) 
      : null
    console.log(`[executeHedgeTaskV2] API返回的组号 - group: ${hedgeData.group}, defaultGroup: ${defaultGroup}`)
    
    for (const item of firstSideList) {
      try {
        const browserNo = item.number
        const share = floorToTwoDecimals(item.share)
        // 优先使用item.group（如果API在每个item中都返回了group），其次使用hedgeData.group，最后使用browserToGroupMap
        let groupNo = '1'
        if (item.group !== undefined && item.group !== null && item.group !== '') {
          groupNo = String(item.group)
        } else if (defaultGroup !== null) {
          groupNo = defaultGroup
        } else {
          groupNo = browserToGroupMap.value[browserNo] || '1'
        }
        console.log(`[executeHedgeTaskV2] 浏览器 ${browserNo} 使用组号: ${groupNo} (item.group: ${item.group}, defaultGroup: ${defaultGroup})`)
        
        // 计算价格：先挂方使用 currentPrice（与模式1一致）
        const taskPrice = parseFloat(hedgeData.currentPrice)
        
        const taskData = {
          groupNo: groupNo,
          numberList: parseInt(browserNo),
          type: 1,  // 模式2使用type=1
          trendingId: config.id,
          exchangeName: 'OP',
          side: hedgeMode.isClose ? 2 : 1,  // 开仓=1，平仓=2
          psSide: firstPsSide,
          amt: share,
          price: taskPrice,
          tp3: isFastMode.value ? "1" : "0",  // 根据模式设置tp3
          tp5: hedgeMode.openOrderCancelHours  // 挂单超过XX小时撤单
        }
        
        // 根据深度差范围和开关决定是否传递tp2和tp4
        const depthDiffRange = hedgeData.depthDiffRange
        let shouldPassTp2Tp4 = false
        let shouldPassTp4For01 = false  // 深度差0.1时只传tp4（固定为1），不传tp2
        if (depthDiffRange === 'gt15' && hedgeMode.enableDepthDiffParamsGt15) {
          shouldPassTp2Tp4 = true
        } else if (depthDiffRange === '2to15' && hedgeMode.enableDepthDiffParams2To15) {
          shouldPassTp2Tp4 = true
        } else if (depthDiffRange === '02to2' && hedgeMode.enableDepthDiffParams02To2) {
          shouldPassTp2Tp4 = true
        } else if (depthDiffRange === '01' && hedgeMode.enableDepthDiffParams01) {
          shouldPassTp4For01 = true  // 深度差0.1时只传tp4，固定为1
        }
        
        if (shouldPassTp2Tp4 && hedgeData.tp2 !== null && hedgeData.tp2 !== undefined) {
          taskData.tp2 = Math.round(hedgeData.tp2)  // tp2转换为整数（秒）
          console.log(`[executeHedgeTaskV2] 先挂方任务添加 tp2 字段: ${taskData.tp2} 秒`)
        }
        
        // 添加tp4字段（最大允许深度）
        if (shouldPassTp2Tp4) {
          taskData.tp4 = getMaxDepth(config)  // 最大允许深度（优先使用保存的单独设置，否则使用全局设置）
          console.log(`[executeHedgeTaskV2] 先挂方任务添加 tp4 字段: ${taskData.tp4}`)
        } else if (shouldPassTp4For01) {
          taskData.tp4 = getMaxDepth(config)  // 深度差0.1时tp4也传最大允许深度
          console.log(`[executeHedgeTaskV2] 深度差0.1先挂方任务添加 tp4 字段: ${taskData.tp4}`)
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
          let taskId = null
          
          if (typeof taskData === 'object' && taskData !== null) {
            taskId = taskData.id
          } else if (typeof taskData === 'number' || typeof taskData === 'string') {
            taskId = taskData
          }
          
          if (taskId === undefined || taskId === null || typeof taskId === 'object') {
            console.error(`模式2 - 提交先挂方任务失败: 无效的任务ID`, { taskData, taskId })
            continue
          }
          
          taskId = String(Number(taskId))
          console.log(`模式2 - 先挂方任务提交成功，浏览器: ${browserNo}, 任务ID: ${taskId}`)
          
          // 保存任务信息
          const taskInfo = {
            number: browserNo,
            share: share,
            taskId: taskId,
            status: 9,  // 初始状态为9（进行中）
            groupNo: groupNo,
            price: taskPrice
          }
          
          if (firstSide === 'YES') {
            hedgeRecord.yesTasks.push(taskInfo)
          } else {
            hedgeRecord.noTasks.push(taskInfo)
          }
          
          hedgeRecord.allTaskIds.push(taskId)
          // 保存子任务映射：浏览器编号 -> 子任务id
          hedgeRecord.subTaskMap[browserNo] = taskId
          firstSideSuccessCount++
        } else if (response.data && response.data.msg) {
          console.error(`模式2 - 提交先挂方任务失败（浏览器: ${browserNo}）:`, response.data.msg)
        }
      } catch (error) {
        console.error(`模式2 - 提交先挂方任务失败（浏览器: ${item.number}）:`, error)
      }
    }
    
    // 如果先挂方任务全部失败，标记为失败
    if (firstSideSuccessCount === 0) {
      console.error(`模式2 - 先挂方任务全部失败，标记对冲为失败`)
      hedgeRecord.finalStatus = 'failed'
      hedgeRecord.errorMsg = '先挂方任务全部提交失败'
      finishHedge(config, hedgeRecord)
      return
    }
    
    console.log(`模式2 - 先挂方任务提交完成，成功: ${firstSideSuccessCount}/${firstSideList.length}`)
    
    // 先挂方任务提交完成后，先调用一次更新接口（包含先挂方的所有子任务）
    // 如果后挂方没有任务，则只调用这一次；如果有后挂方任务，后挂方任务提交完成后会再次调用
    const updateHedgeMissionStatus = async (hedgeRecord) => {
      // 如果没有 missionId，则不调用更新接口
      if (!hedgeRecord.missionId) {
        console.log('模式2 - 没有 missionId，跳过更新接口调用')
        return
      }
      
      // 如果没有订单薄数据，则不调用更新接口
      if (!hedgeRecord.priceInfo) {
        console.log('模式2 - 没有订单薄数据，跳过更新接口调用')
        return
      }
      
      try {
        // 构建 depthStr：买一深度,买一价；卖一价，卖一深度
        const depth1 = hedgeRecord.priceInfo.depth1 || 0  // 买一深度
        const price1 = hedgeRecord.priceInfo.price1 || 0  // 买一价
        const price2 = hedgeRecord.priceInfo.price2 || 0  // 卖一价
        const depth2 = hedgeRecord.priceInfo.depth2 || 0  // 卖一深度
        const depthStr = `${depth1},${price1}；${price2},${depth2}`
        
        // 构建请求数据列表
        const list = []
        for (const [number, misId] of Object.entries(hedgeRecord.subTaskMap)) {
          list.push({
            missionId: hedgeRecord.missionId,
            number: parseInt(number),
            misId: parseInt(misId),
            depthStr: depthStr
          })
        }
        
        // 如果没有子任务，则不调用更新接口
        if (list.length === 0) {
          console.log('模式2 - 没有子任务，跳过更新接口调用')
          return
        }
        
        const requestData = { list: list }
        console.log('模式2 - 调用更新接口:', requestData)
        
        const response = await axios.post(
          'https://sg.bicoin.com.cn/99l/hedge/updateHedgeMissionStatus',
          requestData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data) {
          console.log('模式2 - 更新接口调用成功:', response.data)
        } else {
          console.warn('模式2 - 更新接口调用返回异常:', response.data)
        }
      } catch (error) {
        console.error('模式2 - 更新接口调用失败:', error)
      }
    }
    
    // 根据延时，再为后挂方添加type=1的任务
    const secondSide = firstSide === 'YES' ? 'NO' : 'YES'
    const secondSideList = firstSide === 'YES' ? noList : yesList
    const secondPsSide = firstSide === 'YES' ? 2 : 1
    
    console.log(`模式2 - 等待延时后提交后挂方（${secondSide}）任务，共 ${secondSideList.length} 个`)
    
    // 根据事件间隔类型决定何时提交第二个任务
    const submitSecondSideTasks = async () => {
      for (const item of secondSideList) {
        try {
          const browserNo = item.number
          const share = floorToTwoDecimals(item.share)
          // 优先使用item.group（如果API在每个item中都返回了group），其次使用hedgeData.group，最后使用browserToGroupMap
          let groupNo = '1'
          if (item.group !== undefined && item.group !== null && item.group !== '') {
            groupNo = String(item.group)
          } else if (defaultGroup !== null) {
            groupNo = defaultGroup
          } else {
            groupNo = browserToGroupMap.value[browserNo] || '1'
          }
          console.log(`[executeHedgeTaskV2] 浏览器 ${browserNo} 使用组号: ${groupNo} (item.group: ${item.group}, defaultGroup: ${defaultGroup})`)
          
          // 计算价格：后挂方使用 100 - currentPrice（与模式1一致）
          const taskPrice = 100 - parseFloat(hedgeData.currentPrice)
          
          const taskData = {
            groupNo: groupNo,
            numberList: parseInt(browserNo),
            type: 1,  // 模式2使用type=1
            trendingId: config.id,
            exchangeName: 'OP',
            side: hedgeMode.isClose ? 2 : 1,  // 开仓=1，平仓=2
            psSide: secondPsSide,
            amt: share,
            price: taskPrice,
            tp3: isFastMode.value ? "1" : "0",  // 根据模式设置tp3
            tp5: hedgeMode.openOrderCancelHours  // 挂单超过XX小时撤单
            // 不再需要tp1
          }
          
          // 根据深度差范围和开关决定是否传递tp2和tp4
          const depthDiffRange = hedgeData.depthDiffRange
          let shouldPassTp2Tp4 = false
          let shouldPassTp4For01 = false  // 深度差0.1时只传tp4（固定为1），不传tp2
          if (depthDiffRange === 'gt15' && hedgeMode.enableDepthDiffParamsGt15) {
            shouldPassTp2Tp4 = true
          } else if (depthDiffRange === '2to15' && hedgeMode.enableDepthDiffParams2To15) {
            shouldPassTp2Tp4 = true
          } else if (depthDiffRange === '02to2' && hedgeMode.enableDepthDiffParams02To2) {
            shouldPassTp2Tp4 = true
          } else if (depthDiffRange === '01' && hedgeMode.enableDepthDiffParams01) {
            shouldPassTp4For01 = true  // 深度差0.1时只传tp4，固定为1
          }
          
          if (shouldPassTp2Tp4 && hedgeData.tp2 !== null && hedgeData.tp2 !== undefined) {
            taskData.tp2 = Math.round(hedgeData.tp2)  // tp2转换为整数（秒）
            console.log(`[executeHedgeTaskV2] 后挂方任务添加 tp2 字段: ${taskData.tp2} 秒`)
          }
          
          // 添加tp4字段（最大允许深度）
          if (shouldPassTp2Tp4) {
            taskData.tp4 = getMaxDepth(config)  // 最大允许深度（优先使用保存的单独设置，否则使用全局设置）
            console.log(`[executeHedgeTaskV2] 后挂方任务添加 tp4 字段: ${taskData.tp4}`)
          } else if (shouldPassTp4For01) {
            taskData.tp4 = getMaxDepth(config)  // 深度差0.1时tp4也传最大允许深度
            console.log(`[executeHedgeTaskV2] 深度差0.1后挂方任务添加 tp4 字段: ${taskData.tp4}`)
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
            let taskId = null
            
            if (typeof taskData === 'object' && taskData !== null) {
              taskId = taskData.id
            } else if (typeof taskData === 'number' || typeof taskData === 'string') {
              taskId = taskData
            }
            
            if (taskId === undefined || taskId === null || typeof taskId === 'object') {
              console.error(`模式2 - 提交后挂方任务失败: 无效的任务ID`, { taskData, taskId })
              continue
            }
            
            taskId = String(Number(taskId))
            console.log(`模式2 - 后挂方任务提交成功，浏览器: ${browserNo}, 任务ID: ${taskId}`)
            
            // 保存任务信息
            const taskInfo = {
              number: browserNo,
              share: share,
              taskId: taskId,
              status: 9,  // 初始状态为9（进行中）
              groupNo: groupNo,
              price: taskPrice
            }
            
            if (secondSide === 'YES') {
              hedgeRecord.yesTasks.push(taskInfo)
            } else {
              hedgeRecord.noTasks.push(taskInfo)
            }
            
            hedgeRecord.allTaskIds.push(taskId)
            // 保存子任务映射：浏览器编号 -> 子任务id
            hedgeRecord.subTaskMap[browserNo] = taskId
          }
        } catch (error) {
          console.error(`模式2 - 提交后挂方任务失败（浏览器: ${item.number}）:`, error)
        }
      }
      
      // 所有子任务提交完成后，调用更新接口
      await updateHedgeMissionStatus(hedgeRecord)
    }
    
    // 初始化回调函数变量
    let submitSecondSideTasksCallback = null
    
    if (hedgeMode.intervalType === 'delay') {
      // 延时模式：等待指定时间后提交第二个任务
      console.log(`[模式2-延时模式] 等待 ${hedgeMode.intervalDelay}ms 后提交后挂方任务`)
      setTimeout(async () => {
        if (hedgeRecord.finalStatus === 'running') {
          console.log(`[模式2-延时模式] 延时结束，提交后挂方任务`)
          try {
            await submitSecondSideTasks()
            // submitSecondSideTasks 内部会调用 updateHedgeMissionStatus
          } catch (error) {
            console.error(`[模式2-延时模式] 提交后挂方任务失败:`, error)
            // 不因为后挂方任务提交失败而立即结束对冲，继续监控
          }
        }
      }, hedgeMode.intervalDelay)
      // 延时模式下不需要回调
      submitSecondSideTasksCallback = null
      
      // 延时模式下，先挂方任务提交完成后先调用一次更新接口
      // 如果后挂方没有任务，则只调用这一次；如果有后挂方任务，后挂方任务提交完成后会再次调用
      await updateHedgeMissionStatus(hedgeRecord)
    } else {
      // 挂单成功模式：先提交先挂方任务，等第一个任务成功后提交后挂方任务
      console.log(`[模式2-挂单成功模式] 等待先挂方任务成功后提交后挂方任务`)
      // 监控先挂方任务状态，当第一个任务成功时提交后挂方任务
      submitSecondSideTasksCallback = submitSecondSideTasks
      
      // 挂单成功模式下，先挂方任务提交完成后先调用一次更新接口
      // 如果后挂方没有任务，则只调用这一次；如果有后挂方任务，后挂方任务提交完成后会再次调用
      await updateHedgeMissionStatus(hedgeRecord)
    }
    
    // 开始监控所有任务状态
    monitorHedgeStatusV2(config, hedgeRecord, submitSecondSideTasksCallback)
  } catch (error) {
    console.error('模式2 - 执行对冲任务失败:', error)
    hedgeRecord.finalStatus = 'failed'
    finishHedge(config, hedgeRecord)
  }
}

/**
 * 监控对冲状态（模式2）
 */
const monitorHedgeStatusV2 = (config, hedgeRecord, submitSecondSideTasksCallback = null) => {
  const startTime = new Date(hedgeRecord.startTime)
  let secondSideTasksSubmitted = false
  
  const checkStatus = async () => {
    // 检查是否已完成
    if (hedgeRecord.finalStatus !== 'running') {
      return
    }
    
    const now = new Date()
    const elapsed = (now - startTime) / 1000 / 60
    
    // 检查20分钟超时
    if (elapsed >= 20) {
      console.log(`模式2 - 对冲 ${hedgeRecord.id} 超时（${elapsed.toFixed(1)}分钟）`)
      hedgeRecord.finalStatus = 'timeout'
      finishHedge(config, hedgeRecord)
      return
    }
    
    // 更新所有任务的状态
    if (hedgeRecord.yesTasks && hedgeRecord.yesTasks.length > 0) {
      for (const task of hedgeRecord.yesTasks) {
        if (task.taskId) {
          const taskData = await fetchMissionStatus(task.taskId)
          if (taskData) {
            const oldStatus = task.status
            task.status = taskData.status
            task.msg = taskData.msg || ''
            if (oldStatus !== taskData.status) {
              console.log(`[模式2-monitorHedgeStatus] YES任务 ${task.taskId} 状态变化: ${oldStatus} -> ${taskData.status}`)
            }
          }
        }
      }
    }
    
    if (hedgeRecord.noTasks && hedgeRecord.noTasks.length > 0) {
      for (const task of hedgeRecord.noTasks) {
        if (task.taskId) {
          const taskData = await fetchMissionStatus(task.taskId)
          if (taskData) {
            const oldStatus = task.status
            task.status = taskData.status
            task.msg = taskData.msg || ''
            if (oldStatus !== taskData.status) {
              console.log(`[模式2-monitorHedgeStatus] NO任务 ${task.taskId} 状态变化: ${oldStatus} -> ${taskData.status}`)
            }
          }
        }
      }
    }
    
    // 挂单成功模式：检查先挂方第一个任务是否成功，如果成功则提交后挂方任务
    if (hedgeMode.intervalType === 'success' && submitSecondSideTasksCallback && !secondSideTasksSubmitted) {
      const firstSideTasks = hedgeRecord.firstSide === 'YES' ? hedgeRecord.yesTasks : hedgeRecord.noTasks
      if (firstSideTasks.length > 0 && firstSideTasks[0].status === 2) {
        console.log(`[模式2-挂单成功模式] 先挂方第一个任务成功，开始提交后挂方任务`)
        secondSideTasksSubmitted = true
        await submitSecondSideTasksCallback()
      }
    }
    
    // 检查所有任务是否都完成
    const yesTasks = hedgeRecord.yesTasks || []
    const noTasks = hedgeRecord.noTasks || []
    const allTasks = [...yesTasks, ...noTasks]
    
    // 获取计划任务列表
    const yesList = hedgeRecord.yesList || []
    const noList = hedgeRecord.noList || []
    const plannedTaskCount = yesList.length + noList.length
    
    // 如果没有任务，可能是数据异常，继续监控
    if (allTasks.length === 0) {
      console.warn(`[模式2-monitorHedgeStatus] 对冲 ${hedgeRecord.id} 没有任务数据，继续监控`)
      setTimeout(checkStatus, 5000)
      return
    }
    
    // 检查是否所有计划任务都已提交
    // 只有当所有计划任务都已提交后，才能判断最终状态
    if (allTasks.length < plannedTaskCount) {
      console.log(`[模式2-monitorHedgeStatus] 对冲 ${hedgeRecord.id} 还有任务未提交（已提交: ${allTasks.length}/${plannedTaskCount}），继续监控`)
      setTimeout(checkStatus, 5000)
      return
    }
    
    // 所有计划任务都已提交，检查是否都完成（使用新的判断逻辑）
    const allCompleted = allTasks.every(t => t.status === 2 || t.status === 3 || isTaskSuccess(t.status, t.msg))
    const allSuccess = allTasks.every(t => isTaskSuccess(t.status, t.msg))
    
    // 只有当所有任务都完成（成功或失败）时，才判断最终状态
    if (allCompleted) {
      if (allSuccess) {
        console.log(`[模式2-monitorHedgeStatus] 对冲 ${hedgeRecord.id} 所有任务都成功`)
        hedgeRecord.finalStatus = 'success'
      } else {
        console.log(`[模式2-monitorHedgeStatus] 对冲 ${hedgeRecord.id} 有任务失败（${allTasks.filter(t => !isTaskSuccess(t.status, t.msg)).length}个失败）`)
        hedgeRecord.finalStatus = 'failed'
      }
      finishHedge(config, hedgeRecord)
      return
    }
    
    // 如果还有任务未完成，继续监控
    const runningTasks = allTasks.filter(t => t.status === 9 || t.status === 0 || t.status === 1)
    const completedTasks = allTasks.filter(t => t.status === 2 || t.status === 3 || isTaskSuccess(t.status, t.msg))
    console.log(`[模式2-monitorHedgeStatus] 对冲 ${hedgeRecord.id} 任务进度: ${completedTasks.length}/${allTasks.length} 完成，${runningTasks.length} 个运行中`)
    
    setTimeout(checkStatus, 5000)
  }
  
  checkStatus()
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
  
  console.log(`对冲 ${hedgeRecord.id} 已结束，状态: ${hedgeRecord.finalStatus}，用时: ${hedgeRecord.duration}分钟，YES状态: ${hedgeRecord.yesStatus}, NO状态: ${hedgeRecord.noStatus}，日志已保存`)
  
  // 从数组中移除已完成的对冲记录
  if (config.currentHedges) {
    const index = config.currentHedges.findIndex(h => h.id === hedgeRecord.id)
    if (index !== -1) {
      // 在移除前检查任务是否被计入了统计
      const hedgeToRemove = config.currentHedges[index]
      // 检查任务是否有 wasCounted 标记（只有初始状态为 running 的任务才会有此标记）
      const wasCounted = hedgeToRemove.wasCounted === true
      config.currentHedges.splice(index, 1)
      // 减少正在运行的任务组数（只有被计入统计的任务才减少）
      if (wasCounted && runningHedgeGroupsCount.value > 0) {
        runningHedgeGroupsCount.value--
        console.log(`减少正在运行的任务组数，当前: ${runningHedgeGroupsCount.value}`)
      }
    }
    
    // 如果还有运行中的对冲任务，设置 currentHedge 为最新的运行中的任务
    const runningHedges = config.currentHedges.filter(h => h.finalStatus === 'running')
    if (runningHedges.length > 0) {
      config.currentHedge = runningHedges[runningHedges.length - 1]
    } else {
      // 如果没有运行中的任务了，清除 currentHedge
      config.currentHedge = null
      // 解除暂停状态，允许新的对冲任务
      pausedType3Tasks.value.delete(config.id)
      // 记录任务组结束时间（用于任务间隔控制）
      config.lastGroupFinishTime = Date.now()
      console.log(`配置 ${config.id} - 所有任务已结束，记录结束时间，等待间隔后再分配新任务`)
    }
  } else {
    // 兼容旧代码
    config.currentHedge = null
    pausedType3Tasks.value.delete(config.id)
    // 减少正在运行的任务组数（检查 wasCounted 标记，如果没有标记则假设被计入了，以兼容旧数据）
    if ((hedgeRecord.wasCounted === true || hedgeRecord.wasCounted === undefined) && runningHedgeGroupsCount.value > 0) {
      runningHedgeGroupsCount.value--
      console.log(`减少正在运行的任务组数（兼容旧代码），当前: ${runningHedgeGroupsCount.value}`)
    }
  }
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
 * 更新已存在的对冲记录到本地存储
 */
const saveHedgeLogToStorage = (hedgeRecord) => {
  try {
    const logs = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '[]')
    const index = logs.findIndex(log => log.id === hedgeRecord.id)
    if (index !== -1) {
      logs[index] = hedgeRecord
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(logs))
    }
  } catch (e) {
    console.error('更新对冲日志失败:', e)
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
    
    // 格式化时间为 "YYYY-MM-DD HH:mm:ss" 格式
    const formatDateTime = (dateStr) => {
      const date = new Date(dateStr)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    }
    
    const startTimeStr = formatDateTime(feeQuery.startTime)
    const endTimeStr = formatDateTime(feeQuery.endTime)
    
    // 并行请求本地手续费（type=1 和 type=5）和链上手续费
    const [type1Response, type5Response, chainResponse] = await Promise.all([
      // 调用本地手续费接口 type=1
      axios.get('https://sg.bicoin.com.cn/99l/mission/listPart', {
        params: {
          type: 1,
          startTime: startTimestamp,
          endTime: endTimestamp
        }
      }),
      // 调用本地手续费接口 type=5
      axios.get('https://sg.bicoin.com.cn/99l/mission/listPart', {
        params: {
          type: 5,
          startTime: startTimestamp,
          endTime: endTimestamp
        }
      }),
      // 调用链上手续费接口
      axios.post('https://enstudyai.fatedreamer.com/t3/api/fees/summary', {
        start_time: startTimeStr,
        end_time: endTimeStr
      })
    ])
    
    let missionsCount = 0
    const listPartBrowserNumbers = new Set() // 存储 listPart 中有手续费的浏览器编号
    const listPartBrowserFees = new Map() // 存储每个浏览器编号的手续费总和 {browserNumber: totalFee}
    let totalFee = 0
    
    // 处理本地手续费 - type=1
    if (type1Response.data && type1Response.data.code === 0) {
      const missions = type1Response.data.data.list || []
      missionsCount += missions.length
      
      // 遍历所有任务
      missions.forEach(item => {
        const mission = item.mission
        // 只处理状态为2（成功）的任务
        if (mission && mission.status === 2 && mission.msg) {
          try {
            // 解析 msg JSON
            const msgData = JSON.parse(mission.msg)
            // 检查 transaction_fee 存在且不为 "-"
            if (msgData.transaction_fee && msgData.transaction_fee !== '-' && +msgData.transaction_fee!=0 ) {
              // 提取交易费数字部分（移除 $ 符号和逗号）
              const feeStr = msgData.transaction_fee.replace(/[$,]/g, '')
              const fee = parseFloat(feeStr) || 0
              if (fee > 0) {
                totalFee += fee
                
                // 记录有手续费的浏览器编号和手续费
                if (mission.numberList) {
                  const browserNum = String(mission.numberList)
                  listPartBrowserNumbers.add(browserNum)
                  // 累加该浏览器编号的手续费
                  const currentFee = listPartBrowserFees.get(browserNum) || 0
                  listPartBrowserFees.set(browserNum, currentFee + fee)
                }
              }
            }
          } catch (error) {
            console.error('解析任务消息失败:', mission.id, error)
          }
        }
      })
    }
    
    // 处理本地手续费 - type=5
    if (type5Response.data && type5Response.data.code === 0) {
      const missions = type5Response.data.data.list || []
      missionsCount += missions.length
      
      // 遍历所有任务
      missions.forEach(item => {
        const mission = item.mission
        // 只处理状态为2（成功）的任务
        if (mission && mission.status === 2 && mission.msg) {
          try {
            // 解析 msg JSON
            const msgData = JSON.parse(mission.msg)
            // 检查 transaction_fee 存在且不为 "-"
            if (msgData.transaction_fee && msgData.transaction_fee !== '-' && +msgData.transaction_fee!=0 ) {
              // 提取交易费数字部分（移除 $ 符号和逗号）
              const feeStr = msgData.transaction_fee.replace(/[$,]/g, '')
              const fee = parseFloat(feeStr) || 0
              if (fee > 0) {
                totalFee += fee
                
                // 记录有手续费的浏览器编号和手续费
                if (mission.numberList) {
                  const browserNum = String(mission.numberList)
                  listPartBrowserNumbers.add(browserNum)
                  // 累加该浏览器编号的手续费
                  const currentFee = listPartBrowserFees.get(browserNum) || 0
                  listPartBrowserFees.set(browserNum, currentFee + fee)
                }
              }
            }
          } catch (error) {
            console.error('解析任务消息失败:', mission.id, error)
          }
        }
      })
    }
    
    feeQuery.totalFee = totalFee > 0 ? totalFee : null
    
    // 处理链上手续费
    const summaryBrowserNumbers = new Set() // 存储 summary 中有手续费的浏览器编号
    const summaryBrowserFees = new Map() // 存储每个浏览器编号的手续费 {browserNumber: totalFee}
    if (chainResponse.data) {
      const summary = chainResponse.data.summary || {}
      const addresses = chainResponse.data.addresses || []
      
      feeQuery.chainFee = summary.total_fee || 0
      feeQuery.feeAddresses = addresses
      
      // 提取有手续费的浏览器编号和手续费（total_fee > 0）
      addresses.forEach(addr => {
        if (addr.total_fee && parseFloat(addr.total_fee) > 0 && addr.fingerprint_no) {
          const browserNum = String(addr.fingerprint_no)
          summaryBrowserNumbers.add(browserNum)
          summaryBrowserFees.set(browserNum, parseFloat(addr.total_fee) || 0)
        }
      })
      
      showToast(`查询成功，本地: ${missionsCount} 个任务，链上: ${summary.total_addresses || 0} 个地址`, 'success')
    } else {
      feeQuery.chainFee = null
      feeQuery.feeAddresses = []
    }
    
    // 对比两边有手续费的浏览器编号
    console.log('========== 交易费浏览器编号对比 ==========')
    console.log('listPart 中有手续费的浏览器编号:', Array.from(listPartBrowserNumbers).sort((a, b) => parseInt(a) - parseInt(b)))
    console.log('summary 中有手续费的浏览器编号:', Array.from(summaryBrowserNumbers).sort((a, b) => parseInt(a) - parseInt(b)))
    
    // 找出 listPart 中有但 summary 中没有的（多了哪些）
    const onlyInListPart = Array.from(listPartBrowserNumbers).filter(num => !summaryBrowserNumbers.has(num))
    if (onlyInListPart.length > 0) {
      console.log('⚠️ listPart 中有但 summary 中没有的浏览器编号（多了）:', onlyInListPart.sort((a, b) => parseInt(a) - parseInt(b)))
    } else {
      console.log('✅ listPart 中没有多余的浏览器编号')
    }
    
    // 找出 summary 中有但 listPart 中没有的（少了哪些）
    const onlyInSummary = Array.from(summaryBrowserNumbers).filter(num => !listPartBrowserNumbers.has(num))
    
    // 找出两边都有的浏览器编号，并计算手续费差值
    const commonBrowserNumbers = Array.from(listPartBrowserNumbers).filter(num => summaryBrowserNumbers.has(num))
    if (commonBrowserNumbers.length > 0) {
      console.log('========== 两边都有的浏览器编号手续费对比 ==========')
      const feeDiffs = commonBrowserNumbers.map(browserNum => {
        const listPartFee = listPartBrowserFees.get(browserNum) || 0
        const summaryFee = summaryBrowserFees.get(browserNum) || 0
        const diff = listPartFee - summaryFee
        return {
          browserNum: parseInt(browserNum),
          listPartFee: listPartFee.toFixed(4),
          summaryFee: summaryFee.toFixed(4),
          diff: diff.toFixed(4),
          diffAbs: Math.abs(diff).toFixed(4)
        }
      }).sort((a, b) => a.browserNum - b.browserNum)
      
      feeDiffs.forEach(item => {
        const sign = parseFloat(item.diff) > 0 ? '+' : (parseFloat(item.diff) < 0 ? '-' : '=')
        console.log(`浏览器编号 ${item.browserNum}: listPart=${item.listPartFee}, summary=${item.summaryFee}, 差值=${sign}${item.diffAbs}`)
      })
      
      // 统计总差值
      const totalDiff = feeDiffs.reduce((sum, item) => sum + parseFloat(item.diff), 0)
      console.log(`总差值: ${totalDiff >= 0 ? '+' : ''}${totalDiff.toFixed(4)}`)
    } else {
      console.log('⚠️ 两边没有共同的浏览器编号')
    }
    if (onlyInSummary.length > 0) {
      console.log('⚠️ summary 中有但 listPart 中没有的浏览器编号（少了）:', onlyInSummary.sort((a, b) => parseInt(a) - parseInt(b)))
    } else {
      console.log('✅ summary 中没有缺失的浏览器编号')
    }
    
    // 找出两边都有的
    const inBoth = Array.from(listPartBrowserNumbers).filter(num => summaryBrowserNumbers.has(num))
    console.log('✅ 两边都有的浏览器编号:', inBoth.sort((a, b) => parseInt(a) - parseInt(b)))
    console.log('==========================================')
    
  } catch (error) {
    console.error('查询交易费失败:', error)
    showToast('查询交易费失败: ' + (error.message || '未知错误'), 'error')
    feeQuery.totalFee = null
    feeQuery.chainFee = null
    feeQuery.feeAddresses = []
  }
}

/**
 * 执行自动对冲任务（新逻辑：通过API请求订单薄）
 */
const executeAutoHedgeTasks = async () => {
  console.log('执行自动对冲任务...')
  
  // 检查是否可以下发新的对冲任务
  const canStartNewHedge = !(hedgeStatus.amtSum >= hedgeStatus.amt || hedgeStatus.amt === 0)
  if (!canStartNewHedge) {
    if (hedgeStatus.amt === 0) {
      console.log('对冲总数量为0，不下发新对冲任务')
      showToast('对冲总数量为0，无法对冲。请设置总数量并更新。', 'warning')
    } else {
      console.log(`对冲数量已满（${hedgeStatus.amtSum}/${hedgeStatus.amt}），不下发新对冲任务`)
      showToast(`对冲数量已满（${hedgeStatus.amtSum}/${hedgeStatus.amt}），无法继续对冲`, 'warning')
    }
  }
  
  const configsArray = activeConfigs.value
  for (let i = 0; i < configsArray.length; i++) {
    const config = configsArray[i]
    
    // 每个主题之间间隔0.5秒（第一个主题不需要延迟）
    if (i > 0) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    try {
      // 检查该主题的token是否配置完整
      if (!config.trendingPart1 || !config.trendingPart2) {
        console.log(`配置 ${config.id} - 缺少tokenId配置，跳过`)
        continue
      }
      
      // 检查该主题是否正在执行对冲
      const currentHedges = config.currentHedges || []
      const runningHedges = currentHedges.filter(h => h.finalStatus === 'running')
      
      if (runningHedges.length > 0) {
        // 检查是否有超时的任务
        const now = new Date()
        let hasTimeout = false
        for (const hedge of runningHedges) {
          const startTime = new Date(hedge.startTime)
          const elapsed = (now - startTime) / 1000 / 60
          if (elapsed >= 20) {
            console.log(`配置 ${config.id} 对冲任务 ${hedge.id} 超时（${elapsed.toFixed(1)}分钟），强制结束`)
            hedge.finalStatus = 'timeout'
            finishHedge(config, hedge)
            hasTimeout = true
          }
        }
        
        if (hasTimeout) {
          // 清空错误信息和无法对冲时间
          config.errorMessage = null
          config.noHedgeSince = null
        }
        
        // 检查是否还有运行中的任务，如果有且未达到最大任务数，可以继续
        const remainingRunning = (config.currentHedges || []).filter(h => h.finalStatus === 'running').length
        const maxTasks = getTasksPerTopic(config)
        
        if (remainingRunning >= maxTasks) {
          console.log(`配置 ${config.id} 正在执行 ${remainingRunning} 个对冲任务（已达最大 ${maxTasks}），跳过订单薄请求`)
          continue
        }
      } else {
        // 没有运行中的任务，检查任务间隔
        if (config.lastGroupFinishTime && hedgeTaskInterval.value > 0) {
          const now = Date.now()
          const elapsed = (now - config.lastGroupFinishTime) / 1000 / 60  // 转换为分钟
          const intervalMinutes = hedgeTaskInterval.value
          
          if (elapsed < intervalMinutes) {
            const remaining = Math.ceil((intervalMinutes - elapsed) * 60)
            console.log(`配置 ${config.id} - 任务组刚结束，等待间隔时间（还需等待 ${remaining} 秒）`)
            continue
          } else {
            // 间隔时间已过，清除记录
            config.lastGroupFinishTime = null
            console.log(`配置 ${config.id} - 任务间隔时间已过，可以开始新的任务分配`)
          }
        }
      }
      
      // 检查是否正在请求中
      if (config.isFetching) {
        console.log(`配置 ${config.id} - 正在请求订单薄中，跳过`)
        continue
      }
      
      // 检查是否需要请求订单薄
      const now = Date.now()
      
      // 先检查是否有延迟请求时间（10分钟延迟）
      if (config.nextRequestTime && now < config.nextRequestTime) {
        const remaining = Math.ceil((config.nextRequestTime - now) / 1000)
        console.log(`配置 ${config.id} - 订单薄不满足条件，距离下次请求还有 ${remaining} 秒（${Math.ceil(remaining / 60)} 分钟）`)
        continue
      }
      
      // 清除延迟请求时间（如果已过期）
      if (config.nextRequestTime && now >= config.nextRequestTime) {
        config.nextRequestTime = null
      }
      
      // 根据上一轮任务数调整轮询间隔
      // 如果上一轮任务数大于阈值，使用配置的等待时间；否则使用配置的等待时间
      const maxWaitTime = Math.max(
        (hedgeMode.waitTimeLessThanThreshold || 300) * 1000,
        (hedgeMode.waitTimeGreaterThanThreshold || 60) * 1000
      )
      if (lastRoundEndTime.value && now - lastRoundEndTime.value < maxWaitTime) {
        // 上一轮刚结束，根据任务数设置等待时间
        const taskCountThreshold = hedgeMode.taskCountThreshold || 5
        const waitSeconds = lastRoundTaskCount.value > taskCountThreshold 
          ? (hedgeMode.waitTimeGreaterThanThreshold || 60)
          : (hedgeMode.waitTimeLessThanThreshold || 300)
        const waitTime = waitSeconds * 1000
        
        if (now - lastRoundEndTime.value < waitTime) {
          const remaining = Math.ceil((waitTime - (now - lastRoundEndTime.value)) / 1000)
          console.log(`配置 ${config.id} - 上一轮任务数 ${lastRoundTaskCount.value}，等待 ${waitSeconds} 秒后轮询（还需等待 ${remaining} 秒）`)
          continue
        }
      }
      
      // 检查常规请求间隔（20秒）
      const shouldFetch = !config.lastRequestTime || (now - config.lastRequestTime) >= 20000  // 20秒
      
      if (!shouldFetch) {
        const remaining = Math.ceil((20000 - (now - config.lastRequestTime)) / 1000)
        console.log(`配置 ${config.id} - 距离下次请求还有 ${remaining} 秒`)
        continue
      }
      
      // 检查yes持仓是否满足条件（才交易）
      const positionData = positionDataMap.value.get(config.trending?.trim())
      if (positionData) {
        const thresholdPosition = hedgeMode.yesPositionThreshold * 10000  // 转换为实际数量（万转数量）
        const yesPosition = positionData.yesPosition || 0
        const yesPositionWan = yesPosition / 10000  // 转换为万
        
        let shouldTrade = false
        if (hedgeMode.yesPositionCompareType === 'less') {
          shouldTrade = yesPosition < thresholdPosition
        } else {
          shouldTrade = yesPosition > thresholdPosition
        }
        
        if (!shouldTrade) {
          const compareText = hedgeMode.yesPositionCompareType === 'less' ? '小于' : '大于'
          const positionReason = `yes持仓${compareText}${hedgeMode.yesPositionThreshold}万时才交易 (YES: ${yesPositionWan.toFixed(2)}万, 要求: ${compareText} ${hedgeMode.yesPositionThreshold}万)`
          console.log(`配置 ${config.id} - ${positionReason}，跳过本次请求`)
          // 设置订单薄数据以显示原因
          config.orderbookData = {
            pollTime: Date.now(),
            updateTime: null,
            reason: positionReason,
            firstSide: null,
            price1: null,
            price2: null,
            depth1: null,
            depth2: null,
            diff: null
          }
          config.isFetching = false
          continue
        }
      } else {
        console.log(`配置 ${config.id} - 未获取到持仓数据，跳过本次请求`)
        config.isFetching = false
        continue
      }
      
      // 检查加权时间和yes持仓组合条件（不交易）- 适用于开仓和平仓模式
      // 如果加权时间满足条件 且 yes持仓满足条件，则不交易
      if (hedgeMode.weightedTimeHourOpen > 0 && hedgeMode.weightedTimeYesPositionThreshold > 0) {
        const weightedAvgTime = config.weightedAvgTime || 0
        const weightedTimeHour = weightedAvgTime / 3600000  // 转换为小时
        const thresholdTimeMs = hedgeMode.weightedTimeHourOpen * 3600000  // 小时转毫秒
        
        // 检查加权时间条件
        let weightedTimeMatch = false
        if (hedgeMode.weightedTimeCompareType === 'less') {
          weightedTimeMatch = weightedAvgTime < thresholdTimeMs
        } else {
          weightedTimeMatch = weightedAvgTime > thresholdTimeMs
        }
        
        // 检查yes持仓条件
        const positionData = positionDataMap.value.get(config.trending?.trim())
        let yesPositionMatch = false
        if (positionData) {
          const yesPosition = positionData.yesPosition || 0
          const yesPositionWan = yesPosition / 10000  // 转换为万
          const thresholdPosition = hedgeMode.weightedTimeYesPositionThreshold * 10000  // 转换为实际数量
          
          if (hedgeMode.weightedTimeYesPositionCompareType === 'less') {
            yesPositionMatch = yesPosition < thresholdPosition
          } else {
            yesPositionMatch = yesPosition > thresholdPosition
          }
        }
        
        // 如果两个条件都满足，则不交易
        if (weightedTimeMatch && yesPositionMatch) {
          const timeCompareText = hedgeMode.weightedTimeCompareType === 'less' ? '小于' : '大于'
          const positionCompareText = hedgeMode.weightedTimeYesPositionCompareType === 'less' ? '小于' : '大于'
          const yesPositionWan = positionData ? (positionData.yesPosition || 0) / 10000 : 0
          const weightedTimeReason = `加权时间${timeCompareText}${hedgeMode.weightedTimeHourOpen}小时且事件yes持仓${positionCompareText}${hedgeMode.weightedTimeYesPositionThreshold}万不交易 (加权时间: ${weightedTimeHour.toFixed(2)}h, yes持仓: ${yesPositionWan.toFixed(2)}万)`
          console.log(`配置 ${config.id} - ${weightedTimeReason}，跳过本次请求`)
          // 设置订单薄数据以显示原因
          config.orderbookData = {
            pollTime: Date.now(),
            updateTime: null,
            reason: weightedTimeReason,
            firstSide: null,
            price1: null,
            price2: null,
            depth1: null,
            depth2: null,
            diff: null
          }
          config.isFetching = false
          continue
        }
      }
      
      // 检查24小时交易量和7天平均交易量
      const volume24h = config.volume24h || 0
      const volume7dAvg = config.volume7dAvg || 0
      const maxVolume24h = hedgeMode.maxVolume24hOpen * 10000  // 转换为实际数量（万转数量）
      const maxVolume7dAvg = hedgeMode.maxVolume7dAvgOpen * 10000  // 转换为实际数量（万转数量）
      
      // 24h交易量大于XX万 或 7天平均交易量大于XX万 时不交易
      if (volume24h > maxVolume24h || volume7dAvg > maxVolume7dAvg) {
        const volumeReason = `交易量过大：24h量 ${(volume24h/10000).toFixed(2)}万 > ${hedgeMode.maxVolume24hOpen}万 或 7d均量 ${(volume7dAvg/10000).toFixed(2)}万 > ${hedgeMode.maxVolume7dAvgOpen}万`
        console.log(`配置 ${config.id} - ${volumeReason}，跳过本次请求`)
        // 设置订单薄数据以显示原因
        config.orderbookData = {
          pollTime: Date.now(),
          updateTime: null,
          reason: volumeReason,
          firstSide: null,
          price1: null,
          price2: null,
          depth1: null,
          depth2: null,
          diff: null
        }
        config.isFetching = false
        continue
      }
      
      // 开始请求订单薄
      config.isFetching = true
      config.lastRequestTime = now
      
      // 记录轮询时间（每次请求的时间）
      const pollTime = now
      config.pollTime = pollTime
      
      try {
        console.log(`配置 ${config.id} - 开始请求订单薄...`)
        
        let priceInfo = null
        let orderbookReason = null  // 不满足原因
        
        // 判断是否为平仓且模式1
        const currentMode = hedgeMode.isClose ? hedgeMode.hedgeMode : 1
        const isCloseMode1 = hedgeMode.isClose && currentMode === 1
        
        // 如果是平仓且模式1，先请求 calReadyToHedgeCanClose 接口
        if (isCloseMode1) {
          try {
            console.log(`配置 ${config.id} - 平仓模式1，先请求 calReadyToHedgeCanClose 接口...`)
            
            // 构建请求参数（与 calReadyToHedgeV4 一样，除了 currentPrice 不传）
            const canCloseRequestData = {
              trendingId: config.id,
              isClose: hedgeMode.isClose,
              // currentPrice 不传
              priceOutCome: 'YES',  // 先挂方，随便传一个值
              timePassMin: hedgeMode.timePassMin,
              minUAmt: hedgeMode.minUAmt,  // 最小开单
              maxUAmt: hedgeMode.maxUAmt,   // 最大开单
              minCloseAmt: hedgeMode.minCloseAmt,  // 平仓最小数量（参数1）
              maxOpenHour: hedgeMode.maxOpenHour,  // 可加仓时间（小时）
              closeOpenHourArea: hedgeMode.closeOpenHourArea,  // 可平仓随机区间（小时）
              numberType: parseInt(selectedNumberType.value)  // 账号类型：1-全部账户, 2-1000个账户, 3-1000个账户中未达标的
            }
            // 如果 maxIpDelay 有值，则添加到请求参数中
            if (hedgeMode.maxIpDelay && hedgeMode.maxIpDelay !== '') {
              canCloseRequestData.maxIpDelay = Number(hedgeMode.maxIpDelay)
            }
            // 添加 needJudgeDF 和 maxDHour 字段
            canCloseRequestData.needJudgeDF = hedgeMode.needJudgeDF ? 1 : 0
            canCloseRequestData.maxDHour = Number(hedgeMode.maxDHour) || 12
            // 添加 minCloseMin 字段
            canCloseRequestData.minCloseMin = Number(hedgeMode.minCloseMin) || 60
            // 添加资产优先级校验字段
            canCloseRequestData.needJudgeBalancePriority = hedgeMode.needJudgeBalancePriority
            canCloseRequestData.balancePriority = hedgeMode.balancePriority
            
            const canCloseResponse = await axios.post(
              'https://sg.bicoin.com.cn/99l/hedge/calReadyToHedgeCanClose',
              canCloseRequestData,
              {
                headers: {
                  'Content-Type': 'application/json'
                }
              }
            )
            
            // 处理返回结果，与 calReadyToHedgeV4 一样
            if (canCloseResponse.data && canCloseResponse.data.data) {
              const canCloseData = canCloseResponse.data.data
              if (canCloseData.yesNumber) {
                console.log(`配置 ${config.id} - calReadyToHedgeCanClose 返回 yesNumber，可以开，继续请求订单薄`)
              } else {
                console.log(`配置 ${config.id} - calReadyToHedgeCanClose 未返回 yesNumber，不能开，跳过本次请求`)
                // 不能开，跳过本次请求
                config.isFetching = false
                continue
              }
            } else if (canCloseResponse.data && canCloseResponse.data.msg) {
              // 服务器返回错误消息，添加到对冲信息中（与 calReadyToHedgeV4 一样）
              console.warn(`配置 ${config.id} - calReadyToHedgeCanClose 服务器返回错误:`, canCloseResponse.data.msg)
              
              // 初始化 currentHedges 数组（如果不存在）
              if (!config.currentHedges) {
                config.currentHedges = []
              }
              
              // 创建一个错误记录
              const errorRecord = {
                id: Date.now(),
                trendingId: config.id,
                trendingName: config.trending,
                startTime: new Date().toISOString(),
                endTime: new Date().toISOString(),
                finalStatus: 'failed',
                errorMsg: canCloseResponse.data.msg
              }
              config.currentHedges.push(errorRecord)
              
              // 跳过本次请求
              config.isFetching = false
              continue
            } else {
              console.log(`配置 ${config.id} - calReadyToHedgeCanClose 返回数据异常，跳过本次请求`)
              config.isFetching = false
              continue
            }
          } catch (canCloseError) {
            console.error(`配置 ${config.id} - 请求 calReadyToHedgeCanClose 失败:`, canCloseError)
            // 请求失败，提取错误消息并添加到对冲信息中
            let errorMessage = '请求 calReadyToHedgeCanClose 失败'
            if (canCloseError.response?.data?.msg) {
              errorMessage = canCloseError.response.data.msg
            } else if (canCloseError.message) {
              errorMessage = canCloseError.message
            }
            
            // 初始化 currentHedges 数组（如果不存在）
            if (!config.currentHedges) {
              config.currentHedges = []
            }
            
            // 创建一个错误记录
            const errorRecord = {
              id: Date.now(),
              trendingId: config.id,
              trendingName: config.trending,
              startTime: new Date().toISOString(),
              endTime: new Date().toISOString(),
              finalStatus: 'failed',
              errorMsg: errorMessage
            }
            config.currentHedges.push(errorRecord)
            
            // 跳过本次请求
            config.isFetching = false
            continue
          }
        }
        
        try {
          // 尝试解析订单薄数据（包含完整检查）
          // 如果是平仓且模式1，需要重试5次
          let orderbookSuccess = false
          let lastOrderbookError = null
          
          if (isCloseMode1) {
            // 平仓模式1：重试5次（只对接口请求失败进行重试，不对数据处理失败重试）
            for (let retryCount = 0; retryCount < 5; retryCount++) {
              try {
                priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
                if (priceInfo) {
                  orderbookSuccess = true
                  break
                }
              } catch (orderbookError) {
                lastOrderbookError = orderbookError
                const errorMsg = orderbookError.message || ''
                
                // 判断是否为接口请求失败（需要重试）
                // 如果是数据处理失败（深度不足、价差过大等），不需要重试
                const isInterfaceError = errorMsg.includes('订单薄接口错误') || 
                                         errorMsg.includes('errno') ||
                                         errorMsg.includes('网络') ||
                                         errorMsg.includes('timeout') ||
                                         errorMsg.includes('ECONNREFUSED') ||
                                         errorMsg.includes('ENOTFOUND')
                
                if (isInterfaceError) {
                  // 接口请求失败，需要重试
                  console.warn(`配置 ${config.id} - 请求订单薄接口失败 (第 ${retryCount + 1}/5 次):`, errorMsg)
                  if (retryCount < 4) {
                    // 等待一小段时间后重试
                    await new Promise(resolve => setTimeout(resolve, 500))
                  }
                } else {
                  // 数据处理失败（深度不足、价差过大等），不需要重试，直接抛出错误
                  console.warn(`配置 ${config.id} - 订单薄数据处理失败（不重试）:`, errorMsg)
                  throw orderbookError
                }
              }
            }
            
            if (!orderbookSuccess) {
              throw lastOrderbookError || new Error('请求订单薄失败（重试5次后仍失败）')
            }
          } else {
            // 非平仓模式1：使用原来的逻辑
            priceInfo = await parseOrderbookData(config, hedgeMode.isClose)
          }
          
          if (!priceInfo) {
            throw new Error('解析订单薄数据失败')
          }
          
          // 检查是否满足对冲条件
          const meetsCondition = checkOrderbookHedgeCondition(priceInfo, config)
          
          if (!meetsCondition) {
            // 不满足条件，获取不满足的原因
            const maxDepth = getMaxDepth(config)
            if (priceInfo.diff <= 0.15) {
              if (!hedgeMode.isClose) {
                // 开仓模式：检查买一价值（买一价 × 买一深度 / 100）
                const bidValue = priceInfo.price1 * priceInfo.depth1 / 100
                if (bidValue >= maxDepth) {
                  orderbookReason = `先挂方买一价值 ${bidValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
                } else {
                  orderbookReason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
                }
              } else {
                // 平仓模式：检查卖一价值（卖一价 × 卖一深度 / 100）
                const askValue = priceInfo.price2 * priceInfo.depth2 / 100
                if (askValue >= maxDepth) {
                  orderbookReason = `先挂方卖一价值 ${askValue.toFixed(2)}U 超过最大允许深度 ${maxDepth}U`
                } else {
                  orderbookReason = `先挂方买卖价差 ${priceInfo.diff.toFixed(2)} 不足（需要 > 0.15），且深度条件不满足`
                }
              }
            } else {
              orderbookReason = '不符合对冲条件'
            }
          }
          
          // 记录更新时间（成功获取订单薄的时间）
          priceInfo.updateTime = Date.now()
          priceInfo.pollTime = pollTime
          priceInfo.reason = orderbookReason
          
        } catch (error) {
          // 如果是深度区间开关未开启的错误，直接抛出，不回退到基本数据
          if (error.message && error.message.includes('深度区间开关未开启')) {
            console.error(`配置 ${config.id} - 深度区间开关未开启，直接失败:`, error.message)
            throw error
          }
          
          // parseOrderbookData失败，尝试获取基本订单薄数据
          console.warn(`配置 ${config.id} - 完整订单薄检查失败，尝试获取基本数据:`, error.message)
          
          try {
            const basicInfo = await fetchOrderbookBasic(config, hedgeMode.isClose)
            
            if (basicInfo) {
              // 使用基本数据
              priceInfo = {
                ...basicInfo,
                updateTime: Date.now(),  // 记录更新时间
                pollTime: pollTime,      // 记录轮询时间
                reason: error.message || '订单薄数据不满足条件'  // 记录不满足原因
              }
              orderbookReason = priceInfo.reason
            } else {
              throw new Error('获取基本订单薄数据失败')
            }
          } catch (basicError) {
            // 基本数据也获取失败
            console.error(`配置 ${config.id} - 获取基本订单薄数据也失败:`, basicError)
            throw error  // 抛出原始错误
          }
        }
        
        // 保存订单薄数据（无论是否满足条件都保存）
        config.orderbookData = priceInfo
        config.retryCount = 0  // 重置重试次数
        
        // 如果订单薄成功获取到了数据，且不满足条件，设置下次请求时间为配置的间隔时间后
        if (priceInfo && priceInfo.updateTime && orderbookReason) {
          // 成功获取但不满足条件，设置配置的间隔时间后才能再次请求
          const intervalMinutes = hedgeMode.orderbookMismatchInterval || 10
          config.nextRequestTime = now + intervalMinutes * 60 * 1000
          console.log(`配置 ${config.id} - 订单薄获取成功但不满足条件，下次请求将在 ${intervalMinutes} 分钟后`)
        } else {
          // 获取失败或满足条件，清除延迟请求时间，使用原来的20秒逻辑
          config.nextRequestTime = null
        }
        
        console.log(`配置 ${config.id} - 订单薄数据:`, {
          先挂方: priceInfo.firstSide,
          先挂价格: priceInfo.price1,
          后挂价格: priceInfo.price2,
          价差: priceInfo.diff,
          不满足原因: orderbookReason
        })
        
        // 只有在可以开始新对冲时才判断是否执行对冲
        if (canStartNewHedge && !orderbookReason) {
          // 检查是否满足对冲条件
          if (checkOrderbookHedgeCondition(priceInfo, config)) {
            console.log(`配置 ${config.id} - 满足对冲条件，开始执行对冲`)
            
            // 清空无法对冲时间和标记
            config.noHedgeSince = null
            
            // 执行对冲，并统计任务数
            const taskCount = await executeHedgeFromOrderbook(config, priceInfo)
            roundTaskCount += taskCount || 0
            
            // 记录对冲时间
            config.lastHedgeTime = Date.now()
          } else {
            console.log(`配置 ${config.id} - 不满足对冲条件`)
            
            // 记录开始无法对冲的时间
            if (!config.noHedgeSince) {
              config.noHedgeSince = Date.now()
            } else {
              // 检查是否超过5分钟都无法对冲
              const noHedgeElapsed = (Date.now() - config.noHedgeSince) / 1000 / 60
              if (noHedgeElapsed >= 5) {
                config.errorMessage = `已连续 ${Math.floor(noHedgeElapsed)} 分钟无法对冲`
                console.warn(`配置 ${config.id} - ${config.errorMessage}`)
              }
            }
            
          }
        }
        
      } catch (error) {
        console.error(`配置 ${config.id} - 请求订单薄失败:`, error)
        config.retryCount++
        
        // 获取失败，清除延迟请求时间，使用原来的逻辑
        config.nextRequestTime = null
        
        // 提取错误消息
        let errorMessage = '获取深度失败'
        if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error.message) {
          errorMessage = error.message
        }
        
        // 即使请求失败，也保存轮询时间和错误信息
        config.orderbookData = {
          pollTime: pollTime,
          updateTime: null,  // 请求失败，没有更新时间
          reason: errorMessage,
          firstSide: null,
          price1: null,
          price2: null,
          depth1: null,
          depth2: null,
          diff: null
        }
        
        // 随机1-3秒后重试
        const retryDelay = Math.floor(Math.random() * 2000) + 1000  // 1000-3000ms
        console.log(`配置 ${config.id} - 将在 ${retryDelay}ms 后重试（第 ${config.retryCount} 次）`)
        
        setTimeout(() => {
          config.isFetching = false
          config.lastRequestTime = Date.now() - 20000  // 立即允许重试
        }, retryDelay)
        
        continue
      } finally {
        config.isFetching = false
      }
      
    } catch (error) {
      console.error(`配置 ${config.id} - 处理失败:`, error)
    }
  }
}

/**
 * 获取状态文本
 */
/**
 * 判断任务是否成功（根据 status 和 msg）
 */
const isTaskSuccess = (status, msg) => {
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
    if (msgObj.type === 'TYPE5_SUCCESS') {
      // 全部成交
      return true
    } else if (msgObj.type === 'TYPE5_PARTIAL') {
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
    // 格式如：部分成交 | 现有数量: 0.0 | 成交价格: 78.3 | 挂单价格: 78.3¢ | 进度: $586.57 / $636.57 | 交易费: $0.0
    const progressMatch = msg.match(/进度[:\s]*\$?([\d,]+\.?\d*)\s*\/\s*\$?([\d,]+\.?\d*)/i)
    if (progressMatch) {
      try {
        // 提取前一个值和后一个值，去除逗号和$符号
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
}

/**
 * 从 msg 中提取 [x] 开头的数字
 */
const extractBracketNumber = (msg) => {
  if (!msg) return null
  const match = msg.match(/\[(\d+)\]/)
  if (match) {
    const num = parseInt(match[1])
    if (num < 10) {
      return num
    }
  }
  return null
}

const getStatusText = (status, msg = null) => {
  // 如果传入了 msg，需要根据新的逻辑判断
  if (msg !== null && msg !== undefined) {
    if (isTaskSuccess(status, msg)) {
      return '成功'
    }
  }
  
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
const getStatusClass = (status, msg = null) => {
  // 如果传入了 msg，需要根据新的逻辑判断
  if (msg !== null && msg !== undefined) {
    if (isTaskSuccess(status, msg)) {
      return 'status-completed'
    }
  }
  
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
 * 计算相对时间（X分钟前），用于实时更新
 */
const currentTime = ref(Date.now())
let timeInterval = null

// 定时更新当前时间，用于实时显示相对时间
onMounted(() => {
  timeInterval = setInterval(() => {
    currentTime.value = Date.now()
  }, 1000) // 每秒更新一次
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
    timeInterval = null
  }
})

/**
 * 格式化相对时间（X分钟前）
 */
const formatRelativeTime = (timestamp) => {
  if (!timestamp) return '-'
  const now = currentTime.value
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else {
    const hours = Math.floor(minutes / 60)
    if (hours < 24) {
      return `${hours}小时前`
    } else {
      const days = Math.floor(hours / 24)
      return `${days}天前`
    }
  }
}

/**
 * 判断是否符合订单薄条件
 */
const isOrderbookConditionMet = (orderbookData) => {
  if (!orderbookData) {
    return false
  }
  
  // 如果请求成功（有updateTime）且没有reason，说明符合条件
  if (orderbookData.updateTime && !orderbookData.reason) {
    return true
  }
  
  // 其他情况都不符合条件
  return false
}

/**
 * 获取订单薄状态文本
 */
const getOrderbookStatusText = (orderbookData) => {
  if (!orderbookData || !orderbookData.pollTime) {
    return ''
  }
  
  const relativeTime = formatRelativeTime(orderbookData.pollTime)
  
  // 如果请求失败（没有updateTime但有pollTime）
  if (!orderbookData.updateTime) {
    const errorReason = orderbookData.reason || '获取深度失败'
    return `${relativeTime}轮询，${errorReason}`
  }
  
  // 如果请求成功但不符合条件
  if (orderbookData.reason) {
    return `${relativeTime}轮询，${orderbookData.reason}`
  }
  
  // 如果请求成功且符合条件
  return `${relativeTime}轮询，订单薄符合条件`
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
  // fetchAccountConfig()
  
  // 加载配置
  fetchExchangeConfig()
  
  // 初始加载任务列表
  fetchMissionList()
  
  // 初始加载对冲记录
  // fetchHedgeHistory()
  
  // 启动自动刷新（默认启用，10秒间隔）
  startAutoRefresh()
  
  // 获取对冲状态
  fetchHedgeStatus()
  
  // 启动对冲状态定时刷新（每30秒）
  hedgeStatusInterval.value = setInterval(() => {
    fetchHedgeStatus()
  }, 30000)
  
  // 启动配置自动刷新定时器（每小时05分刷新）
  startConfigAutoRefresh()
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
  if (configAutoRefreshInterval.value) {
    clearInterval(configAutoRefreshInterval.value)
  }
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  width: 100%;
  max-width: 100vw;
  overflow-x: auto;
  box-sizing: border-box;
}

.top-header {
  background: rgba(255, 255, 255, 0.95);
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  min-width: 0;
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
  flex-wrap: wrap;
  min-width: 0;
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
  min-width: 0;
  overflow-x: auto;
}

.container {
  max-width: 100%;
  width: 100%;
  margin: 0 auto;
  padding: 0 1rem;
  box-sizing: border-box;
  display: grid;
  gap: 2rem;
  min-width: 0;
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
  
  .main {
    padding: 1rem;
  }
  
  .container {
    padding: 0 0.5rem;
  }
}

@media (max-width: 768px) {
  .top-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
  }
  
  .top-header h1 {
    font-size: 1.4rem;
  }
  
  .header-actions {
    flex-wrap: wrap;
    width: 100%;
  }
  
  .section {
    padding: 1rem;
  }
  
  .section-header-with-filter {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .trending-filter .filter-input {
    width: 100%;
    max-width: 250px;
  }
  
  .main {
    padding: 0.5rem;
  }
  
  .container {
    padding: 0;
    gap: 1rem;
  }
}

.section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  min-width: 0;
  overflow-x: auto;
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
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
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

.task-time-success {
  color: #4ade80 !important;
}

.task-time-error {
  color: #ef4444 !important;
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

.hedge-mode-select {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.mode-select {
  padding: 0.375rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}

.mode-select:hover:not(:disabled) {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(255, 255, 255, 0.5);
}

.mode-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mode-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
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

/* 最小/最大开单设置 */
.hedge-amount-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.amount-range-input {
  width: 100px;
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #2c3e50;
  font-size: 0.875rem;
  text-align: center;
}

.amount-range-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

.amount-range-input:disabled {
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
  gap: 0.5rem;
  margin-bottom: 0;
  flex-wrap: wrap;
  width: 100%;
}

.trending-name {
  flex: 0 1 auto;
  min-width: 0;
  word-break: break-word;
  font-weight: 500;
}

.btn-log {
  padding: 0.3rem 0.6rem;
  background: rgba(255, 255, 255, 0.3);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  white-space: nowrap;
}

.btn-position {
  padding: 0.3rem 0.6rem;
  background: rgba(100, 181, 246, 0.6);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  white-space: nowrap;
}

.btn-position:hover {
  background: rgba(100, 181, 246, 0.8);
}

.btn-log:hover {
  background: rgba(255, 255, 255, 0.4);
}

.btn-link {
  padding: 0.3rem 0.6rem;
  background: rgba(52, 199, 89, 0.6);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  white-space: nowrap;
  transition: all 0.3s ease;
}

.btn-link:hover {
  background: rgba(52, 199, 89, 0.8);
  transform: scale(1.05);
}

.btn-close-task {
  padding: 0.3rem 0.6rem;
  background: rgba(255, 59, 48, 0.6);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  white-space: nowrap;
  transition: all 0.3s ease;
}

.btn-close-task:hover {
  background: rgba(255, 59, 48, 0.8);
  transform: scale(1.05);
}

.btn-test {
  padding: 0.3rem 0.6rem;
  background: rgba(52, 152, 219, 0.6);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  white-space: nowrap;
  transition: all 0.3s ease;
}

.btn-test:hover:not(:disabled) {
  background: rgba(52, 152, 219, 0.8);
  transform: scale(1.05);
}

.btn-test:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.position-info {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
}

.position-info-green {
  color: #4ade80 !important;
}

.error-badge {
  padding: 0.3rem 0.6rem;
  background: rgba(255, 59, 48, 0.8);
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.orderbook-detail {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.orderbook-detail .price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.orderbook-detail .price-row:last-child {
  border-bottom: none;
}

.orderbook-detail .label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.orderbook-detail .value {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.orderbook-detail .value.highlight {
  color: #4ade80;
  font-weight: 700;
}

/* Type 3 任务和对冲信息容器 */
.task-hedge-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: 1rem;
  margin-top: 0.75rem;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

.type3-task-section,
.hedge-info-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 0.75rem;
  min-width: 0;
  overflow: hidden;
  word-wrap: break-word;
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

.hedge-info.hedge-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 0.75rem;
  margin-top: 0.5rem;
}

.hedge-error-msg {
  color: #ef4444;
  font-size: 0.875rem;
  margin: 0.5rem 0;
  word-break: break-word;
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

.hedge-warning {
  background: #ffc107;
  color: #856404;
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
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 140px), 1fr));
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

/* 服务器数据样式 */
.server-data-section {
  margin-top: 0.5rem;
  margin-left: 1rem;
  padding: 0.75rem;
  background: #f5f5f5;
  border-radius: 6px;
  border-left: 3px solid rgba(100, 200, 255, 0.8);
  font-size: 0.75rem;
}

.server-data-empty {
  color: #666;
  font-style: italic;
  padding: 0.25rem 0;
}

.server-data-group {
  margin-top: 0.5rem;
}

.server-data-group:first-child {
  margin-top: 0;
}

.server-data-title {
  font-weight: 600;
  color: #000;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.server-data-item {
  padding: 0.4rem;
  margin-bottom: 0.3rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  color: #000;
  word-break: break-all;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.server-data-task-label {
  font-weight: 600;
  color: #000;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.btn-save-success {
  padding: 0.2rem 0.6rem;
  font-size: 0.7rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.2s;
}

.btn-save-success:hover {
  background: #218838;
}

.btn-save-success:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
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

.on-chain-balance {
  color: #495057;
  font-size: 0.8rem;
}

.balance-value {
  font-weight: 600;
  margin-left: 0.25rem;
}

.balance-value.success {
  color: #28a745;
}

.balance-value.error {
  color: #dc3545;
}

.balance-value.loading {
  color: #6c757d;
  font-style: italic;
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

.btn-fetch-server-data {
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-fetch-server-data:hover:not(:disabled) {
  background: #138496;
}

.btn-fetch-server-data:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
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

/* Trending自动完成下拉框样式 */
.trending-autocomplete-wrapper {
  position: relative;
  width: 100%;
}

.trending-autocomplete-wrapper input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.3s;
  font-family: inherit;
  box-sizing: border-box;
}

.trending-autocomplete-wrapper input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.trending-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 300px;
  overflow-y: auto;
  z-index: 10000;
  margin-top: 4px;
}

/* 查询区域的下拉菜单需要更高的z-index */
.query-section .trending-autocomplete-wrapper {
  position: relative;
  z-index: 1;
}

.query-section .trending-dropdown {
  z-index: 10001;
}

.trending-dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.trending-dropdown-item:last-child {
  border-bottom: none;
}

.trending-dropdown-item:hover {
  background-color: #f8f9fa;
}

.trending-dropdown-item:active {
  background-color: #e9ecef;
}

/* 查询区域样式 */
.query-section {
  margin-bottom: 1rem;
  overflow: visible;
  padding: 1rem 1.5rem;
}

.query-section .section-header-with-filter {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  overflow: visible;
  position: relative;
  margin-bottom: 0;
}

.query-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  width: 100%;
}

.query-controls {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  flex: 0 0 auto;
}

.query-controls .form-group {
  flex: 0 0 auto;
  min-width: 500px;
  max-width: none;
}

.query-controls .form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.query-result {
  flex: 1;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  background-color: #f8f9fa;
  min-width: 300px;
}

.query-result-error {
  color: #721c24;
  font-weight: 500;
  font-size: 13px;
}

.query-result-reason {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #fff;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
  font-size: 12px;
  line-height: 1.4;
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

.btn-success {
  background: linear-gradient(135deg, #28a745 0%, #218838 100%);
  color: white;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
}

.btn-active {
  background: #28a745 !important;
  border-color: #28a745 !important;
  box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.5);
  font-weight: bold;
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

.status-waiting {
  background: #fff3cd;
  color: #856404;
}

.status-blacklisted {
  background: #f8d7da;
  color: #721c24;
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
  overflow: auto;
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: 1rem;
  }
  
  .modal-content {
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 1rem;
  }
  
  .modal-header h3 {
    font-size: 1.1rem;
  }
  
  .modal-form {
    padding: 1rem;
  }
  
  .modal-actions {
    padding: 1rem;
    flex-wrap: wrap;
  }
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 0;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-x: auto;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-content.large {
  max-width: 2000px;
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

.modal-body {
  padding: 1.5rem 2rem;
  max-height: 70vh;
  overflow-x: auto;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
  z-index: 1;
}

.data-table tbody tr:hover {
  background-color: #f8f9fa;
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

.config-filter-toolbar .filter-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  width: 150px;
  background: white;
  cursor: pointer;
}

.config-filter-toolbar .filter-select:focus {
  outline: none;
  border-color: #007bff;
}

.config-list {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
}

.config-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.config-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.config-table thead {
  background: #f8f9fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

.config-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #dee2e6;
  font-size: 14px;
}

.config-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background-color 0.2s;
}

.config-table tbody tr:hover {
  background-color: #f8f9fa;
}

.config-table tbody tr:last-child {
  border-bottom: none;
}

.config-table td {
  padding: 12px;
  vertical-align: middle;
  font-size: 14px;
}

.config-table td .switch-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.orderbook-display {
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}

.orderbook-valid {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

.orderbook-invalid {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

.orderbook-line {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.orderbook-line:last-child {
  margin-bottom: 0;
}

.orderbook-label {
  font-weight: 600;
  min-width: 35px;
}

.orderbook-depth {
  color: #666;
  font-size: 11px;
}

.orderbook-empty {
  color: #999;
  font-size: 12px;
  text-align: center;
  padding: 8px;
}

.config-table-row .config-index {
  font-size: 1rem;
  font-weight: 600;
  color: #667eea;
  text-align: center;
}

.table-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.table-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
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
  white-space: nowrap;
  min-width: 1.5rem;
  text-align: center;
}

/* 对冲模式开关中的文本样式 */
.hedge-mode-switch .switch-text {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  min-width: 1.2rem;
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

