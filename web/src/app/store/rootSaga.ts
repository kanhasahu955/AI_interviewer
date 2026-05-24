import { all, fork } from 'redux-saga/effects'

import { authSaga } from '@/features/auth/authSaga'
import { interviewsSaga } from '@/features/interviews/interviewsSaga'
import { jdsSaga } from '@/features/jds/jdsSaga'
import { reportsSaga } from '@/features/reports/reportsSaga'
import { resumesSaga } from '@/features/resumes/resumesSaga'
import { userSaga } from '@/features/user/userSaga'

export function* rootSaga() {
  yield all([
    fork(authSaga),
    fork(userSaga),
    fork(interviewsSaga),
    fork(jdsSaga),
    fork(resumesSaga),
    fork(reportsSaga),
  ])
}
