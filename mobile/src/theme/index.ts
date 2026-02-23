// Theme Configuration - Dark mode default
export const theme = {
  colors: {
    // Primary colors
    primary: '#38b2ac',
    primaryDark: '#319795',
    primaryLight: '#4fd1c5',
    
    // Background colors
    background: '#0f172a',
    surface: '#1e293b',
    surfaceVariant: '#334155',
    
    // Text colors
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    textMuted: '#64748b',
    
    // Accent colors
    accent: '#f59e0b',
    success: '#22c55e',
    error: '#ef4444',
    warning: '#f97316',
    info: '#3b82f6',
    
    // Deal colors
    dealHot: '#ef4444',
    dealGood: '#22c55e',
    dealMild: '#3b82f6',
    
    // Border colors
    border: '#334155',
    divider: '#475569',
    
    // Overlay
    overlay: 'rgba(15, 23, 42, 0.8)',
  },
  
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    round: 9999,
  },
  
  typography: {
    h1: {
      fontSize: 32,
      fontWeight: '700' as const,
      lineHeight: 40,
    },
    h2: {
      fontSize: 24,
      fontWeight: '700' as const,
      lineHeight: 32,
    },
    h3: {
      fontSize: 20,
      fontWeight: '600' as const,
      lineHeight: 28,
    },
    h4: {
      fontSize: 18,
      fontWeight: '600' as const,
      lineHeight: 24,
    },
    body: {
      fontSize: 16,
      fontWeight: '400' as const,
      lineHeight: 24,
    },
    bodySmall: {
      fontSize: 14,
      fontWeight: '400' as const,
      lineHeight: 20,
    },
    caption: {
      fontSize: 12,
      fontWeight: '400' as const,
      lineHeight: 16,
    },
    button: {
      fontSize: 16,
      fontWeight: '600' as const,
      lineHeight: 24,
    },
  },
  
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 8,
    },
  },
};

export type Theme = typeof theme;
