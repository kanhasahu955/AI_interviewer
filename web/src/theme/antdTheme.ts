import { theme } from 'antd'

export const antdTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#6366f1',
    colorInfo: '#818cf8',
    colorSuccess: '#34d399',
    colorWarning: '#fbbf24',
    colorError: '#f87171',
    borderRadius: 14,
    borderRadiusLG: 18,
    fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
    fontSize: 14,
    colorBgContainer: 'rgba(255, 255, 255, 0.04)',
    colorBgElevated: '#151d32',
    colorBgLayout: 'transparent',
    colorBorder: 'rgba(255, 255, 255, 0.08)',
    colorText: '#e2e8f0',
    colorTextSecondary: '#94a3b8',
    controlHeight: 42,
    controlHeightLG: 48,
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
    boxShadowSecondary: '0 4px 12px rgba(0, 0, 0, 0.15)',
  },
  components: {
    Layout: {
      bodyBg: 'transparent',
      headerBg: 'transparent',
      siderBg: 'rgba(10, 15, 30, 0.85)',
      triggerBg: 'rgba(255, 255, 255, 0.06)',
    },
    Card: {
      colorBgContainer: 'rgba(255, 255, 255, 0.04)',
      paddingLG: 20,
    },
    Menu: {
      darkItemBg: 'transparent',
      darkSubMenuItemBg: 'transparent',
      itemBorderRadius: 12,
      itemHeight: 44,
      iconSize: 18,
    },
    Button: {
      primaryShadow: '0 4px 14px rgba(99, 102, 241, 0.35)',
      fontWeight: 500,
    },
    Input: {
      activeBorderColor: '#6366f1',
      hoverBorderColor: 'rgba(99, 102, 241, 0.5)',
    },
    Select: {
      optionSelectedBg: 'rgba(99, 102, 241, 0.2)',
    },
    Drawer: {
      colorBgElevated: '#0f1528',
    },
    Tag: {
      borderRadiusSM: 8,
    },
  },
} as const
