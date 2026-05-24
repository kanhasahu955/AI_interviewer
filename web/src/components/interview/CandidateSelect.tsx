import { Select, Spin } from 'antd'
import debounce from 'lodash/debounce'
import { useCallback, useMemo, useState } from 'react'

import { userService } from '@/services/UserService'
import type { UserPublic } from '@/types/api'

interface CandidateSelectProps {
  value?: number
  onChange?: (candidateId: number | undefined) => void
}

export function CandidateSelect({ value, onChange }: CandidateSelectProps) {
  const [options, setOptions] = useState<UserPublic[]>([])
  const [fetching, setFetching] = useState(false)

  const loadCandidates = useMemo(
    () =>
      debounce(async (query: string) => {
        setFetching(true)
        try {
          const rows = await userService.searchCandidates(query || undefined)
          setOptions(rows)
        } catch {
          setOptions([])
        } finally {
          setFetching(false)
        }
      }, 300),
    [],
  )

  const handleSearch = useCallback(
    (query: string) => {
      loadCandidates(query)
    },
    [loadCandidates],
  )

  const handleFocus = () => {
    if (options.length === 0) {
      loadCandidates('')
    }
  }

  return (
    <Select
      showSearch
      allowClear
      size="large"
      filterOption={false}
      className="w-full"
      placeholder="Search by name or email"
      notFoundContent={fetching ? <Spin size="small" /> : 'No candidates found'}
      onSearch={handleSearch}
      onFocus={handleFocus}
      onChange={(next) => onChange?.(next)}
      value={value}
      options={options.map((user) => ({
        value: user.id,
        label: user.full_name
          ? `${user.full_name} · ${user.email}`
          : user.email,
      }))}
    />
  )
}
