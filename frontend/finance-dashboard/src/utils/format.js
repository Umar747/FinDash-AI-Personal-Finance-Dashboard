// src/utils/format.js
export const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 2,
  }).format(amount);
};

export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

export const getCategoryColor = (category) => {
  const colors = {
    'Income': '#10B981', // Green
    'Shopping': '#8B5CF6', // Purple
    'Groceries': '#F59E0B', // Amber
    'Transport': '#3B82F6', // Blue
    'Entertainment': '#EC4899', // Pink
    'Food & Dining': '#EF4444', // Red
    'Health & Fitness': '#06B6D4', // Cyan
    'Bills': '#6366F1', // Indigo
    'Education': '#84CC16', // Lime
    'Other': '#6B7280', // Gray
  };
  return colors[category] || '#6B7280';
};