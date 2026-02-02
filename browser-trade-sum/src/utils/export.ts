import { utils, writeFile } from 'xlsx'

/**
 * 导出数据到 Excel
 * @param headers 表头映射 { key: '中文列名' }
 * @param data 数据数组
 * @param fileName 文件名
 */
export function exportToExcel(
  headers: Record<string, string>,
  data: any[],
  fileName: string = 'export-data.xlsx',
) {
  if (!data || data.length === 0) {
    return
  }

  // 1. 转换数据格式：仅提取 headers 中定义的字段，并重命名 key
  const exportData = data.map((item) => {
    const row: Record<string, any> = {}
    Object.keys(headers).forEach((key) => {
      // 处理可能的 undefined/null，保持空字符串以便 Excel 显示整洁
      const val = item[key]
      row[headers[key]] = (val !== null && val !== undefined) ? val : ''
    })
    return row
  })

  // 2. 创建工作簿和工作表
  const worksheet = utils.json_to_sheet(exportData)
  const workbook = utils.book_new()
  utils.book_append_sheet(workbook, worksheet, 'Sheet1')

  // 3. 写入文件
  writeFile(workbook, fileName)
}