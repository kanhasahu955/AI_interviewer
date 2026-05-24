import { combineReducers, configureStore } from '@reduxjs/toolkit'
import createSagaMiddleware from 'redux-saga'

import { authReducer } from '@/features/auth/authSlice'
import { interviewsReducer } from '@/features/interviews/interviewsSlice'
import { jdsReducer } from '@/features/jds/jdsSlice'
import { reportsReducer } from '@/features/reports/reportsSlice'
import { resumesReducer } from '@/features/resumes/resumesSlice'
import { userReducer } from '@/features/user/userSlice'
import { rootSaga } from '@/app/store/rootSaga'

const sagaMiddleware = createSagaMiddleware()

export const store = configureStore({
  reducer: combineReducers({
    auth: authReducer,
    user: userReducer,
    interviews: interviewsReducer,
    jds: jdsReducer,
    resumes: resumesReducer,
    reports: reportsReducer,
  }),
  middleware: (getDefault) =>
    getDefault({ thunk: false, serializableCheck: false }).concat(
      sagaMiddleware,
    ),
  devTools: import.meta.env.DEV,
})

sagaMiddleware.run(rootSaga)

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
