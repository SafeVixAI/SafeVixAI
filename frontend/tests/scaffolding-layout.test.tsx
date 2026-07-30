jest.mock('next/image', function() { return function(props) { return React.createElement('img', props) } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render } from '@testing-library/react'
import React from 'react'

import AssistantLayout from '@/app/assistant/layout'
import BystanderLayout from '@/app/bystander/layout'
import ChallanLayout from '@/app/challan/layout'
import CommandCenterLayout from '@/app/command-center/layout'
import EmergencyLayout from '@/app/emergency/layout'
import EmergencyCardUserIdLayout from '@/app/emergency-card/[userId]/layout'
import FirstAidLayout from '@/app/first-aid/layout'
import ForgotPasswordLayout from '@/app/forgot-password/layout'
import GuideSlugLayout from '@/app/guide/[slug]/layout'
import GuideLayout from '@/app/guide/layout'
import LandingLayout from '@/app/landing/layout'
import LocatorLayout from '@/app/locator/layout'
import LoginLayout from '@/app/login/layout'
import OfficerLayout from '@/app/officer/layout'
import OfflineLayout from '@/app/offline/layout'
import PrivacyLayout from '@/app/privacy/layout'
import ProfileLayout from '@/app/profile/layout'
import ReportTrackLayout from '@/app/report/track/layout'
import ReportLayout from '@/app/report/layout'
import ResetPasswordLayout from '@/app/reset-password/layout'
import SettingsLayout from '@/app/settings/layout'
import ShareReceiveLayout from '@/app/share-receive/layout'
import SignupLayout from '@/app/signup/layout'
import SosLayout from '@/app/sos/layout'
import TermsLayout from '@/app/terms/layout'
import TrackSessionIdLayout from '@/app/track/[session_id]/layout'
import TrackingLayout from '@/app/tracking/layout'

const testContent = React.createElement('span', null, 'test child')

function R(Layout) { render(React.createElement(Layout, null, testContent)) }

describe('Route layout components', function() {
  it('renders assistant layout with children', function() { R(AssistantLayout); expect(document.body.textContent).toContain('test child') })
  it('renders bystander layout with children', function() { R(BystanderLayout); expect(document.body.textContent).toContain('test child') })
  it('renders challan layout with children', function() { R(ChallanLayout); expect(document.body.textContent).toContain('test child') })
  it('renders command center layout with children', function() { R(CommandCenterLayout); expect(document.body.textContent).toContain('test child') })
  it('renders emergency layout with children', function() { R(EmergencyLayout); expect(document.body.textContent).toContain('test child') })
  it('renders emergency card layout with children', function() { R(EmergencyCardUserIdLayout); expect(document.body.textContent).toContain('test child') })
  it('renders first aid layout with children', function() { R(FirstAidLayout); expect(document.body.textContent).toContain('test child') })
  it('renders forgot password layout with children', function() { R(ForgotPasswordLayout); expect(document.body.textContent).toContain('test child') })
  it('renders guide [slug] layout with children', function() { R(GuideSlugLayout); expect(document.body.textContent).toContain('test child') })
  it('renders guide layout with children', function() { R(GuideLayout); expect(document.body.textContent).toContain('test child') })
  it('renders landing layout with children', function() { R(LandingLayout); expect(document.body.textContent).toContain('test child') })
  it('renders locator layout with children', function() { R(LocatorLayout); expect(document.body.textContent).toContain('test child') })
  it('renders login layout with children', function() { R(LoginLayout); expect(document.body.textContent).toContain('test child') })
  it('renders officer layout with children', function() { R(OfficerLayout); expect(document.body.textContent).toContain('test child') })
  it('renders offline layout with children', function() { R(OfflineLayout); expect(document.body.textContent).toContain('test child') })
  it('renders privacy layout with children', function() { R(PrivacyLayout); expect(document.body.textContent).toContain('test child') })
  it('renders profile layout with children', function() { R(ProfileLayout); expect(document.body.textContent).toContain('test child') })
  it('renders report/track layout with children', function() { R(ReportTrackLayout); expect(document.body.textContent).toContain('test child') })
  it('renders report layout with children', function() { R(ReportLayout); expect(document.body.textContent).toContain('test child') })
  it('renders reset password layout with children', function() { R(ResetPasswordLayout); expect(document.body.textContent).toContain('test child') })
  it('renders settings layout with children', function() { R(SettingsLayout); expect(document.body.textContent).toContain('test child') })
  it('renders share receive layout with children', function() { R(ShareReceiveLayout); expect(document.body.textContent).toContain('test child') })
  it('renders signup layout with children', function() { R(SignupLayout); expect(document.body.textContent).toContain('test child') })
  it('renders sos layout with children', function() { R(SosLayout); expect(document.body.textContent).toContain('test child') })
  it('renders terms layout with children', function() { R(TermsLayout); expect(document.body.textContent).toContain('test child') })
  it('renders track/[session_id] layout with children', function() { R(TrackSessionIdLayout); expect(document.body.textContent).toContain('test child') })
  it('renders tracking layout with children', function() { R(TrackingLayout); expect(document.body.textContent).toContain('test child') })
})
