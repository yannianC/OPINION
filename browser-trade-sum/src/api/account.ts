import type { AccountApiResponse, AccountConfigCacheItem } from '~/types/account'
import { ElMessage } from 'element-plus'

const ACCOUNT_API_URL = 'https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache'

/**
 * 获取账户配置缓存
 * 过滤 computeGroup >= 900 的数据
 */
export async function getAccountConfigCache(): Promise<AccountConfigCacheItem[]> {
  try {
    // 设置超时控制器 (3分钟)
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 180000)

    // eslint-disable-next-line no-console
    console.log('Requesting Account Cache:', ACCOUNT_API_URL)

    const response = await fetch(ACCOUNT_API_URL, {
      method: 'GET',
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const res: AccountApiResponse = await response.json()

    if (res.data && Array.isArray(res.data)) {
      // 过滤逻辑：computeGroup < 900
      // 注意：有些 computeGroup 可能是 null 或 string，需转数字处理
      return res.data.filter((item) => {
        const group = Number(item.computeGroup)
        // 如果转换失败(NaN)或者为0，通常保留；明确大于等于900的过滤
        if (!Number.isNaN(group) && group >= 900) {
          return false
        }
        return true
      })
    }
    return []
  }
  catch (error: any) {
    console.error('Account API Error:', error)
    if (error.name === 'AbortError') {
      ElMessage.error('请求账户配置超时')
    }
    else {
      // 静默失败或轻微提示，避免阻塞主流程
      console.warn('获取账户积分数据失败，将不展示积分信息')
    }
    return []
  }
}