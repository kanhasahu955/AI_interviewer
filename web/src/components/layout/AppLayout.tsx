import {
  FileTextOutlined,
  HomeOutlined,
  LogoutOutlined,
  MenuOutlined,
  ProfileOutlined,
  ReadOutlined,
  ScheduleOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { Avatar, Button, Drawer, Layout, Menu, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { useMemo, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { logoutSession } from '@/features/auth/session'
import { useBreakpoint } from '@/hooks/useBreakpoint'
import type { UserRole } from '@/types/api'

const { Header, Sider, Content } = Layout

const ROLE_NAV: Record<UserRole, MenuProps['items']> = {
  candidate: [
    { key: '/dashboard', icon: <HomeOutlined />, label: 'Dashboard' },
    { key: '/interviews', icon: <ScheduleOutlined />, label: 'Interviews' },
    { key: '/resumes', icon: <UploadOutlined />, label: 'Resumes' },
    { key: '/profile', icon: <ProfileOutlined />, label: 'Profile' },
  ],
  recruiter: [
    { key: '/dashboard', icon: <HomeOutlined />, label: 'Dashboard' },
    { key: '/interviews', icon: <ScheduleOutlined />, label: 'Interviews' },
    { key: '/jds', icon: <ReadOutlined />, label: 'Job Descriptions' },
    { key: '/profile', icon: <ProfileOutlined />, label: 'Profile' },
  ],
  admin: [
    { key: '/dashboard', icon: <HomeOutlined />, label: 'Dashboard' },
    { key: '/interviews', icon: <ScheduleOutlined />, label: 'Interviews' },
    { key: '/jds', icon: <ReadOutlined />, label: 'Job Descriptions' },
    { key: '/resumes', icon: <FileTextOutlined />, label: 'Resumes' },
    { key: '/profile', icon: <ProfileOutlined />, label: 'Profile' },
  ],
}

function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/dashboard" className="flex items-center gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-lg shadow-indigo-500/25">
        IA
      </div>
      {!compact ? (
        <div className="min-w-0">
          <Typography.Text className="!block !truncate !text-white !font-semibold">
            Interviewer AI
          </Typography.Text>
          <Typography.Text className="!block !truncate !text-xs !text-slate-500">
            Smart hiring platform
          </Typography.Text>
        </div>
      ) : null}
    </Link>
  )
}

export function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const user = useAppSelector((state) => state.auth.user)
  const { isMobile, isDesktop } = useBreakpoint()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = useMemo(
    () => ROLE_NAV[user?.role ?? 'candidate'] ?? ROLE_NAV.candidate,
    [user?.role],
  )

  const selectedKey =
    menuItems?.find((item) =>
      location.pathname.startsWith(String(item?.key)),
    )?.key ?? '/dashboard'

  const handleNavigate = (key: string) => {
    navigate(key)
    setDrawerOpen(false)
  }

  const handleLogout = () => {
    setDrawerOpen(false)
    logoutSession(dispatch)
    navigate('/login', { replace: true })
  }

  const sidebarMenu = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[String(selectedKey)]}
      items={menuItems}
      onClick={({ key }) => handleNavigate(String(key))}
      className="border-none bg-transparent px-2"
    />
  )

  const mainOffset = isDesktop ? (collapsed ? 80 : 280) : 0

  return (
    <Layout className="min-h-screen">
      {isDesktop ? (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={280}
          collapsedWidth={80}
          className="!fixed inset-y-0 left-0 z-30 border-r border-white/[0.06] !bg-[rgba(10,15,30,0.92)] backdrop-blur-xl"
        >
          <div
            className={`flex h-16 items-center border-b border-white/[0.06] ${
              collapsed ? 'justify-center px-2' : 'px-5'
            }`}
          >
            <BrandMark compact={collapsed} />
          </div>
          <div className="py-3">{sidebarMenu}</div>
        </Sider>
      ) : null}

      <Drawer
        title={<BrandMark />}
        placement="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={280}
        styles={{ body: { padding: 0 } }}
        className="mobile-nav-drawer"
      >
        <div className="px-2 py-2">{sidebarMenu}</div>
        <div className="border-t border-white/[0.06] p-4">
          <Button block icon={<LogoutOutlined />} onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </Drawer>

      <Layout
        className="min-h-screen bg-transparent transition-[margin] duration-200"
        style={{ marginLeft: mainOffset }}
      >
        <Header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-white/[0.06] bg-[rgba(10,15,30,0.75)] px-4 backdrop-blur-xl sm:px-6">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            {isMobile ? (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setDrawerOpen(true)}
                className="!text-slate-300"
                aria-label="Open menu"
              />
            ) : null}
            <div className="min-w-0">
              <Typography.Text className="!block !truncate !text-sm !text-slate-400">
                Welcome back
              </Typography.Text>
              <Typography.Text className="!block !truncate !text-base !font-medium !text-white">
                {user?.full_name ?? user?.email ?? 'User'}
              </Typography.Text>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <span className="hidden rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs capitalize text-slate-400 sm:inline">
              {user?.role}
            </span>
            <Avatar
              size={isMobile ? 'default' : 'large'}
              className="!bg-gradient-to-br !from-indigo-500 !to-violet-600"
            >
              {(user?.full_name ?? user?.email ?? '?').slice(0, 1).toUpperCase()}
            </Avatar>
            {!isMobile ? (
              <Button
                type="text"
                icon={<LogoutOutlined />}
                onClick={handleLogout}
                className="!text-slate-400 hover:!text-white"
              >
                <span className="hidden lg:inline">Logout</span>
              </Button>
            ) : (
              <Button
                type="text"
                icon={<LogoutOutlined />}
                onClick={handleLogout}
                className="!text-slate-400"
                aria-label="Logout"
              />
            )}
          </div>
        </Header>

        <Content className="px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
