<template>
  <div class="app">
    <div class="container">
      <!-- 查询区域 -->
      <section class="query-section">
        <div class="query-form">
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
      <section class="results-section" v-if="results.length > 0">
        <h2>查询结果 (共 {{ results.length }} 个异常浏览器)</h2>
        
        <div class="browser-list">
          <div 
            v-for="(browser, index) in results" 
            :key="index"
            class="browser-item"
          >
            <div class="browser-header">
              <div class="browser-info">
                <span class="label">浏览器ID:</span>
                <span class="value">{{ browser.browserId }}</span>
              </div>
              <div class="browser-info">
                <span class="label">电脑组:</span>
                <span class="value">{{ browser.groupNo }}</span>
              </div>
              <div class="browser-info">
                <span class="label">失败任务数:</span>
                <span class="value error">{{ browser.tasks.length }}</span>
              </div>
            </div>

            <div class="tasks-container">
              <table class="tasks-table">
                <thead>
                  <tr>
                    <th>主题</th>
                    <th>失败原因</th>
                    <th>任务ID</th>
                    <th>同组任务ID</th>
                    <th>方向</th>
                    <th>数量</th>
                    <th>价格</th>
                    <th>选项</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(task, taskIndex) in browser.tasks" :key="taskIndex">
                    <td class="trending-cell">{{ task.trending }}</td>
                    <td class="msg-cell">{{ task.msg || '无' }}</td>
                    <td>{{ task.id }}</td>
                    <td>{{ task.tp1 || '-' }}</td>
                    <td>
                      <span :class="task.side === 1 ? 'buy' : 'sell'">
                        {{ task.side === 1 ? '买入' : '卖出' }}
                      </span>
                    </td>
                    <td>{{ task.amt }}</td>
                    <td>{{ task.price }}</td>
                    <td>
                      <span :class="task.psSide === 1 ? 'yes' : 'no'">
                        {{ task.psSide === 1 ? 'YES' : 'NO' }}
                      </span>
                    </td>
                    <td>
                      <a 
                        :href="task.opUrl" 
                        target="_blank" 
                        class="link-btn"
                      >
                        查看
                      </a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <!-- 空状态 -->
      <section class="empty-section" v-if="!loading && results.length === 0 && hasQueried">
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
      query: {
        startTime: '',
        endTime: ''
      },
      recentHours: 1, // 默认查询最近1小时
      loading: false,
      results: [],
      hasQueried: false,
      toast: {
        show: false,
        message: '',
        type: 'info'
      }
    }
  },
  methods: {
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
        
        // 调用接口
        const response = await axios.get('https://sg.bicoin.com.cn/99l/mission/listPart', {
          params: {
            type: 5,
            startTime: startTimestamp,
            endTime: endTimestamp
          }
        })
        
        if (response.data && response.data.code === 0) {
          const missions = response.data.data.list || []
          
          // 处理数据：过滤任务，按浏览器ID分组
          // 过滤规则：
          // 1. status === 2：跳过（成功任务）
          // 2. status === 3：直接显示（失败任务）
          // 3. status !== 2 && status !== 3：检查 createTime，如果距离现在超过20分钟才显示
          const browserMap = new Map()
          const now = new Date().getTime()
          const twentyMinutes = 20 * 60 * 1000 // 20分钟的毫秒数
          
          missions.forEach(item => {
            const mission = item.mission
            const exchangeConfig = item.exchangeConfig
            
            // 跳过状态为2（成功）的任务
            if (mission.status === 2) {
              return
            }
            
            // 如果 status !== 3，需要检查创建时间是否超过20分钟
            if (mission.status !== 3) {
              if (mission.createTime) {
                const createTime = new Date(mission.createTime).getTime()
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
            
            const browserId = mission.numberList
            const groupNo = mission.groupNo
            
            // 如果该浏览器ID还没有记录，创建新记录
            if (!browserMap.has(browserId)) {
              browserMap.set(browserId, {
                browserId,
                groupNo,
                tasks: []
              })
            }
            
            // 添加任务信息
            const browser = browserMap.get(browserId)
            browser.tasks.push({
              id: mission.id,
              tp1: mission.tp1,
              msg: mission.msg,
              trending: exchangeConfig.trending,
              opUrl: exchangeConfig.opUrl,
              side: mission.side,
              amt: mission.amt,
              price: mission.price,
              psSide: mission.psSide
            })
          })
          
          // 转换为数组并按浏览器ID排序
          this.results = Array.from(browserMap.values()).sort((a, b) => {
            return a.browserId.localeCompare(b.browserId)
          })
          
          this.hasQueried = true
          this.showToast(`查询成功，共 ${this.results.length} 个异常浏览器`, 'success')
        } else {
          this.showToast('查询失败', 'error')
        }
      } catch (error) {
        console.error('查询账号异常失败:', error)
        this.showToast('查询失败: ' + (error.message || '未知错误'), 'error')
      } finally {
        this.loading = false
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
  max-width: 1400px;
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

.results-section h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 20px;
}

.browser-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.browser-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.browser-header {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 15px 20px;
  display: flex;
  gap: 30px;
  align-items: center;
  flex-wrap: wrap;
}

.browser-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.browser-info .label {
  font-weight: 500;
  color: #666;
}

.browser-info .value {
  font-weight: 600;
  color: #333;
  font-size: 16px;
}

.browser-info .value.error {
  color: #e74c3c;
}

.tasks-container {
  padding: 20px;
  overflow-x: auto;
}

.tasks-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
}

.tasks-table thead {
  background: #667eea;
  color: white;
}

.tasks-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
}

.tasks-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #e0e0e0;
  font-size: 14px;
}

.tasks-table tbody tr:hover {
  background-color: #f8f9fa;
}

.tasks-table tbody tr:last-child td {
  border-bottom: none;
}

.trending-cell {
  max-width: 300px;
  word-break: break-word;
  color: #555;
}

.msg-cell {
  max-width: 200px;
  word-break: break-word;
  color: #e74c3c;
  font-weight: 500;
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
  
  .tasks-container {
    overflow-x: scroll;
  }
  
  .tasks-table {
    min-width: 1000px;
  }
  
  .browser-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>

