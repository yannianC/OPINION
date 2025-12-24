<template>
  <div class="app-container">
    <!-- 页面导航 -->
    <div class="page-navigation">
      <el-button 
        :type="currentPage === 'list' ? 'primary' : 'default'"
        @click="currentPage = 'list'"
      >
        数据列表
      </el-button>
      <el-button 
        :type="currentPage === 'summary' ? 'primary' : 'default'"
        @click="currentPage = 'summary'"
      >
        数据总计
      </el-button>
      <el-button 
        :type="currentPage === 'history' ? 'primary' : 'default'"
        @click="currentPage = 'history'"
      >
        历史查询
      </el-button>
    </div>

    <!-- 数据列表页面 -->
    <div v-if="currentPage === 'list'">
      <h1 class="app-title">OP数据</h1>
      
      <!-- 顶部操作按钮 -->
      <div class="toolbar">
      <el-button type="primary" @click="addRows(1)">增加一行</el-button>
      <el-button type="primary" @click="addRows(10)">增加十行</el-button>
      <el-button type="success" @click="saveAll" :loading="saving">保存所有数据</el-button>
      <el-button type="info" @click="loadData" :loading="loading">刷新列表</el-button>
      
      <!-- 自动刷新控制 -->
      <div class="auto-refresh-control">
        <el-checkbox v-model="autoRefresh.enabled" @change="toggleAutoRefresh">
          自动刷新
        </el-checkbox>
        <el-input 
          v-model.number="autoRefresh.interval" 
          type="number"
          size="small"
          style="width: 80px"
          min="10"
          @blur="resetAutoRefresh"
        />
        <span>秒</span>
      </div>
      
      <el-button type="warning" @click="refreshAllPositions" :loading="refreshingAll">
        刷新全部仓位
      </el-button>
      <el-button type="danger" @click="refreshRedPositions" :loading="refreshingRed">
        刷新变红仓位
      </el-button>
      <el-button type="danger" @click="refreshRedPositionsOld" :loading="refreshingRedOld">
        刷新变红且超过30分钟仓位
      </el-button>
      <el-button type="success" @click="deduplicateAddresses" :loading="deduplicating">
        地址去重
      </el-button>
      <el-button type="primary" @click="getWalletAddresses" :loading="gettingWalletAddresses">
        获取钱包地址
      </el-button>
      <el-button type="info" @click="doSnapAccountConfig" :loading="snappingAccount">
        手动快照
      </el-button>
      <span class="red-count-label">变红仓位数量：<strong>{{ redPositionCount }}</strong></span>
    </div>
    
    <!-- 批量添加区域 -->
    <div class="batch-add-container">
      <div class="batch-add-row">
        <label>批量添加:</label>
        <el-input 
          v-model="batchAddInput" 
          placeholder="格式: 1,4001;2,4002;3,4003,4004,4005"
          clearable
          size="small"
          style="width: 500px"
        />
        <el-button type="primary" size="small" @click="batchAddAccounts">
          确认添加
        </el-button>
        <span class="batch-add-tip">（电脑组,浏览器ID;电脑组,浏览器ID...）</span>
      </div>
    </div>

    <!-- 批量删除区域 -->
    <div class="batch-add-container">
      <div class="batch-add-row">
        <label>批量删除:</label>
        <el-input 
          v-model="batchDeleteInput" 
          placeholder="格式: 4001,4002,4003 或 4001;4002;4003"
          clearable
          size="small"
          style="width: 500px"
        />
        <el-button type="danger" size="small" @click="batchDeleteAccounts" :loading="batchDeleting">
          确认删除
        </el-button>
        <span class="batch-add-tip">（浏览器ID，逗号或分号分隔）</span>
      </div>
    </div>

    <!-- 导出地址区域 -->
    <div class="batch-add-container">
      <div class="batch-add-row">
        <label>导出地址:</label>
        <el-input 
          v-model="exportAddressInput" 
          placeholder="格式: 4001,4002,4003 或 4001;4002;4003"
          clearable
          size="small"
          style="width: 500px"
        />
        <el-button type="primary" size="small" @click="exportAddresses" :loading="exportingAddresses">
          导出地址
        </el-button>
        <span class="batch-add-tip">（浏览器编号，逗号分隔，导出对应的地址(h)到txt文件）</span>
      </div>
    </div>

    <!-- 仓位时间配置区域 -->
    <div class="position-time-config-container">
      <div class="config-row">
        <label>忽略仓位时间的浏览器:</label>
        <el-input 
          v-model="positionTimeConfig.ignoredBrowsers" 
          placeholder="浏览器编号，逗号分隔，如: 4001,4002,4003"
          clearable
          size="small"
          style="width: 700px"
        />
        <el-button type="primary" size="small" @click="saveIgnoredBrowsers">
          确定并保存
        </el-button>
      </div>
      <div class="config-row">
        <el-checkbox v-model="positionTimeConfig.autoUpdate" @change="toggleAutoUpdate">
          自动更新打开时间大于最近
        </el-checkbox>
        <el-input 
          v-model.number="positionTimeConfig.updateThresholdMinutes" 
          type="number"
          size="small"
          style="width: 80px"
          min="1"
        />
        <span>分钟的仓位</span>
      </div>
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
          <el-checkbox v-model="filters.showHasDifference" @change="applyFilters">
            显示与链上信息有差额
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
        <div class="filter-item">
          <label>仓位抓取时间大于:</label>
          <el-input 
            v-model.number="filters.positionTimeGreaterThanHours" 
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
        <el-button type="success" size="small" @click="refreshFilteredPositions" :loading="refreshingFiltered">
          刷新筛选结果仓位
        </el-button>
      </div>
    </div>

    <!-- 积分总计区域 -->
    <div class="points-summary-container">
      <h3 class="points-summary-title">积分总计</h3>
      <div class="points-summary-content">
        <div class="points-by-date">
          <div class="points-date-item" v-for="(item, idx) in pointsSummary.byDescription" :key="`desc-${idx}`">
            <span class="points-date-label">{{ item.description }}:</span>
            <span class="points-date-value">{{ item.total.toFixed(3) }} PTS</span>
          </div>
        </div>
        <div class="points-total">
          <span class="points-total-label">总计:</span>
          <span class="points-total-value">{{ pointsSummary.total.toFixed(3) }} PTS</span>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="paginatedTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      :row-class-name="getRowClassName"
      height="calc(100vh - 520px)"
      :scrollbar-always-on="true"
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
            <el-option label="监控" value="监控" />
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

      <el-table-column label="地址 (h)" width="300" align="center">
        <template #default="scope">
          <el-input 
            v-model="scope.row.h" 
            placeholder="地址"
            size="small"
            @blur="saveRowData(scope.row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="钱包地址 (n)" width="300" align="center">
        <template #default="scope">
          <el-input 
            v-model="scope.row.n" 
            placeholder="钱包地址"
            size="small"
            @blur="saveRowData(scope.row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="持有仓位 (a)" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div 
            v-if="isRowParsed(scope.row) && scope.row.a" 
            class="position-list" 
            :class="{ 'position-mismatch': isPositionMismatched(scope.row) }"
            v-memo="[scope.row.a, isRowParsed(scope.row), isPositionMismatched(scope.row)]"
          >
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
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div 
            v-else-if="scope.row.a" 
            class="raw-data-text"
            :class="{ 'position-mismatch': isPositionMismatched(scope.row) }"
          >
            {{ scope.row.a }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="链上信息" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && getChainInfo(scope.row)" class="position-list" v-memo="[getChainInfo(scope.row), isRowParsed(scope.row)]">
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
          <div v-if="getChainInfo(scope.row) && getPositionDifferences(scope.row).length > 0" class="position-list">
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
          </div>
          <span v-else-if="!getChainInfo(scope.row)" class="empty-text">暂无链上数据</span>
          <span v-else class="empty-text">无差异</span>
        </template>
      </el-table-column>

      <el-table-column label="挂单仓位 (b)" width="400">
        <template #default="scope">
          <!-- 如果已解析，显示解析后的数据 -->
          <div v-if="isRowParsed(scope.row) && scope.row.b" class="position-list" v-memo="[scope.row.b, isRowParsed(scope.row)]">
            <div 
              v-for="(order, idx) in getCachedOrders(scope.row.b)" 
              :key="`${scope.row.index}-order-${idx}`" 
              class="position-item"
            >
              <div class="position-title">{{ order.title }}</div>
              <div class="position-details">
                <!-- 新格式：显示买卖方向和选项 -->
                <template v-if="order.buySellDirection !== undefined">
                  <el-tag 
                    :type="order.buySellDirection === 'Buy' ? 'success' : 'danger'" 
                    size="small"
                  >
                    {{ order.buySellDirection }}
                  </el-tag>
                  <el-tag 
                    :type="order.option === 'YES' ? 'success' : 'danger'" 
                    size="small"
                    style="margin-left: 4px;"
                  >
                    {{ order.option }}
                  </el-tag>
                  <span class="position-price" style="margin-left: 8px;">价格: {{ order.price }}</span>
                  <span class="position-amount" style="margin-left: 8px;">进度: {{ order.progress }}</span>
                </template>
                <!-- 兼容旧格式：只显示价格和进度 -->
                <template v-else>
                  <span class="position-price">{{ order.price }}</span>
                  <span class="position-amount">{{ order.progress }}</span>
                </template>
              </div>
            </div>
          </div>
          <!-- 未解析时直接显示原始字符串 -->
          <div v-else-if="scope.row.b" class="raw-data-text">
            {{ scope.row.b }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="仓位抓取时间(d)" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.d, b.d)">
        <template #default="scope">
          <div class="capture-time-cell">
            <el-icon><Clock /></el-icon>
            <span>{{ formatRelativeTime(scope.row.d) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="打开时间(f)" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.f, b.f)">
        <template #default="scope">
          <div class="capture-time-cell">
            <el-icon><Clock /></el-icon>
            <span>{{ formatRelativeTime(scope.row.f) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="积分 (k)" width="400">
        <template #default="scope">
          <div v-if="scope.row.k" class="raw-data-text">
            {{ scope.row.k }}
          </div>
          <span v-else class="empty-text">暂无数据</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="520" align="center" fixed="right">
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
          <el-button 
            type="primary" 
            size="small"
            @click="refreshPosition(scope.row)"
            :loading="scope.row.refreshing"
          >
            刷新仓位
          </el-button>
          <el-button 
            type="info" 
            size="small"
            @click="showTransactions(scope.row)"
            :disabled="!scope.row.g"
          >
            交易记录
          </el-button>
          <el-button 
            type="success" 
            size="small"
            @click="showMissionLog()"
            :disabled="!latestMissionId"
          >
            日志
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

    <!-- 交易记录弹窗 -->
    <el-dialog 
      v-model="transactionDialogVisible" 
      title="交易记录" 
      width="90%"
      :close-on-click-modal="false"
    >
      <div v-if="currentTransactions.length === 0" class="empty-message">
        暂无交易记录
      </div>
      <el-table 
        v-else
        :data="currentTransactions" 
        border 
        style="width: 100%"
        :max-height="500"
      >
        <el-table-column prop="index" label="序号" width="70" align="center" />
        <el-table-column prop="title" label="主题" min-width="250" />
        <el-table-column prop="direction" label="方向" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.direction === 'Buy' ? 'success' : 'danger'" size="small">
              {{ scope.row.direction === 'Buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="option" label="选项" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.option === 'YES' ? 'success' : 'warning'" size="small">
              {{ scope.row.option }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="数量" width="120" align="center" />
        <el-table-column prop="value" label="金额" width="120" align="center" />
        <el-table-column prop="price" label="价格" width="120" align="center" />
        <el-table-column prop="time" label="时间" min-width="180" align="center" />
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="transactionDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务日志弹窗 -->
    <el-dialog 
      v-model="missionLogDialogVisible" 
      title="任务执行日志" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-loading="loadingMissionStatus" class="mission-log-content">
        <div class="log-item">
          <span class="log-label">任务ID:</span>
          <span class="log-value">{{ latestMissionId || '暂无' }}</span>
        </div>
        <div class="log-item">
          <span class="log-label">状态:</span>
          <el-tag 
            :type="getMissionStatusType(missionStatus.status)" 
            size="large"
          >
            {{ getMissionStatusText(missionStatus.status) }}
          </el-tag>
        </div>
        <div class="log-item" v-if="missionStatus.msg">
          <span class="log-label">消息:</span>
          <span class="log-value">{{ missionStatus.msg }}</span>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="missionLogDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="refreshMissionStatus" :loading="loadingMissionStatus">
            刷新状态
          </el-button>
        </span>
      </template>
    </el-dialog>
    </div>

    <!-- 数据总计页面 -->
    <Summary v-if="currentPage === 'summary'" />

    <!-- 历史查询页面 -->
    <HistoryQuery v-if="currentPage === 'history'" />
  </div>
</template>

<script setup>
/**
 * ==================== 性能优化说明 ====================
 * 
 * 针对大数据量场景进行的优化：
 * 
 * 1. 数据响应式优化
 *    - 使用 shallowRef 代替 ref 减少深度响应式开销
 *    - 使用 Object.freeze 冻结解析后的数据避免不必要的响应式
 * 
 * 2. 数据解析缓存
 *    - parsePositions 和 parseOpenOrders 增加缓存机制
 *    - 避免重复解析相同的持仓和挂单字符串
 *    - 自动限制缓存大小防止内存泄漏
 * 
 * 3. 渐进式渲染 ⭐ 核心优化
 *    - 列表先快速渲染基础信息（余额、时间等）
 *    - 持仓和订单数据异步分批解析（每批20行）
 *    - 使用 requestIdleCallback 在浏览器空闲时解析
 *    - 显示加载状态让用户感知进度
 *    - 极大提升首屏渲染速度和用户体验
 * 
 * 4. 计算属性优化
 *    - filteredTableData: 使用 Set 提高查找效率，分组排序代替全量排序
 *    - summaryData: 单次遍历计算所有汇总数据
 *    - redPositionCount: 使用 for 循环代替 filter 减少中间数组创建
 * 
 * 5. 懒加载优化
 *    - 数据总计默认折叠，仅在用户展开时才计算和渲染
 *    - 避免初始加载时的大量计算和持仓数据解析
 *    - 显著提升首屏加载速度
 * 
 * 6. 渲染优化
 *    - 表格添加固定高度启用虚拟滚动优化
 *    - 使用 v-memo 指令避免不必要的重新渲染
 *    - 优化 key 值确保正确的 diff 算法
 * 
 * 7. 操作优化
 *    - 保存操作添加 500ms 防抖避免频繁请求
 *    - 批量更新时使用新数组触发 shallowRef 更新
 *    - 异步解析支持取消，避免无效计算
 * 
 * 8. 资源管理
 *    - 组件卸载时清理所有定时器和缓存
 *    - 正确管理异步任务的生命周期
 * 
 * ====================================================
 */
import { ref, computed, onMounted, onUnmounted, shallowRef, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import Summary from './Summary.vue'
import HistoryQuery from './HistoryQuery.vue'

/**
 * 基础配置
 */
const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'
const CHAIN_DATA_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/positions/summary/trades'

/**
 * 页面状态
 */
const currentPage = ref('list')  // 'list' 或 'summary'

/**
 * 响应式数据
 * 使用 shallowRef 减少深度响应式开销
 */
const tableData = shallowRef([])
const parsedDataCache = new Map()  // 解析数据缓存
const parsedRowsSet = ref(new Set())  // 已解析的行标识集合
const loading = ref(false)
const saving = ref(false)
const refreshingAll = ref(false)
const refreshingRed = ref(false)  // 刷新变红仓位的加载状态
const refreshingRedOld = ref(false)  // 刷新变红且超过30分钟仓位的加载状态
const refreshingFiltered = ref(false)  // 刷新筛选结果仓位的加载状态
const parsingAll = ref(false)  // 是否正在全部解析
const deduplicating = ref(false)  // 地址去重的加载状态
const gettingWalletAddresses = ref(false)  // 获取钱包地址的加载状态
const snappingAccount = ref(false)  // 手动快照的加载状态
const chainDataMap = ref(new Map())  // 链上信息数据映射，key为wallet_address（小写），value为链上信息字符串
let nextId = 1

/**
 * 分页相关
 */
const currentPageNum = ref(1)
const pageSize = 50

/**
 * 任务日志相关
 */
const latestMissionId = ref(null)  // 最新的任务ID
const missionLogDialogVisible = ref(false)  // 任务日志弹窗显示状态
const loadingMissionStatus = ref(false)  // 加载任务状态的loading
const missionStatus = ref({
  status: null,
  msg: ''
})

/**
 * 交易记录弹窗相关
 */
const transactionDialogVisible = ref(false)
const currentTransactions = ref([])

/**
 * 自动刷新相关
 */
const autoRefresh = ref({
  enabled: false,  // 默认开启
  interval: 60
})
let autoRefreshTimer = null

/**
 * 批量添加相关
 */
const batchAddInput = ref('')

/**
 * 批量删除相关
 */
const batchDeleteInput = ref('')
const batchDeleting = ref(false)

/**
 * 导出地址相关
 */
const exportAddressInput = ref('')
const exportingAddresses = ref(false)

/**
 * 本地新增的行（未保存到服务器的）
 */
const localNewRows = ref(new Set())

/**
 * 筛选条件
 */
const filters = ref({
  computeGroup: '',
  fingerprintNo: '',
  platform: '',
  positionSearch: '',  // 新增：仓位搜索
  balanceMin: '',  // 余额最小值
  balanceMax: '',  // 余额最大值
  showNoAddress: false,  // 显示无地址
  showDuplicateAddress: false,  // 显示地址重复
  showNoPoints: false,  // 显示无积分
  showHasDifference: false,  // 显示与链上信息有差额
  openTimeGreaterThanHours: null,  // 打开时间大于X小时
  positionTimeGreaterThanHours: null  // 仓位抓取时间大于X小时
})

const activeFilters = ref({
  computeGroup: [],
  fingerprintNo: [],
  platform: '',
  positionSearch: '',  // 新增：仓位搜索
  balanceMin: null,  // 余额最小值
  balanceMax: null,  // 余额最大值
  showNoAddress: false,  // 显示无地址
  showDuplicateAddress: false,  // 显示地址重复
  showNoPoints: false,  // 显示无积分
  showHasDifference: false,  // 显示与链上信息有差额
  openTimeGreaterThanHours: null,  // 打开时间大于X小时
  positionTimeGreaterThanHours: null  // 仓位抓取时间大于X小时
})

/**
 * 仓位时间配置
 */
const positionTimeConfig = ref({
  ignoredBrowsers: '',  // 忽略的浏览器编号
  autoUpdate: false,  // 是否自动更新
  updateThresholdMinutes: 30  // 更新阈值（分钟）
})
let autoUpdateTimer = null

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
  // 解析余额范围
  const balanceMin = filters.value.balanceMin ? parseFloat(filters.value.balanceMin) : null
  const balanceMax = filters.value.balanceMax ? parseFloat(filters.value.balanceMax) : null
  
  // 解析打开时间大于X小时
  const openTimeHours = filters.value.openTimeGreaterThanHours !== null && filters.value.openTimeGreaterThanHours !== undefined && filters.value.openTimeGreaterThanHours !== '' 
    ? parseFloat(filters.value.openTimeGreaterThanHours) 
    : null
  
  // 解析仓位抓取时间大于X小时
  const positionTimeHours = filters.value.positionTimeGreaterThanHours !== null && filters.value.positionTimeGreaterThanHours !== undefined && filters.value.positionTimeGreaterThanHours !== '' 
    ? parseFloat(filters.value.positionTimeGreaterThanHours) 
    : null
  
  activeFilters.value = {
    computeGroup: parseInputValues(filters.value.computeGroup),
    fingerprintNo: parseInputValues(filters.value.fingerprintNo),
    platform: filters.value.platform,
    positionSearch: filters.value.positionSearch.trim(),
    balanceMin: isNaN(balanceMin) ? null : balanceMin,
    balanceMax: isNaN(balanceMax) ? null : balanceMax,
    showNoAddress: filters.value.showNoAddress,
    showDuplicateAddress: filters.value.showDuplicateAddress,
    showNoPoints: filters.value.showNoPoints,
    showHasDifference: filters.value.showHasDifference,
    openTimeGreaterThanHours: isNaN(openTimeHours) ? null : openTimeHours,
    positionTimeGreaterThanHours: isNaN(positionTimeHours) ? null : positionTimeHours
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
    platform: '',
    positionSearch: '',
    balanceMin: '',
    balanceMax: '',
    showNoAddress: false,
    showDuplicateAddress: false,
    showNoPoints: false,
    showHasDifference: false,
    openTimeGreaterThanHours: null,
    positionTimeGreaterThanHours: null
  }
  activeFilters.value = {
    computeGroup: [],
    fingerprintNo: [],
    platform: '',
    positionSearch: '',
    balanceMin: null,
    balanceMax: null,
    showNoAddress: false,
    showDuplicateAddress: false,
    showNoPoints: false,
    showHasDifference: false,
    openTimeGreaterThanHours: null,
    positionTimeGreaterThanHours: null
  }
  ElMessage.info('筛选已清除')
}

/**
 * 过滤后的表格数据（优化版本）
 */
const filteredTableData = computed(() => {
  const data = tableData.value
  const filters = activeFilters.value
  
  // 计算地址重复情况（用于地址重复筛选）
  const addressCountMap = new Map()
  if (filters.showDuplicateAddress) {
    for (const row of data) {
      if (row.h && row.h.trim()) {
        const address = row.h.trim()
        addressCountMap.set(address, (addressCountMap.get(address) || 0) + 1)
      }
    }
  }
  
  // 无筛选条件时，只进行排序
  const hasFilters = filters.computeGroup.length > 0 || 
                    filters.fingerprintNo.length > 0 || 
                    filters.platform || 
                    filters.positionSearch ||
                    filters.balanceMin !== null ||
                    filters.balanceMax !== null ||
                    filters.showNoAddress ||
                    filters.showDuplicateAddress ||
                    filters.showNoPoints ||
                    filters.showHasDifference ||
                    (filters.openTimeGreaterThanHours !== null && filters.openTimeGreaterThanHours !== undefined) ||
                    (filters.positionTimeGreaterThanHours !== null && filters.positionTimeGreaterThanHours !== undefined)
  
  let result = data
  
  // 只在有筛选条件时才进行过滤
  if (hasFilters) {
    // 转为 Set 提高查找效率
    const computeGroupSet = new Set(filters.computeGroup)
    const fingerprintNoSet = new Set(filters.fingerprintNo)
    const searchTerm = filters.positionSearch ? filters.positionSearch.toLowerCase() : ''
    
    result = data.filter(row => {
      // 电脑组筛选
      if (computeGroupSet.size > 0 && !computeGroupSet.has(String(row.computeGroup))) {
        return false
      }
      
      // 浏览器编号筛选
      if (fingerprintNoSet.size > 0 && !fingerprintNoSet.has(String(row.fingerprintNo))) {
        return false
      }
      
      // 平台筛选
      if (filters.platform && row.platform !== filters.platform) {
        return false
      }
      
      // 仓位搜索筛选（包含持有仓位、挂单仓位和链上信息）
      if (searchTerm) {
        const chainInfo = getChainInfo(row)
        const hasMatch = (row.a && row.a.toLowerCase().includes(searchTerm)) ||
                        (row.b && row.b.toLowerCase().includes(searchTerm)) ||
                        (chainInfo && chainInfo.toLowerCase().includes(searchTerm))
        if (!hasMatch) {
          return false
        }
      }
      
      // 余额范围筛选
      if (filters.balanceMin !== null || filters.balanceMax !== null) {
        const balance = parseFloat(row.balance) || 0
        if (filters.balanceMin !== null && balance < filters.balanceMin) {
          return false
        }
        if (filters.balanceMax !== null && balance > filters.balanceMax) {
          return false
        }
      }
      
      // 显示无地址筛选
      if (filters.showNoAddress) {
        if (row.h && row.h.trim()) {
          return false  // 有地址，不显示
        }
      }
      
      // 显示地址重复筛选
      if (filters.showDuplicateAddress) {
        if (!row.h || !row.h.trim()) {
          return false  // 没有地址，不显示
        }
        const address = row.h.trim()
        const count = addressCountMap.get(address) || 0
        if (count <= 1) {
          return false  // 地址不重复，不显示
        }
      }
      
      // 显示无积分筛选
      if (filters.showNoPoints) {
        if (row.k && row.k.trim()) {
          return false  // 有积分，不显示
        }
      }
      
      // 显示与链上信息有差额筛选
      if (filters.showHasDifference) {
        if (!hasPositionDifference(row)) {
          return false  // 没有差额，不显示
        }
      }
      
      // 打开时间大于X小时筛选
      if (filters.openTimeGreaterThanHours !== null && filters.openTimeGreaterThanHours !== undefined) {
        if (!row.f) {
          return false  // 没有打开时间的数据不显示
        }
        const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
        const now = Date.now()
        const hoursAgo = parseFloat(filters.openTimeGreaterThanHours)
        const thresholdTime = now - (hoursAgo * 60 * 60 * 1000)  // 转换为毫秒
        
        // 如果打开时间大于阈值时间（即打开时间更早），则显示
        if (openTime > thresholdTime) {
          return false  // 打开时间不够早，不显示
        }
      }
      
      // 仓位抓取时间大于X小时筛选
      if (filters.positionTimeGreaterThanHours !== null && filters.positionTimeGreaterThanHours !== undefined) {
        if (!row.d) {
          return false  // 没有仓位抓取时间的数据不显示
        }
        const positionTime = typeof row.d === 'string' ? parseInt(row.d) : row.d
        const now = Date.now()
        const hoursAgo = parseFloat(filters.positionTimeGreaterThanHours)
        const thresholdTime = now - (hoursAgo * 60 * 60 * 1000)  // 转换为毫秒
        
        // 如果仓位抓取时间大于阈值时间（即抓取时间更早），则显示
        if (positionTime > thresholdTime) {
          return false  // 仓位抓取时间不够早，不显示
        }
      }
      
      return true
    })
  }
  
  // 排序：打开时间>仓位时间的置顶（排除忽略的浏览器）
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  
  // 使用更高效的排序方法：分组后合并
  const highlighted = []
  const normal = []
  
  for (const row of result) {
    const isIgnored = ignoredBrowsersSet.has(String(row.fingerprintNo))
    const isHighlighted = !isIgnored && shouldHighlightRow(row)
    
    if (isHighlighted) {
      highlighted.push(row)
    } else {
      normal.push(row)
    }
  }
  
  return [...highlighted, ...normal]
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
 * 总页数
 */
const totalPages = computed(() => {
  return Math.ceil(filteredTableData.value.length / pageSize)
})

/**
 * 解析积分数据
 * 格式: "2025-12-14|||Reward for Dec 7 - Dec 14, 2025|||+2.279 PTS;2025-12-07|||Reward for Nov 30 - Dec 7, 2025|||+2.355 PTS"
 * 分号分隔多个周期，每个周期用 ||| 分隔：时间|||描述|||积分
 */
const parsePoints = (pointsStr) => {
  if (!pointsStr || !pointsStr.trim()) return []
  
  try {
    const periods = pointsStr.split(';').filter(p => p.trim())
    const result = []
    
    for (const period of periods) {
      const parts = period.split('|||')
      if (parts.length >= 3) {
        const date = parts[0].trim()
        const description = parts[1].trim()
        const pointsStr = parts[2].trim()  // 例如: "+2.279 PTS"
        
        // 提取积分数值（去掉 + 号和 PTS）
        const pointsMatch = pointsStr.match(/[+-]?(\d+\.?\d*)/)
        if (pointsMatch) {
          const points = parseFloat(pointsMatch[0])
          result.push({
            date,
            description,
            points
          })
        }
      }
    }
    
    return result
  } catch (error) {
    console.error('解析积分数据失败:', error)
    return []
  }
}

/**
 * 将描述转换为数字月份格式
 * 例如: "Reward for Dec 7 - Dec 14, 2025" -> "12 7 - 12 14, 2025"
 */
const convertDescriptionToNumericFormat = (description) => {
  // 月份名称映射
  const monthMap = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
  }
  
  // 匹配格式: "Reward for Dec 7 - Dec 14, 2025"
  // 提取: 第一个月份、第一个日期、第二个月份（可选）、第二个日期、年份
  const match = description.match(/(?:Reward for\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d+)\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*(\d+),\s*(\d{4})/)
  
  if (match) {
    const month1 = match[1]
    const day1 = match[2]
    const month2 = match[3] || month1  // 如果没有第二个月份，使用第一个月份
    const day2 = match[4]
    const year = match[5]
    
    const monthNum1 = monthMap[month1]
    const monthNum2 = monthMap[month2]
    
    if (monthNum1 && monthNum2) {
      // 格式: "12 7 - 12 14, 2025"
      return `${monthNum1} ${day1} - ${monthNum2} ${day2}, ${year}`
    }
  }
  
  // 如果无法解析，返回原描述
  return description
}

/**
 * 从转换后的格式中提取排序用的日期
 * 例如: "12 7 - 12 14, 2025" -> 使用结束日期 "2025-12-14" 作为排序键
 */
const getSortKeyFromNumericFormat = (numericFormat) => {
  // 匹配格式: "12 7 - 12 14, 2025"
  const match = numericFormat.match(/(\d+)\s+(\d+)\s*-\s*(\d+)\s+(\d+),\s*(\d{4})/)
  
  if (match) {
    const month2 = parseInt(match[3])
    const day2 = parseInt(match[4])
    const year = parseInt(match[5])
    
    // 使用结束日期作为排序键（格式: "2025-12-14"）
    return `${year}-${String(month2).padStart(2, '0')}-${String(day2).padStart(2, '0')}`
  }
  
  // 如果无法解析，返回一个很旧的日期
  return '1900-01-01'
}

/**
 * 积分总计（按描述分组，转换为数字月份格式并按时间排序）
 */
const pointsSummary = computed(() => {
  const data = filteredTableData.value
  const descriptionMap = new Map()  // key: 原始描述, value: 累计积分
  let total = 0
  
  for (const row of data) {
    if (row.k) {
      const periods = parsePoints(row.k)
      for (const period of periods) {
        const description = period.description
        const points = period.points
        
        // 按描述累加
        descriptionMap.set(description, (descriptionMap.get(description) || 0) + points)
        total += points
      }
    }
  }
  
  // 转换为数组，转换为数字月份格式，并按时间排序（降序，最新的在前）
  const byDescription = Array.from(descriptionMap.entries())
    .map(([description, total]) => {
      const numericFormat = convertDescriptionToNumericFormat(description)
      const sortKey = getSortKeyFromNumericFormat(numericFormat)
      return { 
        description: numericFormat,  // 显示转换后的格式
        total,
        sortKey  // 用于排序
      }
    })
    .sort((a, b) => {
      // 按时间降序排序（最新的在前）
      return b.sortKey.localeCompare(a.sortKey)
    })
  
  return {
    byDescription,
    total
  }
})


/**
 * 计算变红仓位数量（打开时间>仓位时间，且不在忽略列表中，且不是监控类型）
 */
const redPositionCount = computed(() => {
  const data = tableData.value
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  
  let count = 0
  for (const row of data) {
    if (row.fingerprintNo && 
        row.computeGroup && 
        row.platform &&
        row.platform !== '监控' &&
        !ignoredBrowsersSet.has(String(row.fingerprintNo)) &&
        shouldHighlightRow(row)) {
      count++
    }
  }
  
  return count
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
/**
 * 复制地址到剪切板
 */
const copyAddress = async (address) => {
  try {
    await navigator.clipboard.writeText(address)
    ElMessage.success('地址已复制到剪切板')
  } catch (error) {
    // 如果 clipboard API 不可用，使用备用方法
    try {
      const textArea = document.createElement('textarea')
      textArea.value = address
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      ElMessage.success('地址已复制到剪切板')
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('复制地址失败:', err)
    }
  }
}

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
 * 获取忽略的浏览器集合
 */
const getIgnoredBrowsersSet = () => {
  const input = positionTimeConfig.value.ignoredBrowsers.trim()
  if (!input) return new Set()
  
  const browsers = input.split(',').map(b => b.trim()).filter(b => b)
  return new Set(browsers)
}

/**
 * 判断行是否应该高亮（打开时间>仓位时间）
 * 监控类型的数据不需要检测仓位时间和打开时间变红置顶
 */
const shouldHighlightRow = (row) => {
  // 监控类型不需要检测仓位时间和打开时间
  if (row.platform === '监控') return false
  
  if (!row.f || !row.d) return false
  
  const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
  const positionTime = typeof row.d === 'string' ? parseInt(row.d) : row.d
  
  return openTime > positionTime
}

/**
 * 获取行的CSS类名
 */
const getRowClassName = ({ row }) => {
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const isIgnored = ignoredBrowsersSet.has(String(row.fingerprintNo))
  
  if (!isIgnored && shouldHighlightRow(row)) {
    return 'highlight-row'
  }
  return ''
}

/**
 * 保存忽略的浏览器配置
 */
const saveIgnoredBrowsers = () => {
  try {
    localStorage.setItem('ignoredBrowsers', positionTimeConfig.value.ignoredBrowsers)
    ElMessage.success('已保存忽略浏览器配置')
  } catch (error) {
    ElMessage.error('保存配置失败')
    console.error('保存配置失败:', error)
  }
}

/**
 * 切换自动更新
 */
const toggleAutoUpdate = () => {
  if (positionTimeConfig.value.autoUpdate) {
    // 开启自动更新
    performAutoUpdate()  // 立即执行一次
    autoUpdateTimer = setInterval(performAutoUpdate, 20 * 60 * 1000)  // 每20分钟执行一次
    ElMessage.success('已开启自动更新仓位')
  } else {
    // 关闭自动更新
    if (autoUpdateTimer) {
      clearInterval(autoUpdateTimer)
      autoUpdateTimer = null
    }
    ElMessage.info('已关闭自动更新仓位')
  }
}

/**
 * 执行自动更新
 * 监控类型的数据不需要执行刷新仓位的任务
 */
const performAutoUpdate = async () => {
  console.log('[自动更新] 开始检查需要更新的仓位...')
  
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const thresholdMinutes = positionTimeConfig.value.updateThresholdMinutes
  const now = Date.now()
  
  const browsersToUpdate = []
  
  for (const row of tableData.value) {
    // 跳过监控类型的浏览器（不需要执行刷新仓位的任务）
    if (row.platform === '监控') {
      continue
    }
    
    // 跳过忽略的浏览器
    if (ignoredBrowsersSet.has(String(row.fingerprintNo))) {
      continue
    }
    
    // 检查打开时间是否大于仓位时间
    if (!shouldHighlightRow(row)) {
      continue
    }
    
    // 检查打开时间距离现在是否已经过去了阈值分钟数
    const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
    const elapsedMinutes = (now - openTime) / 1000 / 60
    
    if (elapsedMinutes >= thresholdMinutes) {
      browsersToUpdate.push(row)
    }
  }
  
  if (browsersToUpdate.length === 0) {
    console.log('[自动更新] 没有需要更新的仓位')
    return
  }
  
  console.log(`[自动更新] 发现 ${browsersToUpdate.length} 个需要更新的浏览器`)
  
  // 依次更新每个浏览器的仓位
  for (const row of browsersToUpdate) {
    try {
      console.log(`[自动更新] 正在更新浏览器 ${row.fingerprintNo}...`)
      await refreshPosition(row)
      await new Promise(resolve => setTimeout(resolve, 2000))  // 间隔2秒
    } catch (error) {
      console.error(`[自动更新] 更新浏览器 ${row.fingerprintNo} 失败:`, error)
    }
  }
  
  console.log('[自动更新] 完成')
  ElMessage.success(`已自动更新 ${browsersToUpdate.length} 个浏览器的仓位`)
}

/**
 * 检查某行是否已经解析过
 */
const isRowParsed = (row) => {
  const rowKey = row.id || `${row.computeGroup}_${row.fingerprintNo}`
  return parsedRowsSet.value.has(rowKey)
}

/**
 * 获取缓存的持仓数据（避免在模板中重复解析）
 */
const getCachedPositions = (posStr) => {
  if (!posStr) return []
  return parsePositions(posStr)  // parsePositions 内部已经有缓存机制
}

/**
 * 获取缓存的挂单数据（避免在模板中重复解析）
 */
const getCachedOrders = (ordersStr) => {
  if (!ordersStr) return []
  return parseOpenOrders(ordersStr)  // parseOpenOrders 内部已经有缓存机制
}

/**
 * 标记某行已解析
 */
const markRowAsParsed = (row) => {
  const rowKey = row.id || `${row.computeGroup}_${row.fingerprintNo}`
  const newSet = new Set(parsedRowsSet.value)
  newSet.add(rowKey)
  parsedRowsSet.value = newSet
}

/**
 * 格式化链上信息的Markets数据
 * 将markets数组格式化为 "title|||YES/NO|||amount" 格式
 * 判断YES的数量多还是NO的数量多，YES的数量多则为YES，第三个值为 yes_amount - no_amount
 * 当 yes_amount - no_amount 的绝对值小于0.01的时候，不记录
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
    // diff = yesAmount - noAmount
    // 当YES多时，diff为正数；当NO多时，diff为负数
    // 所以直接使用diff即可，不需要再转换
    const amount = diff.toFixed(2)
    
    formattedItems.push(`${market.title}|||${option}|||${amount}`)
  }
  
  return formattedItems.join(';')
}

/**
 * 加载链上数据
 */
const loadChainData = async () => {
  try {
    const response = await axios.get(CHAIN_DATA_API_URL)
    
    if (response.data && response.data.items && Array.isArray(response.data.items)) {
      const newChainDataMap = new Map()
      
      for (const item of response.data.items) {
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
    }
  } catch (error) {
    console.error('加载链上数据失败:', error)
    ElMessage.warning('加载链上数据失败: ' + (error.message || '网络错误'))
  }
}

/**
 * 分页变化处理
 */
const handlePageChange = (page) => {
  currentPageNum.value = page
  // 滚动到表格顶部
  const tableEl = document.querySelector('.el-table__body-wrapper')
  if (tableEl) {
    tableEl.scrollTop = 0
  }
}

/**
 * 比较持有仓位和链上信息是否匹配
 * 链上信息会多一个价格部分（在分号后面），不需要比较价格部分
 * 比较时，需要去掉价格部分（最后一个|||后面的内容）
 * 数量比较时需要考虑数值精度（保留2位小数比较）
 */
const comparePositionsWithChain = (positionStr, chainStr) => {
  if (!positionStr && !chainStr) return true
  if (!positionStr || !chainStr) return false
  
  // 解析持有仓位数据，只保留 title|||option|||amount 部分
  const parsePositionForCompare = (str) => {
    if (!str) return []
    const items = str.split(';').filter(item => item.trim())
    return items.map(item => {
      const parts = item.split('|||')
      if (parts.length >= 3) {
        const title = parts[0].trim()
        const option = parts[1].trim()
        let amount = parts[2].trim()
        
        // 处理数量格式，向下取整后比较
        const numAmount = parseFloat(amount)
        if (!isNaN(numAmount)) {
          // 向下取整（对于负数，Math.floor会向下取整，例如 -1.5 -> -2）
          amount = Math.floor(numAmount).toString()
        }
        
        // 只取前3部分：title|||option|||amount（忽略价格部分）
        return `${title}|||${option}|||${amount}`
      }
      return item.trim()
    }).sort()  // 排序以便比较
  }
  
  const positionItems = parsePositionForCompare(positionStr)
  const chainItems = parsePositionForCompare(chainStr)
  
  // 如果数量不同，则不匹配
  if (positionItems.length !== chainItems.length) {
    return false
  }
  
  // 逐个比较
  for (let i = 0; i < positionItems.length; i++) {
    if (positionItems[i] !== chainItems[i]) {
      return false
    }
  }
  
  return true
}

/**
 * 获取行的链上信息
 */
const getChainInfo = (row) => {
  if (!row.h) return ''
  const address = row.h.trim().toLowerCase()
  return chainDataMap.value.get(address) || ''
}

/**
 * 检查持有仓位是否与链上信息匹配
 */
const isPositionMismatched = (row) => {
  if (!row.a) return false
  const chainInfo = getChainInfo(row)
  if (!chainInfo) return false
  return !comparePositionsWithChain(row.a, chainInfo)
}

/**
 * 检查是否有与链上信息的差额（差异绝对值>=1）
 */
const hasPositionDifference = (row) => {
  const differences = getPositionDifferences(row)
  return differences.length > 0
}

/**
 * 计算持有仓位和链上信息的信息差
 * 返回每个市场的差异数组
 */
const getPositionDifferences = (row) => {
  const differences = []
  
  if (!row.a) return differences
  
  const chainInfo = getChainInfo(row)
  if (!chainInfo) return differences
  
  // 解析持有仓位
  const holdingPositions = parsePositions(row.a)
  // 解析链上仓位
  const chainPositions = parsePositions(chainInfo)
  
  // 创建链上仓位的映射（按title匹配，支持基础title匹配）
  const chainMap = new Map()
  for (const chainPos of chainPositions) {
    const titleKey = chainPos.title.split('###')[0].trim()
    const existing = chainMap.get(titleKey)
    if (existing) {
      // 如果已有相同基础title，累加数量
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
 * 解析持仓数据字符串（带缓存优化）
 * 格式: "标题1|||选项1|||数量1|||均价1;标题2|||选项2|||数量2|||均价2"
 * 兼容旧格式: "标题1,选项1,数量1,均价1;标题2,选项2,数量2,均价2"
 * 性能优化：使用更高效的字符串处理方法，减少重复代码
 */
const parsePositions = (posStr) => {
  if (!posStr) return []
  
  // 使用缓存避免重复解析
  const cacheKey = `pos_${posStr}`
  if (parsedDataCache.has(cacheKey)) {
    return parsedDataCache.get(cacheKey)
  }
  
  try {
    const positions = []
    // 优化：如果字符串很长，使用更高效的分割方式
    const items = posStr.split(';')
    const itemsLength = items.length
    
    // 优化：预先判断格式类型，避免重复检查
    const isNewFormat = posStr.includes('|||')
    const separator = isNewFormat ? '|||' : ','
    
    for (let i = 0; i < itemsLength; i++) {
      const item = items[i]
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
      } else if (partsLength >= 3 && isNewFormat) {
        // 新格式的3个字段：title|||option|||amount（链上信息格式，无价格）
        let title = parts[0].trim()
        let option = parts[1].trim()
        let amount = parts[2].trim()
        
        positions.push({
          title: title,
          option: option,
          amount: amount,
          avgPrice: ''  // 链上信息没有价格
        })
      } else if (partsLength >= 3 && !isNewFormat) {
        // 只对旧格式处理3个字段的情况
        positions.push({
          title: parts[0].trim(),
          option: parts[1].trim(),
          amount: parts[2].trim(),
          avgPrice: ''
        })
      } else if (partsLength >= 2 && !isNewFormat) {
        // 只对旧格式处理2个字段的情况
        positions.push({
          title: parts[0].trim(),
          option: '',
          amount: parts[1].trim(),
          avgPrice: ''
        })
      }
    }
    
    // 冻结对象避免响应式开销
    const frozenPositions = Object.freeze(positions)
    parsedDataCache.set(cacheKey, frozenPositions)
    
    // 限制缓存大小，避免内存泄漏
    if (parsedDataCache.size > 1000) {
      const firstKey = parsedDataCache.keys().next().value
      parsedDataCache.delete(firstKey)
    }
    
    return frozenPositions
  } catch {
    return []
  }
}

/**
 * 解析挂单数据字符串（带缓存优化）
 * 新格式: "唯一标题|||买卖方向|||选项|||价格|||进度;唯一标题|||买卖方向|||选项|||价格|||进度"
 * 兼容旧格式: "标题1|||价格1|||进度1;标题2|||价格2|||进度2"
 * 兼容更旧格式: "标题1,价格1,进度1;标题2,价格2,进度2"
 */
const parseOpenOrders = (ordersStr) => {
  if (!ordersStr) return []
  
  // 使用缓存避免重复解析
  const cacheKey = `order_${ordersStr}`
  if (parsedDataCache.has(cacheKey)) {
    return parsedDataCache.get(cacheKey)
  }
  
  try {
    const orders = []
    const items = ordersStr.split(';')
    for (const item of items) {
      if (!item.trim()) continue
      
      // 优先尝试新格式（5个字段：唯一标题|||买卖方向|||选项|||价格|||进度）
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 5) {
          // 新格式：唯一标题|||买卖方向|||选项|||价格|||进度
          orders.push({
            title: parts[0].trim(),
            buySellDirection: parts[1].trim(), // "Buy" 或 "Sell"
            option: parts[2].trim(), // "YES" 或 "NO"
            price: parts[3].trim(),
            progress: parts[4].trim()
          })
        } else if (parts.length >= 3) {
          // 兼容旧格式（3个字段：标题|||价格|||进度）
          orders.push({
            title: parts[0].trim(),
            price: parts[1].trim(),
            progress: parts[2].trim()
          })
        }
      } else {
        // 兼容更旧格式（逗号分隔符）
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
    
    // 冻结对象避免响应式开销
    const frozenOrders = Object.freeze(orders)
    parsedDataCache.set(cacheKey, frozenOrders)
    
    // 限制缓存大小
    if (parsedDataCache.size > 1000) {
      const firstKey = parsedDataCache.keys().next().value
      parsedDataCache.delete(firstKey)
    }
    
    return frozenOrders
  } catch {
    return []
  }
}

/**
 * 解析交易记录数据字符串
 * 格式: "标题1|||方向1|||选项1|||数量1|||金额1|||价格1|||时间1;标题2|||方向2|||选项2|||数量2|||金额2|||价格2|||时间2"
 */
const parseTransactions = (transStr) => {
  if (!transStr) return []
  try {
    const transactions = []
    const items = transStr.split(';')
    for (const item of items) {
      if (item.includes('|||')) {
        const parts = item.split('|||')
        if (parts.length >= 7) {
          transactions.push({
            title: parts[0].trim(),
            direction: parts[1].trim(),
            option: parts[2].trim(),
            amount: parts[3].trim(),
            value: parts[4].trim(),
            price: parts[5].trim(),
            time: parts[6].trim()
          })
        }
      }
    }
    return transactions
  } catch {
    return []
  }
}


/**
 * 解析单行数据
 */
const parseRow = async (row) => {
  if (isRowParsed(row)) {
    return
  }
  
  // 设置解析状态
  const currentData = [...tableData.value]
  const rowIndex = currentData.findIndex(r => {
    if (row.id && r.id) {
      return r.id === row.id
    }
    return r.fingerprintNo === row.fingerprintNo && 
           r.computeGroup === row.computeGroup
  })
  
  if (rowIndex === -1) return
  
  currentData[rowIndex] = { ...currentData[rowIndex], parsing: true }
  tableData.value = currentData
  
  try {
    // 解析持仓数据
    if (row.a) {
      parsePositions(row.a)
    }
    // 解析挂单数据
    if (row.b) {
      parseOpenOrders(row.b)
    }
    // 标记为已解析
    markRowAsParsed(row)
    
    ElMessage.success('解析完成')
  } catch (error) {
    console.error('解析失败:', error)
    ElMessage.error('解析失败')
  } finally {
    // 清除解析状态
    const updatedData = [...tableData.value]
    const idx = updatedData.findIndex(r => {
      if (row.id && r.id) {
        return r.id === row.id
      }
      return r.fingerprintNo === row.fingerprintNo && 
             r.computeGroup === row.computeGroup
    })
    if (idx !== -1) {
      updatedData[idx] = { ...updatedData[idx], parsing: false }
      tableData.value = updatedData
    }
  }
}

/**
 * 解析所有行数据（分批处理，避免阻塞UI）
 */
const parseAllRows = async () => {
  const data = tableData.value
  const unparsedRows = data.filter(row => !isRowParsed(row))
  
  if (unparsedRows.length === 0) {
    ElMessage.info('所有数据已解析')
    return
  }
  
  parsingAll.value = true
  ElMessage.info(`开始解析 ${unparsedRows.length} 行数据...`)
  
  try {
    const batchSize = 5  // 每批处理5行
    
    for (let i = 0; i < unparsedRows.length; i += batchSize) {
      const batch = unparsedRows.slice(i, Math.min(i + batchSize, unparsedRows.length))
      
      // 解析这批数据
      for (const row of batch) {
        if (row.a) {
          parsePositions(row.a)
        }
        if (row.b) {
          parseOpenOrders(row.b)
        }
        markRowAsParsed(row)
      }
      
      // 让出主线程，避免阻塞UI
      await new Promise(resolve => {
        if (typeof requestIdleCallback !== 'undefined') {
          requestIdleCallback(() => resolve(), { timeout: 200 })
        } else {
          setTimeout(resolve, 50)
        }
      })
    }
    
    ElMessage.success(`解析完成，共解析 ${unparsedRows.length} 行数据`)
  } catch (error) {
    console.error('全部解析失败:', error)
    ElMessage.error('解析过程中出现错误')
  } finally {
    parsingAll.value = false
  }
}

/**
 * 显示交易记录弹窗
 */
const showTransactions = (row) => {
  if (!row.g) {
    ElMessage.warning('该账户暂无交易记录')
    return
  }
  
  const transactions = parseTransactions(row.g)
  currentTransactions.value = transactions.map((trans, index) => ({
    index: index + 1,
    ...trans
  }))
  
  transactionDialogVisible.value = true
}


/**
 * 下载文本文件
 */
const downloadTextFile = (content, filename) => {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 加载数据列表（支持静默刷新）
 */
const loadData = async (silent = false) => {
  if (!silent) {
    loading.value = true
  }
  
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/findAccountConfigCache`)
    
    if (response.data && response.data.data) {
      const serverData = response.data.data
      
      // 提取所有的 fingerprintNo 并保存到 txt 文件
      const fingerprintNos = []
      serverData.forEach(item => {
        if (item.fingerprintNo) {
          fingerprintNos.push(String(item.fingerprintNo))
        }
      })
      
      // 保存到 txt 文件（每行一个 fingerprintNo，先从小到大排序）
      // if (fingerprintNos.length > 0) {
      //   // 按数字大小排序（从小到大）
      //   fingerprintNos.sort((a, b) => {
      //     const numA = parseInt(a) || 0
      //     const numB = parseInt(b) || 0
      //     return numA - numB
      //   })
        
      //   const content = fingerprintNos.join('\n')
      //   const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      //   const filename = `fingerprintNo_${timestamp}.txt`
      //   downloadTextFile(content, filename)
      //   console.log(`已保存 ${fingerprintNos.length} 个 fingerprintNo 到 ${filename}`)
      // }
      
      // 保存本地新增的行（没有 id 的）
      const localRows = tableData.value.filter(row => !row.id)
      
      // 创建一个 map 存储服务器数据，key 为 fingerprintNo
      const serverDataMap = new Map()
      serverData.forEach(item => {
        if (item.fingerprintNo) {
          serverDataMap.set(String(item.fingerprintNo), item)
        }
      })
      
      // 更新已存在的行
      const updatedData = []
      
      // 首先添加所有服务器数据
      serverData.forEach(item => {
        updatedData.push({
          ...item,
          platform: item.e || item.platform || 'OP',
          refreshing: false
        })
      })
      
      // 然后添加本地新增的行（如果服务器没有相同的 fingerprintNo）
      localRows.forEach(localRow => {
        if (!localRow.fingerprintNo || !serverDataMap.has(String(localRow.fingerprintNo))) {
          updatedData.push(localRow)
        }
      })
      
      // 重新计算序号
      updatedData.forEach((item, index) => {
        item.index = index + 1
      })
      
      // 使用 shallowRef 的 .value 赋值来触发更新
      tableData.value = updatedData
      nextId = Math.max(...tableData.value.map(item => item.id || 0)) + 1
      
      // 清除缓存和已解析标记，以便重新解析
      parsedDataCache.clear()
      parsedRowsSet.value = new Set()
      
      if (!silent) {
        ElMessage.success('数据加载成功')
      } else {
        console.log('数据静默刷新成功')
      }
      
      // 不再自动解析，由用户手动触发
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    if (!silent) {
      ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
    }
  } finally {
    if (!silent) {
      loading.value = false
    }
  }
}

/**
 * 添加行
 */
const addRows = (count) => {
  const currentData = [...tableData.value]
  
  for (let i = 0; i < count; i++) {
    const newRow = {
      index: currentData.length + 1,
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
    currentData.push(newRow)
  }
  
  // 重新计算序号
  currentData.forEach((row, index) => {
    row.index = index + 1
  })
  
  // 使用新数组触发 shallowRef 更新
  tableData.value = currentData
  
  ElMessage.success(`已添加 ${count} 行`)
}

/**
 * 防抖定时器
 */
let saveRowTimers = new Map()

/**
 * 保存单行数据（带防抖）
 */
const saveRowData = async (row) => {
  // 使用行ID或浏览器编号作为唯一标识
  const rowKey = row.id || `temp_${row.fingerprintNo}`
  
  // 清除之前的定时器
  if (saveRowTimers.has(rowKey)) {
    clearTimeout(saveRowTimers.get(rowKey))
  }
  
  // 设置新的防抖定时器
  const timer = setTimeout(async () => {
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
        // 如果是新增数据，静默重新加载以获取服务器分配的ID
        if (!row.id) {
          await loadData(true)
        }
      }
    } catch (error) {
      console.error('保存行数据失败:', error)
      ElMessage.error('保存失败: ' + (error.message || '网络错误'))
    } finally {
      saveRowTimers.delete(rowKey)
    }
  }, 500) // 500ms 防抖延迟
  
  saveRowTimers.set(rowKey, timer)
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
  
  // 找到行在数组中的索引（使用唯一标识符而不是引用比较）
  // 因为 loadData 会创建新对象，导致引用失效
  const currentData = [...tableData.value]
  const rowIndex = currentData.findIndex(r => {
    // 优先使用 id，如果没有 id 则使用 fingerprintNo + computeGroup 组合
    if (row.id && r.id) {
      return r.id === row.id
    }
    return r.fingerprintNo === row.fingerprintNo && 
           r.computeGroup === row.computeGroup
  })
  if (rowIndex === -1) {
    console.warn("未找到行在数组中的索引", {
      fingerprintNo: row.fingerprintNo,
      computeGroup: row.computeGroup,
      id: row.id,
      tableDataLength: currentData.length
    })
    ElMessage.warning('无法找到对应的数据行，请刷新列表后重试')
    return
  }
  
  // 检查平台类型，仅支持 OP 平台
  if (row.platform != 'OP'){
    ElMessage.warning('当前仅支持 OP 平台的仓位刷新')
    return
  }
  
  currentData[rowIndex] = { ...currentData[rowIndex], refreshing: true }
  tableData.value = currentData
  
  try {
    // 1. 发送 type=2 任务请求，让服务器采集最新数据
    ElMessage.info(`正在采集浏览器 ${row.fingerprintNo} 的最新仓位数据...`)
    const taskData = {
      groupNo: row.computeGroup,
      numberList: parseInt(row.fingerprintNo),
      type: 2,  // Type 2 任务
      exchangeName: row.platform === 'OP' ? 'OP' : '监控'
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
    
    // 2. 等待一段时间让任务执行
    const waitTime = 60000  // 统一等待 60 秒
    ElMessage.info(`预计需要 ${waitTime / 1000} 秒，请稍候...`)
    
    await new Promise(resolve => setTimeout(resolve, waitTime))
    
    // 3. 获取更新后的数据
    const response = await axios.get(
      `${API_BASE_URL}/boost/findAccountConfigByNo?no=${row.fingerprintNo}`
    )
    
    if (response.data && response.data.data) {
      const newData = response.data.data
      
      // 更新整行数据
      const updatedData = [...tableData.value]
      const idx = updatedData.findIndex(r => r.fingerprintNo === row.fingerprintNo)
      if (idx !== -1) {
        updatedData[idx] = {
          ...updatedData[idx],
          balance: newData.balance || 0,
          a: newData.a || '',  // 持仓
          b: newData.b || '',  // 挂单
          c: newData.c || '0', // Portfolio
          d: newData.d || '',  // 时间戳
          platform: newData.e || updatedData[idx].platform,  // 平台
          refreshing: false
        }
        
        // 清除相关缓存，并标记为未解析
        if (newData.a) parsedDataCache.delete(`pos_${newData.a}`)
        if (newData.b) parsedDataCache.delete(`order_${newData.b}`)
        
        // 从已解析集合中移除该行
        const rowKey = updatedData[idx].id || `${updatedData[idx].computeGroup}_${updatedData[idx].fingerprintNo}`
        const newSet = new Set(parsedRowsSet.value)
        newSet.delete(rowKey)
        parsedRowsSet.value = newSet
        
        tableData.value = updatedData
        
        // 异步解析该行数据
        setTimeout(() => {
          if (updatedData[idx].a) parsePositions(updatedData[idx].a)
          if (updatedData[idx].b) parseOpenOrders(updatedData[idx].b)
          markRowAsParsed(updatedData[idx])
        }, 10)
      }
      
      ElMessage.success(`浏览器 ${row.fingerprintNo} 仓位数据已更新`)
    } else {
      ElMessage.warning('数据采集完成，但未获取到更新数据')
    }
  } catch (error) {
    console.error('刷新仓位失败:', error)
    const errorMsg = error.response?.data?.msg || error.message || '网络错误'
    ElMessage.error('刷新仓位失败: ' + errorMsg)
    
    // 重置 refreshing 状态
    const updatedData = [...tableData.value]
    const idx = updatedData.findIndex(r => r.fingerprintNo === row.fingerprintNo)
    if (idx !== -1) {
      updatedData[idx] = { ...updatedData[idx], refreshing: false }
      tableData.value = updatedData
    }
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
 * 切换自动刷新
 */
const toggleAutoRefresh = () => {
  if (autoRefresh.value.enabled) {
    startAutoRefresh()
    ElMessage.success(`自动刷新已启动，间隔 ${autoRefresh.value.interval} 秒`)
  } else {
    stopAutoRefresh()
    ElMessage.info('自动刷新已关闭')
  }
}

/**
 * 启动自动刷新
 */
const startAutoRefresh = () => {
  stopAutoRefresh()  // 先清除旧的定时器
  
  if (autoRefresh.value.enabled && autoRefresh.value.interval > 0) {
    autoRefreshTimer = setInterval(() => {
      console.log('自动刷新数据...')
      loadData(true)  // 静默刷新
      loadChainData()  // 同时刷新链上数据
    }, autoRefresh.value.interval * 1000)
  }
}

/**
 * 停止自动刷新
 */
const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

/**
 * 重置自动刷新（间隔改变时）
 */
const resetAutoRefresh = () => {
  if (autoRefresh.value.enabled) {
    startAutoRefresh()
    ElMessage.success(`自动刷新间隔已更新为 ${autoRefresh.value.interval} 秒`)
  }
}

/**
 * 刷新全部仓位
 */
const refreshAllPositions = async () => {
  // 获取所有有浏览器编号和电脑组的行
  const validRows = tableData.value.filter(row => 
    row.fingerprintNo && row.computeGroup && row.platform
  )
  
  if (validRows.length === 0) {
    ElMessage.warning('没有可刷新的账户')
    return
  }
  
  refreshingAll.value = true
  ElMessage.info(`开始刷新 ${validRows.length} 个账户的仓位数据，请稍候...`)
  
  let successCount = 0
  let failCount = 0
  
  try {
    // 提交所有 type=2 任务
    const taskPromises = validRows.map(async (row) => {
      try {
        if (row.platform == 'OP'){
            const taskData = {
              groupNo: row.computeGroup,
              numberList: parseInt(row.fingerprintNo),
              type: 2,
              exchangeName: row.platform === 'OP' ? 'OP' : '监控'
            }
            
            await axios.post(
              `${API_BASE_URL}/mission/add`,
              taskData,
              {
                headers: {
                  'Content-Type': 'application/json'
                }
              }
            )
            
            console.log(`浏览器 ${row.fingerprintNo} 刷新任务已提交`)
            successCount++
        }
      
      } catch (error) {
        console.error(`浏览器 ${row.fingerprintNo} 刷新任务提交失败:`, error)
        failCount++
      }
    })
    
    await Promise.all(taskPromises)
    
    ElMessage.success(`已提交 ${successCount} 个刷新任务${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 等待 70 秒后自动刷新列表
    ElMessage.info('任务已全部提交，70秒后自动刷新列表...')
    setTimeout(async () => {
      await loadData(true)  // 静默刷新
      ElMessage.success('数据已自动更新')
    }, 70000)
    
  } catch (error) {
    console.error('刷新全部仓位失败:', error)
    ElMessage.error('刷新全部仓位失败: ' + (error.message || '网络错误'))
  } finally {
    refreshingAll.value = false
  }
}

/**
 * 刷新变红仓位（打开时间>仓位时间的）
 */
const refreshRedPositions = async () => {
  // 获取所有背景标红的行（打开时间>仓位时间，且不在忽略列表中）
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const redRows = tableData.value.filter(row => 
    row.fingerprintNo && 
    row.computeGroup && 
    row.platform &&
    !ignoredBrowsersSet.has(String(row.fingerprintNo)) &&
    shouldHighlightRow(row)
  )
  
  if (redRows.length === 0) {
    ElMessage.warning('没有需要刷新的变红仓位')
    return
  }
  
  refreshingRed.value = true
  ElMessage.info(`开始刷新 ${redRows.length} 个变红仓位，请稍候...`)
  
  let successCount = 0
  let failCount = 0
  
  try {
    // 提交所有 type=2 任务
    const taskPromises = redRows.map(async (row) => {
      try {
        if (row.platform == 'OP'){
          const taskData = {
            groupNo: row.computeGroup,
            numberList: parseInt(row.fingerprintNo),
            type: 2,
            exchangeName: row.platform === 'OP' ? 'OP' : '监控'
          }
          
          const response = await axios.post(
            `${API_BASE_URL}/mission/add`,
            taskData,
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )
          
          // 保存最新的任务ID（只保留最后一个）
          if (response.data && response.data.data && response.data.data.id) {
            latestMissionId.value = response.data.data.id
          }
          
          console.log(`浏览器 ${row.fingerprintNo} 刷新任务已提交`)
          successCount++

        }
     
      } catch (error) {
        console.error(`浏览器 ${row.fingerprintNo} 刷新任务提交失败:`, error)
        failCount++
      }
    })
    
    await Promise.all(taskPromises)
    
    ElMessage.success(`已提交 ${successCount} 个刷新任务${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 等待 70 秒后自动刷新列表
    ElMessage.info('任务已全部提交，70秒后自动刷新列表...')
    setTimeout(async () => {
      await loadData(true)  // 静默刷新
      ElMessage.success('数据已自动更新')
    }, 70000)
    
  } catch (error) {
    console.error('刷新变红仓位失败:', error)
    ElMessage.error('刷新变红仓位失败: ' + (error.message || '网络错误'))
  } finally {
    refreshingRed.value = false
  }
}

/**
 * 刷新筛选结果的仓位（只刷新当前筛选后显示的行）
 */
const refreshFilteredPositions = async () => {
  // 获取当前筛选后的所有行（不分页）
  const filteredRows = filteredTableData.value.filter(row => 
    row.fingerprintNo && row.computeGroup && row.platform
  )
  
  if (filteredRows.length === 0) {
    ElMessage.warning('没有可刷新的账户')
    return
  }
  
  refreshingFiltered.value = true
  ElMessage.info(`开始刷新筛选结果中的 ${filteredRows.length} 个账户的仓位数据，请稍候...`)
  
  let successCount = 0
  let failCount = 0
  
  try {
    // 提交所有 type=2 任务
    const taskPromises = filteredRows.map(async (row) => {
      try {
        if (row.platform == 'OP') {
          const taskData = {
            groupNo: row.computeGroup,
            numberList: parseInt(row.fingerprintNo),
            type: 2,
            exchangeName: row.platform === 'OP' ? 'OP' : '监控'
          }
          
          await axios.post(
            `${API_BASE_URL}/mission/add`,
            taskData,
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )
          
          console.log(`浏览器 ${row.fingerprintNo} 刷新任务已提交`)
          successCount++
        }
      } catch (error) {
        console.error(`浏览器 ${row.fingerprintNo} 刷新任务提交失败:`, error)
        failCount++
      }
    })
    
    await Promise.all(taskPromises)
    
    ElMessage.success(`已提交 ${successCount} 个刷新任务${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 等待 70 秒后自动刷新列表
    ElMessage.info('任务已全部提交，70秒后自动刷新列表...')
    setTimeout(async () => {
      await loadData(true)  // 静默刷新
      ElMessage.success('数据已自动更新')
    }, 70000)
    
  } catch (error) {
    console.error('刷新筛选结果仓位失败:', error)
    ElMessage.error('刷新筛选结果仓位失败: ' + (error.message || '网络错误'))
  } finally {
    refreshingFiltered.value = false
  }
}

/**
 * 刷新变红且超过30分钟仓位（打开时间>仓位时间，且打开时间距离现在超过30分钟）
 */
const refreshRedPositionsOld = async () => {
  // 获取所有背景标红且打开时间超过30分钟的行
  const ignoredBrowsersSet = getIgnoredBrowsersSet()
  const now = Date.now()
  const thirtyMinutesAgo = now - (30 * 60 * 1000)  // 30分钟前的毫秒时间戳

  const redOldRows = tableData.value.filter(row =>
    row.fingerprintNo &&
    row.computeGroup &&
    row.platform &&
    !ignoredBrowsersSet.has(String(row.fingerprintNo)) &&
    shouldHighlightRow(row) &&
    row.f // 确保有打开时间
  ).filter(row => {
    // 检查打开时间距离现在是否超过30分钟
    const openTime = typeof row.f === 'string' ? parseInt(row.f) : row.f
    return openTime <= thirtyMinutesAgo
  })

  if (redOldRows.length === 0) {
    ElMessage.warning('没有需要刷新的变红且超过30分钟的仓位')
    return
  }

  refreshingRedOld.value = true
  ElMessage.info(`开始刷新 ${redOldRows.length} 个变红且超过30分钟的仓位，请稍候...`)

  let successCount = 0
  let failCount = 0

  try {
    // 提交所有 type=2 任务
    const taskPromises = redOldRows.map(async (row) => {
      try {
        if (row.platform == 'OP'){
          const taskData = {
            groupNo: row.computeGroup,
            numberList: parseInt(row.fingerprintNo),
            type: 2,
            exchangeName: row.platform === 'OP' ? 'OP' : '监控'
          }

          const response = await axios.post(
            `${API_BASE_URL}/mission/add`,
            taskData,
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )

          // 保存最新的任务ID（只保留最后一个）
          if (response.data && response.data.data && response.data.data.id) {
            latestMissionId.value = response.data.data.id
          }

          console.log(`浏览器 ${row.fingerprintNo} 刷新任务已提交`)
          successCount++

        }

      } catch (error) {
        console.error(`浏览器 ${row.fingerprintNo} 刷新任务提交失败:`, error)
        failCount++
      }
    })

    await Promise.all(taskPromises)

    ElMessage.success(`已提交 ${successCount} 个刷新任务${failCount > 0 ? `，${failCount} 个失败` : ''}`)

    // 等待 70 秒后自动刷新列表
    ElMessage.info('任务已全部提交，70秒后自动刷新列表...')
    setTimeout(async () => {
      await loadData(true)  // 静默刷新
      ElMessage.success('数据已自动更新')
    }, 70000)

  } catch (error) {
    console.error('刷新变红且超过30分钟仓位失败:', error)
    ElMessage.error('刷新变红且超过30分钟仓位失败: ' + (error.message || '网络错误'))
  } finally {
    refreshingRedOld.value = false
  }
}

/**
 * 获取任务状态文本
 */
const getMissionStatusText = (status) => {
  if (status === null || status === undefined) return '未知'
  switch (status) {
    case 0:
      return '尚未执行'
    case 2:
      return '成功'
    case 3:
      return '失败'
    case 9:
      return '进行中'
    default:
      return `状态${status}`
  }
}

/**
 * 获取任务状态类型（用于标签颜色）
 */
const getMissionStatusType = (status) => {
  if (status === null || status === undefined) return 'info'
  switch (status) {
    case 0:
      return 'info'
    case 2:
      return 'success'
    case 3:
      return 'danger'
    case 9:
      return 'warning'
    default:
      return 'info'
  }
}

/**
 * 显示任务日志弹窗
 */
const showMissionLog = async () => {
  if (!latestMissionId.value) {
    ElMessage.warning('暂无任务ID')
    return
  }
  
  missionLogDialogVisible.value = true
  await refreshMissionStatus()
}

/**
 * 刷新任务状态
 */
const refreshMissionStatus = async () => {
  if (!latestMissionId.value) {
    ElMessage.warning('暂无任务ID')
    return
  }
  
  loadingMissionStatus.value = true
  
  try {
    const response = await axios.get(
      `${API_BASE_URL}/mission/status`,
      {
        params: {
          id: latestMissionId.value
        }
      }
    )
    
    if (response.data && response.data.data && response.data.data.mission) {
      const mission = response.data.data.mission
      missionStatus.value = {
        status: mission.status,
        msg: mission.msg || ''
      }
    } else {
      ElMessage.warning('未获取到任务状态')
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
    ElMessage.error('获取任务状态失败: ' + (error.message || '网络错误'))
  } finally {
    loadingMissionStatus.value = false
  }
}

/**
 * 地址去重
 * 检测数据中地址(h)是否有重复：
 * - 如果地址没有重复的，将字段 i 更新为"1"
 * - 如果地址有重复的，将字段 i 更新为""
 */
const deduplicateAddresses = async () => {
  deduplicating.value = true
  
  try {
    const data = tableData.value
    
    // 统计每个地址出现的次数
    const addressCountMap = new Map()
    
    for (const row of data) {
      if (row.h && row.h.trim()) {
        const address = row.h.trim()
        addressCountMap.set(address, (addressCountMap.get(address) || 0) + 1)
      }
    }
    
    // 找出只出现一次的地址（没有重复的）和出现多次的地址（有重复的）
    const uniqueAddresses = new Set()  // 唯一地址
    const duplicateAddresses = new Set()  // 重复地址
    
    for (const [address, count] of addressCountMap.entries()) {
      if (count === 1) {
        uniqueAddresses.add(address)
      } else if (count > 1) {
        duplicateAddresses.add(address)
      }
    }
    
    if (uniqueAddresses.size === 0 && duplicateAddresses.size === 0) {
      ElMessage.warning('没有找到有效的地址')
      return
    }
    
    // 更新数据：唯一地址的字段 i 为"1"，重复地址的字段 i 为""
    const updatedData = [...tableData.value]
    let updateCount = 0
    const updatedRowKeys = new Set()  // 记录被更新的行的唯一标识
    
    for (let i = 0; i < updatedData.length; i++) {
      const row = updatedData[i]
      if (row.h && row.h.trim()) {
        const address = row.h.trim()
        let shouldUpdate = false
        let newValue = null
        
        // 获取当前 i 字段的值（处理 null、undefined 等情况）
        const currentI = row.i === null || row.i === undefined ? '' : String(row.i)
        
        if (uniqueAddresses.has(address)) {
          // 唯一地址：设置为"1"（只有当原本不是"1"时才更新）
          if (currentI !== '1') {
            newValue = '1'
            shouldUpdate = true
          }
        } else if (duplicateAddresses.has(address)) {
          // 重复地址：设置为""（只有当原本不是""时才更新）
          if (currentI !== '') {
            newValue = ''
            shouldUpdate = true
          }
        }
        
        // 只有当值真正需要改变时才更新
        if (shouldUpdate) {
          updatedData[i] = { ...row, i: newValue }
          updateCount++
          // 记录被更新的行的唯一标识（优先使用id，否则使用fingerprintNo）
          const rowKey = row.id || row.fingerprintNo
          if (rowKey) {
            updatedRowKeys.add(rowKey)
          }
        }
      }
    }
    
    if (updateCount === 0) {
      ElMessage.warning('没有需要更新的数据')
      return
    }
    
    // 更新表格数据
    tableData.value = updatedData
    
    // 保存更新后的数据
    ElMessage.info(`发现 ${uniqueAddresses.size} 个唯一地址，${duplicateAddresses.size} 个重复地址，正在更新 ${updateCount} 条数据...`)
    
    // 批量保存更新后的数据（只保存实际被更新的数据）
    const dataToSave = updatedData
      .filter(row => {
        const rowKey = row.id || row.fingerprintNo
        return rowKey && updatedRowKeys.has(rowKey)
      })
      .map(row => {
        const saveData = { ...row }
        saveData.e = saveData.platform
        delete saveData.index
        delete saveData.refreshing
        if (!saveData.id) {
          delete saveData.id
        }
        return saveData
      })
    
    // 逐个保存，像输入框自动保存一样一个一个传
    let successCount = 0
    let failCount = 0
    
    for (let i = 0; i < dataToSave.length; i++) {
      const saveData = dataToSave[i]
      
      try {
        await axios.post(`${API_BASE_URL}/boost/addAccountConfig`, saveData)
        successCount++
        console.log(`已保存 ${successCount}/${dataToSave.length} 条数据`)
      } catch (error) {
        failCount++
        console.error(`保存数据失败:`, error)
      }
      
      // 避免请求过快，每个请求间隔200ms
      if (i < dataToSave.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 200))
      }
    }
    
    if (failCount === 0) {
      ElMessage.success(`地址去重完成：已更新 ${updateCount} 条数据（唯一地址设为"1"，重复地址设为""），全部保存成功`)
    } else {
      ElMessage.warning(`地址去重完成：已更新 ${updateCount} 条数据，成功保存 ${successCount} 条，失败 ${failCount} 条`)
    }
    
    // 重新加载数据以确保同步
    await loadData(true)
    
  } catch (error) {
    console.error('地址去重失败:', error)
    ElMessage.error('地址去重失败: ' + (error.message || '网络错误'))
  } finally {
    deduplicating.value = false
  }
}

/**
 * 获取浏览器代理配置
 * 调用 getIp API 获取代理 IP 和配置信息
 */
const getProxyConfig = async (browserId) => {
  try {
    const url = `${API_BASE_URL}/bro/getIp`
    const payload = { number: browserId }
    
    const response = await axios.post(url, payload, {
      timeout: 15000
    })
    
    if (response.status === 200) {
      const result = response.data
      const code = result?.code
      
      if (code === 0) {
        const data = result.data || {}
        const ip = data.ip
        const isMain = data.isMain || 0
        
        if (!ip) {
          console.error(`[${browserId}] 返回数据中没有IP字段`)
          return null
        }
        
        // 根据 isMain 字段决定如何构建代理配置
        if (isMain === 1) {
          const port = data.port
          const username = data.username
          const password = data.password
          
          if (ip && port && username && password) {
            return {
              ip: ip,
              port: String(port),
              username: username,
              password: password,
              type: 'http',
              isMain: isMain
            }
          } else {
            console.error(`[${browserId}] isMain=1 但返回数据中缺少必要字段`)
            return null
          }
        } else {
          // isMain != 1 时使用默认配置
          return {
            ip: ip,
            port: '50101',
            username: 'nolanwang',
            password: 'HFVsyegfeyigrfkjb',
            type: 'socks5',
            isMain: isMain
          }
        }
      } else {
        console.error(`[${browserId}] 获取IP失败: code=${code}, msg=${result?.msg}`)
        return null
      }
    } else {
      console.error(`[${browserId}] 获取IP请求失败: HTTP状态码 ${response.status}`)
      return null
    }
  } catch (error) {
    console.error(`[${browserId}] 获取代理配置失败:`, error)
    return null
  }
}

/**
 * 使用代理配置请求 contract-creator API
 * 直接请求 API，使用代理配置
 * 
 * 代理配置：
 * - type: 固定为 'http'
 * - port: 固定为 '50100'
 * - ip, username, password: 使用从服务器获取的数据
 */
const getContractCreatorWithProxy = async (address, proxyConfig) => {
  // 构建代理配置
  // type 固定为 'http'，port 固定为 '50100'
  const finalProxyConfig = {
    ip: proxyConfig.ip,
    port: '50100',  // 固定端口
    username: proxyConfig.username,
    password: proxyConfig.password,
    type: 'SOCKS5'  // 固定类型
  }
  
  console.log(`[代理请求] 地址: ${address}, 代理: ${finalProxyConfig.ip}:${finalProxyConfig.port} (${finalProxyConfig.type})`)
  console.log(`[代理配置] IP: ${finalProxyConfig.ip}, Port: ${finalProxyConfig.port}, Username: ${finalProxyConfig.username}, Type: ${finalProxyConfig.type}`)
  
  // 直接请求 API
  // 注意：浏览器无法直接使用 HTTP/SOCKS5 代理，这里先直接请求
  // 如果需要使用代理，需要通过后端转发或使用其他方式
  const apiUrl = `http://opinion.api.predictscan.dev:10001/api/user/contract-creator/${address}`
  
  try {
    const response = await axios.get(apiUrl, {
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
      // 注意：axios 在浏览器中无法直接配置代理
      // 如果需要使用代理，需要通过后端转发
    })
    
    return response
  } catch (error) {
    console.error(`[请求失败] 地址: ${address}, 错误:`, error)
    throw error
  }
}

/**
 * 手动快照
 * 调用 /boost/doSnapAccountConfig 接口
 */
const doSnapAccountConfig = async () => {
  snappingAccount.value = true
  
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/doSnapAccountConfig`)
    
    if (response.data) {
      ElMessage.success('手动快照成功')
      // 可选：快照成功后刷新列表
      setTimeout(async () => {
        await loadData(true)
      }, 1000)
    } else {
      ElMessage.warning('手动快照完成，但未返回数据')
    }
  } catch (error) {
    console.error('手动快照失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error('手动快照失败: ' + errorMsg)
  } finally {
    snappingAccount.value = false
  }
}

/**
 * 获取钱包地址
 * 遍历列表，对于 n 字段为空的记录：
 * - 如果 h 为空，跳过（或使用内置钱包地址，需要用户提供）
 * - 如果 h 不为空，先获取代理 IP，然后使用代理请求 API 获取 contractCreator，保存到 n 字段
 * - 每请求一个就立即更新一个
 */
const getWalletAddresses = async () => {
  gettingWalletAddresses.value = true
  
  try {
    const data = tableData.value
    
    // 找出 n 字段为空的记录
    const rowsToProcess = data.filter(row => {
      // n 字段为空（null、undefined 或空字符串）
      const nValue = row.n
      return !nValue || (typeof nValue === 'string' && !nValue.trim())
    })
    
    if (rowsToProcess.length === 0) {
      ElMessage.warning('没有需要处理的记录（所有记录的 n 字段都已填写）')
      return
    }
    
    ElMessage.info(`开始处理 ${rowsToProcess.length} 条记录...`)
    
    const updatedData = [...tableData.value]
    let successCount = 0
    let failCount = 0
    let skippedCount = 0  // h 为空跳过的记录数
    
    // 内置钱包地址（如果用户需要，可以在这里配置）
    const DEFAULT_WALLET_ADDRESS = null  // 用户需要提供内置钱包地址
    
    for (let i = 0; i < rowsToProcess.length; i++) {
      const row = rowsToProcess[i]
      let addressToUse = row.h ? row.h.trim() : ''
      
      // 如果 h 为空
      if (!addressToUse) {
        // 如果配置了默认钱包地址，使用默认地址
        if (DEFAULT_WALLET_ADDRESS) {
          addressToUse = DEFAULT_WALLET_ADDRESS
          // 更新 h 字段
          const rowIndex = updatedData.findIndex(r => {
            if (row.id && r.id) {
              return r.id === row.id
            }
            return r.fingerprintNo === row.fingerprintNo && 
                   r.computeGroup === row.computeGroup
          })
          if (rowIndex !== -1) {
            updatedData[rowIndex] = { ...updatedData[rowIndex], h: DEFAULT_WALLET_ADDRESS }
          }
        } else {
          // 没有配置默认地址，跳过
          skippedCount++
          console.log(`跳过记录 ${row.fingerprintNo || row.index}：h 字段为空且未配置默认钱包地址`)
          continue
        }
      }
      
      // 需要浏览器编号来获取代理配置
      if (!row.fingerprintNo) {
        skippedCount++
        console.log(`跳过记录 ${row.index}：缺少浏览器编号`)
        continue
      }
      
      // 1. 先获取代理配置
      console.log(`[${row.fingerprintNo}] 正在获取代理配置...`)
      const proxyConfig = await getProxyConfig(row.fingerprintNo)
      
      if (!proxyConfig) {
        failCount++
        console.error(`[${row.fingerprintNo}] 获取代理配置失败，跳过`)
        continue
      }
      
      console.log(`[${row.fingerprintNo}] 代理配置获取成功: IP=${proxyConfig.ip}, Port=${proxyConfig.port}, Type=${proxyConfig.type}`)
      
      // 2. 使用代理配置请求 contract-creator
      try {
        const response = await getContractCreatorWithProxy(addressToUse, proxyConfig)
        
        // 处理后端代理 API 的返回格式
        let contractCreator = null
        if (response.data) {
          // 如果后端代理 API 返回的数据格式与直接请求相同
          if (response.data.success && response.data.data && response.data.data.contractCreator) {
            contractCreator = response.data.data.contractCreator
          }
          // 如果后端代理 API 直接返回 contractCreator
          else if (response.data.contractCreator) {
            contractCreator = response.data.contractCreator
          }
          // 如果后端代理 API 返回的数据在 data 字段中
          else if (response.data.data && typeof response.data.data === 'string') {
            contractCreator = response.data.data
          }
        }
        
        if (contractCreator) {
          
          // 找到行在数组中的索引
          const rowIndex = updatedData.findIndex(r => {
            if (row.id && r.id) {
              return r.id === row.id
            }
            return r.fingerprintNo === row.fingerprintNo && 
                   r.computeGroup === row.computeGroup
          })
          
          if (rowIndex !== -1) {
            // 更新 n 字段
            updatedData[rowIndex] = { ...updatedData[rowIndex], n: contractCreator }
            tableData.value = updatedData  // 立即更新表格数据
            
            // 3. 立即保存到服务器
            try {
              const saveData = { ...updatedData[rowIndex] }
              saveData.e = saveData.platform
              delete saveData.index
              delete saveData.refreshing
              if (!saveData.id) {
                delete saveData.id
              }
              
              await axios.post(`${API_BASE_URL}/boost/addAccountConfig`, saveData)
              successCount++
              console.log(`[${row.fingerprintNo}] ✓ 成功获取并保存钱包地址: ${contractCreator}`)
            } catch (saveError) {
              // 即使保存失败，也记录为成功获取（因为已经更新到本地）
              successCount++
              console.error(`[${row.fingerprintNo}] 获取成功但保存失败:`, saveError)
            }
          }
        } else {
          failCount++
          console.error(`[${row.fingerprintNo}] 获取钱包地址失败：API 返回数据格式不正确`, response.data)
        }
      } catch (error) {
        failCount++
        let errorMsg = '未知错误'
        if (error.code === 'ERR_NETWORK') {
          errorMsg = '网络错误，可能是跨域问题或服务器不可访问'
        } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          errorMsg = '请求超时'
        } else if (error.response) {
          errorMsg = `服务器错误: ${error.response.status} - ${error.response.statusText}`
        } else if (error.message) {
          errorMsg = error.message
        }
        console.error(`[${row.fingerprintNo}] 获取钱包地址失败，地址: ${addressToUse}，错误: ${errorMsg}`, error)
      }
      
      // 避免请求过快，每个请求间隔500ms
      if (i < rowsToProcess.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }
    
    // 显示最终结果
    if (successCount === 0 && failCount === 0 && skippedCount > 0) {
      ElMessage.warning(`所有记录都因为 h 字段为空而跳过（共 ${skippedCount} 条）`)
    } else if (successCount > 0) {
      ElMessage.success(`获取钱包地址完成：成功 ${successCount} 个${skippedCount > 0 ? `，跳过 ${skippedCount} 个` : ''}${failCount > 0 ? `，失败 ${failCount} 个` : ''}`)
    } else {
      ElMessage.warning(`获取钱包地址完成：成功 ${successCount} 个，失败 ${failCount} 个${skippedCount > 0 ? `，跳过 ${skippedCount} 个` : ''}`)
    }
    
    // 重新加载数据以确保同步
    await loadData(true)
    
  } catch (error) {
    console.error('获取钱包地址失败:', error)
    ElMessage.error('获取钱包地址失败: ' + (error.message || '网络错误'))
  } finally {
    gettingWalletAddresses.value = false
  }
}

/**
 * 批量添加账户
 */
const batchAddAccounts = async () => {
  if (!batchAddInput.value || !batchAddInput.value.trim()) {
    ElMessage.warning('请输入要添加的数据')
    return
  }
  
  try {
    const input = batchAddInput.value.trim()
    const groups = input.split(';').map(g => g.trim()).filter(g => g)
    
    if (groups.length === 0) {
      ElMessage.warning('输入格式错误')
      return
    }
    
    const accountsToAdd = []
    
    for (const group of groups) {
      const parts = group.split(',').map(p => p.trim()).filter(p => p)
      
      if (parts.length < 2) {
        ElMessage.warning(`格式错误: ${group}，至少需要电脑组和一个浏览器ID`)
        continue
      }
      
      const computeGroup = parts[0]
      const browserIds = parts.slice(1)
      
      // 为每个浏览器ID创建账户配置
      for (const browserId of browserIds) {
        accountsToAdd.push({
          computeGroup: computeGroup,
          fingerprintNo: browserId,
          platform: 'OP',
          balance: 0,
          a: '',
          b: '',
          c: '0',
          d: '',
          e: 'OP',
          f: null,
          g: null,
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
        })
      }
    }
    
    if (accountsToAdd.length === 0) {
      ElMessage.warning('没有有效的账户数据')
      return
    }
    
    ElMessage.info(`开始添加 ${accountsToAdd.length} 个账户...`)
    
    // 逐个添加账户
    let successCount = 0
    let failCount = 0
    
    for (const account of accountsToAdd) {
      try {
        await axios.post(`${API_BASE_URL}/boost/addAccountConfig`, account)
        successCount++
        console.log(`账户 ${account.fingerprintNo} 添加成功`)
      } catch (error) {
        failCount++
        console.error(`账户 ${account.fingerprintNo} 添加失败:`, error)
      }
    }
    
    ElMessage.success(`成功添加 ${successCount} 个账户${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    
    // 清空输入框
    batchAddInput.value = ''
    
    // 重新加载数据
    await loadData()
    
  } catch (error) {
    console.error('批量添加失败:', error)
    ElMessage.error('批量添加失败: ' + (error.message || '网络错误'))
  }
}

/**
 * 批量删除账户
 */
const batchDeleteAccounts = async () => {
  if (!batchDeleteInput.value || !batchDeleteInput.value.trim()) {
    ElMessage.warning('请输入要删除的浏览器ID')
    return
  }
  
  batchDeleting.value = true
  
  try {
    const input = batchDeleteInput.value.trim()
    // 支持逗号和分号分隔
    const browserIds = input.split(/[,;]/).map(id => id.trim()).filter(id => id)
    
    if (browserIds.length === 0) {
      ElMessage.warning('输入格式错误，请输入浏览器ID')
      return
    }
    
    // 从表格数据中查找对应的行
    const rowsToDelete = []
    const notFoundIds = []
    
    for (const browserId of browserIds) {
      const row = tableData.value.find(r => String(r.fingerprintNo) === String(browserId))
      if (row && row.id) {
        rowsToDelete.push(row)
      } else {
        notFoundIds.push(browserId)
      }
    }
    
    if (rowsToDelete.length === 0) {
      ElMessage.warning('没有找到可删除的数据（所有浏览器ID都没有对应的数据或没有ID）')
      if (notFoundIds.length > 0) {
        ElMessage.info(`未找到的浏览器ID: ${notFoundIds.join(', ')}`)
      }
      return
    }
    
    // 确认删除
    try {
      await ElMessageBox.confirm(
        `确定要删除 ${rowsToDelete.length} 个账户吗？\n浏览器ID: ${rowsToDelete.map(r => r.fingerprintNo).join(', ')}`,
        '批量删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      ElMessage.info('已取消删除')
      return
    }
    
    ElMessage.info(`开始删除 ${rowsToDelete.length} 个账户...`)
    
    // 逐个删除账户
    let successCount = 0
    let failCount = 0
    
    for (const row of rowsToDelete) {
      try {
        await axios.post(`${API_BASE_URL}/boost/deleteAccountConfig`, {
          id: row.id
        })
        successCount++
        console.log(`账户 ${row.fingerprintNo} (ID: ${row.id}) 删除成功`)
      } catch (error) {
        failCount++
        console.error(`账户 ${row.fingerprintNo} (ID: ${row.id}) 删除失败:`, error)
      }
      
      // 避免请求过快
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    if (notFoundIds.length > 0) {
      ElMessage.warning(`删除完成：成功删除 ${successCount} 个账户${failCount > 0 ? `，失败 ${failCount} 个` : ''}。未找到的浏览器ID: ${notFoundIds.join(', ')}`)
    } else {
      ElMessage.success(`删除完成：成功删除 ${successCount} 个账户${failCount > 0 ? `，失败 ${failCount} 个` : ''}`)
    }
    
    // 清空输入框
    batchDeleteInput.value = ''
    
    // 重新加载数据
    await loadData()
    
  } catch (error) {
    console.error('批量删除失败:', error)
    ElMessage.error('批量删除失败: ' + (error.message || '网络错误'))
  } finally {
    batchDeleting.value = false
  }
}

/**
 * 导出地址
 * 根据浏览器编号，导出对应的地址(h)到txt文件
 */
const exportAddresses = () => {
  if (!exportAddressInput.value || !exportAddressInput.value.trim()) {
    ElMessage.warning('请输入浏览器编号')
    return
  }
  
  exportingAddresses.value = true
  
  try {
    const input = exportAddressInput.value.trim()
    // 支持逗号和分号分隔
    const browserIds = input.split(/[,;]/).map(id => id.trim()).filter(id => id)
    
    if (browserIds.length === 0) {
      ElMessage.warning('输入格式错误，请输入浏览器编号')
      return
    }
    
    // 从表格数据中查找对应的地址
    const addresses = []
    const notFoundIds = []
    
    for (const browserId of browserIds) {
      const row = tableData.value.find(r => String(r.fingerprintNo) === String(browserId))
      if (row && row.h && row.h.trim()) {
        addresses.push(row.h.trim())
      } else {
        notFoundIds.push(browserId)
      }
    }
    
    if (addresses.length === 0) {
      ElMessage.warning('没有找到有效的地址')
      if (notFoundIds.length > 0) {
        ElMessage.info(`未找到地址的浏览器编号: ${notFoundIds.join(', ')}`)
      }
      return
    }
    
    // 生成文件内容（每行一个地址）
    const content = addresses.join('\n')
    
    // 生成文件名（包含时间戳）
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    const filename = `addresses_${timestamp}.txt`
    
    // 下载文件
    downloadTextFile(content, filename)
    
    // 显示成功消息
    if (notFoundIds.length > 0) {
      ElMessage.warning(`已导出 ${addresses.length} 个地址到 ${filename}，未找到地址的浏览器编号: ${notFoundIds.join(', ')}`)
    } else {
      ElMessage.success(`已导出 ${addresses.length} 个地址到 ${filename}`)
    }
    
    // 清空输入框
    exportAddressInput.value = ''
    
  } catch (error) {
    console.error('导出地址失败:', error)
    ElMessage.error('导出地址失败: ' + (error.message || '未知错误'))
  } finally {
    exportingAddresses.value = false
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadData()
  loadChainData()  // 加载链上数据
  
  // 如果自动刷新已启用，启动定时器
  if (autoRefresh.value.enabled) {
    startAutoRefresh()
  }
  
  // 加载忽略浏览器配置
  try {
    const savedIgnoredBrowsers = localStorage.getItem('ignoredBrowsers')
    if (savedIgnoredBrowsers) {
      positionTimeConfig.value.ignoredBrowsers = savedIgnoredBrowsers
    }
  } catch (error) {
    console.error('加载忽略浏览器配置失败:', error)
  }
  
  // 监听导航事件
  window.addEventListener('navigate-to-list', () => {
    currentPage.value = 'list'
  })
})

/**
 * 组件卸载时清理定时器
 */
onUnmounted(() => {
  stopAutoRefresh()
  
  // 清理自动更新定时器
  if (autoUpdateTimer) {
    clearInterval(autoUpdateTimer)
    autoUpdateTimer = null
  }
  
  // 清理所有防抖定时器
  for (const timer of saveRowTimers.values()) {
    clearTimeout(timer)
  }
  saveRowTimers.clear()
  
  // 清理缓存
  parsedDataCache.clear()
  parsedRowsSet.value.clear()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-navigation {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  gap: 10px;
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
  align-items: center;
  flex-wrap: wrap;
}

.auto-refresh-control {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border-left: 2px solid #ddd;
  border-right: 2px solid #ddd;
}

.auto-refresh-control span {
  font-size: 14px;
  color: #606266;
}

.red-count-label {
  font-size: 14px;
  color: #f56c6c;
  padding: 0 12px;
  border-left: 2px solid #ddd;
  white-space: nowrap;
}

.red-count-label strong {
  font-size: 16px;
  color: #e74c3c;
  font-weight: 700;
}

.parsing-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border-left: 2px solid #ddd;
  color: #409eff;
  font-size: 14px;
  white-space: nowrap;
}

.parsing-progress .el-icon {
  font-size: 14px;
}

.batch-add-container {
  margin-bottom: 15px;
  padding: 12px 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.batch-add-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-add-row label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.batch-add-tip {
  font-size: 12px;
  color: #999;
  font-style: italic;
}

.position-time-config-container {
  margin-bottom: 15px;
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.position-time-config-container .config-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.position-time-config-container .config-row:last-child {
  margin-bottom: 0;
}

.position-time-config-container label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.position-time-config-container span {
  font-size: 14px;
  color: #606266;
}

.filter-container {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.points-summary-container {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.points-summary-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e0e0e0;
}

.points-summary-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.points-by-date {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.points-date-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.points-date-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.points-date-value {
  font-size: 14px;
  color: #409eff;
  font-weight: 600;
}

.points-total {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  margin-top: 5px;
}

.points-total-label {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.points-total-value {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
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

/* 总计信息容器 */
.summary-container {
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.3s ease;
}

.summary-container.collapsed {
  padding: 15px 20px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.summary-container.collapsed .summary-header {
  margin-bottom: 0;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-hint {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.8);
  font-style: italic;
  text-shadow: none;
}

.collapse-btn {
  background-color: rgba(255, 255, 255, 0.2) !important;
  border: none !important;
  color: #fff !important;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.3) !important;
  transform: scale(1.1);
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* 折叠过渡动画 */
.summary-collapse-enter-active,
.summary-collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.summary-collapse-enter-from,
.summary-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 15px;
  background-color: rgba(255, 255, 255, 0.15);
  padding: 12px 15px;
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

.summary-positions {
  flex-direction: column;
  align-items: flex-start;
}

.summary-positions-list {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.empty-summary {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-style: italic;
}

.summary-position-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  transition: all 0.3s;
}

.summary-position-item:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateX(5px);
}

.position-title-summary {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
  flex: 1;
  line-height: 1.4;
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

.empty-text {
  color: #999;
  font-size: 12px;
}

.address-text {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #409eff;
  word-break: break-all;
  cursor: pointer;
  user-select: all;
  padding: 4px 8px;
  background-color: #f0f9ff;
  border-radius: 4px;
  display: inline-block;
  max-width: 100%;
  transition: background-color 0.2s;
}

.address-text:hover {
  background-color: #e0f2fe;
}

.raw-data-text {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  line-height: 1.5;
}

.parsing-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #409eff;
  font-size: 13px;
  padding: 10px;
}

.parsing-text .el-icon {
  font-size: 14px;
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

/* 弹窗内的空消息 */
.empty-message {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: center;
}

/* 高亮行（打开时间>仓位时间） */
:deep(.el-table__row.highlight-row) {
  background-color: #fee !important;
}

:deep(.el-table__row.highlight-row:hover > td) {
  background-color: #fdd !important;
}

/* 持有仓位不匹配时的黄色背景 */
.position-mismatch {
  background-color: #fffacd !important;
}

.raw-data-text.position-mismatch {
  background-color: #fffacd !important;
}

.position-list.position-mismatch {
  background-color: #fffacd !important;
}

.position-list.position-mismatch .position-item {
  background-color: #fffacd !important;
}

/* 分页容器 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* 任务日志弹窗样式 */
.mission-log-content {
  padding: 20px;
  min-height: 150px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-label {
  font-size: 15px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
  min-width: 80px;
}

.log-value {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  word-break: break-all;
}
</style>

