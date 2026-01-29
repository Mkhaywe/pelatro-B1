/**
 * Utility functions for API responses
 */

/**
 * Extract data from DRF paginated response or direct array
 */
export function extractData<T>(response: any): T[] {
  // Handle case where response is wrapped in an array (backend bug)
  if (Array.isArray(response) && response.length > 0) {
    const firstItem = response[0]
    // If first item looks like a paginated response, extract results from it
    if (firstItem && typeof firstItem === 'object' && 'results' in firstItem && 'count' in firstItem) {
      return firstItem.results || []
    }
    // Otherwise, return the array as-is
    return response
  }
  if (response?.data) {
    return extractData(response.data)
  }
  if (response?.results) {
    return response.results
  }
  return []
}

/**
 * Extract pagination info from DRF response
 */
export function extractPagination(response: any) {
  if (response?.data && !Array.isArray(response.data)) {
    return {
      count: response.data.count || 0,
      next: response.data.next,
      previous: response.data.previous,
    }
  }
  return {
    count: Array.isArray(response?.data) ? response.data.length : 0,
    next: null,
    previous: null,
  }
}

