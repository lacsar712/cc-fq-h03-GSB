export function displayMetrics(metrics) {
  if (!metrics || metrics.placeholder) {
    return { reads: '-', mean_quality: '-', n_rate: '-', note: '占位' }
  }
  return metrics
}

export function cardList(metrics) {
  const m = displayMetrics(metrics)
  return [
    { label: 'reads', value: m.reads },
    { label: 'mean_quality', value: m.mean_quality },
    { label: 'n_rate', value: m.n_rate },
  ]
}
