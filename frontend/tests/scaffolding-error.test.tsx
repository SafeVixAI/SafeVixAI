const mockRouter = { push: jest.fn(), back: jest.fn(), replace: jest.fn() }
jest.mock('next/navigation', function() { return { useRouter: function() { return mockRouter }, useSearchParams: function() { return new URLSearchParams() }, useParams: function() { return {} } } })
jest.mock('next/image', function() { return function(props) { return React.createElement('img', props) } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })
jest.mock('@/lib/client-logger', function() { return { logClientError: jest.fn() } })

import { render, screen } from '@testing-library/react'
import React from 'react'
import { logClientError } from '@/lib/client-logger'

import AssistantError from '@/app/assistant/error'
import BystanderError from '@/app/bystander/error'
import ChallanError from '@/app/challan/error'
import CommandCenterError from '@/app/command-center/error'
import EmergencyError from '@/app/emergency/error'
import EmergencyCardUserIdError from '@/app/emergency-card/[userId]/error'
import FirstAidError from '@/app/first-aid/error'
import ForgotPasswordError from '@/app/forgot-password/error'
import GuideSlugError from '@/app/guide/[slug]/error'
import GuideError from '@/app/guide/error'
import LandingError from '@/app/landing/error'
import LocatorError from '@/app/locator/error'
import LoginError from '@/app/login/error'
import OfficerError from '@/app/officer/error'
import OfflineError from '@/app/offline/error'
import PrivacyError from '@/app/privacy/error'
import ProfileError from '@/app/profile/error'
import ReportTrackError from '@/app/report/track/error'
import ReportError from '@/app/report/error'
import ResetPasswordError from '@/app/reset-password/error'
import SettingsError from '@/app/settings/error'
import ShareReceiveError from '@/app/share-receive/error'
import SignupError from '@/app/signup/error'
import SosError from '@/app/sos/error'
import TermsError from '@/app/terms/error'
import TrackSessionIdError from '@/app/track/[session_id]/error'
import TrackingError from '@/app/tracking/error'

const testError = new Error('Test error message')
const mockReset = jest.fn()

function R(Comp) { render(React.createElement(Comp, { error: testError, reset: mockReset })) }

describe('Route error components', function() {
  beforeEach(function() { jest.clearAllMocks() })

  it('renders assistant error', function() { R(AssistantError); expect(screen.getByText('Chat service unavailable')).toBeTruthy(); expect(logClientError).toHaveBeenCalled() })
  it('renders bystander error', function() { R(BystanderError); expect(logClientError).toHaveBeenCalled() })
  it('renders challan error', function() { R(ChallanError); expect(logClientError).toHaveBeenCalled() })
  it('renders command center error', function() { R(CommandCenterError); expect(logClientError).toHaveBeenCalled() })
  it('renders emergency error', function() { R(EmergencyError); expect(logClientError).toHaveBeenCalled() })
  it('renders emergency card error', function() { R(EmergencyCardUserIdError); expect(logClientError).toHaveBeenCalled() })
  it('renders first aid error', function() { R(FirstAidError); expect(logClientError).toHaveBeenCalled() })
  it('renders forgot password error', function() { R(ForgotPasswordError); expect(logClientError).toHaveBeenCalled() })
  it('renders guide [slug] error', function() { R(GuideSlugError); expect(logClientError).toHaveBeenCalled() })
  it('renders guide error', function() { R(GuideError); expect(logClientError).toHaveBeenCalled() })
  it('renders landing error', function() { R(LandingError); expect(logClientError).toHaveBeenCalled() })
  it('renders locator error', function() { R(LocatorError); expect(logClientError).toHaveBeenCalled() })
  it('renders login error', function() { R(LoginError); expect(logClientError).toHaveBeenCalled() })
  it('renders officer error', function() { R(OfficerError); expect(logClientError).toHaveBeenCalled() })
  it('renders offline error', function() { R(OfflineError); expect(logClientError).toHaveBeenCalled() })
  it('renders privacy error', function() { R(PrivacyError); expect(logClientError).toHaveBeenCalled() })
  it('renders profile error', function() { R(ProfileError); expect(logClientError).toHaveBeenCalled() })
  it('renders report/track error', function() { R(ReportTrackError); expect(logClientError).toHaveBeenCalled() })
  it('renders report error', function() { R(ReportError); expect(logClientError).toHaveBeenCalled() })
  it('renders reset password error', function() { R(ResetPasswordError); expect(logClientError).toHaveBeenCalled() })
  it('renders settings error', function() { R(SettingsError); expect(logClientError).toHaveBeenCalled() })
  it('renders share receive error', function() { R(ShareReceiveError); expect(logClientError).toHaveBeenCalled() })
  it('renders signup error', function() { R(SignupError); expect(logClientError).toHaveBeenCalled() })
  it('renders sos error', function() { R(SosError); expect(logClientError).toHaveBeenCalled() })
  it('renders terms error', function() { R(TermsError); expect(logClientError).toHaveBeenCalled() })
  it('renders track/[session_id] error', function() { R(TrackSessionIdError); expect(logClientError).toHaveBeenCalled() })
  it('renders tracking error', function() { R(TrackingError); expect(logClientError).toHaveBeenCalled() })
})
