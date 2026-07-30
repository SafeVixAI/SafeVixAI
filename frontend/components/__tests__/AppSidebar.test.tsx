// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

let mockPathname = '/'
jest.mock('next/navigation', function() {
  return { usePathname: function() { return mockPathname } }
})

let mockState: any = { isDesktopSidebarCollapsed: true, setDesktopSidebarCollapsed: jest.fn(), isThinSidebarEnabled: false, setThinSidebarEnabled: jest.fn() }
jest.mock('@/lib/store', function() {
  return {
    useAppStore: function(selector: any) {
      if (typeof selector === 'function') return selector(mockState)
      return mockState
    },
  }
})

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { AppSidebar } from '../AppSidebar'

describe('AppSidebar', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockPathname = '/'
    mockState = { isDesktopSidebarCollapsed: true, setDesktopSidebarCollapsed: jest.fn(), isThinSidebarEnabled: false, setThinSidebarEnabled: jest.fn() }
  })

  it('renders hamburger when collapsed', function() {
    render(React.createElement(AppSidebar))
    expect(screen.getByLabelText('Expand sidebar')).toBeTruthy()
    expect(screen.queryByText('SAFEVIX_AI')).toBeNull()
  })

  it('renders full content when expanded', function() {
    mockState.isDesktopSidebarCollapsed = false
    render(React.createElement(AppSidebar))
    expect(screen.getByText('SAFEVIX_AI')).toBeTruthy()
    expect(screen.getByText('System SOS')).toBeTruthy()
  })

  it('renders navigation items when expanded', function() {
    mockState.isDesktopSidebarCollapsed = false
    render(React.createElement(AppSidebar))
    expect(screen.getByText('Map')).toBeTruthy()
    expect(screen.getByText('AI Assistant')).toBeTruthy()
    expect(screen.getByText('Locator')).toBeTruthy()
  })

  it('shows emergency dials when expanded', function() {
    mockState.isDesktopSidebarCollapsed = false
    render(React.createElement(AppSidebar))
    expect(screen.getByText('112')).toBeTruthy()
    expect(screen.getByText('100')).toBeTruthy()
  })

  it('calls setDesktopSidebarCollapsed when hamburger clicked', function() {
    render(React.createElement(AppSidebar))
    fireEvent.click(screen.getByLabelText('Expand sidebar'))
    expect(mockState.setDesktopSidebarCollapsed).toHaveBeenCalledWith(false)
  })

  it('calls setDesktopSidebarCollapsed when X clicked', function() {
    mockState.isDesktopSidebarCollapsed = false
    render(React.createElement(AppSidebar))
    fireEvent.click(screen.getByLabelText('Close sidebar'))
    expect(mockState.setDesktopSidebarCollapsed).toHaveBeenCalledWith(true)
  })

  it('shows SYSTEM ONLINE indicator when expanded', function() {
    mockState.isDesktopSidebarCollapsed = false
    render(React.createElement(AppSidebar))
    expect(screen.getByText('SYSTEM ONLINE')).toBeTruthy()
  })

  it('calls setThinSidebarEnabled on pin toggle click', function() {
    mockState.isDesktopSidebarCollapsed = false
    render(React.createElement(AppSidebar))
    fireEvent.click(screen.getByLabelText('Pin sidebar'))
    expect(mockState.setThinSidebarEnabled).toHaveBeenCalledWith(true)
  })

  it('shows Unpin label when thin sidebar enabled', function() {
    mockState.isDesktopSidebarCollapsed = false
    mockState.isThinSidebarEnabled = true
    render(React.createElement(AppSidebar))
    expect(screen.getByLabelText('Unpin sidebar')).toBeTruthy()
  })

  it('hides labels when sidebar is collapsed', function() {
    mockState.isDesktopSidebarCollapsed = true
    mockState.isThinSidebarEnabled = false
    render(React.createElement(AppSidebar))
    // Nav item labels should not be visible
    expect(screen.queryByText('Emergency Dial')).toBeNull()
    expect(screen.queryByText('SYSTEM ONLINE')).toBeNull()
  })
})
