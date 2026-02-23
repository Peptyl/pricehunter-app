// Utility functions

/**
 * Format price with currency symbol
 */
export const formatPrice = (price: number, currency: string = 'GBP'): string => {
  const symbols: Record<string, string> = {
    GBP: '£',
    USD: '$',
    EUR: '€',
  };
  const symbol = symbols[currency] || currency;
  return `${symbol}${price.toFixed(2)}`;
};

/**
 * Format savings percentage
 */
export const formatSavings = (percent: number): string => {
  return `${Math.round(percent)}% off`;
};

/**
 * Format relative time
 */
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  });
};

/**
 * Get deal temperature based on savings
 */
export const getDealTemperature = (savingsPercent: number): 'hot' | 'good' | 'mild' => {
  if (savingsPercent >= 30) return 'hot';
  if (savingsPercent >= 15) return 'good';
  return 'mild';
};

/**
 * Get temperature color
 */
export const getTemperatureColor = (temp: 'hot' | 'good' | 'mild'): string => {
  const colors = {
    hot: '#ef4444',
    good: '#22c55e',
    mild: '#3b82f6',
  };
  return colors[temp];
};

/**
 * Debounce function
 */
export const debounce = <T extends (...args: any[]) => void>(
  fn: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
};
