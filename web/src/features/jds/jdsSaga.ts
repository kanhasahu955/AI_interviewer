import { call, put, takeLatest } from 'redux-saga/effects'

import { jdsActions } from '@/features/jds/jdsSlice'
import { ApiError } from '@/core/errors/ApiError'
import { jdService } from '@/services/JdService'
import type { JDPublic } from '@/types/api'

function* handleFetchJds(): Generator {
  try {
    const items: JDPublic[] = yield call([jdService, jdService.list])
    yield put(jdsActions.fetchJdsSuccess(items))
  } catch (error) {
    yield put(
      jdsActions.fetchJdsFailure(
        error instanceof ApiError ? error.message : 'Failed to load job descriptions',
      ),
    )
  }
}

function* handleCreateJd(
  action: ReturnType<typeof jdsActions.createJdRequest>,
): Generator {
  try {
    const jd: JDPublic = yield call(
      [jdService, jdService.create],
      action.payload,
    )
    yield put(jdsActions.createJdSuccess(jd))
  } catch (error) {
    yield put(
      jdsActions.createJdFailure(
        error instanceof ApiError ? error.message : 'Failed to create job description',
      ),
    )
  }
}

export function* jdsSaga(): Generator {
  yield takeLatest(jdsActions.fetchJdsRequest.type, handleFetchJds)
  yield takeLatest(jdsActions.createJdRequest.type, handleCreateJd)
}
