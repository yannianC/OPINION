import type { TradeApiResponse, TradeItem, TradeQueryParams } from '~/types/trade'
import { ElMessage } from 'element-plus'

/**
 * 获取浏览器交易汇总数据
 * API: /99l/data/browserTradeSum
 */
export async function getBrowserTradeSum(params: TradeQueryParams): Promise<TradeItem[]> {
  try {
    // 直接调用远程真实接口
    const BASE_URL = 'https://sg.bicoin.com.cn/99l/data/browserTradeSum'

    const queryString = new URLSearchParams({
      startTime: params.startTime.toString(),
      endTime: params.endTime.toString(),
    }).toString()

    const fullUrl = `${BASE_URL}?${queryString}`
    // eslint-disable-next-line no-console
    console.log('Requesting Remote URL:', fullUrl)

    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const res: TradeApiResponse = await response.json()

    if (res.code === 0) {
      return res.data.list
    }
    else {
      ElMessage.error(res.msg || '获取数据失败')
      return []
    }
  }
  catch (error: any) {
    console.error('API Error:', error)
    // 如果是跨域问题，给个提示
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      ElMessage.error('请求失败：可能是跨域(CORS)限制，目标服务器拒绝了直连。')
    }
    else {
      ElMessage.error(error.message || '网络请求异常')
    }
    return []
  }
}
