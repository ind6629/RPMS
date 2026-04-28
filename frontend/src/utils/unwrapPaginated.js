/** 解析 DRF 分页 { count, results } 或旧版纯数组 */
export function unwrapPaginated(data) {
  if (data && Array.isArray(data.results)) {
    const count = typeof data.count === 'number' ? data.count : data.results.length
    return { list: data.results, count }
  }
  if (Array.isArray(data)) {
    return { list: data, count: data.length }
  }
  return { list: [], count: 0 }
}
