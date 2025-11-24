/**
 * Design System - Typography Scale
 * Clear typographic hierarchy for consistent text styling
 */

export const typography = {
  // Font sizes
  fontSize: {
    xs: '0.75rem',    // 12px - Labels/captions
    sm: '0.875rem',   // 14px - Secondary text
    base: '1rem',     // 16px - Default text
    lg: '1.125rem',   // 18px - Large text
    xl: '1.25rem',    // 20px - Card titles
    '2xl': '1.5rem',  // 24px - Subsection titles
    '3xl': '2rem',    // 32px - Section titles
    '4xl': '2.5rem',  // 40px - Page titles
  },

  // Font weights
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Line heights
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },

  // Letter spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },

  // Heading styles
  heading: {
    h1: {
      fontSize: '2.5rem',      // 40px
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '2rem',         // 32px
      fontWeight: 600,
      lineHeight: 1.25,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontSize: '1.5rem',       // 24px
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '0em',
    },
    h4: {
      fontSize: '1.25rem',      // 20px
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0em',
    },
  },

  // Text styles
  text: {
    body: {
      fontSize: '1rem',        // 16px
      fontWeight: 400,
      lineHeight: 1.5,
    },
    small: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 400,
      lineHeight: 1.5,
    },
    tiny: {
      fontSize: '0.75rem',      // 12px
      fontWeight: 400,
      lineHeight: 1.4,
    },
    label: {
      fontSize: '0.75rem',      // 12px
      fontWeight: 500,
      lineHeight: 1.4,
      letterSpacing: '0.05em',
      textTransform: 'uppercase' as const,
    },
  },

  // Responsive typography (for mobile scaling)
  responsive: {
    mobile: {
      h1: 'text-2xl',           // Smaller on mobile
      h2: 'text-xl',
      h3: 'text-lg',
      h4: 'text-base',
    },
    desktop: {
      h1: 'text-4xl',           // Full size on desktop
      h2: 'text-3xl',
      h3: 'text-2xl',
      h4: 'text-xl',
    },
  },
} as const;

/**
 * Get typography style by key
 */
export const getTypography = (category: 'heading' | 'text', key: string) => {
  return typography[category][key as keyof typeof typography[typeof category]] || typography.text.body;
};

/**
 * Get responsive heading class
 */
export const getResponsiveHeading = (
  level: 1 | 2 | 3 | 4,
  breakpoint: 'mobile' | 'desktop' = 'desktop'
): string => {
  const key = `h${level}` as keyof typeof typography.responsive.desktop;
  return typography.responsive[breakpoint][key] || typography.responsive.desktop[key];
};

