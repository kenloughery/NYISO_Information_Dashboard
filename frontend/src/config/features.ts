/**
 * Feature Flags Configuration
 * Control optional features that can be enabled/disabled
 */

export const FEATURES = {
  // Sidebar overlay mode (mobile-friendly overlay instead of push)
  OVERLAY_SIDEBAR: false, // Start disabled for backward compatibility
  
  // Enhanced card components (gradual migration)
  ENHANCED_CARDS: false,
  
  // Mobile table cards (transform tables to cards on mobile)
  MOBILE_TABLE_CARDS: false,
} as const;

export type FeatureKey = keyof typeof FEATURES;

/**
 * Check if a feature is enabled
 */
export const isFeatureEnabled = (feature: FeatureKey): boolean => {
  return Boolean(FEATURES[feature]);
};

