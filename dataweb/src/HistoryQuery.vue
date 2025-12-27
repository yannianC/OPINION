<template>
  <div class="history-query-page">
    <h1 class="page-title">历史查询</h1>
    
    <!-- 查询工具栏 -->
    <div class="toolbar">
      <el-date-picker
        v-model="historyDate"
        type="date"
        placeholder="选择日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        size="default"
        style="width: 160px"
      />
      <el-button type="primary" @click="loadHistoryData" :loading="loading" :disabled="!historyDate">
        查询历史
      </el-button>
      <span style="margin: 0 10px; color: #666; font-weight: 600;">vs</span>
      <el-date-picker
        v-model="historyDate2"
        type="date"
        placeholder="选择日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        size="default"
        style="width: 160px"
      />
      <el-button type="primary" @click="loadHistoryData2" :loading="loading2" :disabled="!historyDate2">
        查询历史
      </el-button>
    </div>

    <!-- 数据总计表格（默认折叠） -->
    <div class="summary-section">
      <div class="summary-header">
        <h2 class="summary-title">数据总计{{ historyDate ? ` (${historyDate})` : '' }}</h2>
        <el-button 
          type="text" 
          @click="summaryExpanded = !summaryExpanded"
          class="collapse-btn"
        >
          {{ summaryExpanded ? '收起' : '展开' }}
        </el-button>
      </div>
      
      <el-collapse-transition>
        <div v-show="summaryExpanded">
          <!-- 总计信息 -->
          <div class="summary-totals">
            <div class="total-item">
              <span class="total-label">余额总计:</span>
              <span class="total-value">{{ formatNumber(summaryTotals.totalBalance) }}</span>
              <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(calculateChange(summaryTotals.totalBalance, summaryTotals2.totalBalance))">
                {{ formatChange(calculateChange(summaryTotals.totalBalance, summaryTotals2.totalBalance)) }}
              </span>
            </div>
            <div class="total-item">
              <span class="total-label">Portfolio总计:</span>
              <span class="total-value">{{ formatNumber(summaryTotals.totalPortfolio) }}</span>
              <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(calculateChange(summaryTotals.totalPortfolio, summaryTotals2.totalPortfolio))">
                {{ formatChange(calculateChange(summaryTotals.totalPortfolio, summaryTotals2.totalPortfolio)) }}
              </span>
            </div>
          </div>
          
          <el-table 
            :data="eventTableData" 
            border 
            style="width: 100%"
            v-loading="loading"
            max-height="500px"
          >
            <el-table-column prop="eventName" label="事件名" width="400" fixed>
              <template #default="scope">
                <div class="event-name-cell">{{ scope.row.eventName }}</div>
              </template>
            </el-table-column>

            <el-table-column label="yes持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesPosition, b.yesPosition)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.yesPosition) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.yesPosition) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'yesPosition'))">
                  {{ formatChange(getEventChange(scope.row, 'yesPosition')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="no持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noPosition, b.noPosition)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.noPosition) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.noPosition) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'noPosition'))">
                  {{ formatChange(getEventChange(scope.row, 'noPosition')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="链上yes持仓数量" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainYesPosition, b.chainYesPosition)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.chainYesPosition) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.chainYesPosition) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'chainYesPosition'))">
                  {{ formatChange(getEventChange(scope.row, 'chainYesPosition')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="链上no持仓数量" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainNoPosition, b.chainNoPosition)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.chainNoPosition) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.chainNoPosition) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'chainNoPosition'))">
                  {{ formatChange(getEventChange(scope.row, 'chainNoPosition')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="实际差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.actualDiff, b.actualDiff)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.actualDiff) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.actualDiff) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'actualDiff'))">
                  {{ formatChange(getEventChange(scope.row, 'actualDiff')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="链上差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainActualDiff, b.chainActualDiff)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.chainActualDiff) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.chainActualDiff) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'chainActualDiff'))">
                  {{ formatChange(getEventChange(scope.row, 'chainActualDiff')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="挂单yes数量" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderYes, b.orderYes)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.orderYes) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.orderYes) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'orderYes'))">
                  {{ formatChange(getEventChange(scope.row, 'orderYes')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="挂单no数量" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderNo, b.orderNo)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.orderNo) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.orderNo) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'orderNo'))">
                  {{ formatChange(getEventChange(scope.row, 'orderNo')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="挂单差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderDiff, b.orderDiff)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.orderDiff) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.orderDiff) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'orderDiff'))">
                  {{ formatChange(getEventChange(scope.row, 'orderDiff')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="成交后差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.finalDiff, b.finalDiff)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.finalDiff) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.finalDiff) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'finalDiff'))">
                  {{ formatChange(getEventChange(scope.row, 'finalDiff')) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="链上成交后差额" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainFinalDiff, b.chainFinalDiff)">
              <template #default="scope">
                <span :class="parseFloat(scope.row.chainFinalDiff) >= 0 ? 'positive' : 'negative'">
                  {{ formatNumber(scope.row.chainFinalDiff) }}
                </span>
                <span v-if="eventTableData2.length > 0" class="change-value" :class="getChangeClass(getEventChange(scope.row, 'chainFinalDiff'))">
                  {{ formatChange(getEventChange(scope.row, 'chainFinalDiff')) }}
                </span>
              </template>
            </el-table-column>
          </el-table>

          <!-- 第二个日期的数据总计表格 -->
          <div v-if="eventTableData2.length > 0" style="margin-top: 30px;">
            <h3 class="summary-title" style="margin-bottom: 15px;">数据总计{{ historyDate2 ? ` (${historyDate2})` : '' }}</h3>
            <div class="summary-totals">
              <div class="total-item">
                <span class="total-label">余额总计:</span>
                <span class="total-value">{{ formatNumber(summaryTotals2.totalBalance) }}</span>
              </div>
              <div class="total-item">
                <span class="total-label">Portfolio总计:</span>
                <span class="total-value">{{ formatNumber(summaryTotals2.totalPortfolio) }}</span>
              </div>
            </div>
            
            <el-table 
              :data="eventTableData2" 
              border 
              style="width: 100%"
              v-loading="loading2"
              max-height="500px"
            >
              <el-table-column prop="eventName" label="事件名" width="400" fixed>
                <template #default="scope">
                  <div class="event-name-cell">{{ scope.row.eventName }}</div>
                </template>
              </el-table-column>

              <el-table-column label="yes持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesPosition, b.yesPosition)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.yesPosition) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.yesPosition) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="no持仓数量" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noPosition, b.noPosition)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.noPosition) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.noPosition) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="链上yes持仓数量" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainYesPosition, b.chainYesPosition)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.chainYesPosition) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.chainYesPosition) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="链上no持仓数量" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainNoPosition, b.chainNoPosition)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.chainNoPosition) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.chainNoPosition) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="实际差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.actualDiff, b.actualDiff)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.actualDiff) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.actualDiff) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="链上差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainActualDiff, b.chainActualDiff)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.chainActualDiff) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.chainActualDiff) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="挂单yes数量" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderYes, b.orderYes)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.orderYes) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.orderYes) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="挂单no数量" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderNo, b.orderNo)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.orderNo) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.orderNo) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="挂单差额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.orderDiff, b.orderDiff)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.orderDiff) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.orderDiff) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="成交后差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.finalDiff, b.finalDiff)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.finalDiff) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.finalDiff) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="链上成交后差额" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainFinalDiff, b.chainFinalDiff)">
                <template #default="scope">
                  <span :class="parseFloat(scope.row.chainFinalDiff) >= 0 ? 'positive' : 'negative'">
                    {{ formatNumber(scope.row.chainFinalDiff) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-collapse-transition>
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
            <el-option label="监控" value="监控" />
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
        <div class="filter-item">
          <label>余额范围:</label>
          <el-input 
            v-model="filters.balanceMin" 
            placeholder="最小值"
            clearable
            size="small"
            style="width: 120px"
            type="number"
          />
          <span style="margin: 0 8px; color: #666;">-</span>
          <el-input 
            v-model="filters.balanceMax" 
            placeholder="最大值"
            clearable
            size="small"
            style="width: 120px"
            type="number"
          />
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showNoAddress" @change="applyFilters">
            显示无地址
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showDuplicateAddress" @change="applyFilters">
            显示地址重复
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showNoPoints" @change="applyFilters">
            显示无积分
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showNoPosition" @change="applyFilters">
            显示无持有仓位
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showHasDifference" @change="applyFilters">
            显示有信息差的
          </el-checkbox>
        </div>
        <div class="filter-item">
          <el-checkbox v-model="filters.showPositionTimeBeforeOpenTime" @change="applyFilters">
            显示仓位抓取时间小于打开时间的
          </el-checkbox>
        </div>
        <div class="filter-item">
          <label>打开时间大于:</label>
          <el-input 
            v-model.number="filters.openTimeGreaterThanHours" 
            placeholder="小时数"
            clearable
            size="small"
            style="width: 120px"
            type="number"
            min="0"
          />
          <span style="margin-left: 5px; color: #666;">小时</span>
        </div>
        <el-button type="primary" size="small" @click="applyFilters">应用筛选</el-button>
        <el-button size="small" @click="clearFilters">清除筛选</el-button>
        <el-button type="warning" size="small" @click="parseAllRows" :loading="parsingAll">
          全部解析
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="paginatedTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 600px)"
      :scrollbar-always-on="true"
    >
      <el-table-column prop="index" label="序号" width="80" align="center" fixed />
      
      <el-table-column label="电脑组" width="100" align="center" sortable :sort-method="(a, b) => sortByNumber(a.computeGroup, b.computeGroup)">
        <template #default="scope">
          {{ scope.row.computeGroup }}
        </template>
      </el-table-column>

      <el-table-column label="指纹浏览器编号" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.fingerprintNo, b.fingerprintNo)">
        <template #default="scope">
          {{ scope.row.fingerprintNo }}
        </template>
      </el-table-column>

      <el-table-column label="余额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.balance, b.balance)">
        <template #default="scope">
          {{ formatNumber(scope.row.balance) }}
        </template>
      </el-table-column>

      <el-table-column label="可用" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.p, b.p)">
        <template #default="scope">
          {{ formatNumber(scope.row.p) }}
        </template>
      </el-table-column>

      <el-table-column label="Portfolio" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.c, b.c)">
        <template #default="scope">
          {{ scope.row.c || '0' }}
        </template>
      </el-table-column>

      <el-table-column label="持有仓位" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && scope.row.a" class="position-list">
            <template v-if="filters.positionSearch">
              <template v-if="filterPositionsBySearch(getCachedPositions(scope.row.a), filters.positionSearch).length > 0">
                <div 
                  v-for="(pos, idx) in filterPositionsBySearch(getCachedPositions(scope.row.a), filters.positionSearch)" 
                  :key="`${scope.row.index}-pos-${idx}`" 
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
              </template>
              <span v-else class="empty-text">无匹配的仓位</span>
            </template>
            <template v-else>
              <div 
                v-for="(pos, idx) in getCachedPositions(scope.row.a)" 
                :key="`${scope.row.index}-pos-${idx}`" 
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
            </template>
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div v-else-if="scope.row.a" class="raw-data-text">
            {{ scope.row.a }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="链上信息" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && getChainInfo(scope.row)" class="position-list">
            <template v-if="filters.positionSearch">
              <template v-if="filterPositionsBySearch(getCachedPositions(getChainInfo(scope.row)), filters.positionSearch).length > 0">
                <div 
                  v-for="(pos, idx) in filterPositionsBySearch(getCachedPositions(getChainInfo(scope.row)), filters.positionSearch)" 
                  :key="`${scope.row.index}-chain-${idx}`" 
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
              </template>
              <span v-else class="empty-text">无匹配的仓位</span>
            </template>
            <template v-else>
              <div 
                v-for="(pos, idx) in getCachedPositions(getChainInfo(scope.row))" 
                :key="`${scope.row.index}-chain-${idx}`" 
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
            </template>
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div v-else-if="getChainInfo(scope.row)" class="raw-data-text">
            {{ getChainInfo(scope.row) }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="信息差" width="400">
        <template #default="scope">
          <div v-if="getPositionDifferences(scope.row).length > 0" class="position-list">
            <template v-if="filters.positionSearch">
              <template v-if="filterDifferencesBySearch(getPositionDifferences(scope.row), filters.positionSearch).length > 0">
                <div 
                  v-for="(diff, idx) in filterDifferencesBySearch(getPositionDifferences(scope.row), filters.positionSearch)" 
                  :key="`${scope.row.index}-diff-${idx}`" 
                  class="position-item"
                >
                  <div class="position-title">{{ diff.title }}</div>
                  <div class="position-details">
                    <span class="difference-value" :class="getDifferenceClass(diff.difference)">
                      信息差: {{ formatDifference(diff.difference) }}
                    </span>
                    <span class="position-amount">持有: {{ diff.holdingAmount }}</span>
                    <span class="position-amount">链上: {{ diff.chainAmount }}</span>
                  </div>
                </div>
              </template>
              <span v-else class="empty-text">无匹配的仓位</span>
            </template>
            <template v-else>
              <div 
                v-for="(diff, idx) in getPositionDifferences(scope.row)" 
                :key="`${scope.row.index}-diff-${idx}`" 
                class="position-item"
              >
                <div class="position-title">{{ diff.title }}</div>
                <div class="position-details">
                  <span class="difference-value" :class="getDifferenceClass(diff.difference)">
                    信息差: {{ formatDifference(diff.difference) }}
                  </span>
                  <span class="position-amount">持有: {{ diff.holdingAmount }}</span>
                  <span class="position-amount">链上: {{ diff.chainAmount }}</span>
                </div>
              </div>
            </template>
          </div>
          <span v-else class="empty-text">无差异</span>
        </template>
      </el-table-column>

      <el-table-column label="挂单仓位" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && scope.row.b" class="position-list">
            <template v-if="filters.positionSearch">
              <template v-if="filterOrdersBySearch(getCachedOrders(scope.row.b), filters.positionSearch).length > 0">
                <div 
                  v-for="(order, idx) in filterOrdersBySearch(getCachedOrders(scope.row.b), filters.positionSearch)" 
                  :key="`${scope.row.index}-order-${idx}`" 
                  class="position-item"
                >
                  <div class="position-title">{{ order.title }}</div>
                  <div class="position-details">
                    <el-tag :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" size="small">
                      {{ order.option || order.buySellDirection }}
                    </el-tag>
                    <span class="position-amount">未成交: {{ formatNumber(order.pending) }}</span>
                    <span class="position-price">价格: {{ order.price }}</span>
                  </div>
                </div>
              </template>
              <span v-else class="empty-text">无匹配的仓位</span>
            </template>
            <template v-else>
              <div 
                v-for="(order, idx) in getCachedOrders(scope.row.b)" 
                :key="`${scope.row.index}-order-${idx}`" 
                class="position-item"
              >
                <div class="position-title">{{ order.title }}</div>
                <div class="position-details">
                  <el-tag :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" size="small">
                    {{ order.option || order.buySellDirection }}
                  </el-tag>
                  <span class="position-amount">未成交: {{ formatNumber(order.pending) }}</span>
                  <span class="position-price">价格: {{ order.price }}</span>
                </div>
              </div>
            </template>
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div v-else-if="scope.row.b" class="raw-data-text">
            {{ scope.row.b }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="仓位抓取时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.d, b.d)">
        <template #default="scope">
          {{ formatTime(scope.row.d) }}
        </template>
      </el-table-column>

      <el-table-column label="打开时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.f, b.f)">
        <template #default="scope">
          {{ formatTime(scope.row.f) }}
        </template>
      </el-table-column>

      <el-table-column label="积分" width="400">
        <template #default="scope">
          <div v-if="scope.row.k" class="raw-data-text">
            {{ scope.row.k }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="scope">
          <el-button 
            type="warning" 
            size="small"
            @click="parseRow(scope.row)"
            :loading="scope.row.parsing"
            :disabled="isRowParsed(scope.row)"
          >
            {{ isRowParsed(scope.row) ? '已解析' : '解析' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页组件 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPageNum"
        :page-size="pageSize"
        :total="filteredTableData.length"
        layout="total, prev, pager, next, jumper"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 第二个日期的筛选区域和数据表格 -->
    <div v-if="tableData2.length > 0" style="margin-top: 40px; border-top: 2px solid #e4e7ed; padding-top: 20px;">
      <h2 class="page-title" style="margin-bottom: 20px;">数据列表{{ historyDate2 ? ` (${historyDate2})` : '' }}</h2>
      
      <!-- 筛选区域 -->
      <div class="filter-container">
        <div class="filter-row">
          <div class="filter-item">
            <label>电脑组:</label>
            <el-input 
              v-model="filters2.computeGroup" 
              placeholder="如: 1 或 1,2,3 或 1-3"
              clearable
              size="small"
              style="width: 200px"
            />
          </div>
          <div class="filter-item">
            <label>浏览器编号:</label>
            <el-input 
              v-model="filters2.fingerprintNo" 
              placeholder="如: 4001 或 4001,4002 或 4001-4010"
              clearable
              size="small"
              style="width: 250px"
            />
          </div>
          <div class="filter-item">
            <label>平台:</label>
            <el-select 
              v-model="filters2.platform" 
              placeholder="全部"
              clearable
              size="small"
              style="width: 120px"
            >
              <el-option label="OP" value="OP" />
              <el-option label="监控" value="监控" />
            </el-select>
          </div>
          <div class="filter-item">
            <label>仓位搜索:</label>
            <el-input 
              v-model="filters2.positionSearch" 
              placeholder="搜索持有仓位或挂单名称"
              clearable
              size="small"
              style="width: 250px"
            />
          </div>
          <div class="filter-item">
            <label>余额范围:</label>
            <el-input 
              v-model="filters2.balanceMin" 
              placeholder="最小值"
              clearable
              size="small"
              style="width: 120px"
              type="number"
            />
            <span style="margin: 0 8px; color: #666;">-</span>
            <el-input 
              v-model="filters2.balanceMax" 
              placeholder="最大值"
              clearable
              size="small"
              style="width: 120px"
              type="number"
            />
          </div>
          <div class="filter-item">
            <el-checkbox v-model="filters2.showNoAddress" @change="applyFilters2">
              显示无地址
            </el-checkbox>
          </div>
          <div class="filter-item">
            <el-checkbox v-model="filters2.showDuplicateAddress" @change="applyFilters2">
              显示地址重复
            </el-checkbox>
          </div>
          <div class="filter-item">
            <el-checkbox v-model="filters2.showNoPoints" @change="applyFilters2">
              显示无积分
            </el-checkbox>
          </div>
          <div class="filter-item">
            <el-checkbox v-model="filters2.showNoPosition" @change="applyFilters2">
              显示无持有仓位
            </el-checkbox>
          </div>
          <div class="filter-item">
            <el-checkbox v-model="filters2.showHasDifference" @change="applyFilters2">
              显示有信息差的
            </el-checkbox>
          </div>
          <div class="filter-item">
            <el-checkbox v-model="filters2.showPositionTimeBeforeOpenTime" @change="applyFilters2">
              显示仓位抓取时间小于打开时间的
            </el-checkbox>
          </div>
          <div class="filter-item">
            <label>打开时间大于:</label>
            <el-input 
              v-model.number="filters2.openTimeGreaterThanHours" 
              placeholder="小时数"
              clearable
              size="small"
              style="width: 120px"
              type="number"
              min="0"
            />
            <span style="margin-left: 5px; color: #666;">小时</span>
          </div>
          <el-button type="primary" size="small" @click="applyFilters2">应用筛选</el-button>
          <el-button size="small" @click="clearFilters2">清除筛选</el-button>
          <el-button type="warning" size="small" @click="parseAllRows2" :loading="parsingAll2">
            全部解析
          </el-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table 
        :data="paginatedTableData2" 
        border 
        style="width: 100%"
        v-loading="loading2"
        height="calc(100vh - 600px)"
        :scrollbar-always-on="true"
      >
        <el-table-column prop="index" label="序号" width="80" align="center" fixed />
        
        <el-table-column label="电脑组" width="100" align="center" sortable :sort-method="(a, b) => sortByNumber(a.computeGroup, b.computeGroup)">
          <template #default="scope">
            {{ scope.row.computeGroup }}
          </template>
        </el-table-column>

        <el-table-column label="指纹浏览器编号" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.fingerprintNo, b.fingerprintNo)">
          <template #default="scope">
            {{ scope.row.fingerprintNo }}
          </template>
        </el-table-column>

        <el-table-column label="余额" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.balance, b.balance)">
          <template #default="scope">
            {{ formatNumber(scope.row.balance) }}
          </template>
        </el-table-column>

        <el-table-column label="可用" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.p, b.p)">
          <template #default="scope">
            {{ formatNumber(scope.row.p) }}
          </template>
        </el-table-column>

        <el-table-column label="Portfolio" width="120" align="center" sortable :sort-method="(a, b) => sortByNumber(a.c, b.c)">
          <template #default="scope">
            {{ scope.row.c || '0' }}
          </template>
        </el-table-column>

        <el-table-column label="持有仓位" width="400">
          <template #default="scope">
            <div v-if="isRowParsed2(scope.row) && scope.row.a" class="position-list">
              <template v-if="filters2.positionSearch">
                <template v-if="filterPositionsBySearch(getCachedPositions2(scope.row.a), filters2.positionSearch).length > 0">
                  <div 
                    v-for="(pos, idx) in filterPositionsBySearch(getCachedPositions2(scope.row.a), filters2.positionSearch)" 
                    :key="`${scope.row.index}-pos-${idx}`" 
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
                </template>
                <span v-else class="empty-text">无匹配的仓位</span>
              </template>
              <template v-else>
                <div 
                  v-for="(pos, idx) in getCachedPositions2(scope.row.a)" 
                  :key="`${scope.row.index}-pos-${idx}`" 
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
              </template>
            </div>
            <div v-else-if="scope.row.a" class="raw-data-text">
              {{ scope.row.a }}
            </div>
            <span v-else class="empty-text">暂无数据</span>
          </template>
        </el-table-column>

        <el-table-column label="链上信息" width="400">
          <template #default="scope">
            <div v-if="isRowParsed2(scope.row) && getChainInfo2(scope.row)" class="position-list">
              <template v-if="filters2.positionSearch">
                <template v-if="filterPositionsBySearch(getCachedPositions2(getChainInfo2(scope.row)), filters2.positionSearch).length > 0">
                  <div 
                    v-for="(pos, idx) in filterPositionsBySearch(getCachedPositions2(getChainInfo2(scope.row)), filters2.positionSearch)" 
                    :key="`${scope.row.index}-chain-${idx}`" 
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
                </template>
                <span v-else class="empty-text">无匹配的仓位</span>
              </template>
              <template v-else>
                <div 
                  v-for="(pos, idx) in getCachedPositions2(getChainInfo2(scope.row))" 
                  :key="`${scope.row.index}-chain-${idx}`" 
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
              </template>
            </div>
            <div v-else-if="getChainInfo2(scope.row)" class="raw-data-text">
              {{ getChainInfo2(scope.row) }}
            </div>
            <span v-else class="empty-text">暂无数据</span>
          </template>
        </el-table-column>

        <el-table-column label="信息差" width="400">
          <template #default="scope">
            <div v-if="getPositionDifferences2(scope.row).length > 0" class="position-list">
              <template v-if="filters2.positionSearch">
                <template v-if="filterDifferencesBySearch(getPositionDifferences2(scope.row), filters2.positionSearch).length > 0">
                  <div 
                    v-for="(diff, idx) in filterDifferencesBySearch(getPositionDifferences2(scope.row), filters2.positionSearch)" 
                    :key="`${scope.row.index}-diff-${idx}`" 
                    class="position-item"
                  >
                    <div class="position-title">{{ diff.title }}</div>
                    <div class="position-details">
                      <span class="difference-value" :class="getDifferenceClass(diff.difference)">
                        信息差: {{ formatDifference(diff.difference) }}
                      </span>
                      <span class="position-amount">持有: {{ diff.holdingAmount }}</span>
                      <span class="position-amount">链上: {{ diff.chainAmount }}</span>
                    </div>
                  </div>
                </template>
                <span v-else class="empty-text">无匹配的仓位</span>
              </template>
              <template v-else>
                <div 
                  v-for="(diff, idx) in getPositionDifferences2(scope.row)" 
                  :key="`${scope.row.index}-diff-${idx}`" 
                  class="position-item"
                >
                  <div class="position-title">{{ diff.title }}</div>
                  <div class="position-details">
                    <span class="difference-value" :class="getDifferenceClass(diff.difference)">
                      信息差: {{ formatDifference(diff.difference) }}
                    </span>
                    <span class="position-amount">持有: {{ diff.holdingAmount }}</span>
                    <span class="position-amount">链上: {{ diff.chainAmount }}</span>
                  </div>
                </div>
              </template>
            </div>
            <span v-else class="empty-text">无差异</span>
          </template>
        </el-table-column>

        <el-table-column label="挂单仓位" width="400">
          <template #default="scope">
            <div v-if="isRowParsed2(scope.row) && scope.row.b" class="position-list">
              <template v-if="filters2.positionSearch">
                <template v-if="filterOrdersBySearch(getCachedOrders2(scope.row.b), filters2.positionSearch).length > 0">
                  <div 
                    v-for="(order, idx) in filterOrdersBySearch(getCachedOrders2(scope.row.b), filters2.positionSearch)" 
                    :key="`${scope.row.index}-order-${idx}`" 
                    class="position-item"
                  >
                    <div class="position-title">{{ order.title }}</div>
                    <div class="position-details">
                      <el-tag :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" size="small">
                        {{ order.option || order.buySellDirection }}
                      </el-tag>
                      <span class="position-amount">未成交: {{ formatNumber(order.pending) }}</span>
                      <span class="position-price">价格: {{ order.price }}</span>
                    </div>
                  </div>
                </template>
                <span v-else class="empty-text">无匹配的仓位</span>
              </template>
              <template v-else>
                <div 
                  v-for="(order, idx) in getCachedOrders2(scope.row.b)" 
                  :key="`${scope.row.index}-order-${idx}`" 
                  class="position-item"
                >
                  <div class="position-title">{{ order.title }}</div>
                  <div class="position-details">
                    <el-tag :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" size="small">
                      {{ order.option || order.buySellDirection }}
                    </el-tag>
                    <span class="position-amount">未成交: {{ formatNumber(order.pending) }}</span>
                    <span class="position-price">价格: {{ order.price }}</span>
                  </div>
                </div>
              </template>
            </div>
            <div v-else-if="scope.row.b" class="raw-data-text">
              {{ scope.row.b }}
            </div>
            <span v-else class="empty-text">暂无数据</span>
          </template>
        </el-table-column>

        <el-table-column label="仓位抓取时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.d, b.d)">
          <template #default="scope">
            {{ formatTime(scope.row.d) }}
          </template>
        </el-table-column>

        <el-table-column label="打开时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.f, b.f)">
          <template #default="scope">
            {{ formatTime(scope.row.f) }}
          </template>
        </el-table-column>

        <el-table-column label="积分" width="400">
          <template #default="scope">
            <div v-if="scope.row.k" class="raw-data-text">
              {{ scope.row.k }}
            </div>
            <span v-else class="empty-text">暂无数据</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="scope">
            <el-button 
              type="warning" 
              size="small"
              @click="parseRow2(scope.row)"
              :loading="scope.row.parsing"
              :disabled="isRowParsed2(scope.row)"
            >
              {{ isRowParsed2(scope.row) ? '已解析' : '解析' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPageNum2"
          :page-size="pageSize"
          :total="filteredTableData2.length"
          layout="total, prev, pager, next, jumper"
          @current-change="handlePageChange2"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'

const loading = ref(false)
const historyDate = ref(null)
const summaryExpanded = ref(false)
const parsingAll = ref(false)
const currentPageNum = ref(1)
const pageSize = 50

// 第二个日期的相关变量
const loading2 = ref(false)
const historyDate2 = ref(null)
const parsingAll2 = ref(false)
const currentPageNum2 = ref(1)

// 表格数据
const tableData = shallowRef([])
const parsedDataCache = new Map()
const parsedRowsSet = ref(new Set())
const chainDataMap = ref(new Map())  // 链上信息数据映射，key为wallet_address（小写），value为链上信息字符串

// 第二个日期的表格数据
const tableData2 = shallowRef([])
const parsedDataCache2 = new Map()
const parsedRowsSet2 = ref(new Set())
const chainDataMap2 = ref(new Map())

// 筛选
const filters = ref({
  computeGroup: '',
  fingerprintNo: '',
  platform: '',
  positionSearch: '',
  balanceMin: '',
  balanceMax: '',
  showNoAddress: false,
  showDuplicateAddress: false,
  showNoPoints: false,
  showNoPosition: false,  // 显示无持有仓位
  openTimeGreaterThanHours: null,  // 打开时间大于X小时
  showHasDifference: false,  // 显示有信息差的
  showPositionTimeBeforeOpenTime: false  // 显示仓位抓取时间小于打开时间的
})

// 第二个日期的筛选
const filters2 = ref({
  computeGroup: '',
  fingerprintNo: '',
  platform: '',
  positionSearch: '',
  balanceMin: '',
  balanceMax: '',
  showNoAddress: false,
  showDuplicateAddress: false,
  showNoPoints: false,
  showNoPosition: false,
  openTimeGreaterThanHours: null,
  showHasDifference: false,
  showPositionTimeBeforeOpenTime: false
})

// 事件统计数据
const eventTableData = ref([])
const eventTableData2 = ref([])

// 总计数据
const summaryTotals = ref({
  totalBalance: 0,
  totalPortfolio: 0
})
const summaryTotals2 = ref({
  totalBalance: 0,
  totalPortfolio: 0
})

/**
 * 解析筛选条件的电脑组和浏览器编号
 */
const parseFilterValues = (value) => {
  if (!value) return []
  const result = new Set()
  const parts = value.split(/[,;，；]/)
  
  for (const part of parts) {
    const trimmed = part.trim()
    if (!trimmed) continue
    
    // 检查是否是范围格式（如：1-3 或 4001-4010）
    const rangeMatch = trimmed.match(/^(\d+)-(\d+)$/)
    if (rangeMatch) {
      const start = parseInt(rangeMatch[1])
      const end = parseInt(rangeMatch[2])
      if (start <= end) {
        for (let i = start; i <= end; i++) {
          result.add(String(i))
        }
      }
    } else {
      result.add(trimmed)
    }
  }
  
  return Array.from(result)
}

/**
 * 过滤后的表格数据
 */
const filteredTableData = computed(() => {
  const data = tableData.value
  const filterVals = filters.value
  
  // 计算地址重复情况
  const addressCountMap = new Map()
  if (filterVals.showDuplicateAddress) {
    for (const row of data) {
      if (row.h && row.h.trim()) {
        const address = row.h.trim()
        addressCountMap.set(address, (addressCountMap.get(address) || 0) + 1)
      }
    }
  }
  
  const computeGroups = parseFilterValues(filterVals.computeGroup)
  const fingerprintNos = parseFilterValues(filterVals.fingerprintNo)
  const computeGroupSet = new Set(computeGroups)
  const fingerprintNoSet = new Set(fingerprintNos)
  const searchTerm = filterVals.positionSearch ? filterVals.positionSearch.toLowerCase() : ''
  
  const hasFilters = computeGroups.length > 0 || 
                    fingerprintNos.length > 0 || 
                    filterVals.platform || 
                    filterVals.positionSearch ||
                    filterVals.balanceMin ||
                    filterVals.balanceMax ||
                    filterVals.showNoAddress ||
                    filterVals.showDuplicateAddress ||
                    filterVals.showNoPoints ||
                    filterVals.showNoPosition ||
                    filterVals.showHasDifference ||
                    filterVals.showPositionTimeBeforeOpenTime ||
                    (filterVals.openTimeGreaterThanHours !== null && filterVals.openTimeGreaterThanHours !== undefined && filterVals.openTimeGreaterThanHours !== '')
  
  if (!hasFilters) {
    return data
  }
  
  return data.filter(row => {
    // 电脑组筛选
    if (computeGroupSet.size > 0 && !computeGroupSet.has(String(row.computeGroup))) {
      return false
    }
    
    // 浏览器编号筛选
    if (fingerprintNoSet.size > 0 && !fingerprintNoSet.has(String(row.fingerprintNo))) {
      return false
    }
    
    // 平台筛选
    if (filterVals.platform && row.platform !== filterVals.platform) {
      return false
    }
    
    // 仓位搜索筛选（检查持有仓位、挂单仓位和链上信息）
    if (searchTerm) {
      // 检查持有仓位
      let hasMatch = false
      if (row.a) {
        const holdingPositions = parsePositions(row.a)
        hasMatch = holdingPositions.some(pos => 
          pos.title && pos.title.toLowerCase().includes(searchTerm)
        )
      }
      // 检查挂单仓位
      if (!hasMatch && row.b) {
        const orders = parseOrders(row.b)
        hasMatch = orders.some(order => 
          order.title && order.title.toLowerCase().includes(searchTerm)
        )
      }
      // 检查链上信息
      if (!hasMatch) {
        const chainInfo = getChainInfo(row)
        if (chainInfo) {
          const chainPositions = parsePositions(chainInfo)
          hasMatch = chainPositions.some(pos => 
            pos.title && pos.title.toLowerCase().includes(searchTerm)
          )
        }
      }
      if (!hasMatch) {
        return false
      }
    }
    
    // 余额范围筛选
    if (filterVals.balanceMin || filterVals.balanceMax) {
      const balance = parseFloat(row.balance) || 0
      if (filterVals.balanceMin && balance < parseFloat(filterVals.balanceMin)) {
        return false
      }
      if (filterVals.balanceMax && balance > parseFloat(filterVals.balanceMax)) {
        return false
      }
    }
    
    // 显示无地址筛选
    if (filterVals.showNoAddress) {
      if (row.h && row.h.trim()) {
        return false
      }
    }
    
    // 显示地址重复筛选
    if (filterVals.showDuplicateAddress) {
      if (!row.h || !row.h.trim()) {
        return false
      }
      const address = row.h.trim()
      const count = addressCountMap.get(address) || 0
      if (count <= 1) {
        return false
      }
    }
    
    // 显示无积分筛选
    if (filterVals.showNoPoints) {
      if (row.k && row.k.trim()) {
        return false
      }
    }
    
    // 显示无持有仓位筛选
    if (filterVals.showNoPosition) {
      if (row.a && row.a.trim()) {
        return false  // 有持有仓位，不显示
      }
    }
    
    // 显示有信息差的筛选
    if (filterVals.showHasDifference) {
      const differences = getPositionDifferences(row)
      if (differences.length === 0) {
        return false  // 没有信息差，不显示
      }
    }
    
    // 显示仓位抓取时间小于打开时间的筛选
    if (filterVals.showPositionTimeBeforeOpenTime) {
      if (!row.d || !row.f) {
        return false  // 缺少时间字段，不显示
      }
      const positionTime = typeof row.d === 'string' ? parseInt(row.d) : row.d
      const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
      if (isNaN(positionTime) || isNaN(openTime)) {
        return false  // 时间格式无效，不显示
      }
      if (positionTime >= openTime) {
        return false  // 仓位抓取时间不小于打开时间，不显示
      }
    }
    
    // 打开时间大于X小时筛选
    if (filterVals.openTimeGreaterThanHours !== null && filterVals.openTimeGreaterThanHours !== undefined && filterVals.openTimeGreaterThanHours !== '') {
      if (!row.f) {
        return false  // 没有打开时间的数据不显示
      }
      const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
      const now = Date.now()
      const hoursAgo = parseFloat(filterVals.openTimeGreaterThanHours)
      const thresholdTime = now - (hoursAgo * 60 * 60 * 1000)  // 转换为毫秒
      
      // 如果打开时间大于阈值时间（即打开时间更早），则显示
      if (openTime > thresholdTime) {
        return false  // 打开时间不够早，不显示
      }
    }
    
    return true
  })
})

/**
 * 分页后的表格数据
 */
const paginatedTableData = computed(() => {
  const filtered = filteredTableData.value
  const start = (currentPageNum.value - 1) * pageSize
  const end = start + pageSize
  return filtered.slice(start, end)
})

/**
 * 格式化数字
 */
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '0.00'
  const num = parseFloat(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

/**
 * 格式化时间
 */
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  // 将字符串时间戳转换为数字
  const timestampNum = typeof timestamp === 'string' ? parseInt(timestamp) : timestamp
  if (isNaN(timestampNum)) return ''
  const date = new Date(timestampNum)
  if (isNaN(date.getTime())) return ''
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
 * 数字排序方法
 */
const sortByNumber = (a, b) => {
  const numA = parseFloat(a) || 0
  const numB = parseFloat(b) || 0
  return numA - numB
}

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
        // 新格式：title|||option|||amount|||avgPrice
        let title = parts[0].trim()
        let option = parts[1].trim()
        let amount = parts[2].trim()
        let avgPrice = parts[3].trim()
        
        positions.push({
          title: title,
          option: option,
          amount: parseFloat(amount) || 0,
          avgPrice: avgPrice
        })
      } else if (partsLength >= 3) {
        // 新格式3字段：title|||option|||amount（链上数据格式）
        if (isNewFormat) {
          let title = parts[0].trim()
          let option = parts[1].trim()
          let amount = parts[2].trim()
          
          positions.push({
            title: title,
            option: option,
            amount: parseFloat(amount) || 0,
            avgPrice: ''
          })
        } else {
          // 旧格式3字段：title,option,amount
          positions.push({
            title: parts[0].trim(),
            option: parts[1].trim(),
            amount: parseFloat(parts[2].trim()) || 0,
            avgPrice: ''
          })
        }
      } else if (partsLength >= 2 && !isNewFormat) {
        // 旧格式2字段：title,amount
        positions.push({
          title: parts[0].trim(),
          option: '',
          amount: parseFloat(parts[1].trim()) || 0,
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
 * 解析挂单数据字符串
 */
const parseOrders = (ordersStr) => {
  if (!ordersStr) return []
  
  try {
    const orders = []
    const items = ordersStr.split(';')
    
    for (const item of items) {
      if (!item.trim()) continue
      
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 5) {
          const title = parts[0].trim()
          const buySellDirection = parts[1].trim()
          const option = parts[2].trim()
          const price = parts[3].trim()
          const progress = parts[4].trim()
          
          let pending = 0
          const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
          if (progressMatch) {
            const filled = parseFloat(progressMatch[1].replace(/,/g, '')) || 0
            const total = parseFloat(progressMatch[2].replace(/,/g, '')) || 0
            pending = total - filled
          }
          
          orders.push({
            title: title,
            buySellDirection: buySellDirection,
            option: option,
            price: price,
            pending: pending
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
 * 获取缓存的持仓数据
 */
const getCachedPositions = (posStr) => {
  if (!posStr) return []
  if (parsedDataCache.has(posStr)) {
    return parsedDataCache.get(posStr)
  }
  const parsed = parsePositions(posStr)
  parsedDataCache.set(posStr, parsed)
  return parsed
}

/**
 * 获取缓存的挂单数据
 */
const getCachedOrders = (ordersStr) => {
  if (!ordersStr) return []
  const cacheKey = `order_${ordersStr}`
  if (parsedDataCache.has(cacheKey)) {
    return parsedDataCache.get(cacheKey)
  }
  const parsed = parseOrders(ordersStr)
  parsedDataCache.set(cacheKey, parsed)
  return parsed
}

/**
 * 获取链上信息
 */
const getChainInfo = (row) => {
  if (!row.h) return ''
  const address = row.h.trim().toLowerCase()
  return chainDataMap.value.get(address) || ''
}

/**
 * 根据仓位搜索条件过滤持仓列表
 */
const filterPositionsBySearch = (positions, searchTerm) => {
  if (!searchTerm || !positions || positions.length === 0) return positions
  const lowerSearchTerm = searchTerm.toLowerCase()
  return positions.filter(pos => {
    return pos.title && pos.title.toLowerCase().includes(lowerSearchTerm)
  })
}

/**
 * 根据仓位搜索条件过滤挂单列表
 */
const filterOrdersBySearch = (orders, searchTerm) => {
  if (!searchTerm || !orders || orders.length === 0) return orders
  const lowerSearchTerm = searchTerm.toLowerCase()
  return orders.filter(order => {
    return order.title && order.title.toLowerCase().includes(lowerSearchTerm)
  })
}

/**
 * 根据仓位搜索条件过滤信息差列表
 */
const filterDifferencesBySearch = (differences, searchTerm) => {
  if (!searchTerm || !differences || differences.length === 0) return differences
  const lowerSearchTerm = searchTerm.toLowerCase()
  return differences.filter(diff => {
    return diff.title && diff.title.toLowerCase().includes(lowerSearchTerm)
  })
}

/**
 * 计算持有仓位和链上信息的信息差
 */
const getPositionDifferences = (row) => {
  const differences = []
  
  const chainInfo = getChainInfo(row)
  
  // 如果持有仓位没有且链上信息也没有，返回空数组
  if (!row.a && !chainInfo) return differences
  
  // 解析持有仓位
  const holdingPositions = row.a ? parsePositions(row.a) : []
  // 解析链上仓位
  const chainPositions = chainInfo ? parsePositions(chainInfo) : []
  
  // 创建链上仓位的映射（按title匹配，支持基础title匹配）
  const chainMap = new Map()
  for (const chainPos of chainPositions) {
    const titleKey = chainPos.title.split('###')[0].trim()
    const existing = chainMap.get(titleKey)
    if (existing) {
      existing.amount = (parseFloat(existing.amount) || 0) + (parseFloat(chainPos.amount) || 0)
    } else {
      chainMap.set(titleKey, {
        title: chainPos.title,
        amount: parseFloat(chainPos.amount) || 0
      })
    }
  }
  
  // 创建持有仓位的映射
  const holdingMap = new Map()
  for (const holdingPos of holdingPositions) {
    const titleKey = holdingPos.title.split('###')[0].trim()
    const existing = holdingMap.get(titleKey)
    if (existing) {
      existing.amount = (parseFloat(existing.amount) || 0) + (parseFloat(holdingPos.amount) || 0)
    } else {
      holdingMap.set(titleKey, {
        title: holdingPos.title,
        amount: parseFloat(holdingPos.amount) || 0
      })
    }
  }
  
  // 计算所有市场的差异
  const allTitles = new Set([...holdingMap.keys(), ...chainMap.keys()])
  
  // 如果持有仓位没有或链上信息没有，也要算成差额
  // 如果持有仓位没有但链上信息有，所有链上仓位都算差额
  if (!row.a && chainInfo && chainMap.size > 0) {
    for (const [titleKey, chain] of chainMap.entries()) {
      differences.push({
        title: chain.title,
        holdingAmount: '0.00',
        chainAmount: chain.amount.toFixed(2),
        difference: -chain.amount
      })
    }
  }
  // 如果持有仓位有但链上信息没有，所有持有仓位都算差额
  else if (row.a && !chainInfo && holdingMap.size > 0) {
    for (const [titleKey, holding] of holdingMap.entries()) {
      differences.push({
        title: holding.title,
        holdingAmount: holding.amount.toFixed(2),
        chainAmount: '0.00',
        difference: holding.amount
      })
    }
  }
  // 如果两者都有，计算差异
  else if (row.a && chainInfo) {
    for (const titleKey of allTitles) {
      const holding = holdingMap.get(titleKey)
      const chain = chainMap.get(titleKey)
      
      const holdingAmount = holding ? holding.amount : 0
      const chainAmount = chain ? chain.amount : 0
      const difference = holdingAmount - chainAmount
      
      // 只显示有差异的市场（差异绝对值大于等于1）
      if (Math.abs(difference) >= 1) {
        differences.push({
          title: holding ? holding.title : (chain ? chain.title : titleKey),
          holdingAmount: holdingAmount.toFixed(2),
          chainAmount: chainAmount.toFixed(2),
          difference: difference
        })
      }
    }
  }
  
  // 按差异绝对值排序
  differences.sort((a, b) => Math.abs(b.difference) - Math.abs(a.difference))
  
  return differences
}

/**
 * 格式化差异值
 */
const formatDifference = (diff) => {
  if (diff === null || diff === undefined) return '0.00'
  const sign = diff > 0 ? '+' : ''
  return `${sign}${diff.toFixed(2)}`
}

/**
 * 获取差异值的样式类
 */
const getDifferenceClass = (diff) => {
  if (diff === null || diff === undefined) return 'difference-zero'
  if (diff > 0) return 'difference-positive'
  if (diff < 0) return 'difference-negative'
  return 'difference-zero'
}

/**
 * 格式化链上信息的Markets数据
 */
const formatChainMarkets = (markets) => {
  if (!markets || !Array.isArray(markets)) return ''
  
  const formattedItems = []
  
  for (const market of markets) {
    const yesAmount = parseFloat(market.yes_amount || 0)
    const noAmount = parseFloat(market.no_amount || 0)
    const diff = yesAmount - noAmount
    
    // 当绝对值小于0.01时，不记录
    if (Math.abs(diff) < 0.01) {
      continue
    }
    
    // 判断YES的数量多还是NO的数量多
    const option = yesAmount > noAmount ? 'YES' : 'NO'
    const amount = diff.toFixed(2)
    
    formattedItems.push(`${market.title}|||${option}|||${amount}`)
  }
  
  return formattedItems.join(';')
}

/**
 * 加载链上数据
 */
const loadChainData = async (dateStr) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/getChainData?dateStr=${dateStr}`)
    
    if (response.data && response.data.data && response.data.data.items) {
      const newChainDataMap = new Map()
      
      for (const item of response.data.data.items) {
        if (item.wallet_address && item.markets) {
          const address = item.wallet_address.trim().toLowerCase()
          const formattedMarkets = formatChainMarkets(item.markets)
          if (formattedMarkets) {
            newChainDataMap.set(address, formattedMarkets)
          }
        }
      }
      
      chainDataMap.value = newChainDataMap
      console.log(`已加载 ${newChainDataMap.size} 个地址的链上信息`)
      return response.data.data
    }
    return null
  } catch (error) {
    console.error('加载链上数据失败:', error)
    ElMessage.warning('加载链上数据失败: ' + (error.message || '网络错误'))
    return null
  }
}

/**
 * 匹配事件名称和链上数据的title
 */
const matchEventName = (eventName, chainTitle) => {
  if (!eventName || !chainTitle) return false
  
  // 去除首尾空格后完全匹配
  const trimmedEvent = eventName.trim()
  const trimmedChain = chainTitle.trim()
  if (trimmedEvent === trimmedChain) return true
  
  // 去除###后面的部分后匹配
  const eventBase = trimmedEvent.split('###')[0].trim()
  const chainBase = trimmedChain.split('###')[0].trim()
  if (eventBase === chainBase && eventBase.length > 0) return true
  
  return false
}

/**
 * 检查行是否已解析
 */
const isRowParsed = (row) => {
  return parsedRowsSet.value.has(row.index)
}

/**
 * 解析单行数据
 */
const parseRow = async (row) => {
  row.parsing = true
  try {
    // 预解析持仓和挂单数据
    if (row.a) {
      getCachedPositions(row.a)
    }
    if (row.b) {
      getCachedOrders(row.b)
    }
    // 预解析链上信息
    const chainInfo = getChainInfo(row)
    if (chainInfo) {
      getCachedPositions(chainInfo)
    }
    parsedRowsSet.value.add(row.index)
  } catch (error) {
    console.error('解析失败:', error)
    ElMessage.error('解析失败')
  } finally {
    row.parsing = false
  }
}

/**
 * 解析所有行
 */
const parseAllRows = async () => {
  parsingAll.value = true
  try {
    const data = filteredTableData.value
    for (const row of data) {
      if (!isRowParsed(row)) {
        await parseRow(row)
      }
    }
    ElMessage.success('全部解析完成')
  } catch (error) {
    console.error('批量解析失败:', error)
    ElMessage.error('批量解析失败')
  } finally {
    parsingAll.value = false
  }
}

/**
 * 应用筛选
 */
const applyFilters = () => {
  currentPageNum.value = 1
}

/**
 * 清除筛选
 */
const clearFilters = () => {
  filters.value = {
    computeGroup: '',
    fingerprintNo: '',
    platform: '',
    positionSearch: '',
    balanceMin: '',
    balanceMax: '',
    showNoAddress: false,
    showDuplicateAddress: false,
    showNoPoints: false,
    showNoPosition: false,
    openTimeGreaterThanHours: null,
    showHasDifference: false,
    showPositionTimeBeforeOpenTime: false
  }
  currentPageNum.value = 1
}

/**
 * 分页改变
 */
const handlePageChange = (page) => {
  currentPageNum.value = page
}

/**
 * 计算事件统计数据
 */
const calculateEventStats = (data, chainData) => {
  const eventMap = new Map()
  
  // 处理账户持仓和挂单数据
  for (const row of data) {
    // 解析持仓数据
    if (row.a) {
      const positions = parsePositions(row.a)
      for (const pos of positions) {
        const eventName = pos.title
        if (!eventMap.has(eventName)) {
          eventMap.set(eventName, {
            eventName: eventName,
            yesPosition: 0,
            noPosition: 0,
            actualDiff: 0,
            orderYes: 0,
            orderNo: 0,
            orderDiff: 0,
            finalDiff: 0,
            chainYesPosition: 0,
            chainNoPosition: 0,
            chainActualDiff: 0,
            chainFinalDiff: 0
          })
        }
        
        const event = eventMap.get(eventName)
        const amount = Math.abs(pos.amount)
        
        let isYes = false
        let isNo = false
        
        if (eventName.includes('First to 5k')) {
          if (pos.option === 'GOLD') {
            isYes = true
          } else if (pos.option === 'ETH') {
            isNo = true
          }
        } else if (eventName.includes('Monad vs MegaETH')) {
          if (pos.option === 'Monad') {
            isYes = true
          } else if (pos.option === 'MegaETH') {
            isNo = true
          }
        } else {
          if (pos.option === 'YES' || (pos.amount >= 0 && !pos.option)) {
            isYes = true
          } else if (pos.option === 'NO' || pos.amount < 0) {
            isNo = true
          }
        }
        
        if (isYes) {
          event.yesPosition += amount
        } else if (isNo) {
          event.noPosition += amount
        }
      }
    }
    
    // 解析挂单数据
    if (row.b) {
      const orders = parseOrders(row.b)
      for (const order of orders) {
        const eventName = order.title
        if (!eventMap.has(eventName)) {
          eventMap.set(eventName, {
            eventName: eventName,
            yesPosition: 0,
            noPosition: 0,
            actualDiff: 0,
            orderYes: 0,
            orderNo: 0,
            orderDiff: 0,
            finalDiff: 0,
            chainYesPosition: 0,
            chainNoPosition: 0,
            chainActualDiff: 0,
            chainFinalDiff: 0
          })
        }
        
        const event = eventMap.get(eventName)
        const pending = order.pending
        const sign = order.buySellDirection === 'Buy' ? 1 : -1
        
        let isYes = false
        let isNo = false
        
        if (eventName.includes('First to 5k')) {
          if (order.option === 'GOLD') {
            isYes = true
          } else if (order.option === 'ETH') {
            isNo = true
          }
        } else if (eventName.includes('Monad vs MegaETH')) {
          if (order.option === 'Monad') {
            isYes = true
          } else if (order.option === 'MegaETH') {
            isNo = true
          }
        } else {
          if (order.option === 'YES') {
            isYes = true
          } else if (order.option === 'NO') {
            isNo = true
          }
        }
        
        if (isYes) {
          event.orderYes += sign * pending
        } else if (isNo) {
          event.orderNo += sign * pending
        }
      }
    }
  }
  
  // 处理链上数据
  if (chainData && chainData.items) {
    // 创建链上数据的映射（按title聚合，使用完整title作为key）
    const chainTitleMap = new Map()
    
    for (const item of chainData.items) {
      if (item.markets) {
        for (const market of item.markets) {
          const title = market.title.trim()
          const yesAmount = parseFloat(market.yes_amount || 0)
          const noAmount = parseFloat(market.no_amount || 0)
          
          // 使用完整title作为key，累加相同title的数据
          if (chainTitleMap.has(title)) {
            const existing = chainTitleMap.get(title)
            existing.yesAmount += yesAmount
            existing.noAmount += noAmount
          } else {
            chainTitleMap.set(title, {
              title: title,
              yesAmount: yesAmount,
              noAmount: noAmount
            })
          }
        }
      }
    }
    
    // 将链上数据匹配到事件
    for (const [chainTitle, chainData] of chainTitleMap.entries()) {
      // 尝试匹配已有的事件
      let matched = false
      for (const [eventName, event] of eventMap.entries()) {
        if (matchEventName(eventName, chainTitle)) {
          event.chainYesPosition += chainData.yesAmount
          event.chainNoPosition += chainData.noAmount
          matched = true
          break
        }
      }
      
      // 如果没有匹配到，创建新的事件（只包含链上数据）
      if (!matched) {
        eventMap.set(chainTitle, {
          eventName: chainTitle,
          yesPosition: 0,
          noPosition: 0,
          actualDiff: 0,
          orderYes: 0,
          orderNo: 0,
          orderDiff: 0,
          finalDiff: 0,
          chainYesPosition: chainData.yesAmount,
          chainNoPosition: chainData.noAmount,
          chainActualDiff: 0,
          chainFinalDiff: 0
        })
      }
    }
  }
  
  // 计算差额
  for (const event of eventMap.values()) {
    event.actualDiff = event.yesPosition - event.noPosition
    event.orderDiff = event.orderYes - event.orderNo
    event.finalDiff = event.actualDiff + event.orderDiff
    event.chainActualDiff = event.chainYesPosition - event.chainNoPosition
    // 链上成交后差额 = 链上差额 + 挂单差额
    event.chainFinalDiff = event.chainActualDiff + event.orderDiff
  }
  
  // 转换为数组并排序
  return Array.from(eventMap.values()).sort((a, b) => {
    return Math.abs(b.finalDiff) - Math.abs(a.finalDiff)
  })
}

/**
 * 计算总计数据（余额总计和Portfolio总计）
 */
const calculateSummaryTotals = (data) => {
  let totalBalance = 0
  let totalPortfolio = 0
  
  for (const row of data) {
    totalBalance += parseFloat(row.balance) || 0
    totalPortfolio += parseFloat(row.c) || 0
  }
  
  summaryTotals.value = {
    totalBalance: totalBalance,
    totalPortfolio: totalPortfolio
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
 * 获取事件的变化值
 */
const getEventChange = (row, field) => {
  if (eventTableData2.value.length === 0) return 0
  const event2 = eventTableData2.value.find(e => e.eventName === row.eventName)
  if (!event2) return 0
  const value1 = parseFloat(row[field]) || 0
  const value2 = parseFloat(event2[field]) || 0
  return value1 - value2
}

/**
 * 加载历史数据
 */
const loadHistoryData = async () => {
  if (!historyDate.value) {
    ElMessage.warning('请先选择日期')
    return
  }
  
  loading.value = true
  
  try {
    // 并行加载账户数据和链上数据
    const [accountResponse, chainData] = await Promise.all([
      axios.get(`${API_BASE_URL}/boost/findAccountConfigHist?dateStr=${historyDate.value}`),
      loadChainData(historyDate.value)
    ])
    
    if (accountResponse.data && accountResponse.data.data) {
      const serverData = accountResponse.data.data
      
      // 格式化数据
      const formattedData = serverData.map((item, index) => ({
        ...item,
        index: index + 1,
        platform: item.e || item.platform || 'OP',
        parsing: false
      }))
      
      tableData.value = formattedData
      parsedDataCache.clear()
      parsedRowsSet.value = new Set()
      currentPageNum.value = 1
      
      // 计算事件统计数据（包含链上数据）
      eventTableData.value = calculateEventStats(serverData, chainData)
      
      // 计算总计数据
      calculateSummaryTotals(serverData)
      
      ElMessage.success(`已加载 ${historyDate.value} 的历史数据，共 ${serverData.length} 条`)
    } else {
      ElMessage.warning('未获取到历史数据')
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
    ElMessage.error('加载历史数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 加载链上数据（第二个日期）
 */
const loadChainData2 = async (dateStr) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/getChainData?dateStr=${dateStr}`)
    
    if (response.data && response.data.data && response.data.data.items) {
      const newChainDataMap = new Map()
      
      for (const item of response.data.data.items) {
        if (item.wallet_address && item.markets) {
          const address = item.wallet_address.trim().toLowerCase()
          const formattedMarkets = formatChainMarkets(item.markets)
          if (formattedMarkets) {
            newChainDataMap.set(address, formattedMarkets)
          }
        }
      }
      
      chainDataMap2.value = newChainDataMap
      console.log(`已加载 ${newChainDataMap.size} 个地址的链上信息（第二个日期）`)
      return response.data.data
    }
    return null
  } catch (error) {
    console.error('加载链上数据失败:', error)
    ElMessage.warning('加载链上数据失败: ' + (error.message || '网络错误'))
    return null
  }
}

/**
 * 获取缓存的持仓数据（第二个日期）
 */
const getCachedPositions2 = (posStr) => {
  if (!posStr) return []
  if (parsedDataCache2.has(posStr)) {
    return parsedDataCache2.get(posStr)
  }
  const parsed = parsePositions(posStr)
  parsedDataCache2.set(posStr, parsed)
  return parsed
}

/**
 * 获取缓存的挂单数据（第二个日期）
 */
const getCachedOrders2 = (ordersStr) => {
  if (!ordersStr) return []
  const cacheKey = `order_${ordersStr}`
  if (parsedDataCache2.has(cacheKey)) {
    return parsedDataCache2.get(cacheKey)
  }
  const parsed = parseOrders(ordersStr)
  parsedDataCache2.set(cacheKey, parsed)
  return parsed
}

/**
 * 获取链上信息（第二个日期）
 */
const getChainInfo2 = (row) => {
  if (!row.h) return ''
  const address = row.h.trim().toLowerCase()
  return chainDataMap2.value.get(address) || ''
}

/**
 * 计算持有仓位和链上信息的信息差（第二个日期）
 */
const getPositionDifferences2 = (row) => {
  const differences = []
  
  const chainInfo = getChainInfo2(row)
  
  // 如果持有仓位没有且链上信息也没有，返回空数组
  if (!row.a && !chainInfo) return differences
  
  // 解析持有仓位
  const holdingPositions = row.a ? parsePositions(row.a) : []
  // 解析链上仓位
  const chainPositions = chainInfo ? parsePositions(chainInfo) : []
  
  // 创建链上仓位的映射（按title匹配，支持基础title匹配）
  const chainMap = new Map()
  for (const chainPos of chainPositions) {
    const titleKey = chainPos.title.split('###')[0].trim()
    const existing = chainMap.get(titleKey)
    if (existing) {
      existing.amount = (parseFloat(existing.amount) || 0) + (parseFloat(chainPos.amount) || 0)
    } else {
      chainMap.set(titleKey, {
        title: chainPos.title,
        amount: parseFloat(chainPos.amount) || 0
      })
    }
  }
  
  // 创建持有仓位的映射
  const holdingMap = new Map()
  for (const holdingPos of holdingPositions) {
    const titleKey = holdingPos.title.split('###')[0].trim()
    const existing = holdingMap.get(titleKey)
    if (existing) {
      existing.amount = (parseFloat(existing.amount) || 0) + (parseFloat(holdingPos.amount) || 0)
    } else {
      holdingMap.set(titleKey, {
        title: holdingPos.title,
        amount: parseFloat(holdingPos.amount) || 0
      })
    }
  }
  
  // 计算所有市场的差异
  const allTitles = new Set([...holdingMap.keys(), ...chainMap.keys()])
  
  // 如果持有仓位没有或链上信息没有，也要算成差额
  // 如果持有仓位没有但链上信息有，所有链上仓位都算差额
  if (!row.a && chainInfo && chainMap.size > 0) {
    for (const [titleKey, chain] of chainMap.entries()) {
      differences.push({
        title: chain.title,
        holdingAmount: '0.00',
        chainAmount: chain.amount.toFixed(2),
        difference: -chain.amount
      })
    }
  }
  // 如果持有仓位有但链上信息没有，所有持有仓位都算差额
  else if (row.a && !chainInfo && holdingMap.size > 0) {
    for (const [titleKey, holding] of holdingMap.entries()) {
      differences.push({
        title: holding.title,
        holdingAmount: holding.amount.toFixed(2),
        chainAmount: '0.00',
        difference: holding.amount
      })
    }
  }
  // 如果两者都有，计算差异
  else if (row.a && chainInfo) {
    for (const titleKey of allTitles) {
      const holding = holdingMap.get(titleKey)
      const chain = chainMap.get(titleKey)
      
      const holdingAmount = holding ? holding.amount : 0
      const chainAmount = chain ? chain.amount : 0
      const difference = holdingAmount - chainAmount
      
      // 只显示有差异的市场（差异绝对值大于等于1）
      if (Math.abs(difference) >= 1) {
        differences.push({
          title: holding ? holding.title : (chain ? chain.title : titleKey),
          holdingAmount: holdingAmount.toFixed(2),
          chainAmount: chainAmount.toFixed(2),
          difference: difference
        })
      }
    }
  }
  
  // 按差异绝对值排序
  differences.sort((a, b) => Math.abs(b.difference) - Math.abs(a.difference))
  
  return differences
}

/**
 * 检查行是否已解析（第二个日期）
 */
const isRowParsed2 = (row) => {
  return parsedRowsSet2.value.has(row.index)
}

/**
 * 解析单行数据（第二个日期）
 */
const parseRow2 = async (row) => {
  row.parsing = true
  try {
    // 预解析持仓和挂单数据
    if (row.a) {
      getCachedPositions2(row.a)
    }
    if (row.b) {
      getCachedOrders2(row.b)
    }
    // 预解析链上信息
    const chainInfo = getChainInfo2(row)
    if (chainInfo) {
      getCachedPositions2(chainInfo)
    }
    parsedRowsSet2.value.add(row.index)
  } catch (error) {
    console.error('解析失败:', error)
    ElMessage.error('解析失败')
  } finally {
    row.parsing = false
  }
}

/**
 * 解析所有行（第二个日期）
 */
const parseAllRows2 = async () => {
  parsingAll2.value = true
  try {
    const data = filteredTableData2.value
    for (const row of data) {
      if (!isRowParsed2(row)) {
        await parseRow2(row)
      }
    }
    ElMessage.success('全部解析完成')
  } catch (error) {
    console.error('批量解析失败:', error)
    ElMessage.error('批量解析失败')
  } finally {
    parsingAll2.value = false
  }
}

/**
 * 过滤后的表格数据（第二个日期）
 */
const filteredTableData2 = computed(() => {
  const data = tableData2.value
  const filterVals = filters2.value
  
  // 计算地址重复情况
  const addressCountMap = new Map()
  if (filterVals.showDuplicateAddress) {
    for (const row of data) {
      if (row.h && row.h.trim()) {
        const address = row.h.trim()
        addressCountMap.set(address, (addressCountMap.get(address) || 0) + 1)
      }
    }
  }
  
  const computeGroups = parseFilterValues(filterVals.computeGroup)
  const fingerprintNos = parseFilterValues(filterVals.fingerprintNo)
  const computeGroupSet = new Set(computeGroups)
  const fingerprintNoSet = new Set(fingerprintNos)
  const searchTerm = filterVals.positionSearch ? filterVals.positionSearch.toLowerCase() : ''
  
  const hasFilters = computeGroups.length > 0 || 
                    fingerprintNos.length > 0 || 
                    filterVals.platform || 
                    filterVals.positionSearch ||
                    filterVals.balanceMin ||
                    filterVals.balanceMax ||
                    filterVals.showNoAddress ||
                    filterVals.showDuplicateAddress ||
                    filterVals.showNoPoints ||
                    filterVals.showNoPosition ||
                    filterVals.showHasDifference ||
                    filterVals.showPositionTimeBeforeOpenTime ||
                    (filterVals.openTimeGreaterThanHours !== null && filterVals.openTimeGreaterThanHours !== undefined && filterVals.openTimeGreaterThanHours !== '')
  
  if (!hasFilters) {
    return data
  }
  
  return data.filter(row => {
    // 电脑组筛选
    if (computeGroupSet.size > 0 && !computeGroupSet.has(String(row.computeGroup))) {
      return false
    }
    
    // 浏览器编号筛选
    if (fingerprintNoSet.size > 0 && !fingerprintNoSet.has(String(row.fingerprintNo))) {
      return false
    }
    
    // 平台筛选
    if (filterVals.platform && row.platform !== filterVals.platform) {
      return false
    }
    
    // 仓位搜索筛选（检查持有仓位、挂单仓位和链上信息）
    if (searchTerm) {
      let hasMatch = false
      if (row.a) {
        const holdingPositions = parsePositions(row.a)
        hasMatch = holdingPositions.some(pos => 
          pos.title && pos.title.toLowerCase().includes(searchTerm)
        )
      }
      if (!hasMatch && row.b) {
        const orders = parseOrders(row.b)
        hasMatch = orders.some(order => 
          order.title && order.title.toLowerCase().includes(searchTerm)
        )
      }
      if (!hasMatch) {
        const chainInfo = getChainInfo2(row)
        if (chainInfo) {
          const chainPositions = parsePositions(chainInfo)
          hasMatch = chainPositions.some(pos => 
            pos.title && pos.title.toLowerCase().includes(searchTerm)
          )
        }
      }
      if (!hasMatch) {
        return false
      }
    }
    
    // 余额范围筛选
    if (filterVals.balanceMin || filterVals.balanceMax) {
      const balance = parseFloat(row.balance) || 0
      if (filterVals.balanceMin && balance < parseFloat(filterVals.balanceMin)) {
        return false
      }
      if (filterVals.balanceMax && balance > parseFloat(filterVals.balanceMax)) {
        return false
      }
    }
    
    // 显示无地址筛选
    if (filterVals.showNoAddress) {
      if (row.h && row.h.trim()) {
        return false
      }
    }
    
    // 显示地址重复筛选
    if (filterVals.showDuplicateAddress) {
      if (!row.h || !row.h.trim()) {
        return false
      }
      const address = row.h.trim()
      const count = addressCountMap.get(address) || 0
      if (count <= 1) {
        return false
      }
    }
    
    // 显示无积分筛选
    if (filterVals.showNoPoints) {
      if (row.k && row.k.trim()) {
        return false
      }
    }
    
    // 显示无持有仓位筛选
    if (filterVals.showNoPosition) {
      if (row.a && row.a.trim()) {
        return false
      }
    }
    
    // 显示有信息差的筛选
    if (filterVals.showHasDifference) {
      const differences = getPositionDifferences2(row)
      if (differences.length === 0) {
        return false
      }
    }
    
    // 显示仓位抓取时间小于打开时间的筛选
    if (filterVals.showPositionTimeBeforeOpenTime) {
      if (!row.d || !row.f) {
        return false
      }
      const positionTime = typeof row.d === 'string' ? parseInt(row.d) : row.d
      const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
      if (isNaN(positionTime) || isNaN(openTime)) {
        return false
      }
      if (positionTime >= openTime) {
        return false
      }
    }
    
    // 打开时间大于X小时筛选
    if (filterVals.openTimeGreaterThanHours !== null && filterVals.openTimeGreaterThanHours !== undefined && filterVals.openTimeGreaterThanHours !== '') {
      if (!row.f) {
        return false
      }
      const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
      const now = Date.now()
      const hoursAgo = parseFloat(filterVals.openTimeGreaterThanHours)
      const thresholdTime = now - (hoursAgo * 60 * 60 * 1000)
      
      if (openTime > thresholdTime) {
        return false
      }
    }
    
    return true
  })
})

/**
 * 分页后的表格数据（第二个日期）
 */
const paginatedTableData2 = computed(() => {
  const filtered = filteredTableData2.value
  const start = (currentPageNum2.value - 1) * pageSize
  const end = start + pageSize
  return filtered.slice(start, end)
})

/**
 * 应用筛选（第二个日期）
 */
const applyFilters2 = () => {
  currentPageNum2.value = 1
}

/**
 * 清除筛选（第二个日期）
 */
const clearFilters2 = () => {
  filters2.value = {
    computeGroup: '',
    fingerprintNo: '',
    platform: '',
    positionSearch: '',
    balanceMin: '',
    balanceMax: '',
    showNoAddress: false,
    showDuplicateAddress: false,
    showNoPoints: false,
    showNoPosition: false,
    openTimeGreaterThanHours: null,
    showHasDifference: false,
    showPositionTimeBeforeOpenTime: false
  }
  currentPageNum2.value = 1
}

/**
 * 分页改变（第二个日期）
 */
const handlePageChange2 = (page) => {
  currentPageNum2.value = page
}

/**
 * 加载历史数据（第二个日期）
 */
const loadHistoryData2 = async () => {
  if (!historyDate2.value) {
    ElMessage.warning('请先选择日期')
    return
  }
  
  loading2.value = true
  
  try {
    // 并行加载账户数据和链上数据
    const [accountResponse, chainData] = await Promise.all([
      axios.get(`${API_BASE_URL}/boost/findAccountConfigHist?dateStr=${historyDate2.value}`),
      loadChainData2(historyDate2.value)
    ])
    
    if (accountResponse.data && accountResponse.data.data) {
      const serverData = accountResponse.data.data
      
      // 格式化数据
      const formattedData = serverData.map((item, index) => ({
        ...item,
        index: index + 1,
        platform: item.e || item.platform || 'OP',
        parsing: false
      }))
      
      tableData2.value = formattedData
      parsedDataCache2.clear()
      parsedRowsSet2.value = new Set()
      currentPageNum2.value = 1
      
      // 计算事件统计数据（包含链上数据）
      eventTableData2.value = calculateEventStats(serverData, chainData)
      
      // 计算总计数据
      calculateSummaryTotals2(serverData)
      
      ElMessage.success(`已加载 ${historyDate2.value} 的历史数据，共 ${serverData.length} 条`)
    } else {
      ElMessage.warning('未获取到历史数据')
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
    ElMessage.error('加载历史数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading2.value = false
  }
}

/**
 * 计算总计数据（第二个日期）
 */
const calculateSummaryTotals2 = (data) => {
  let totalBalance = 0
  let totalPortfolio = 0
  
  for (const row of data) {
    totalBalance += parseFloat(row.balance) || 0
    totalPortfolio += parseFloat(row.c) || 0
  }
  
  summaryTotals2.value = {
    totalBalance: totalBalance,
    totalPortfolio: totalPortfolio
  }
}
</script>

<style scoped>
.history-query-page {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 200px);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.summary-section {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.summary-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.collapse-btn {
  padding: 0;
  font-size: 14px;
}

.filter-container {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.position-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.position-item {
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.position-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  word-break: break-word;
}

.position-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.position-amount {
  font-size: 12px;
  color: #666;
}

.position-price {
  font-size: 12px;
  color: #999;
}

.raw-data-text {
  font-size: 12px;
  color: #666;
  word-break: break-word;
  white-space: pre-wrap;
}

.empty-text {
  color: #999;
  font-style: italic;
}

.event-name-cell {
  font-size: 13px;
  line-height: 1.4;
  word-break: break-word;
}

.positive {
  color: #67c23a;
  font-weight: 600;
}

.negative {
  color: #f56c6c;
  font-weight: 600;
}

.difference-value {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  white-space: nowrap;
}

.difference-positive {
  background-color: rgba(103, 194, 58, 0.15);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.4);
}

.difference-negative {
  background-color: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.4);
}

.difference-zero {
  background-color: rgba(144, 147, 153, 0.15);
  color: #909399;
  border: 1px solid rgba(144, 147, 153, 0.3);
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.summary-totals {
  display: flex;
  gap: 30px;
  padding: 15px 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 15px;
  border: 1px solid #e4e7ed;
}

.total-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.total-label {
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.total-value {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.change-value {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.change-positive {
  background-color: rgba(103, 194, 58, 0.15);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.4);
}

.change-negative {
  background-color: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.4);
}

.change-zero {
  background-color: rgba(144, 147, 153, 0.15);
  color: #909399;
  border: 1px solid rgba(144, 147, 153, 0.3);
}
</style>

