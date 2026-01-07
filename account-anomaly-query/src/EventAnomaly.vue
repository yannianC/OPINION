<template>
  <div class="event-anomaly-page">
    <!-- 数量统计表 -->
    <el-collapse v-model="statisticsCollapseActive" class="statistics-collapse">
      <el-collapse-item name="statistics" title="表1-数量">
        <el-table 
          :data="quantityStatisticsData" 
          border 
          style="width: 100%"
          class="statistics-table"
        >
          <el-table-column prop="label" label="" width="150" align="center" fixed />
          <el-table-column prop="total" label="总量" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.total }}</span>
              <span v-else>{{ formatNumber(scope.row.total) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range0_50" label="0到50" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range0_50 }}</span>
              <span v-else>{{ formatNumber(scope.row.range0_50) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range50_100" label="50到100" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range50_100 }}</span>
              <span v-else>{{ formatNumber(scope.row.range50_100) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range100_200" label="100到200" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range100_200 }}</span>
              <span v-else>{{ formatNumber(scope.row.range100_200) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range200_300" label="200到300" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range200_300 }}</span>
              <span v-else>{{ formatNumber(scope.row.range200_300) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range300_500" label="300到500" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range300_500 }}</span>
              <span v-else>{{ formatNumber(scope.row.range300_500) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range500_1000" label="500到1000" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range500_1000 }}</span>
              <span v-else>{{ formatNumber(scope.row.range500_1000) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range1000_2000" label="1000到2000" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range1000_2000 }}</span>
              <span v-else>{{ formatNumber(scope.row.range1000_2000) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range2000_plus" label="2000+" width="120" align="center">
            <template #default="scope">
              <span v-if="scope.row.label === 'yesno占总比'">{{ scope.row.range2000_plus }}</span>
              <span v-else>{{ formatNumber(scope.row.range2000_plus) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <!-- 仓位更新时间统计表 -->
    <el-collapse v-model="timeStatisticsCollapseActive" class="statistics-collapse">
      <el-collapse-item :name="'timeStatistics'" :title="`表2-仓位更新时间${dataUpdateTime ? ' (数据更新时间: ' + dataUpdateTime + ')' : ''}`">
        <el-table 
          :data="timeStatisticsData" 
          border 
          style="width: 100%"
          class="statistics-table"
        >
          <el-table-column prop="label" label="" width="150" align="center" fixed />
          <el-table-column prop="total" label="总量" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.total) : scope.row.total }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range0_1h" label="0到1小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range0_1h) : scope.row.range0_1h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range1_4h" label="1小时到4小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range1_4h) : scope.row.range1_4h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range4_8h" label="4小时到8小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range4_8h) : scope.row.range4_8h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range8_12h" label="8小时到12小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range8_12h) : scope.row.range8_12h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range12_24h" label="12小时到24小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range12_24h) : scope.row.range12_24h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range24_48h" label="24小时到48小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range24_48h) : scope.row.range24_48h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range48_96h" label="48小时到96小时" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range48_96h) : scope.row.range48_96h }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="range96h_plus" label="96小时以上" width="120" align="center">
            <template #default="scope">
              <span>{{ scope.row.label === '事件金额' ? formatNumber(scope.row.range96h_plus) : scope.row.range96h_plus }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <h1 class="page-title">事件异常</h1>
    
    <div class="toolbar">
      <el-button type="primary" @click="loadAndCalculate" :loading="loading">
        刷新数据
      </el-button>
      <el-button type="success" @click="exportAndCopy" :disabled="selectedCount === 0" style="margin-left: 10px;">
        导出勾选主题并复制 ({{ selectedCount }})
      </el-button>
      <el-button type="warning" @click="exportAllBrowsers" :disabled="selectedCount === 0" style="margin-left: 10px;">
        导出勾选主题相关的所有浏览器编号 ({{ selectedCount }})
      </el-button>
      <el-button type="danger" @click="exportRedBrowsers" :disabled="selectedCount === 0" style="margin-left: 10px;">
        导出勾选主题相关的变红浏览器编号 ({{ selectedCount }})
      </el-button>
      <el-button type="warning" @click="saveAllBlacklistStatus" :loading="savingBlacklist" style="margin-left: 10px;">
        保存勾选状态
      </el-button>
      <el-button type="info" @click="snapAllPos" style="margin-left: 10px;">
        快照
      </el-button>
      <el-select 
        v-model="selectedSnapRecordId" 
        style="width: 150px; margin-left: 10px;"
        placeholder="选择快照记录"
        @focus="loadSnapPosTime"
      >
        <el-option 
          v-for="record in snapRecordList" 
          :key="record.recordId" 
          :label="formatSnapTime(record.recordTime)" 
          :value="record.recordId" 
        />
      </el-select>
      <el-button type="primary" @click="querySnapRecord" :disabled="!selectedSnapRecordId" style="margin-left: 10px;">
        查询快照
      </el-button>
      <el-button type="primary" @click="updateOrderbook" :loading="updatingOrderbook" style="margin-left: 10px;">
        更新订单薄
      </el-button>
      <el-select 
        v-model="selectedGroup" 
        @change="handleGroupChange"
        style="width: 120px; margin-left: 10px;"
        placeholder="选择分组"
      >
        <el-option label="全部" value="all" />
        <el-option label="分组1" value="1" />
        <el-option label="分组2" value="2" />
      </el-select>
    </div>

    <!-- 显示复制的内容 -->
    <div class="copied-content-display" v-if="copiedContent.eventNames || copiedContent.allBrowsers || copiedContent.redBrowsers">
      <div v-if="copiedContent.eventNames" class="copied-item">
        <div class="copied-label">
          导出勾选主题并复制：
          <span class="count-badge">({{ getEventNamesCount() }} 个主题)</span>
        </div>
        <div class="copied-text">{{ copiedContent.eventNames }}</div>
      </div>
      <div v-if="copiedContent.allBrowsers" class="copied-item">
        <div class="copied-label">
          导出勾选主题相关的所有浏览器编号：
          <span class="count-badge">({{ getAllBrowsersCount() }} 个浏览器)</span>
        </div>
        <div class="copied-text">{{ copiedContent.allBrowsers }}</div>
        
        <!-- 上一次导出结果和最终结果 -->
        <div v-if="browserExportState.type === 'all'" class="export-extra-section">
          <div class="export-section">
            <div class="export-label">
              上一次导出结果：
              <span class="count-badge">({{ browserExportState.previousResult ? browserExportState.previousResult.split(',').filter(item => item.trim()).length : 0 }} 个浏览器)</span>
            </div>
            <el-input
              v-model="browserExportState.previousResult"
              type="textarea"
              :rows="3"
              placeholder="上一次导出的结果（可编辑）"
              class="export-input"
            />
          </div>
          
          <div class="export-section">
            <div class="export-label">
              最终结果（交集）：
              <span class="count-badge">({{ finalResult ? finalResult.split(',').filter(item => item.trim()).length : 0 }} 个浏览器)</span>
            </div>
            <div class="copied-text final-result">{{ finalResult || '（上一次结果为空，直接使用本次结果）' }}</div>
          </div>
          
          <div class="export-actions">
            <el-button type="primary" @click="confirmAndCopy" :disabled="!finalResult || !finalResult.trim()">
              确定并复制
            </el-button>
          </div>
        </div>
      </div>
      <div v-if="copiedContent.redBrowsers" class="copied-item">
        <div class="copied-label">
          导出勾选主题相关的变红浏览器编号：
          <span class="count-badge">({{ getRedBrowsersCount() }} 个浏览器)</span>
        </div>
        <div class="copied-text">{{ copiedContent.redBrowsers }}</div>
        
        <!-- 上一次导出结果和最终结果 -->
        <div v-if="browserExportState.type === 'red'" class="export-extra-section">
          <div class="export-section">
            <div class="export-label">
              上一次导出结果：
              <span class="count-badge">({{ browserExportState.previousResult ? browserExportState.previousResult.split(',').filter(item => item.trim()).length : 0 }} 个浏览器)</span>
            </div>
            <el-input
              v-model="browserExportState.previousResult"
              type="textarea"
              :rows="3"
              placeholder="上一次导出的结果（可编辑）"
              class="export-input"
            />
          </div>
          
          <div class="export-section">
            <div class="export-label">
              最终结果（交集）：
              <span class="count-badge">({{ finalResult ? finalResult.split(',').filter(item => item.trim()).length : 0 }} 个浏览器)</span>
            </div>
            <div class="copied-text final-result">{{ finalResult || '（上一次结果为空，直接使用本次结果）' }}</div>
          </div>
          
          <div class="export-actions">
            <el-button type="primary" @click="confirmAndCopy" :disabled="!finalResult || !finalResult.trim()">
              确定并复制
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 事件统计表格 -->
    <el-table 
      :data="eventTableData" 
      border 
      style="width: 100%"
      v-loading="loading"
      height="calc(100vh - 500px)"
    >
      <el-table-column type="index" label="序号" width="60" align="center" :index="indexMethod" fixed />
      <el-table-column prop="eventName" label="事件名" width="400" fixed>
        <template #default="scope">
          <div class="event-name-cell">
            <el-checkbox 
              v-model="scope.row.selected" 
              style="margin-right: 10px;"
              @change="() => handleSelectionChange(scope.row)"
            />
            {{ scope.row.eventName }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="拉黑状态" width="120" align="center" fixed sortable :sort-method="(a, b) => sortByBlacklistStatus(a.blacklistStatus, b.blacklistStatus)">
        <template #default="scope">
          <span :class="scope.row.blacklistStatus === '1' || scope.row.blacklistStatus === 1 ? 'blacklisted' : 'not-blacklisted'">
            {{ scope.row.blacklistStatus === '1' || scope.row.blacklistStatus === 1 ? '已拉黑' : '未拉黑' }}
          </span>
        </template>
      </el-table-column>

      <!-- <el-table-column label="拉黑" width="100" align="center" fixed>
        <template #default="scope">
          <el-checkbox 
            v-model="scope.row.isBlacklisted" 
            :disabled="!scope.row.configId"
          />
        </template>
      </el-table-column> -->

      <el-table-column label="yes持仓数量" width="120" align="center" fixed sortable :sort-method="(a, b) => sortByNumber(a.yesPosition, b.yesPosition)">
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

      <el-table-column label="链上实际差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.chainActualDiff, b.chainActualDiff)">
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

      <el-table-column label="忽略的差额" width="130" align="center" sortable :sort-method="(a, b) => sortByNumber(a.ignoreDiff, b.ignoreDiff)">
        <template #default="scope">
          <el-input 
            v-model.number="scope.row.ignoreDiff" 
            type="number" 
            size="small"
            placeholder="0"
            @blur="updateIgnoreDiff(scope.row)"
            style="width: 100px;"
          />
        </template>
      </el-table-column>

      <el-table-column label="使用忽略后的差额" width="160" align="center" sortable :sort-method="(a, b) => sortByNumber(a.finalDiffAfterIgnore, b.finalDiffAfterIgnore)">
        <template #default="scope">
          <span :class="parseFloat(scope.row.finalDiffAfterIgnore) >= 0 ? 'positive' : 'negative'">
            {{ formatNumber(scope.row.finalDiffAfterIgnore) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="仓位平均更新时间" width="150" align="center" sortable :sort-method="(a, b) => sortByNumber(a.avgUpdateTime, b.avgUpdateTime)">
        <template #default="scope">
          <span>{{ formatAvgTimeAgo(scope.row.avgUpdateTime) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="仓位最新一次更新时间" width="180" align="center" sortable :sort-method="(a, b) => sortByNumber(a.latestUpdateTime, b.latestUpdateTime)">
        <template #default="scope">
          <span>{{ formatTimeAgo(scope.row.latestUpdateTime) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="持有yes的账户数量" width="160" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesAccountCount, b.yesAccountCount)">
        <template #default="scope">
          <span>{{ scope.row.yesAccountCount || 0 }}</span>
        </template>
      </el-table-column>

      <el-table-column label="持有no的账户数量" width="160" align="center" sortable :sort-method="(a, b) => sortByNumber(a.noAccountCount, b.noAccountCount)">
        <template #default="scope">
          <span>{{ scope.row.noAccountCount || 0 }}</span>
        </template>
      </el-table-column>

      <el-table-column label="YES买一价及深度" width="140" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesBidPrice, b.yesBidPrice)">
        <template #default="scope">
          <div 
            v-if="scope.row.yesBidPrice !== null && scope.row.yesBidPrice !== undefined && scope.row.yesBidDepth !== null && scope.row.yesBidDepth !== undefined" 
            :class="{ 'depth-qualified': isDepthQualified(scope.row) }"
            style="line-height: 1.5;"
          >
            <div>{{ formatNumber(scope.row.yesBidPrice) }}</div>
            <div style="font-size: 12px; color: #909399;">{{ formatNumber(scope.row.yesBidDepth) }}</div>
          </div>
          <span v-else style="color: #909399;">-</span>
        </template>
      </el-table-column>

      <el-table-column label="YES卖一价及深度" width="140" align="center" sortable :sort-method="(a, b) => sortByNumber(a.yesAskPrice, b.yesAskPrice)">
        <template #default="scope">
          <div 
            v-if="scope.row.yesAskPrice !== null && scope.row.yesAskPrice !== undefined && scope.row.yesAskDepth !== null && scope.row.yesAskDepth !== undefined" 
            :class="{ 'depth-qualified': isDepthQualified(scope.row) }"
            style="line-height: 1.5;"
          >
            <div>{{ formatNumber(scope.row.yesAskPrice) }}</div>
            <div style="font-size: 12px; color: #909399;">{{ formatNumber(scope.row.yesAskDepth) }}</div>
          </div>
          <span v-else style="color: #909399;">-</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="scope">
          <el-button 
            type="success" 
            size="small" 
            @click="openOpUrl(scope.row)"
            :disabled="!scope.row.opUrl"
          >
            打开
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'https://sg.bicoin.com.cn/99l'
const CHAIN_STATS_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/markets/stats'
const ORDERBOOK_API_URL = 'https://enstudyai.fatedreamer.com/t3/api/orderbooks'

const loading = ref(false)
const eventTableData = ref([])
const selectedGroup = ref('all')
const groupConfigList = ref([]) // 存储当前分组的事件名列表
const accountDataCache = ref([]) // 存储原始账户数据，用于导出浏览器编号
const exchangeConfigList = ref([]) // 存储 exchangeConfig 配置列表
const configMap = ref(new Map()) // 存储 trending -> config 的映射
const idToTrendingMap = ref(new Map()) // 存储 id -> trending 的映射
const savingBlacklist = ref(false) // 是否正在保存拉黑状态
const updatingOrderbook = ref(false) // 是否正在更新订单薄
const statisticsCollapseActive = ref([]) // 统计表折叠状态，默认为空数组（折叠）
const timeStatisticsCollapseActive = ref([]) // 时间统计表折叠状态，默认为空数组（折叠）
const dataUpdateTime = ref('') // 数据更新时间（格式化字符串，用于显示）
const dataUpdateTimestamp = ref(0) // 数据更新时间戳（用于计算）
const snapRecordList = ref([]) // 快照记录列表
const selectedSnapRecordId = ref(null) // 选中的快照记录ID
const copiedContent = ref({
  eventNames: '', // 导出勾选主题并复制的内容
  allBrowsers: '', // 导出所有浏览器编号的内容
  redBrowsers: '' // 导出变红浏览器编号的内容
})
// 浏览器编号导出相关状态
const browserExportState = ref({
  type: '', // 'all' 或 'red'，表示当前导出类型
  currentResult: '', // 本次导出结果
  previousResult: '' // 上一次导出结果（可编辑）
})

/**
 * 计算选中的事件数量
 */
const selectedCount = computed(() => {
  return eventTableData.value.filter(item => item.selected).length
})

/**
 * 计算数量统计数据
 * 按每个账号每个事件的yes/no数量来统计区间
 */
const quantityStatisticsData = computed(() => {
  // 定义区间范围
  const ranges = [
    { min: 0, max: 50, key: 'range0_50' },
    { min: 50, max: 100, key: 'range50_100' },
    { min: 100, max: 200, key: 'range100_200' },
    { min: 200, max: 300, key: 'range200_300' },
    { min: 300, max: 500, key: 'range300_500' },
    { min: 500, max: 1000, key: 'range500_1000' },
    { min: 1000, max: 2000, key: 'range1000_2000' },
    { min: 2000, max: Infinity, key: 'range2000_plus' }
  ]
  
  // 初始化统计数据
  const stats = {
    yes: {
      total: 0,
      range0_50: 0,
      range50_100: 0,
      range100_200: 0,
      range200_300: 0,
      range300_500: 0,
      range500_1000: 0,
      range1000_2000: 0,
      range2000_plus: 0
    },
    no: {
      total: 0,
      range0_50: 0,
      range50_100: 0,
      range100_200: 0,
      range200_300: 0,
      range300_500: 0,
      range500_1000: 0,
      range1000_2000: 0,
      range2000_plus: 0
    }
  }
  
  // 从accountDataCache遍历每个账号的每个事件
  if (accountDataCache.value && accountDataCache.value.length > 0) {
    for (const row of accountDataCache.value) {
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
      
      // 获取该账号该事件的yes/no数量
      const amount = Math.abs(parseFloat(row.amt) || 0)
      const outComeUpper = (row.outCome || direction).toUpperCase()
      
      if (outComeUpper === 'YES') {
        // 累加yes总量
        stats.yes.total += amount
        
        // 统计yes数量区间
        for (const range of ranges) {
          if (range.max === Infinity) {
            // 2000+区间
            if (amount >= range.min) {
              stats.yes[range.key] += amount
              break
            }
          } else {
            // 其他区间
            if (amount >= range.min && amount < range.max) {
              stats.yes[range.key] += amount
              break
            }
          }
        }
      } else if (outComeUpper === 'NO') {
        // 累加no总量
        stats.no.total += amount
        
        // 统计no数量区间
        for (const range of ranges) {
          if (range.max === Infinity) {
            // 2000+区间
            if (amount >= range.min) {
              stats.no[range.key] += amount
              break
            }
          } else {
            // 其他区间
            if (amount >= range.min && amount < range.max) {
              stats.no[range.key] += amount
              break
            }
          }
        }
      }
    }
  }
  
  // 计算yes+no总量
  const yesNoTotal = {
    total: stats.yes.total + stats.no.total,
    range0_50: stats.yes.range0_50 + stats.no.range0_50,
    range50_100: stats.yes.range50_100 + stats.no.range50_100,
    range100_200: stats.yes.range100_200 + stats.no.range100_200,
    range200_300: stats.yes.range200_300 + stats.no.range200_300,
    range300_500: stats.yes.range300_500 + stats.no.range300_500,
    range500_1000: stats.yes.range500_1000 + stats.no.range500_1000,
    range1000_2000: stats.yes.range1000_2000 + stats.no.range1000_2000,
    range2000_plus: stats.yes.range2000_plus + stats.no.range2000_plus
  }
  
  // 计算占比（yesno占总比）
  const totalAmount = yesNoTotal.total
  const percentage = {
    total: totalAmount > 0 ? (totalAmount / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range0_50: totalAmount > 0 ? (yesNoTotal.range0_50 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range50_100: totalAmount > 0 ? (yesNoTotal.range50_100 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range100_200: totalAmount > 0 ? (yesNoTotal.range100_200 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range200_300: totalAmount > 0 ? (yesNoTotal.range200_300 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range300_500: totalAmount > 0 ? (yesNoTotal.range300_500 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range500_1000: totalAmount > 0 ? (yesNoTotal.range500_1000 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range1000_2000: totalAmount > 0 ? (yesNoTotal.range1000_2000 / totalAmount * 100).toFixed(2) + '%' : '0.00%',
    range2000_plus: totalAmount > 0 ? (yesNoTotal.range2000_plus / totalAmount * 100).toFixed(2) + '%' : '0.00%'
  }
  
  // 返回表格数据
  return [
    {
      label: 'yes数量',
      total: stats.yes.total,
      range0_50: stats.yes.range0_50,
      range50_100: stats.yes.range50_100,
      range100_200: stats.yes.range100_200,
      range200_300: stats.yes.range200_300,
      range300_500: stats.yes.range300_500,
      range500_1000: stats.yes.range500_1000,
      range1000_2000: stats.yes.range1000_2000,
      range2000_plus: stats.yes.range2000_plus
    },
    {
      label: 'no数量',
      total: stats.no.total,
      range0_50: stats.no.range0_50,
      range50_100: stats.no.range50_100,
      range100_200: stats.no.range100_200,
      range200_300: stats.no.range200_300,
      range300_500: stats.no.range300_500,
      range500_1000: stats.no.range500_1000,
      range1000_2000: stats.no.range1000_2000,
      range2000_plus: stats.no.range2000_plus
    },
    {
      label: 'yes+no总量',
      total: yesNoTotal.total,
      range0_50: yesNoTotal.range0_50,
      range50_100: yesNoTotal.range50_100,
      range100_200: yesNoTotal.range100_200,
      range200_300: yesNoTotal.range200_300,
      range300_500: yesNoTotal.range300_500,
      range500_1000: yesNoTotal.range500_1000,
      range1000_2000: yesNoTotal.range1000_2000,
      range2000_plus: yesNoTotal.range2000_plus
    },
    {
      label: 'yesno占总比',
      total: percentage.total,
      range0_50: percentage.range0_50,
      range50_100: percentage.range50_100,
      range100_200: percentage.range100_200,
      range200_300: percentage.range200_300,
      range300_500: percentage.range300_500,
      range500_1000: percentage.range500_1000,
      range1000_2000: percentage.range1000_2000,
      range2000_plus: percentage.range2000_plus
    }
  ]
})

/**
 * 计算仓位更新时间统计数据
 * 按每个事件的 ctime 与数据更新时间的差值来统计区间
 */
const timeStatisticsData = computed(() => {
  // 定义时间区间范围（单位：毫秒）
  const ranges = [
    { min: 0, max: 1 * 60 * 60 * 1000, key: 'range0_1h' }, // 0到1小时
    { min: 1 * 60 * 60 * 1000, max: 4 * 60 * 60 * 1000, key: 'range1_4h' }, // 1小时到4小时
    { min: 4 * 60 * 60 * 1000, max: 8 * 60 * 60 * 1000, key: 'range4_8h' }, // 4小时到8小时
    { min: 8 * 60 * 60 * 1000, max: 12 * 60 * 60 * 1000, key: 'range8_12h' }, // 8小时到12小时
    { min: 12 * 60 * 60 * 1000, max: 24 * 60 * 60 * 1000, key: 'range12_24h' }, // 12小时到24小时
    { min: 24 * 60 * 60 * 1000, max: 48 * 60 * 60 * 1000, key: 'range24_48h' }, // 24小时到48小时
    { min: 48 * 60 * 60 * 1000, max: 96 * 60 * 60 * 1000, key: 'range48_96h' }, // 48小时到96小时
    { min: 96 * 60 * 60 * 1000, max: Infinity, key: 'range96h_plus' } // 96小时以上
  ]
  
  // 初始化统计数据
  const stats = {
    eventCount: {
      total: 0,
      range0_1h: 0,
      range1_4h: 0,
      range4_8h: 0,
      range8_12h: 0,
      range12_24h: 0,
      range24_48h: 0,
      range48_96h: 0,
      range96h_plus: 0
    },
    eventAmount: {
      total: 0,
      range0_1h: 0,
      range1_4h: 0,
      range4_8h: 0,
      range8_12h: 0,
      range12_24h: 0,
      range24_48h: 0,
      range48_96h: 0,
      range96h_plus: 0
    }
  }
  
  // 如果没有数据更新时间戳，返回空数据
  if (!dataUpdateTimestamp.value || dataUpdateTimestamp.value === 0) {
    return [
      {
        label: '事件数量',
        total: 0,
        range0_1h: 0,
        range1_4h: 0,
        range4_8h: 0,
        range8_12h: 0,
        range12_24h: 0,
        range24_48h: 0,
        range48_96h: 0,
        range96h_plus: 0
      },
      {
        label: '事件金额',
        total: 0,
        range0_1h: 0,
        range1_4h: 0,
        range4_8h: 0,
        range8_12h: 0,
        range12_24h: 0,
        range24_48h: 0,
        range48_96h: 0,
        range96h_plus: 0
      }
    ]
  }
  
  // 使用存储的时间戳
  const updateTimestamp = dataUpdateTimestamp.value
  
  // 从accountDataCache遍历每个事件
  if (accountDataCache.value && accountDataCache.value.length > 0) {
    for (const row of accountDataCache.value) {
      // 获取 ctime（仓位创建时间）
      if (!row.ctime) {
        continue
      }
      
      const ctime = typeof row.ctime === 'string' ? parseInt(row.ctime) : row.ctime
      if (isNaN(ctime)) {
        continue
      }
      
      // 计算时间差（数据更新时间 - ctime）
      const timeDiff = updateTimestamp - ctime
      
      // 如果时间差为负数，跳过（ctime 晚于数据更新时间）
      if (timeDiff < 0) {
        continue
      }
      
      // 获取事件金额：amt * avgPrice
      const amt = parseFloat(row.amt) || 0
      const avgPrice = parseFloat(row.avgPrice) || 0
      const eventAmount = amt * avgPrice
      
      // 累加总量
      stats.eventCount.total += 1
      stats.eventAmount.total += eventAmount
      
      // 统计时间区间
      for (const range of ranges) {
        if (range.max === Infinity) {
          // 96小时以上区间
          if (timeDiff >= range.min) {
            stats.eventCount[range.key] += 1
            stats.eventAmount[range.key] += eventAmount
            break
          }
        } else {
          // 其他区间
          if (timeDiff >= range.min && timeDiff < range.max) {
            stats.eventCount[range.key] += 1
            stats.eventAmount[range.key] += eventAmount
            break
          }
        }
      }
    }
  }
  
  // 返回表格数据
  return [
    {
      label: '事件数量',
      total: stats.eventCount.total,
      range0_1h: stats.eventCount.range0_1h,
      range1_4h: stats.eventCount.range1_4h,
      range4_8h: stats.eventCount.range4_8h,
      range8_12h: stats.eventCount.range8_12h,
      range12_24h: stats.eventCount.range12_24h,
      range24_48h: stats.eventCount.range24_48h,
      range48_96h: stats.eventCount.range48_96h,
      range96h_plus: stats.eventCount.range96h_plus
    },
    {
      label: '事件金额',
      total: stats.eventAmount.total,
      range0_1h: stats.eventAmount.range0_1h,
      range1_4h: stats.eventAmount.range1_4h,
      range4_8h: stats.eventAmount.range4_8h,
      range8_12h: stats.eventAmount.range8_12h,
      range12_24h: stats.eventAmount.range12_24h,
      range24_48h: stats.eventAmount.range24_48h,
      range48_96h: stats.eventAmount.range48_96h,
      range96h_plus: stats.eventAmount.range96h_plus
    }
  ]
})

/**
 * 计算最终结果（交集）
 */
const finalResult = computed(() => {
  const current = browserExportState.value.currentResult
  const previous = browserExportState.value.previousResult
  
  // 如果上一次结果为空，直接返回本次结果
  if (!previous || !previous.trim()) {
    return current || ''
  }
  
  // 如果本次结果为空，返回空
  if (!current || !current.trim()) {
    return ''
  }
  
  // 计算交集
  const currentSet = new Set(current.split(',').map(item => item.trim()).filter(item => item))
  const previousSet = new Set(previous.split(',').map(item => item.trim()).filter(item => item))
  
  const intersection = Array.from(currentSet).filter(item => previousSet.has(item))
  
  // 排序并返回
  return intersection.sort((a, b) => parseInt(a) - parseInt(b)).join(',')
})

/**
 * 序号计算方法（从1开始）
 */
const indexMethod = (index) => {
  return index + 1
}

/**
 * 保存勾选状态到本地存储
 */
const saveSelectionState = () => {
  try {
    const selectedEvents = eventTableData.value
      .filter(item => item.selected)
      .map(item => item.eventName)
    
    localStorage.setItem('eventAnomaly_selectedEvents', JSON.stringify(selectedEvents))
    console.log('[事件异常] 勾选状态已保存到本地，共', selectedEvents.length, '个')
  } catch (error) {
    console.error('[事件异常] 保存勾选状态失败:', error)
  }
}

/**
 * 从本地存储加载勾选状态
 */
/**
 * 从本地存储恢复勾选状态（已废弃，现在从服务器的字段 b 获取）
 * 保留此函数以避免调用错误，但不执行任何操作
 * 勾选状态在 loadAndCalculate 中已从服务器的 b 字段设置
 */
const loadSelectionState = () => {
  // 不再从本地存储恢复，而是从服务器的字段 b 获取
  // 勾选状态在 loadAndCalculate 中已从服务器的 b 字段设置
  console.log('[事件异常] 勾选状态已从服务器的字段 b 获取，不再使用本地存储')
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (row) => {
  // 同步更新 isBlacklisted 状态，确保两者一致
  // selected 勾选状态对应拉黑状态：勾选=拉黑，未勾选=未拉黑
  row.isBlacklisted = row.selected
  // 不再保存到本地存储，因为现在从服务器的字段 b 获取
  // saveSelectionState()
}

/**
 * 格式化数字
 */
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '0.00'
  const num = parseFloat(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

/**
 * 格式化时间差（显示为几分钟前/几小时前/几天前）
 */
const formatTimeAgo = (timestamp) => {
  if (!timestamp || timestamp === 0) return '-'
  
  const now = Date.now()
  const diff = now - timestamp
  
  if (diff < 0) return '未来时间'
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
}

/**
 * 格式化平均更新时间（显示为几分钟前/几小时前/几天前）
 */
const formatAvgTimeAgo = (avgMinutes) => {
  if (avgMinutes === null || avgMinutes === undefined || avgMinutes === 0) return '-'
  
  const hours = Math.floor(avgMinutes / 60)
  const days = Math.floor(avgMinutes / (60 * 24))
  
  if (avgMinutes < 60) return `${Math.round(avgMinutes)}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
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
 * 拉黑状态排序方法
 * 已拉黑（a === "1" 或 a === 1）排在前面，未拉黑排在后面
 */
const sortByBlacklistStatus = (a, b) => {
  const isBlacklistedA = a === '1' || a === 1
  const isBlacklistedB = b === '1' || b === 1
  
  // 如果都是拉黑或都不是拉黑，按原始值排序
  if (isBlacklistedA === isBlacklistedB) {
    // 如果都是拉黑，返回0（保持原顺序）
    if (isBlacklistedA) {
      return 0
    }
    // 如果都不是拉黑，按值排序（null/undefined 排在最后）
    if (a === null || a === undefined) return 1
    if (b === null || b === undefined) return -1
    const numA = parseFloat(a) || 0
    const numB = parseFloat(b) || 0
    return numA - numB
  }
  
  // 已拉黑排在前面
  return isBlacklistedA ? -1 : 1
}

/**
 * 判断深度是否符合条件
 * 条件：卖一价减去买一价大于0.15，或者买一价或卖一价的深度小于100
 */
const isDepthQualified = (row) => {
  if (!row) {
    return false
  }
  
  const bidPrice = parseFloat(row.yesBidPrice) || 0
  const askPrice = parseFloat(row.yesAskPrice) || 0
  const bidDepth = parseFloat(row.yesBidDepth) || 0
  const askDepth = parseFloat(row.yesAskDepth) || 0
  
  // 如果数据不完整，返回false
  if (bidPrice === 0 && askPrice === 0) {
    return false
  }
  
  // 卖一价减去买一价大于0.15
  const priceDiff = askPrice - bidPrice
  if (priceDiff > 0.15) {
    return true
  }
  
  // 买一价或卖一价的深度小于100
  if (bidDepth < 100 || askDepth < 100) {
    return true
  }
  
  return false
}

/**
 * 解析持仓数据字符串（a字段）
 * 格式: "事件唯一名|||方向|||数量|||价格;..."
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
          amount: parseFloat(amount) || 0,
          avgPrice: avgPrice
        })
      } else if (partsLength >= 3 && !isNewFormat) {
        positions.push({
          title: parts[0].trim(),
          option: parts[1].trim(),
          amount: parseFloat(parts[2].trim()) || 0,
          avgPrice: ''
        })
      } else if (partsLength >= 2 && !isNewFormat) {
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
 * 解析带逗号的数字字符串（如：1,369.55）
 */
const parseNumberWithComma = (str) => {
  if (!str) return 0
  // 移除逗号后解析
  const cleaned = str.replace(/,/g, '')
  return parseFloat(cleaned) || 0
}

/**
 * 解析挂单数据字符串（b字段）
 * 支持多种格式：
 * 1. 新格式（5个字段）："事件唯一名|||买卖方向|||方向|||价格|||进度"
 * 2. 旧格式（3个字段）："标题|||价格|||进度"
 * 3. 更旧格式（逗号分隔）："标题,价格,进度"
 * 进度格式支持：
 * - 数量格式：60.55/554.74shares 或 239.13/1,369.55shares
 * - 金额格式：$0/$462.2 或 $0/$1,462.2
 */
const parseOrders = (ordersStr) => {
  if (!ordersStr) return []
  
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
          const title = parts[0].trim()
          const buySellDirection = parts[1].trim() // "Buy" 或 "Sell"
          const option = parts[2].trim() // "YES" 或 "NO"
          const price = parts[3].trim()
          const progress = parts[4].trim()
          
          // 解析价格：83.8 ¢ -> 提取数字部分
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pending = 0
          let filled = 0
          let total = 0
          
          // 判断进度格式：$0/$462.2（金额格式）或 60.55/554.74shares 或 239.13/1,369.55shares（数量格式）
          if (progress.includes('$')) {
            // 金额格式：$0/$462.2 或 $0/$1,462.2 -> 未成交金额 = 总金额 - 已成交金额
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              const pendingAmount = totalAmount - filledAmount
              // 未成交数量 = 未成交金额 * 100 / 价格
              if (priceNum > 0) {
                pending = (pendingAmount * 100) / priceNum
              }
              filled = filledAmount
              total = totalAmount
            }
          } else {
            // 数量格式：60.55/554.74shares 或 239.13/1,369.55shares -> 未成交数量 = 总数量 - 已成交数量
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              filled = parseNumberWithComma(progressMatch[1])
              total = parseNumberWithComma(progressMatch[2])
              pending = total - filled
            }
          }
          
          orders.push({
            title: title,
            buySellDirection: buySellDirection,
            option: option,
            price: price,
            filled: filled,
            total: total,
            pending: pending
          })
        } else if (parts.length >= 3) {
          // 兼容旧格式（3个字段：标题|||价格|||进度）
          const title = parts[0].trim()
          const price = parts[1].trim()
          const progress = parts[2].trim()
          
          // 解析价格
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pending = 0
          let filled = 0
          let total = 0
          
          // 判断进度格式
          if (progress.includes('$')) {
            // 金额格式
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              const pendingAmount = totalAmount - filledAmount
              if (priceNum > 0) {
                pending = (pendingAmount * 100) / priceNum
              }
              filled = filledAmount
              total = totalAmount
            }
          } else {
            // 数量格式
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              filled = parseNumberWithComma(progressMatch[1])
              total = parseNumberWithComma(progressMatch[2])
              pending = total - filled
            }
          }
          
          orders.push({
            title: title,
            price: price,
            filled: filled,
            total: total,
            pending: pending
          })
        }
      } else {
        // 兼容更旧格式（逗号分隔符）
        const parts = item.split(',')
        if (parts.length >= 3) {
          const title = parts[0].trim()
          const price = parts[1].trim()
          const progress = parts[2].trim()
          
          // 解析价格
          let priceNum = 0
          const priceMatch = price.match(/([\d.]+)/)
          if (priceMatch) {
            priceNum = parseFloat(priceMatch[1]) || 0
          }
          
          let pending = 0
          let filled = 0
          let total = 0
          
          // 判断进度格式
          if (progress.includes('$')) {
            // 金额格式
            const amountMatch = progress.match(/\$?([\d.,]+)\/\$?([\d.,]+)/)
            if (amountMatch) {
              const filledAmount = parseNumberWithComma(amountMatch[1])
              const totalAmount = parseNumberWithComma(amountMatch[2])
              const pendingAmount = totalAmount - filledAmount
              if (priceNum > 0) {
                pending = (pendingAmount * 100) / priceNum
              }
              filled = filledAmount
              total = totalAmount
            }
          } else {
            // 数量格式
            const progressMatch = progress.match(/([\d.,]+)\/([\d.,]+)/)
            if (progressMatch) {
              filled = parseNumberWithComma(progressMatch[1])
              total = parseNumberWithComma(progressMatch[2])
              pending = total - filled
            }
          }
          
          orders.push({
            title: title,
            price: price,
            filled: filled,
            total: total,
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
 * 匹配事件名称和链上数据的title
 * 支持完全匹配和部分匹配（去除特殊字符后匹配）
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
  
  // 去除特殊字符后匹配（去除问号等）
  const normalize = (str) => {
    return str
      .split('###')[0]  // 去除 ### 后面的部分
      .replace(/[?()]/g, '')  // 去除问号、括号
      .replace(/\s+/g, ' ')  // 多个空格合并为一个
      .trim()
      .toLowerCase()
  }
  
  const normalizedEvent = normalize(eventName)
  const normalizedChain = normalize(chainTitle)
  
  // 部分匹配：检查是否包含主要关键词
  if (normalizedEvent && normalizedChain) {
    // 如果去除特殊字符后相同，则匹配
    if (normalizedEvent === normalizedChain) return true
    
    // 如果事件名称包含在链上title中，或链上title包含在事件名称中，也认为匹配
    if (normalizedEvent.includes(normalizedChain) || normalizedChain.includes(normalizedEvent)) {
      return true
    }
  }
  
  return false
}

/**
 * 加载分组配置数据
 */
const loadGroupConfig = async (groupNo) => {
  try {
    console.log(`[事件异常] 开始加载分组${groupNo}配置...`)
    const response = await axios.get(`${API_BASE_URL}/mission/exchangeConfigByGroupNo?groupNo=${groupNo}`)
    
    if (response.data && response.data.code === 0 && response.data.data && response.data.data.configList) {
      // 提取所有trending字段作为事件名列表
      const eventNames = response.data.data.configList
        .map(config => config.trending)
        .filter(trending => trending) // 过滤掉null或undefined
      
      console.log(`[事件异常] 分组${groupNo}配置加载完成，共 ${eventNames.length} 个事件`)
      return eventNames
    } else {
      console.warn(`[事件异常] 未获取到分组${groupNo}配置数据`)
      return []
    }
  } catch (error) {
    console.error(`[事件异常] 加载分组${groupNo}配置失败:`, error)
    return []
  }
}

/**
 * 加载 exchangeConfig 配置
 */
const loadExchangeConfig = async () => {
  try {
    console.log('[事件异常] 开始加载 exchangeConfig 配置...')
    const response = await axios.get(`${API_BASE_URL}/mission/exchangeConfig`)
    
    if (response.data && response.data.code === 0 && response.data.data && response.data.data.configList) {
      exchangeConfigList.value = response.data.data.configList
      
      // 创建 trending -> config 的映射（完全匹配）
      const newConfigMap = new Map()
      // 创建 id -> trending 的映射
      const newIdToTrendingMap = new Map()
      for (const config of exchangeConfigList.value) {
        if (config.trending) {
          const trending = config.trending.trim()
          newConfigMap.set(trending, config)
        }
        if (config.id && config.trending) {
          newIdToTrendingMap.set(String(config.id), config.trending.trim())
        }
      }
      configMap.value = newConfigMap
      idToTrendingMap.value = newIdToTrendingMap
      
      console.log(`[事件异常] exchangeConfig 配置加载完成，共 ${exchangeConfigList.value.length} 个配置`)
      console.log(`[事件异常] id -> trending 映射完成，共 ${newIdToTrendingMap.size} 个映射`)
      return exchangeConfigList.value
    } else {
      console.warn('[事件异常] 未获取到 exchangeConfig 配置数据')
      return []
    }
  } catch (error) {
    console.error('[事件异常] 加载 exchangeConfig 配置失败:', error)
    return []
  }
}

/**
 * 加载链上数据
 */
const loadChainStats = async () => {
  try {
    console.log('[事件异常] 开始加载链上数据...')
    const response = await axios.get(CHAIN_STATS_API_URL)
    
    if (response.data && response.data.markets && Array.isArray(response.data.markets)) {
      const chainDataMap = new Map()
      
      // 处理每个市场的数据，按完整title存储（包括###后面的部分）
      // 如果同一个完整title出现多次，则累加数据
      for (const item of response.data.markets) {
        if (item.title) {
          const fullTitle = item.title.trim()
          const yesTotal = parseFloat(item.yes_total || 0)
          const noTotal = parseFloat(item.no_total || 0)
          
          // 如果同一个完整title已经存在，累加数据
          if (chainDataMap.has(fullTitle)) {
            const existing = chainDataMap.get(fullTitle)
            existing.yesTotal += yesTotal
            existing.noTotal += noTotal
          } else {
            // 新建条目，使用完整title作为key
            chainDataMap.set(fullTitle, {
              title: fullTitle.split('###')[0].trim(),  // 基础title（去除###后的部分）
              fullTitle: fullTitle,  // 完整title
              yesTotal: yesTotal,  // 直接使用，可能是负数
              noTotal: noTotal  // 直接使用，可能是负数
            })
          }
        }
      }
      
      console.log(`[事件异常] 链上数据加载完成，共 ${chainDataMap.size} 个市场`)
      console.log('[事件异常] 链上数据示例:', Array.from(chainDataMap.entries()).slice(0, 5))
      return chainDataMap
    } else {
      console.warn('[事件异常] 未获取到链上数据')
      return new Map()
    }
  } catch (error) {
    console.error('[事件异常] 加载链上数据失败:', error)
    return new Map()
  }
}

/**
 * 匹配并更新链上数据
 */
const matchAndUpdateChainData = (chainDataMap) => {
  console.log('[事件异常] 开始匹配链上数据，事件数量:', eventTableData.value.length, '链上数据数量:', chainDataMap.size)
  
  // 直接更新表格数据中的链上数据
  for (const event of eventTableData.value) {
    const trimmedEventName = event.eventName.trim()
    let matched = false
    
    // 尝试完全匹配
    if (chainDataMap.has(trimmedEventName)) {
      const chainData = chainDataMap.get(trimmedEventName)
      event.chainYesPosition = chainData.yesTotal
      event.chainNoPosition = chainData.noTotal
      matched = true
  
    } else {
      // 遍历链上数据，尝试完全匹配（去除首尾空格）
      for (const [chainTitle, chainData] of chainDataMap.entries()) {
        if (trimmedEventName === chainData.fullTitle.trim() || trimmedEventName === chainTitle.trim()) {
          event.chainYesPosition = chainData.yesTotal
          event.chainNoPosition = chainData.noTotal
          matched = true
          console.log('[事件异常] 完全匹配成功（去除空格）:', trimmedEventName, '->', chainData.fullTitle, 'yes:', chainData.yesTotal, 'no:', chainData.noTotal)
          break
        }
      }
    }
    
    if (!matched) {
      console.log('[事件异常] 未匹配到链上数据（需要完全匹配）:', trimmedEventName)
    }
    
    // 重新计算链上相关差额
    // 链上实际差额：链上yes持仓数量 - 链上no持仓数量
    event.chainActualDiff = event.chainYesPosition - event.chainNoPosition
    
    // 链上成交后差额：链上实际差额 + 挂单差额（使用原有的挂单差额）
    event.chainFinalDiff = event.chainActualDiff + event.orderDiff
  }
}

/**
 * 加载数据并计算事件统计
 */
const loadAndCalculate = async () => {
  loading.value = true
  
  try {
    console.log('[事件异常] 开始加载数据...')
    
    // 如果选择了分组且分组配置列表为空，先加载分组配置
    if (selectedGroup.value !== 'all' && groupConfigList.value.length === 0) {
      const eventNames = await loadGroupConfig(selectedGroup.value)
      groupConfigList.value = eventNames
    }
    
    // 先加载 exchangeConfig 配置（需要用于 id -> trending 映射）
    await loadExchangeConfig()
    
    // 加载账户数据（不等待链上数据）
    const accountResponse = await axios.get(`${API_BASE_URL}/boost/getAllPosSnap`)
    
    // 记录数据更新时间（当前时间）
    const now = new Date()
    dataUpdateTimestamp.value = now.getTime() // 保存时间戳用于计算
    dataUpdateTime.value = now.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
    
    if (accountResponse.data && accountResponse.data.data && accountResponse.data.data.list) {
      const data = accountResponse.data.data.list
      console.log(`[事件异常] 获取到 ${data.length} 条数据，开始解析...`)
      
      // 过滤掉 amt < 1 的数据
      const filteredData = data.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt >= 1
      })
      console.log(`[事件异常] 过滤后剩余 ${filteredData.length} 条数据（已过滤掉 ${data.length - filteredData.length} 条 amt < 1 的数据）`)
      
      // 保存原始账户数据，用于导出浏览器编号（使用过滤后的数据）
      accountDataCache.value = filteredData
      
      // 使用 Map 存储每个事件的统计数据
      const eventMap = new Map()
      
      // 处理每条数据（使用过滤后的数据）
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
          console.warn(`[事件异常] 未找到 id=${configId} 对应的 trending`)
          continue
        }
        
        // 初始化事件数据
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
            chainFinalDiff: 0,
            yesBidPrice: null,
            yesBidDepth: null,
            yesAskPrice: null,
            yesAskDepth: null,
            noBidPrice: null,
            noBidDepth: null,
            noAskPrice: null,
            noAskDepth: null,
            trendingPart1: null,
            trendingPart2: null,
            opUrl: null,
            updatingOrderbook: false,
            // 新增字段
            avgUpdateTime: null, // 仓位平均更新时间（分钟数）
            latestUpdateTime: null, // 仓位最新一次更新时间（时间戳）
            yesAccountCount: 0, // 持有YES的账户数量
            noAccountCount: 0, // 持有NO的账户数量
            // 用于计算的临时数据
            _positions: [], // 存储所有仓位数据
            _yesAccounts: new Set(), // 存储持有YES的账户编号
            _noAccounts: new Set() // 存储持有NO的账户编号
          })
        }
        
        const event = eventMap.get(eventName)
        const amount = Math.abs(parseFloat(row.amt) || 0)
        
        // 根据 outCome 判断方向（YES/NO）
        const outComeUpper = (row.outCome || direction).toUpperCase()
        if (outComeUpper === 'YES') {
          event.yesPosition += amount
          // 记录持有YES的账户
          if (row.number) {
            event._yesAccounts.add(String(row.number))
          }
        } else if (outComeUpper === 'NO') {
          event.noPosition += amount
          // 记录持有NO的账户
          if (row.number) {
            event._noAccounts.add(String(row.number))
          }
        }
        
        // 保存仓位数据用于计算平均更新时间
        if (row.utime) {
          const utime = typeof row.utime === 'string' ? parseInt(row.utime) : row.utime
          if (!isNaN(utime)) {
            event._positions.push({
              utime: utime,
              amount: amount
            })
          }
        }
      }
      
      // 计算差额（先不包含链上数据）
      // 使用数据更新时间作为基准时间（已在前面设置）
      const now = dataUpdateTimestamp.value || Date.now()
      for (const event of eventMap.values()) {
        // 实际差额：yes持仓数量 - no持仓数量（将no置为负数后相加）
        event.actualDiff = event.yesPosition - event.noPosition
        
        // 挂单差额：挂单yes数量 + (-挂单no数量) = 挂单yes数量 - 挂单no数量
        event.orderDiff = event.orderYes - event.orderNo
        
        // 成交后差额：实际差额 + 挂单差额
        event.finalDiff = event.actualDiff + event.orderDiff
        
        // 链上实际差额：链上yes持仓数量 - 链上no持仓数量（暂时为0）
        event.chainActualDiff = event.chainYesPosition - event.chainNoPosition
        
        // 链上成交后差额：链上实际差额 + 挂单差额（暂时为0）
        event.chainFinalDiff = event.chainActualDiff + event.orderDiff
        
        // 计算持有YES的账户数量
        event.yesAccountCount = event._yesAccounts.size
        
        // 计算持有NO的账户数量
        event.noAccountCount = event._noAccounts.size
        
        // 计算仓位最新一次更新时间（找到最大的utime）
        if (event._positions.length > 0) {
          const maxUtime = Math.max(...event._positions.map(p => p.utime))
          event.latestUpdateTime = maxUtime
          
          // 检查最新更新时间是否小于3分钟，如果是则打印所有符合条件的账户
          const timeDiff = now - maxUtime
          const minutesAgo = timeDiff / (1000 * 60)
          if (minutesAgo < 3 && minutesAgo >= 0) {
            // 遍历原始数据，找出该事件下所有 utime 小于3分钟的账户（使用 Set 去重 number）
            const recentAccountNumbers = new Set()
            for (const row of accountDataCache.value) {
              if (!row.trendingKey) continue
              const parts = row.trendingKey.split('::')
              if (parts.length < 2) continue
              const configId = parts[0].trim()
              const eventNameFromId = idToTrendingMap.value.get(configId)
              if (eventNameFromId === event.eventName && row.utime) {
                const utime = typeof row.utime === 'string' ? parseInt(row.utime) : row.utime
                if (!isNaN(utime)) {
                  const rowTimeDiff = now - utime
                  const rowMinutesAgo = rowTimeDiff / (1000 * 60)
                  if (rowMinutesAgo < 3 && rowMinutesAgo >= 0 && row.number) {
                    recentAccountNumbers.add(String(row.number))
                  }
                }
              }
            }
            // 打印所有符合条件的账户
            // if (recentAccountNumbers.size > 0) {
            //   console.log(`[事件异常] 事件 "${event.eventName}" 最近一次仓位更新时间小于3分钟，符合条件的账户：`)
            //   recentAccountNumbers.forEach(number => {
            //     console.log(`  - number: ${number}, 事件名: ${event.eventName}`)
            //   })
            // }
          }
        } else {
          event.latestUpdateTime = null
        }
        
        // 计算仓位平均更新时间（加权平均：每个仓位距离现在的分钟数 * 数量，然后全部相加，再除以所有数量相加）
        if (event._positions.length > 0) {
          let totalWeightedMinutes = 0
          let totalAmount = 0
          
          for (const pos of event._positions) {
            const timeDiff = now - pos.utime
            // 如果时间差为负数（未来时间），跳过或设为0
            if (timeDiff < 0) {
              continue
            }
            const minutesAgo = timeDiff / (1000 * 60) // 转换为分钟
            totalWeightedMinutes += minutesAgo * pos.amount
            totalAmount += pos.amount
          }
          
          if (totalAmount > 0) {
            event.avgUpdateTime = totalWeightedMinutes / totalAmount
          } else {
            event.avgUpdateTime = null
          }
        } else {
          event.avgUpdateTime = null
        }
        
        // 清理临时数据
        delete event._positions
        delete event._yesAccounts
        delete event._noAccounts
      }
      
      // 转换为数组并排序（按成交后差额绝对值降序）
      let allEvents = Array.from(eventMap.values()).sort((a, b) => {
        return Math.abs(b.finalDiff) - Math.abs(a.finalDiff)
      })
      
      // 初始化选中状态，并匹配 exchangeConfig 配置
      allEvents.forEach(event => {
        // 匹配 exchangeConfig 配置（完全匹配）
        const eventName = event.eventName.trim()
        const matchedConfig = configMap.value.get(eventName)
        
        if (matchedConfig) {
          // 从配置的 a 字段获取忽略的差额，如果为空则显示为 0
          event.ignoreDiff = matchedConfig.a !== null && matchedConfig.a !== undefined 
            ? parseFloat(matchedConfig.a) || 0 
            : 0
          event.configId = matchedConfig.id // 保存配置ID，用于更新
          // 保存 a 字段的原始值，用于显示拉黑状态
          event.blacklistStatus = matchedConfig.a !== null && matchedConfig.a !== undefined ? matchedConfig.a : null
          // 从配置的 b 字段获取拉黑状态：b=1 表示拉黑，b=0/null/undefined 表示未拉黑
          event.isBlacklisted = matchedConfig.b === 1 || matchedConfig.b === '1'
          // 保存原始 b 值，用于后续比较（处理 null、undefined、0、1 等情况）
          event.originalB = matchedConfig.b !== null && matchedConfig.b !== undefined ? matchedConfig.b : 0
          // 事件名前面的勾选状态从服务器的字段 b 获取：b=1 则勾选，b!=1 则不勾选
          event.selected = matchedConfig.b === 1 || matchedConfig.b === '1'
          // 保存trendingPart1和trendingPart2，用于获取订单薄数据
          event.trendingPart1 = matchedConfig.trendingPart1 || null
          event.trendingPart2 = matchedConfig.trendingPart2 || null
          // 保存opUrl，用于打开链接
          event.opUrl = matchedConfig.opUrl || null
          // 保存opTopicId，用于匹配订单薄数据（market_id对应opTopicId）
          event.opTopicId = matchedConfig.opTopicId || null
        } else {
          event.ignoreDiff = 0
          event.configId = null
          event.blacklistStatus = null  // 未匹配到配置，拉黑状态为 null
          event.isBlacklisted = false
          event.originalB = 0  // 未匹配到配置，默认为未拉黑
          event.selected = false  // 未匹配到配置，默认不勾选
          event.trendingPart1 = null
          event.trendingPart2 = null
          event.opUrl = null
          event.opTopicId = null
        }
        
        // 初始化更新订单薄状态
        event.updatingOrderbook = false
        
        // 计算使用忽略后的差额：成交后差额 - 忽略的差额
        event.finalDiffAfterIgnore = event.finalDiff - event.ignoreDiff
      })
      
      // 根据选择的分组进行过滤
      if (selectedGroup.value !== 'all' && groupConfigList.value.length > 0) {
        // 创建事件名集合用于快速查找（支持完全匹配和去除空格后的匹配）
        const eventNameSet = new Set(groupConfigList.value.map(name => name.trim()))
        const normalizedEventNameSet = new Set(
          groupConfigList.value.map(name => {
            // 去除首尾空格，去除###后面的部分
            return name.trim().split('###')[0].trim()
          })
        )
        
        allEvents = allEvents.filter(event => {
          const eventName = event.eventName.trim()
          const eventNameBase = eventName.split('###')[0].trim()
          
          // 完全匹配
          if (eventNameSet.has(eventName)) return true
          
          // 基础名称匹配（去除###后的部分）
          if (normalizedEventNameSet.has(eventNameBase)) return true
          
          // 检查是否包含在配置列表中（部分匹配）
          for (const configName of groupConfigList.value) {
            const configNameTrimmed = configName.trim()
            const configNameBase = configNameTrimmed.split('###')[0].trim()
            
            if (eventName === configNameTrimmed || eventNameBase === configNameBase) {
              return true
            }
            
            // 如果事件名包含配置名或配置名包含事件名，也认为匹配
            if (eventName.includes(configNameTrimmed) || configNameTrimmed.includes(eventName)) {
              return true
            }
            if (eventNameBase && configNameBase && 
                (eventNameBase.includes(configNameBase) || configNameBase.includes(eventNameBase))) {
              return true
            }
          }
          
          return false
        })
        
        console.log(`[事件异常] 分组${selectedGroup.value}过滤后，共 ${allEvents.length} 个事件`)
      }
      
      eventTableData.value = allEvents
      
      // 从本地存储恢复勾选状态
      loadSelectionState()
      
      console.log('[事件异常] 主要数据计算完成，开始异步加载链上数据...')
      ElMessage.success(`数据加载并计算完成，共 ${eventTableData.value.length} 个事件`)
      
      // 异步加载链上数据和订单薄数据
      Promise.all([
        loadChainStats().then(chainDataMap => {
          console.log('[事件异常] 链上数据加载完成，开始匹配并更新...')
          matchAndUpdateChainData(chainDataMap)
          console.log('[事件异常] 链上数据匹配完成')
          return chainDataMap
        }).catch(error => {
          console.error('[事件异常] 加载链上数据失败:', error)
          return null
        }),
        loadAllOrderbooks().then(orderbooks => {
          console.log('[事件异常] 订单薄数据加载完成，开始匹配并更新...')
          matchAndUpdateOrderbookData(orderbooks)
          console.log('[事件异常] 订单薄数据匹配完成')
          return orderbooks
        }).catch(error => {
          console.error('[事件异常] 加载订单薄数据失败:', error)
          return []
        })
      ]).then(() => {
        ElMessage.success('链上数据和订单薄数据已更新')
      })
    } else {
      ElMessage.warning('未获取到数据')
    }
  } catch (error) {
    console.error('[事件异常] 加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 处理分组变化
 */
const handleGroupChange = async (value) => {
  console.log('[事件异常] 分组选择变化:', value)
  
  if (value === 'all') {
    // 选择"全部"时，清空分组配置列表
    groupConfigList.value = []
    // 重新加载数据（会显示所有事件）
    await loadAndCalculate()
  } else {
    // 选择分组1或分组2时，加载对应的配置
    const eventNames = await loadGroupConfig(value)
    groupConfigList.value = eventNames
    
    if (eventNames.length === 0) {
      ElMessage.warning(`分组${value}配置为空，将显示所有事件`)
    } else {
      console.log(`[事件异常] 分组${value}包含的事件:`, eventNames)
      // 重新加载数据（会根据分组配置过滤）
      await loadAndCalculate()
    }
  }
}

/**
 * 计算导出的主题数量
 */
const getEventNamesCount = () => {
  if (!copiedContent.value.eventNames) return 0
  // 按分号分隔，计算数量
  return copiedContent.value.eventNames.split(';').filter(item => item.trim()).length
}

/**
 * 计算导出的所有浏览器编号数量
 */
const getAllBrowsersCount = () => {
  if (!copiedContent.value.allBrowsers) return 0
  // 按逗号分隔，计算数量
  return copiedContent.value.allBrowsers.split(',').filter(item => item.trim()).length
}

/**
 * 计算导出的变红浏览器编号数量
 */
const getRedBrowsersCount = () => {
  if (!copiedContent.value.redBrowsers) return 0
  // 按逗号分隔，计算数量
  return copiedContent.value.redBrowsers.split(',').filter(item => item.trim()).length
}

/**
 * 从本地存储加载上一次导出结果
 */
const loadPreviousBrowserResult = (type) => {
  try {
    const key = type === 'all' ? 'eventAnomaly_previousAllBrowsers' : 'eventAnomaly_previousRedBrowsers'
    const saved = localStorage.getItem(key)
    if (saved) {
      return saved
    }
  } catch (error) {
    console.error('[事件异常] 加载上一次导出结果失败:', error)
  }
  return ''
}

/**
 * 保存最终结果到本地存储
 */
const saveFinalResultToLocal = (type, result) => {
  try {
    const key = type === 'all' ? 'eventAnomaly_previousAllBrowsers' : 'eventAnomaly_previousRedBrowsers'
    localStorage.setItem(key, result)
    console.log(`[事件异常] 已保存${type === 'all' ? '所有' : '变红'}浏览器编号到本地存储`)
  } catch (error) {
    console.error('[事件异常] 保存最终结果失败:', error)
  }
}

/**
 * 导出并复制选中的事件名
 */
const exportAndCopy = async () => {
  const selectedEvents = eventTableData.value
    .filter(item => item.selected)
    .map(item => item.eventName)
  
  if (selectedEvents.length === 0) {
    ElMessage.warning('请至少选择一个事件')
    return
  }
  
  // 清空其他导出内容，只显示当前导出的主题
  copiedContent.value.allBrowsers = ''
  copiedContent.value.redBrowsers = ''
  browserExportState.value.type = ''
  browserExportState.value.currentResult = ''
  browserExportState.value.previousResult = ''
  
  // 按分号拼接
  const result = selectedEvents.join(';')
  
  try {
    // 复制到剪切板
    await navigator.clipboard.writeText(result)
    // 保存复制的内容用于显示
    copiedContent.value.eventNames = result
    ElMessage.success(`已复制 ${selectedEvents.length} 个事件名到剪切板`)
    console.log('[事件异常] 导出的内容:', result)
  } catch (error) {
    // 如果 clipboard API 不可用，使用备用方法
    const textArea = document.createElement('textarea')
    textArea.value = result
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      // 保存复制的内容用于显示
      copiedContent.value.eventNames = result
      ElMessage.success(`已复制 ${selectedEvents.length} 个事件名到剪切板`)
      console.log('[事件异常] 导出的内容:', result)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('[事件异常] 复制失败:', err)
    }
    document.body.removeChild(textArea)
  }
}

/**
 * 导出所有浏览器编号（包含选中主题的）
 */
const exportAllBrowsers = async () => {
  const selectedEvents = eventTableData.value
    .filter(item => item.selected)
    .map(item => item.eventName)
  
  if (selectedEvents.length === 0) {
    ElMessage.warning('请至少选择一个事件')
    return
  }
  
  if (accountDataCache.value.length === 0) {
    ElMessage.warning('请先刷新数据')
    return
  }
  
  // 创建选中主题的集合（支持完全匹配）
  const selectedEventSet = new Set(selectedEvents.map(e => e.trim()))
  
  // 收集包含选中主题的浏览器编号
  const browserSet = new Set()
  
  for (const row of accountDataCache.value) {
    // 从 trendingKey 中提取 id（格式：id::方向）
    if (!row.trendingKey) {
      continue
    }
    
    const parts = row.trendingKey.split('::')
    if (parts.length < 2) {
      continue
    }
    
    const configId = parts[0].trim()
    
    // 通过 id 查找对应的 trending（事件名）
    const eventName = idToTrendingMap.value.get(configId)
    if (!eventName) {
      continue
    }
    
    // 检查是否在选中的主题中
    if (selectedEventSet.has(eventName.trim())) {
      if (row.number) {
        browserSet.add(String(row.number))
      }
    }
  }
  
  if (browserSet.size === 0) {
    ElMessage.warning('未找到包含选中主题的浏览器')
    return
  }
  
  // 按逗号拼接
  const result = Array.from(browserSet).sort((a, b) => parseInt(a) - parseInt(b)).join(',')
  
  // 清空其他导出内容，只显示当前导出的所有浏览器编号
  copiedContent.value.eventNames = ''
  copiedContent.value.redBrowsers = ''
  
  // 设置导出状态
  browserExportState.value.type = 'all'
  browserExportState.value.currentResult = result
  browserExportState.value.previousResult = loadPreviousBrowserResult('all')
  // finalResult 会自动通过 computed 计算
  
  // 保存到显示区域（用于兼容原有显示）
  copiedContent.value.allBrowsers = result
  
  ElMessage.success(`已导出 ${browserSet.size} 个浏览器编号`)
  console.log('[事件异常] 导出的浏览器编号:', result)
}

/**
 * 导出变红浏览器编号（包含选中主题的，且 catchTime < utime）
 */
const exportRedBrowsers = async () => {
  const selectedEvents = eventTableData.value
    .filter(item => item.selected)
    .map(item => item.eventName)
  
  if (selectedEvents.length === 0) {
    ElMessage.warning('请至少选择一个事件')
    return
  }
  
  if (accountDataCache.value.length === 0) {
    ElMessage.warning('请先刷新数据')
    return
  }
  
  // 创建选中主题的集合（支持完全匹配）
  const selectedEventSet = new Set(selectedEvents.map(e => e.trim()))
  
  // 收集包含选中主题且变红的浏览器编号
  const browserSet = new Set()
  
  for (const row of accountDataCache.value) {
    // 判断是否变红：catchTime < utime（抓取时间 < 仓位更新时间）
    if (!row.catchTime || !row.utime) {
      continue
    }
    
    const catchTime = typeof row.catchTime === 'string' ? parseInt(row.catchTime) : row.catchTime
    const utime = typeof row.utime === 'string' ? parseInt(row.utime) : row.utime
    
    if (isNaN(catchTime) || isNaN(utime)) {
      continue
    }
    
    // 判断是否变红：仓位更新时间 > 抓取时间，即 catchTime < utime
    if (utime <= catchTime) {
      continue
    }
    
    // 从 trendingKey 中提取 id（格式：id::方向）
    if (!row.trendingKey) {
      continue
    }
    
    const parts = row.trendingKey.split('::')
    if (parts.length < 2) {
      continue
    }
    
    const configId = parts[0].trim()
    
    // 通过 id 查找对应的 trending（事件名）
    const eventName = idToTrendingMap.value.get(configId)
    if (!eventName) {
      continue
    }
    
    // 检查是否在选中的主题中
    if (selectedEventSet.has(eventName.trim())) {
      if (row.number) {
        browserSet.add(String(row.number))
      }
    }
  }
  
  if (browserSet.size === 0) {
    ElMessage.warning('未找到包含选中主题的变红浏览器')
    return
  }
  
  // 按逗号拼接
  const result = Array.from(browserSet).sort((a, b) => parseInt(a) - parseInt(b)).join(',')
  
  // 清空其他导出内容，只显示当前导出的变红浏览器编号
  copiedContent.value.eventNames = ''
  copiedContent.value.allBrowsers = ''
  
  // 设置导出状态
  browserExportState.value.type = 'red'
  browserExportState.value.currentResult = result
  browserExportState.value.previousResult = loadPreviousBrowserResult('red')
  // finalResult 会自动通过 computed 计算
  
  // 保存到显示区域（用于兼容原有显示）
  copiedContent.value.redBrowsers = result
  
  ElMessage.success(`已导出 ${browserSet.size} 个变红浏览器编号`)
  console.log('[事件异常] 导出的变红浏览器编号:', result)
}

/**
 * 确定并复制最终结果
 */
const confirmAndCopy = async () => {
  const final = finalResult.value
  
  if (!final || !final.trim()) {
    ElMessage.warning('最终结果为空，无法复制')
    return
  }
  
  try {
    // 复制到剪切板
    await navigator.clipboard.writeText(final)
    // 保存最终结果到本地存储（不立即更新 previousResult，等下次点击导出按钮时再加载）
    saveFinalResultToLocal(browserExportState.value.type, final)
    ElMessage.success(`已复制 ${final.split(',').filter(item => item.trim()).length} 个浏览器编号到剪切板，并已保存到本地`)
    console.log('[事件异常] 最终结果已复制:', final)
  } catch (error) {
    // 如果 clipboard API 不可用，使用备用方法
    const textArea = document.createElement('textarea')
    textArea.value = final
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      // 保存最终结果到本地存储（不立即更新 previousResult，等下次点击导出按钮时再加载）
      saveFinalResultToLocal(browserExportState.value.type, final)
      ElMessage.success(`已复制 ${final.split(',').filter(item => item.trim()).length} 个浏览器编号到剪切板，并已保存到本地`)
      console.log('[事件异常] 最终结果已复制:', final)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('[事件异常] 复制失败:', err)
    }
    document.body.removeChild(textArea)
  }
}

/**
 * 更新忽略的差额
 */
const updateIgnoreDiff = async (event) => {
  if (!event.configId) {
    ElMessage.warning('该事件未匹配到配置，无法更新')
    return
  }
  
  // 重新计算使用忽略后的差额
  event.finalDiffAfterIgnore = event.finalDiff - (event.ignoreDiff || 0)
  
  // 找到对应的配置
  const config = exchangeConfigList.value.find(c => c.id === event.configId)
  if (!config) {
    ElMessage.warning('未找到对应的配置')
    return
  }
  
  try {
    // 构建更新数据
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
        weight: config.weight || 2,
        isOpen: config.isOpen || 0,
        groupNo: config.groupNo || null,
        a: event.ignoreDiff || 0  // 更新忽略的差额
      }]
    }
    
    console.log('[事件异常] 更新忽略的差额:', submitData)
    
    const response = await axios.post(
      `${API_BASE_URL}/mission/exchangeConfig`,
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.code === 0) {
      // 更新本地配置缓存
      config.a = event.ignoreDiff || 0
      ElMessage.success('忽略的差额已更新')
      console.log('[事件异常] 忽略的差额更新成功')
    } else {
      ElMessage.error('更新失败: ' + (response.data?.msg || '未知错误'))
    }
  } catch (error) {
    console.error('[事件异常] 更新忽略的差额失败:', error)
    const errorMsg = error.response?.data?.msg || error.message || '未知错误'
    ElMessage.error('更新失败: ' + errorMsg)
  }
}

/**
 * 保存所有拉黑状态
 */
const saveAllBlacklistStatus = async () => {
  savingBlacklist.value = true
  
  try {
    // 收集需要更新的配置（只包含有更改的）
    const modifiedConfigs = []
    
    for (const event of eventTableData.value) {
      if (!event.configId) {
        continue // 跳过未匹配到配置的事件
      }
      
      // 找到对应的配置
      const config = exchangeConfigList.value.find(c => c.id === event.configId)
      if (!config) {
        continue
      }
      
      // 判断是否有更改：当前拉黑状态（从 selected 勾选状态获取）与配置中的 b 字段不一致
      // selected 勾选状态对应拉黑状态：勾选=拉黑(b=1)，未勾选=未拉黑(b=0)
      // 使用 selected 作为主要判断依据，因为用户操作的是事件名前面的勾选框
      const currentBlacklistStatus = event.selected ? 1 : 0
      // 处理 b 字段可能为 null、undefined、0、1 等情况
      // 优先使用 event.originalB（初始化时保存的原始值），如果没有则使用 config.b
      const originalB = event.originalB !== undefined && event.originalB !== null ? event.originalB : (config.b !== null && config.b !== undefined ? config.b : 0)
      const originalBlacklistStatus = (originalB === 1 || originalB === '1') ? 1 : 0
      
      console.log(`[事件异常] 检查拉黑状态: ${event.eventName}, 当前=${currentBlacklistStatus}, 原始=${originalBlacklistStatus}, originalB=${originalB}, config.b=${config.b}, event.selected=${event.selected}, event.isBlacklisted=${event.isBlacklisted}`)
      
      if (currentBlacklistStatus !== originalBlacklistStatus) {
        modifiedConfigs.push({
          id: config.id,
          trending: config.trending,
          trendingPart1: config.trendingPart1 || null,
          trendingPart2: config.trendingPart2 || null,
          trendingPart3: config.trendingPart3 || null,
          opUrl: config.opUrl || '',
          polyUrl: config.polyUrl || '',
          opTopicId: config.opTopicId || '',
          weight: config.weight || 2,
          isOpen: config.isOpen || 0,
          groupNo: config.groupNo || null,
          a: config.a || null,
          b: currentBlacklistStatus  // 更新拉黑状态：勾选的为1，未勾选的为0
        })
      }
    }
    
    if (modifiedConfigs.length === 0) {
      ElMessage.info('没有需要更新的拉黑状态')
      return
    }
    
    console.log(`[事件异常] 准备更新 ${modifiedConfigs.length} 个配置的拉黑状态`)
    
    // 构建提交数据
    const submitData = {
      list: modifiedConfigs
    }
    
    const response = await axios.post(
      `${API_BASE_URL}/mission/exchangeConfig`,
      submitData,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data && response.data.code === 0) {
      // 更新本地配置缓存和事件数据
      for (const modifiedConfig of modifiedConfigs) {
        const config = exchangeConfigList.value.find(c => c.id === modifiedConfig.id)
        if (config) {
          config.b = modifiedConfig.b
        }
        // 更新事件数据中的原始值和拉黑状态，以便下次比较时使用
        const event = eventTableData.value.find(e => e.configId === modifiedConfig.id)
        if (event) {
          event.originalB = modifiedConfig.b
          // 同步更新 isBlacklisted 和 selected 状态，确保两者一致
          event.isBlacklisted = modifiedConfig.b === 1 || modifiedConfig.b === '1'
          event.selected = modifiedConfig.b === 1 || modifiedConfig.b === '1'
        }
      }
      
      ElMessage.success(`已成功更新 ${modifiedConfigs.length} 个配置的拉黑状态`)
      console.log('[事件异常] 拉黑状态更新成功')
    } else {
      ElMessage.error('更新失败: ' + (response.data?.msg || '未知错误'))
    }
  } catch (error) {
    console.error('[事件异常] 保存拉黑状态失败:', error)
    const errorMsg = error.response?.data?.msg || error.message || '未知错误'
    ElMessage.error('保存失败: ' + errorMsg)
  } finally {
    savingBlacklist.value = false
  }
}

/**
 * 执行快照
 */
const snapAllPos = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/boost/snapAllPos`, {})
    if (response.data && response.data.code === 0) {
      ElMessage.success('快照执行成功')
      // 执行成功后刷新快照记录列表
      await loadSnapPosTime()
    } else {
      ElMessage.error('快照执行失败')
    }
  } catch (error) {
    console.error('[事件异常] 执行快照失败:', error)
    ElMessage.error('执行快照失败: ' + (error.message || '未知错误'))
  }
}

/**
 * 格式化快照时间（月-日格式）
 */
const formatSnapTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

/**
 * 加载快照时间列表
 */
const loadSnapPosTime = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/boost/getSnapPosTime`)
    if (response.data && response.data.code === 0 && response.data.data && response.data.data.list) {
      snapRecordList.value = response.data.data.list
      console.log('[事件异常] 快照记录列表加载完成，共', snapRecordList.value.length, '条记录')
    } else {
      console.warn('[事件异常] 未获取到快照记录列表')
      snapRecordList.value = []
    }
  } catch (error) {
    console.error('[事件异常] 加载快照记录列表失败:', error)
    ElMessage.error('加载快照记录列表失败: ' + (error.message || '未知错误'))
    snapRecordList.value = []
  }
}

/**
 * 查询快照记录并更新页面数据
 */
const querySnapRecord = async () => {
  if (!selectedSnapRecordId.value) {
    ElMessage.warning('请先选择快照记录')
    return
  }
  
  loading.value = true
  
  try {
    console.log('[事件异常] 开始查询快照记录，recordId:', selectedSnapRecordId.value)
    
    // 获取快照记录数据
    const response = await axios.get(`${API_BASE_URL}/boost/getSnapPosRecord`, {
      params: {
        recordId: selectedSnapRecordId.value
      }
    })
    
    if (response.data && response.data.code === 0 && response.data.data) {
      const snapData = response.data.data
      
      // 如果返回的是列表格式，使用列表；否则尝试其他格式
      let dataList = []
      if (Array.isArray(snapData)) {
        dataList = snapData
      } else if (snapData.list && Array.isArray(snapData.list)) {
        dataList = snapData.list
      } else {
        ElMessage.warning('快照记录数据格式不正确')
        return
      }
      
      console.log(`[事件异常] 获取到快照记录 ${dataList.length} 条数据，开始更新页面...`)
      
      // 过滤掉 amt < 1 的数据
      const filteredData = dataList.filter(row => {
        const amt = parseFloat(row.amt) || 0
        return amt >= 1
      })
      console.log(`[事件异常] 过滤后剩余 ${filteredData.length} 条数据`)
      
      // 更新 accountDataCache
      accountDataCache.value = filteredData
      
      // 先加载 exchangeConfig 配置（需要用于 id -> trending 映射）
      await loadExchangeConfig()
      
      // 记录数据更新时间（当前时间）
      const now = new Date()
      dataUpdateTimestamp.value = now.getTime()
      dataUpdateTime.value = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
      
      // 使用 Map 存储每个事件的统计数据
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
          console.warn(`[事件异常] 未找到 id=${configId} 对应的 trending`)
          continue
        }
        
        // 初始化事件数据
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
            chainFinalDiff: 0,
            yesBidPrice: null,
            yesBidDepth: null,
            yesAskPrice: null,
            yesAskDepth: null,
            noBidPrice: null,
            noBidDepth: null,
            noAskPrice: null,
            noAskDepth: null,
            trendingPart1: null,
            trendingPart2: null,
            opUrl: null,
            updatingOrderbook: false,
            avgUpdateTime: null,
            latestUpdateTime: null,
            yesAccountCount: 0,
            noAccountCount: 0,
            _positions: [],
            _yesAccounts: new Set(),
            _noAccounts: new Set()
          })
        }
        
        const event = eventMap.get(eventName)
        const amount = Math.abs(parseFloat(row.amt) || 0)
        
        // 根据 outCome 判断方向（YES/NO）
        const outComeUpper = (row.outCome || direction).toUpperCase()
        if (outComeUpper === 'YES') {
          event.yesPosition += amount
          if (row.number) {
            event._yesAccounts.add(String(row.number))
          }
        } else if (outComeUpper === 'NO') {
          event.noPosition += amount
          if (row.number) {
            event._noAccounts.add(String(row.number))
          }
        }
        
        // 保存仓位数据用于计算平均更新时间
        if (row.utime) {
          const utime = typeof row.utime === 'string' ? parseInt(row.utime) : row.utime
          if (!isNaN(utime)) {
            event._positions.push({
              utime: utime,
              amount: amount
            })
          }
        }
      }
      
      // 计算差额
      const updateTimestamp = dataUpdateTimestamp.value || Date.now()
      for (const event of eventMap.values()) {
        event.actualDiff = event.yesPosition - event.noPosition
        event.orderDiff = event.orderYes - event.orderNo
        event.finalDiff = event.actualDiff + event.orderDiff
        event.chainActualDiff = event.chainYesPosition - event.chainNoPosition
        event.chainFinalDiff = event.chainActualDiff + event.orderDiff
        
        event.yesAccountCount = event._yesAccounts.size
        event.noAccountCount = event._noAccounts.size
        
        // 计算仓位最新一次更新时间
        if (event._positions.length > 0) {
          const maxUtime = Math.max(...event._positions.map(p => p.utime))
          event.latestUpdateTime = maxUtime
        } else {
          event.latestUpdateTime = null
        }
        
        // 计算仓位平均更新时间
        if (event._positions.length > 0) {
          let totalWeightedMinutes = 0
          let totalAmount = 0
          
          for (const pos of event._positions) {
            const timeDiff = updateTimestamp - pos.utime
            if (timeDiff < 0) {
              continue
            }
            const minutesAgo = timeDiff / (1000 * 60)
            totalWeightedMinutes += minutesAgo * pos.amount
            totalAmount += pos.amount
          }
          
          if (totalAmount > 0) {
            event.avgUpdateTime = totalWeightedMinutes / totalAmount
          } else {
            event.avgUpdateTime = null
          }
        } else {
          event.avgUpdateTime = null
        }
        
        // 清理临时数据
        delete event._positions
        delete event._yesAccounts
        delete event._noAccounts
      }
      
      // 转换为数组并排序
      let allEvents = Array.from(eventMap.values()).sort((a, b) => {
        return Math.abs(b.finalDiff) - Math.abs(a.finalDiff)
      })
      
      // 初始化选中状态，并匹配 exchangeConfig 配置
      allEvents.forEach(event => {
        const eventName = event.eventName.trim()
        const matchedConfig = configMap.value.get(eventName)
        
        if (matchedConfig) {
          event.ignoreDiff = matchedConfig.a !== null && matchedConfig.a !== undefined 
            ? parseFloat(matchedConfig.a) || 0 
            : 0
          event.configId = matchedConfig.id
          event.blacklistStatus = matchedConfig.a !== null && matchedConfig.a !== undefined ? matchedConfig.a : null
          event.isBlacklisted = matchedConfig.b === 1 || matchedConfig.b === '1'
          event.originalB = matchedConfig.b !== null && matchedConfig.b !== undefined ? matchedConfig.b : 0
          event.selected = matchedConfig.b === 1 || matchedConfig.b === '1'
          event.trendingPart1 = matchedConfig.trendingPart1 || null
          event.trendingPart2 = matchedConfig.trendingPart2 || null
          event.opUrl = matchedConfig.opUrl || null
          event.opTopicId = matchedConfig.opTopicId || null
        } else {
          event.ignoreDiff = 0
          event.configId = null
          event.blacklistStatus = null
          event.isBlacklisted = false
          event.originalB = 0
          event.selected = false
          event.trendingPart1 = null
          event.trendingPart2 = null
          event.opUrl = null
          event.opTopicId = null
        }
        
        event.updatingOrderbook = false
        event.finalDiffAfterIgnore = event.finalDiff - event.ignoreDiff
      })
      
      // 根据选择的分组进行过滤
      if (selectedGroup.value !== 'all' && groupConfigList.value.length > 0) {
        const eventNameSet = new Set(groupConfigList.value.map(name => name.trim()))
        const normalizedEventNameSet = new Set(
          groupConfigList.value.map(name => {
            return name.trim().split('###')[0].trim()
          })
        )
        
        allEvents = allEvents.filter(event => {
          const eventName = event.eventName.trim()
          const eventNameBase = eventName.split('###')[0].trim()
          
          if (eventNameSet.has(eventName)) return true
          if (normalizedEventNameSet.has(eventNameBase)) return true
          
          for (const configName of groupConfigList.value) {
            const configNameTrimmed = configName.trim()
            const configNameBase = configNameTrimmed.split('###')[0].trim()
            
            if (eventName === configNameTrimmed || eventNameBase === configNameBase) {
              return true
            }
            
            if (eventName.includes(configNameTrimmed) || configNameTrimmed.includes(eventName)) {
              return true
            }
            if (eventNameBase && configNameBase && 
                (eventNameBase.includes(configNameBase) || configNameBase.includes(eventNameBase))) {
              return true
            }
          }
          
          return false
        })
        
        console.log(`[事件异常] 分组${selectedGroup.value}过滤后，共 ${allEvents.length} 个事件`)
      }
      
      eventTableData.value = allEvents
      
      loadSelectionState()
      
      console.log('[事件异常] 快照记录数据更新完成，开始异步加载链上数据...')
      ElMessage.success(`快照记录数据加载完成，共 ${eventTableData.value.length} 个事件`)
      
      // 异步加载链上数据和订单薄数据
      Promise.all([
        loadChainStats().then(chainDataMap => {
          console.log('[事件异常] 链上数据加载完成，开始匹配并更新...')
          matchAndUpdateChainData(chainDataMap)
          console.log('[事件异常] 链上数据匹配完成')
          return chainDataMap
        }).catch(error => {
          console.error('[事件异常] 加载链上数据失败:', error)
          return null
        }),
        loadAllOrderbooks().then(orderbooks => {
          console.log('[事件异常] 订单薄数据加载完成，开始匹配并更新...')
          matchAndUpdateOrderbookData(orderbooks)
          console.log('[事件异常] 订单薄数据匹配完成')
          return orderbooks
        }).catch(error => {
          console.error('[事件异常] 加载订单薄数据失败:', error)
          return []
        })
      ]).then(() => {
        ElMessage.success('链上数据和订单薄数据已更新')
      })
    } else {
      ElMessage.warning('未获取到快照记录数据')
    }
  } catch (error) {
    console.error('[事件异常] 查询快照记录失败:', error)
    ElMessage.error('查询快照记录失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 加载所有订单薄数据（总接口）
 */
const loadAllOrderbooks = async () => {
  try {
    console.log('[事件异常] 开始加载所有订单薄数据...')
    const response = await axios.get(ORDERBOOK_API_URL)
    
    if (response.data && response.data.orderbooks && Array.isArray(response.data.orderbooks)) {
      console.log(`[事件异常] 获取到 ${response.data.orderbooks.length} 条订单薄数据`)
      return response.data.orderbooks
    }
    
    console.warn('[事件异常] 订单薄数据格式错误')
    return []
  } catch (error) {
    console.error('[事件异常] 加载所有订单薄数据失败:', error)
    return []
  }
}

/**
 * 匹配并更新订单薄数据
 */
const matchAndUpdateOrderbookData = (orderbooks) => {
  console.log('[事件异常] 开始匹配订单薄数据，事件数量:', eventTableData.value.length, '订单薄数量:', orderbooks.length)
  
  // 创建 market_id -> orderbook 的映射（market_id对应opTopicId）
  const orderbookMap = new Map()
  for (const orderbook of orderbooks) {
    if (orderbook.market_id) {
      orderbookMap.set(String(orderbook.market_id), orderbook)
    }
  }
  
  // 更新每个事件的订单薄数据
  let matchedCount = 0
  for (const event of eventTableData.value) {
    if (!event.opTopicId) {
      continue
    }
    
    const orderbook = orderbookMap.get(String(event.opTopicId))
    if (!orderbook) {
      continue
    }
    
    try {
      // 解析bids_json和asks_json（它们是JSON字符串）
      let bids = []
      let asks = []
      
      try {
        bids = JSON.parse(orderbook.bids_json || '[]')
        asks = JSON.parse(orderbook.asks_json || '[]')
      } catch (parseError) {
        console.warn(`[事件异常] ${event.eventName} 解析订单薄JSON失败:`, parseError)
        // 如果解析失败，尝试使用best_bid_price和best_ask_price
        if (orderbook.best_bid_price !== null && orderbook.best_bid_price !== undefined &&
            orderbook.best_ask_price !== null && orderbook.best_ask_price !== undefined) {
          bids = [{ price: orderbook.best_bid_price, size: orderbook.best_bid_size || 0 }]
          asks = [{ price: orderbook.best_ask_price, size: orderbook.best_ask_size || 0 }]
        } else {
          continue
        }
      }
      
      // 基本数据检查
      if (bids.length === 0 || asks.length === 0) {
        continue
      }
      
      // 对 bids 和 asks 进行排序（确保顺序正确）
      bids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
      asks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
      
      // 获取买一和卖一（bids_json是yes买的数据，asks_json是yes卖的数据）
      const bid = bids[0]
      const ask = asks[0]
      
      // 转换为百分比格式（API返回的是小数，需要乘以100）
      event.yesBidPrice = parseFloat(bid.price) * 100
      event.yesAskPrice = parseFloat(ask.price) * 100
      
      event.yesBidDepth = parseFloat(bid.size)
      event.yesAskDepth = parseFloat(ask.size)
      
      matchedCount++
    } catch (error) {
      console.error(`[事件异常] 更新 ${event.eventName} 订单薄数据失败:`, error)
    }
  }
  
  console.log(`[事件异常] 订单薄数据匹配完成，共匹配 ${matchedCount} 个事件`)
}

/**
 * 请求订单薄数据（通过market_id，用于单个更新）
 */
const fetchOrderbook = async (marketId) => {
  try {
    const response = await axios.get(ORDERBOOK_API_URL, {
      params: {
        market_id: marketId
      }
    })
    
    if (response.data && response.data.orderbooks && response.data.orderbooks.length > 0) {
      // 返回第一个匹配的订单薄数据
      return response.data.orderbooks[0]
    }
    
    throw new Error('订单薄数据格式错误或未找到数据')
  } catch (error) {
    console.error('[事件异常] 获取订单薄失败:', error)
    throw error
  }
}

/**
 * 更新订单薄数据（使用总接口）
 */
const updateOrderbook = async () => {
  updatingOrderbook.value = true
  
  try {
    console.log('[事件异常] 开始更新订单薄数据...')
    
    // 加载所有订单薄数据
    const orderbooks = await loadAllOrderbooks()
    
    if (orderbooks.length === 0) {
      ElMessage.warning({
        message: '未获取到订单薄数据',
        duration: 5000
      })
      return
    }
    
    // 匹配并更新订单薄数据
    matchAndUpdateOrderbookData(orderbooks)
    
    // 统计匹配成功的事件数量
    const matchedCount = eventTableData.value.filter(event => 
      event.opTopicId && event.yesBidPrice !== null && event.yesBidPrice !== undefined
    ).length
    
    console.log(`[事件异常] 订单薄更新完成，共匹配 ${matchedCount} 个事件`)
    ElMessage.success({
      message: `订单薄更新完成，共匹配 ${matchedCount} 个事件`,
      duration: 5000
    })
  } catch (error) {
    console.error('[事件异常] 更新订单薄失败:', error)
    ElMessage.error({
      message: '更新订单薄失败: ' + (error.message || '未知错误'),
      duration: 5000
    })
  } finally {
    updatingOrderbook.value = false
  }
}

/**
 * 打开opUrl链接
 */
const openOpUrl = (event) => {
  if (!event.opUrl) {
    ElMessage.warning('该事件没有配置opUrl')
    return
  }
  
  // 在新标签页中打开链接
  window.open(event.opUrl, '_blank')
  console.log(`[事件异常] 打开 ${event.eventName} 的opUrl:`, event.opUrl)
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadAndCalculate()
})
</script>

<style scoped>
.event-anomaly-page {
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
}

.statistics-collapse {
  margin-bottom: 20px;
}

.statistics-table {
  margin-top: 10px;
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

.blacklisted {
  color: #f56c6c;
  font-weight: 600;
}

.not-blacklisted {
  color: #67c23a;
  font-weight: 500;
}

.copied-content-display {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.copied-item {
  margin-bottom: 15px;
}

.copied-item:last-child {
  margin-bottom: 0;
}

.copied-label {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.count-badge {
  font-size: 13px;
  font-weight: 500;
  color: #409eff;
  margin-left: 8px;
}

.copied-text {
  font-size: 13px;
  color: #303133;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.export-section {
  margin-bottom: 15px;
}

.export-section:last-of-type {
  margin-bottom: 10px;
}

.export-label {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.export-text {
  font-size: 13px;
  color: #303133;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.export-text.final-result {
  background-color: #e8f4fd;
  border: 1px solid #b3d8ff;
}

.export-input {
  margin-top: 8px;
}

.export-input :deep(.el-textarea__inner) {
  font-size: 13px;
  font-family: monospace;
  word-break: break-all;
}

.export-extra-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.export-extra-section .export-section {
  margin-bottom: 15px;
}

.export-extra-section .export-section:last-of-type {
  margin-bottom: 10px;
}

.export-actions {
  margin-top: 10px;
  text-align: left;
}

.depth-qualified {
  background-color: #e6f4ff !important;
  padding: 5px;
  border-radius: 4px;
}
</style>

