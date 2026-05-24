import { call, put, takeLatest } from 'redux-saga/effects'

import { resumesActions } from '@/features/resumes/resumesSlice'
import { ApiError } from '@/core/errors/ApiError'
import { resumeService } from '@/services/ResumeService'
import type { ResumePublic } from '@/types/api'

function* handleFetchResumes(): Generator {
  try {
    const items: ResumePublic[] = yield call([resumeService, resumeService.list])
    yield put(resumesActions.fetchResumesSuccess(items))
  } catch (error) {
    yield put(
      resumesActions.fetchResumesFailure(
        error instanceof ApiError ? error.message : 'Failed to load resumes',
      ),
    )
  }
}

function* handleUploadResume(
  action: ReturnType<typeof resumesActions.uploadResumeRequest>,
): Generator {
  try {
    const resume: ResumePublic = yield call(
      [resumeService, resumeService.upload],
      action.payload,
    )
    yield put(resumesActions.uploadResumeSuccess(resume))
  } catch (error) {
    yield put(
      resumesActions.uploadResumeFailure(
        error instanceof ApiError ? error.message : 'Failed to upload resume',
      ),
    )
  }
}

export function* resumesSaga(): Generator {
  yield takeLatest(resumesActions.fetchResumesRequest.type, handleFetchResumes)
  yield takeLatest(resumesActions.uploadResumeRequest.type, handleUploadResume)
}
