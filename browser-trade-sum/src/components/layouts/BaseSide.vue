<script lang="ts" setup>
import { DataLine } from '@element-plus/icons-vue'

function handleOpen(key: string, keyPath: string[]) {
  // eslint-disable-next-line no-console
  console.log(key, keyPath)
}
function handleClose(key: string, keyPath: string[]) {
  // eslint-disable-next-line no-console
  console.log(key, keyPath)
}
</script>

<template>
  <el-menu
    router
    default-active="/"
    class="el-menu-vertical-demo"
    @open="handleOpen"
    @close="handleClose"
  >
    <el-menu-item index="/">
      <el-icon>
        <DataLine />
      </el-icon>
      <template #title>
        交易数据汇总
      </template>
    </el-menu-item>
  </el-menu>
</template>
