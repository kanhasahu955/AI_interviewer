import { HomeOutlined } from '@ant-design/icons'
import { Button, Result } from 'antd'
import { Link } from 'react-router-dom'

import { PageContainer } from '@/components/common/PageContainer'

export function NotFoundPage() {
  return (
    <PageContainer>
      <div className="flex min-h-[70vh] items-center justify-center">
        <Result
          status="404"
          title="Page not found"
          subTitle="The page you requested doesn't exist or was moved."
          extra={
            <Link to="/dashboard">
              <Button type="primary" size="large" icon={<HomeOutlined />}>
                Back to dashboard
              </Button>
            </Link>
          }
        />
      </div>
    </PageContainer>
  )
}
