export interface AccountConfigCacheItem {
  id: string
  computeGroup: string | number // 电脑组编号
  fingerprintNo: string // 指纹浏览器编号 (对应 trade.number)
  platform: string
  balance?: number
  k?: string // 积分数据 raw string: timestamp|||desc|||value;...
  addr?: string
  f?: number // 打开时间戳
  d?: number // 持仓抓取时间戳
  [key: string]: any
}

export interface PointItem {
  timestamp: number
  dateStr: string
  description: string
  value: string
  raw: string
}

export interface AccountApiResponse {
  msg: string
  code: number
  data: AccountConfigCacheItem[]
}