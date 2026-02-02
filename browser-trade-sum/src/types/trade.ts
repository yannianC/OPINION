export interface TradeQueryParams {
  startTime: number
  endTime: number
}

export interface TradeItem {
  number: string // 浏览器编号
  makerAmt: number // 挂单量
  takerAmt: number // 吃单量
  feeAmt: number // 手续费
  totalAmt: number // 成交总量
  feeRate: number // 手续费率
}

export interface TradeApiResponse {
  msg: string
  code: number
  data: {
    list: TradeItem[]
  }
}
