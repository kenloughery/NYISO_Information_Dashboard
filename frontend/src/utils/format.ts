/**
 * Utility functions for formatting data
 */

/**
 * Replace underscores with spaces in labels
 */
export const formatLabel = (label: string | null | undefined): string => {
  if (!label) return '';
  return label.replace(/_/g, ' ');
};

