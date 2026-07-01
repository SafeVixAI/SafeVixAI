var mockRouter = { push: jest.fn(), back: jest.fn(), replace: jest.fn() }
jest.mock('next/navigation', function() { return { useRouter: function() { return mockRouter }, useSearchParams: function() { return new URLSearchParams() }, useParams: function() { return {} } } })
jest.mock('next/image', function() { return function(props) { return React.createElement('img', props) } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render } from '@testing-library/react'
import React from 'react'

import RootLoading from '@/app/loading'
import AssistantLoading from '@/app/assistant/loading'
import BystanderLoading from '@/app/bystander/loading'
import ChallanLoading from '@/app/challan/loading'
import CommandCenterLoading from '@/app/command-center/loading'
import EmergencyLoading from '@/app/emergency/loading'
import EmergencyCardUserIdLoading from '@/app/emergency-card/[userId]/loading'
import FirstAidLoading from '@/app/first-aid/loading'
import ForgotPasswordLoading from '@/app/forgot-password/loading'
import GuideSlugLoading from '@/app/guide/[slug]/loading'
import GuideLoading from '@/app/guide/loading'
import LandingLoading from '@/app/landing/loading'
import LocatorLoading from '@/app/locator/loading'
import LoginLoading from '@/app/login/loading'
import OfficerLoading from '@/app/officer/loading'
import OfflineLoading from '@/app/offline/loading'
import PrivacyLoading from '@/app/privacy/loading'
import ProfileLoading from '@/app/profile/loading'
import ReportTrackLoading from '@/app/report/track/loading'
import ReportLoading from '@/app/report/loading'
import ResetPasswordLoading from '@/app/reset-password/loading'
import SettingsLoading from '@/app/settings/loading'
import ShareReceiveLoading from '@/app/share-receive/loading'
import SignupLoading from '@/app/signup/loading'
import SosLoading from '@/app/sos/loading'
import TermsLoading from '@/app/terms/loading'
import TrackSessionIdLoading from '@/app/track/[session_id]/loading'
import TrackingLoading from '@/app/tracking/loading'

describe('Route loading components', function() {
  beforeEach(function() { jest.clearAllMocks() })

  it('renders root loading', function() { var { container } = render(React.createElement(RootLoading)); expect(container).toBeTruthy() })
  it('renders assistant loading', function() { var { container } = render(React.createElement(AssistantLoading)); expect(container).toBeTruthy() })
  it('renders bystander loading', function() { var { container } = render(React.createElement(BystanderLoading)); expect(container).toBeTruthy() })
  it('renders challan loading', function() { var { container } = render(React.createElement(ChallanLoading)); expect(container).toBeTruthy() })
  it('renders command center loading', function() { var { container } = render(React.createElement(CommandCenterLoading)); expect(container).toBeTruthy() })
  it('renders emergency loading', function() { var { container } = render(React.createElement(EmergencyLoading)); expect(container).toBeTruthy() })
  it('renders emergency card loading', function() { var { container } = render(React.createElement(EmergencyCardUserIdLoading)); expect(container).toBeTruthy() })
  it('renders first aid loading', function() { var { container } = render(React.createElement(FirstAidLoading)); expect(container).toBeTruthy() })
  it('renders forgot password loading', function() { var { container } = render(React.createElement(ForgotPasswordLoading)); expect(container).toBeTruthy() })
  it('renders guide [slug] loading', function() { var { container } = render(React.createElement(GuideSlugLoading)); expect(container).toBeTruthy() })
  it('renders guide loading', function() { var { container } = render(React.createElement(GuideLoading)); expect(container).toBeTruthy() })
  it('renders landing loading', function() { var { container } = render(React.createElement(LandingLoading)); expect(container).toBeTruthy() })
  it('renders locator loading', function() { var { container } = render(React.createElement(LocatorLoading)); expect(container).toBeTruthy() })
  it('renders login loading', function() { var { container } = render(React.createElement(LoginLoading)); expect(container).toBeTruthy() })
  it('renders officer loading', function() { var { container } = render(React.createElement(OfficerLoading)); expect(container).toBeTruthy() })
  it('renders offline loading', function() { var { container } = render(React.createElement(OfflineLoading)); expect(container).toBeTruthy() })
  it('renders privacy loading', function() { var { container } = render(React.createElement(PrivacyLoading)); expect(container).toBeTruthy() })
  it('renders profile loading', function() { var { container } = render(React.createElement(ProfileLoading)); expect(container).toBeTruthy() })
  it('renders report/track loading', function() { var { container } = render(React.createElement(ReportTrackLoading)); expect(container).toBeTruthy() })
  it('renders report loading', function() { var { container } = render(React.createElement(ReportLoading)); expect(container).toBeTruthy() })
  it('renders reset password loading', function() { var { container } = render(React.createElement(ResetPasswordLoading)); expect(container).toBeTruthy() })
  it('renders settings loading', function() { var { container } = render(React.createElement(SettingsLoading)); expect(container).toBeTruthy() })
  it('renders share receive loading', function() { var { container } = render(React.createElement(ShareReceiveLoading)); expect(container).toBeTruthy() })
  it('renders signup loading', function() { var { container } = render(React.createElement(SignupLoading)); expect(container).toBeTruthy() })
  it('renders sos loading', function() { var { container } = render(React.createElement(SosLoading)); expect(container).toBeTruthy() })
  it('renders terms loading', function() { var { container } = render(React.createElement(TermsLoading)); expect(container).toBeTruthy() })
  it('renders track/[session_id] loading', function() { var { container } = render(React.createElement(TrackSessionIdLoading)); expect(container).toBeTruthy() })
  it('renders tracking loading', function() { var { container } = render(React.createElement(TrackingLoading)); expect(container).toBeTruthy() })
})
