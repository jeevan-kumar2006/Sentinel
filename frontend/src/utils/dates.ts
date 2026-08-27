export const formatDate = (isoString: string | null | undefined): string => {
  if (!isoString) return 'N/A';
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'UTC'
    }) + ' UTC';
  } catch {
    return 'Invalid Date';
  }
};