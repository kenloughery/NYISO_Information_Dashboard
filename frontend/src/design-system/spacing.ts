/**
 * Design System - Spacing Scale
 * Standardized spacing system based on 8px base unit
 * Provides consistent spacing throughout the application
 */

export const spacing = {
  // Base spacing scale (8px increments)
  xs: '0.5rem',   // 8px
  sm: '1rem',     // 16px
  md: '1.5rem',   // 24px
  lg: '2rem',     // 32px
  xl: '3rem',     // 48px
  '2xl': '4rem',  // 64px
  '3xl': '6rem',  // 96px
  '4xl': '8rem',  // 128px

  // Component-specific spacing
  card: {
    padding: '1.5rem',    // 24px - Standard card padding
    paddingSmall: '1rem',  // 16px - Small card padding
    paddingLarge: '2rem',  // 32px - Large card padding
    gap: '1.5rem',         // 24px - Gap between card elements
  },

  section: {
    gap: '1.5rem',         // 24px - Gap between sections
    padding: '1.5rem',     // 24px - Section padding
    marginBottom: '2rem',  // 32px - Bottom margin
  },

  grid: {
    gap: '1.5rem',         // 24px - Standard grid gap
    gapSmall: '1rem',      // 16px - Small grid gap
    gapLarge: '2rem',      // 32px - Large grid gap
  },

  // Responsive spacing (for mobile/desktop differences)
  responsive: {
    mobile: {
      sectionGap: '1rem',      // 16px on mobile
      cardPadding: '1rem',      // 16px on mobile
      gridGap: '1rem',          // 16px on mobile
    },
    desktop: {
      sectionGap: '1.5rem',    // 24px on desktop
      cardPadding: '1.5rem',    // 24px on desktop
      gridGap: '1.5rem',        // 24px on desktop
    },
  },
} as const;

/**
 * Get spacing value by key
 */
export const getSpacing = (key: string): string => {
  // Handle nested keys like 'card.padding'
  const keys = key.split('.');
  let value: any = spacing;
  
  for (const k of keys) {
    value = value?.[k];
    if (value === undefined) break;
  }
  
  return typeof value === 'string' ? value : spacing.sm;
};

/**
 * Get responsive spacing (mobile/desktop)
 */
export const getResponsiveSpacing = (
  category: 'sectionGap' | 'cardPadding' | 'gridGap',
  breakpoint: 'mobile' | 'desktop' = 'desktop'
): string => {
  return spacing.responsive[breakpoint][category];
};

