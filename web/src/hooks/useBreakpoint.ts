import { Grid } from 'antd'

export function useBreakpoint() {
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md
  const isTablet = Boolean(screens.md && !screens.lg)
  const isDesktop = Boolean(screens.lg)

  return { screens, isMobile, isTablet, isDesktop }
}
