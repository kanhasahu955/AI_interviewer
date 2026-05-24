import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { ReportPublic } from '@/types/api'

export interface ReportsState {
  current: ReportPublic | null
  loading: boolean
  error: string | null
}

const initialState: ReportsState = {
  current: null,
  loading: false,
  error: null,
}

const reportsSlice = createSlice({
  name: 'reports',
  initialState,
  reducers: {
    fetchReportRequest(state, _action: PayloadAction<number>) {
      state.loading = true
      state.error = null
    },
    fetchReportSuccess(state, action: PayloadAction<ReportPublic>) {
      state.loading = false
      state.current = action.payload
    },
    fetchReportFailure(state, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    clearReport(state) {
      state.current = null
      state.error = null
    },
  },
})

export const reportsActions = reportsSlice.actions
export const reportsReducer = reportsSlice.reducer
