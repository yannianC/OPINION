<template>
  <div class="app-container">
    <header class="header">
      <h1>页面2-异常查询</h1>
    </header>
    
    <nav class="navigation">
      <router-link to="/task-anomaly" class="nav-link">任务异常查询</router-link>
      <router-link to="/account-anomaly" class="nav-link">账号异常查询</router-link>
      <router-link to="/event-anomaly" class="nav-link">事件异常</router-link>
      <router-link to="/position-detail" class="nav-link">持仓详情</router-link>
      <router-link to="/open-order-detail" class="nav-link">挂单详情</router-link>
      <router-link to="/browser-task-info" class="nav-link">浏览器任务信息</router-link>
      <router-link to="/event-task-info" class="nav-link">事件任务信息</router-link>
    </nav>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header h1 {
  text-align: center;
  font-size: 28px;
  font-weight: 600;
}

.navigation {
  background: white;
  padding: 15px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  gap: 20px;
}

.nav-link {
  padding: 10px 20px;
  text-decoration: none;
  color: #666;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.3s;
}

.nav-link:hover {
  background-color: #f0f0f0;
  color: #667eea;
}

.nav-link.router-link-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.main {
  padding: 20px;
}
</style>
