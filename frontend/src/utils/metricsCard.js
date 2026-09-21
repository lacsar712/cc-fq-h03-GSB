// 卡面与接口一致:直接渲染 API 返回的指标,不做任何占位/改写
export function displayMetrics(metrics) {
  return metrics || null
}

export function cardList(metrics) {
  const m = displayMetrics(metrics)
  if (!m) return []
  return [
    { label: 'reads', value: m.reads ?? '—' },
    { label: 'mean_quality', value: m.mean_quality ?? '—' },
    { label: 'n_rate', value: m.n_rate ?? '—' },
  ]
}
