<template>
  <div class="virtual-table-container" :style="{ height: height + 'px' }">
    <div class="virtual-table-header" :style="{ width: totalWidth + 'px' }">
      <div
        v-for="column in columns"
        :key="column.prop || column.type"
        class="virtual-table-header-cell"
        :style="{
          width: column.width + 'px',
          left: column.fixed === 'left' ? getFixedLeft(column) + 'px' : 'auto',
          right: column.fixed === 'right' ? getFixedRight(column) + 'px' : 'auto',
          position: column.fixed ? 'sticky' : 'relative',
          zIndex: column.fixed ? 10 : 1
        }"
        :class="{ 'sortable': column.sortable }"
        @click="handleSort(column)"
      >
        <span>{{ column.label }}</span>
        <span v-if="column.sortable" class="sort-icon">
          <span v-if="sortColumn === (column.prop || column.type) && sortOrder === 'asc'">↑</span>
          <span v-else-if="sortColumn === (column.prop || column.type) && sortOrder === 'desc'">↓</span>
          <span v-else>⇅</span>
        </span>
      </div>
    </div>
    <div
      class="virtual-table-body"
      ref="scrollContainer"
      @scroll="handleScroll"
      :style="{ height: (height - headerHeight) + 'px', width: totalWidth + 'px' }"
    >
      <div class="virtual-table-spacer" :style="{ height: topSpacerHeight + 'px' }"></div>
      <div class="virtual-table-rows">
        <div
          v-for="(row, index) in visibleRows"
          :key="getRowKey(row, startIndex + index)"
          class="virtual-table-row"
          :style="{ width: totalWidth + 'px' }"
        >
          <div
            v-for="column in columns"
            :key="column.prop || column.type"
            class="virtual-table-cell"
            :style="{
              width: column.width + 'px',
              left: column.fixed === 'left' ? getFixedLeft(column) + 'px' : 'auto',
              right: column.fixed === 'right' ? getFixedRight(column) + 'px' : 'auto',
              position: column.fixed ? 'sticky' : 'relative',
              zIndex: column.fixed ? 9 : 1
            }"
          >
            <slot
              :name="column.prop || column.type"
              :row="row"
              :index="startIndex + index"
              :column="column"
            >
              <span v-if="column.type === 'index'">{{ startIndex + index + 1 }}</span>
              <span v-else>{{ getCellValue(row, column) }}</span>
            </slot>
          </div>
        </div>
      </div>
      <div class="virtual-table-spacer" :style="{ height: bottomSpacerHeight + 'px' }"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  columns: {
    type: Array,
    required: true
  },
  height: {
    type: Number,
    default: 400
  },
  rowHeight: {
    type: Number,
    default: 40
  },
  headerHeight: {
    type: Number,
    default: 40
  },
  buffer: {
    type: Number,
    default: 5 // 缓冲区行数
  },
  getRowKey: {
    type: Function,
    default: (row, index) => index
  }
})

const emit = defineEmits(['sort-change'])

const scrollContainer = ref(null)
const scrollTop = ref(0)
const sortColumn = ref(null)
const sortOrder = ref(null)

// 计算总宽度
const totalWidth = computed(() => {
  return props.columns.reduce((sum, col) => sum + (col.width || 100), 0)
})

// 计算可见行数
const visibleCount = computed(() => {
  return Math.ceil((props.height - props.headerHeight) / props.rowHeight) + props.buffer * 2
})

// 计算起始索引
const startIndex = computed(() => {
  const index = Math.floor(scrollTop.value / props.rowHeight)
  return Math.max(0, index - props.buffer)
})

// 计算结束索引
const endIndex = computed(() => {
  return Math.min(props.data.length, startIndex.value + visibleCount.value)
})

// 计算可见行数据
const visibleRows = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value)
})

// 计算顶部占位高度
const topSpacerHeight = computed(() => {
  return startIndex.value * props.rowHeight
})

// 计算底部占位高度
const bottomSpacerHeight = computed(() => {
  const remainingRows = props.data.length - endIndex.value
  return remainingRows * props.rowHeight
})

// 获取固定列左侧位置
const getFixedLeft = (column) => {
  if (column.fixed !== 'left') return 0
  let left = 0
  for (const col of props.columns) {
    if (col === column) break
    if (col.fixed === 'left') {
      left += col.width || 100
    }
  }
  return left
}

// 获取固定列右侧位置
const getFixedRight = (column) => {
  if (column.fixed !== 'right') return 0
  let right = 0
  for (let i = props.columns.length - 1; i >= 0; i--) {
    const col = props.columns[i]
    if (col === column) break
    if (col.fixed === 'right') {
      right += col.width || 100
    }
  }
  return right
}

// 获取单元格值
const getCellValue = (row, column) => {
  if (column.prop) {
    return row[column.prop] ?? '-'
  }
  return '-'
}

// 处理滚动
const handleScroll = (e) => {
  scrollTop.value = e.target.scrollTop
}

// 处理排序
const handleSort = (column) => {
  if (!column.sortable) return
  
  const columnKey = column.prop || column.type
  
  if (sortColumn.value === columnKey) {
    if (sortOrder.value === 'asc') {
      sortOrder.value = 'desc'
    } else if (sortOrder.value === 'desc') {
      sortColumn.value = null
      sortOrder.value = null
    }
  } else {
    sortColumn.value = columnKey
    sortOrder.value = 'asc'
  }
  
  emit('sort-change', {
    column: sortColumn.value,
    order: sortOrder.value,
    sortMethod: column.sortMethod
  })
}

// 暴露方法
defineExpose({
  scrollToTop: () => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = 0
      scrollTop.value = 0
    }
  },
  scrollToIndex: (index) => {
    if (scrollContainer.value) {
      const targetScrollTop = index * props.rowHeight
      scrollContainer.value.scrollTop = targetScrollTop
      scrollTop.value = targetScrollTop
    }
  }
})
</script>

<style scoped>
.virtual-table-container {
  position: relative;
  overflow: hidden;
  border: 1px solid #ebeef5;
  background-color: #fff;
}

.virtual-table-header {
  position: relative;
  display: flex;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  z-index: 11;
}

.virtual-table-header-cell {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  border-right: 1px solid #ebeef5;
  font-weight: 600;
  font-size: 14px;
  color: #606266;
  background-color: #f5f7fa;
  user-select: none;
  flex-shrink: 0;
  box-sizing: border-box;
}

.virtual-table-header-cell.sortable {
  cursor: pointer;
}

.virtual-table-header-cell.sortable:hover {
  background-color: #e4e7ed;
}

.sort-icon {
  margin-left: 5px;
  font-size: 12px;
  color: #909399;
}

.virtual-table-body {
  position: relative;
  overflow-y: auto;
  overflow-x: auto;
}

.virtual-table-spacer {
  width: 100%;
}

.virtual-table-rows {
  position: relative;
}

.virtual-table-row {
  display: flex;
  border-bottom: 1px solid #ebeef5;
  height: 40px;
}

.virtual-table-row:hover {
  background-color: #f5f7fa;
}

.virtual-table-cell {
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  border-right: 1px solid #ebeef5;
  font-size: 13px;
  color: #606266;
  background-color: #fff;
  flex-shrink: 0;
  box-sizing: border-box;
}

.virtual-table-cell > * {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.virtual-table-cell:last-child {
  border-right: none;
}
</style>

