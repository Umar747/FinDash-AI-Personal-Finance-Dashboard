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
    'Income': '#10B981',
    'Shopping & Retail': '#8B5CF6',
    'Groceries': '#F59E0B',
    'Travel': '#3B82F6',
    'Entertainment': '#EF4444',
    'Dining': '#06B6D4',
    'Bills': '#6366F1',
    'Other': '#6B7280',
  };
  return colors[category] || '#6B7280';
};