import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { JDCreate, JDPublic } from '@/types/api'

export interface JdsState {
  items: JDPublic[]
  selected: JDPublic | null
  loading: boolean
  creating: boolean
  error: string | null
}

const initialState: JdsState = {
  items: [],
  selected: null,
  loading: false,
  creating: false,
  error: null,
}

const jdsSlice = createSlice({
  name: 'jds',
  initialState,
  reducers: {
    fetchJdsRequest(state) {
      state.loading = true
      state.error = null
    },
    fetchJdsSuccess(state, action: PayloadAction<JDPublic[]>) {
      state.loading = false
      state.items = action.payload
    },
    fetchJdsFailure(state, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    createJdRequest(state, _action: PayloadAction<JDCreate>) {
      state.creating = true
      state.error = null
    },
    createJdSuccess(state, action: PayloadAction<JDPublic>) {
      state.creating = false
      state.items = [action.payload, ...state.items]
    },
    createJdFailure(state, action: PayloadAction<string>) {
      state.creating = false
      state.error = action.payload
    },
  },
})

export const jdsActions = jdsSlice.actions
export const jdsReducer = jdsSlice.reducer
