import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { ResumePublic } from '@/types/api'

export interface ResumesState {
  items: ResumePublic[]
  uploading: boolean
  loading: boolean
  error: string | null
}

const initialState: ResumesState = {
  items: [],
  uploading: false,
  loading: false,
  error: null,
}

const resumesSlice = createSlice({
  name: 'resumes',
  initialState,
  reducers: {
    fetchResumesRequest(state) {
      state.loading = true
      state.error = null
    },
    fetchResumesSuccess(state, action: PayloadAction<ResumePublic[]>) {
      state.loading = false
      state.items = action.payload
    },
    fetchResumesFailure(state, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    uploadResumeRequest(state, _action: PayloadAction<File>) {
      state.uploading = true
      state.error = null
    },
    uploadResumeSuccess(state, action: PayloadAction<ResumePublic>) {
      state.uploading = false
      state.items = [action.payload, ...state.items]
    },
    uploadResumeFailure(state, action: PayloadAction<string>) {
      state.uploading = false
      state.error = action.payload
    },
  },
})

export const resumesActions = resumesSlice.actions
export const resumesReducer = resumesSlice.reducer
