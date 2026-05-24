import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { UserPublic } from '@/types/api'

export interface UserState {
  profile: UserPublic | null
  updating: boolean
  error: string | null
}

const initialState: UserState = {
  profile: null,
  updating: false,
  error: null,
}

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setProfile(state, action: PayloadAction<UserPublic | null>) {
      state.profile = action.payload
    },
    updateProfileRequest(state, _action: PayloadAction<{ full_name: string }>) {
      state.updating = true
      state.error = null
    },
    updateProfileSuccess(state, action: PayloadAction<UserPublic>) {
      state.updating = false
      state.profile = action.payload
    },
    updateProfileFailure(state, action: PayloadAction<string>) {
      state.updating = false
      state.error = action.payload
    },
    clearProfile(state) {
      state.profile = null
      state.error = null
    },
  },
})

export const userActions = userSlice.actions
export const userReducer = userSlice.reducer
