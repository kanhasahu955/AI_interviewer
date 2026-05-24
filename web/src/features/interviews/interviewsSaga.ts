import { call, put, takeLatest } from 'redux-saga/effects'

import { interviewsActions } from '@/features/interviews/interviewsSlice'
import { ApiError } from '@/core/errors/ApiError'
import { interviewService } from '@/services/InterviewService'
import type { InterviewPublic, LiveKitTokenResponse, TurnPublic } from '@/types/api'

function* handleFetchInterviews(): Generator {
  try {
    const items: InterviewPublic[] = yield call([
      interviewService,
      interviewService.list,
    ])
    yield put(interviewsActions.fetchInterviewsSuccess(items))
  } catch (error) {
    yield put(
      interviewsActions.fetchInterviewsFailure(
        error instanceof ApiError ? error.message : 'Failed to load interviews',
      ),
    )
  }
}

function* handleFetchInterview(
  action: ReturnType<typeof interviewsActions.fetchInterviewRequest>,
): Generator {
  try {
    const id = action.payload
    const interview: InterviewPublic = yield call(
      [interviewService, interviewService.getById],
      id,
    )
    const turns: TurnPublic[] = yield call(
      [interviewService, interviewService.getTurns],
      id,
    )
    yield put(interviewsActions.fetchInterviewSuccess({ interview, turns }))
  } catch (error) {
    yield put(
      interviewsActions.fetchInterviewFailure(
        error instanceof ApiError ? error.message : 'Failed to load interview',
      ),
    )
  }
}

function* handleCreateInterview(
  action: ReturnType<typeof interviewsActions.createInterviewRequest>,
): Generator {
  try {
    const interview: InterviewPublic = yield call(
      [interviewService, interviewService.create],
      action.payload,
    )
    yield put(interviewsActions.createInterviewSuccess(interview))
  } catch (error) {
    yield put(
      interviewsActions.createInterviewFailure(
        error instanceof ApiError ? error.message : 'Failed to create interview',
      ),
    )
  }
}

function* handleCreateSelfInterview(
  action: ReturnType<typeof interviewsActions.createSelfInterviewRequest>,
): Generator {
  try {
    const interview: InterviewPublic = yield call(
      [interviewService, interviewService.createSelf],
      action.payload,
    )
    yield put(interviewsActions.createSelfInterviewSuccess(interview))
  } catch (error) {
    yield put(
      interviewsActions.createSelfInterviewFailure(
        error instanceof ApiError ? error.message : 'Failed to start interview',
      ),
    )
  }
}

function* handleEndInterview(
  action: ReturnType<typeof interviewsActions.endInterviewRequest>,
): Generator {
  try {
    const id = action.payload
    const interview: InterviewPublic = yield call(
      [interviewService, interviewService.end],
      id,
    )
    yield put(interviewsActions.endInterviewSuccess(interview))
  } catch (error) {
    yield put(
      interviewsActions.endInterviewFailure(
        error instanceof ApiError ? error.message : 'Failed to end interview',
      ),
    )
  }
}

function* handleFetchLiveKitToken(
  action: ReturnType<typeof interviewsActions.fetchLiveKitTokenRequest>,
): Generator {
  try {
    const token: LiveKitTokenResponse = yield call(
      [interviewService, interviewService.getToken],
      action.payload,
    )
    yield put(interviewsActions.fetchLiveKitTokenSuccess(token))
  } catch (error) {
    yield put(
      interviewsActions.fetchLiveKitTokenFailure(
        error instanceof ApiError ? error.message : 'Could not join room',
      ),
    )
  }
}

export function* interviewsSaga(): Generator {
  yield takeLatest(
    interviewsActions.fetchInterviewsRequest.type,
    handleFetchInterviews,
  )
  yield takeLatest(
    interviewsActions.fetchInterviewRequest.type,
    handleFetchInterview,
  )
  yield takeLatest(
    interviewsActions.createInterviewRequest.type,
    handleCreateInterview,
  )
  yield takeLatest(
    interviewsActions.createSelfInterviewRequest.type,
    handleCreateSelfInterview,
  )
  yield takeLatest(
    interviewsActions.endInterviewRequest.type,
    handleEndInterview,
  )
  yield takeLatest(
    interviewsActions.fetchLiveKitTokenRequest.type,
    handleFetchLiveKitToken,
  )
}
