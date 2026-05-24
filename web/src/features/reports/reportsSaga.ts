import { call, put, takeLatest } from 'redux-saga/effects'

import { reportsActions } from '@/features/reports/reportsSlice'
import { ApiError } from '@/core/errors/ApiError'
import { reportService } from '@/services/ReportService'
import type { ReportPublic } from '@/types/api'

function* handleFetchReport(
  action: ReturnType<typeof reportsActions.fetchReportRequest>,
): Generator {
  try {
    const report: ReportPublic = yield call(
      [reportService, reportService.getByInterviewId],
      action.payload,
    )
    yield put(reportsActions.fetchReportSuccess(report))
  } catch (error) {
    yield put(
      reportsActions.fetchReportFailure(
        error instanceof ApiError ? error.message : 'Report not available yet',
      ),
    )
  }
}

export function* reportsSaga(): Generator {
  yield takeLatest(reportsActions.fetchReportRequest.type, handleFetchReport)
}
