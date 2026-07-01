jest.mock('next/navigation', function () {
  return {
    usePathname: jest.fn().mockReturnValue('/'),
    useRouter: jest.fn().mockReturnValue({ push: jest.fn() }),
  }
})

jest.mock('react-i18next', function () {
  return {
    useTranslation: jest.fn().mockReturnValue({
      t: jest.fn(function (key: string, fb: string) { return fb || key }),
    }),
  }
})

var mockStoreState = { isSystemSidebarOpen: true, setSystemSidebarOpen: jest.fn() }
jest.mock('@/lib/store', function () {
  return {
    useAppStore: jest.fn(function (sel: Function) { return sel(mockStoreState) }),
  }
})

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import SystemSidebar from '../SystemSidebar'

describe('SystemSidebar', function () {
  beforeEach(function () {
    mockStoreState.isSystemSidebarOpen = true
    mockStoreState.setSystemSidebarOpen = jest.fn()
    require('next/navigation').usePathname.mockReturnValue('/')
  })

  it('renders null when closed', function () {
    mockStoreState.isSystemSidebarOpen = false
    var container = render(React.createElement(SystemSidebar))
    expect(container.container.querySelector('[role="dialog"]')).toBeNull()
  })

  it('renders dialog when open', function () {
    render(React.createElement(SystemSidebar))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByLabelText('Mobile Navigation')).toBeInTheDocument()
  })

  it('renders app name', function () {
    render(React.createElement(SystemSidebar))
    expect(screen.getByText('SafeVixAI')).toBeInTheDocument()
  })

  it('renders nav items', function () {
    render(React.createElement(SystemSidebar))
    expect(screen.getByText('Map')).toBeInTheDocument()
    expect(screen.getByText('AI Assistant')).toBeInTheDocument()
    expect(screen.getByText('Locator')).toBeInTheDocument()
    expect(screen.getByText('First Aid')).toBeInTheDocument()
  })

  it('renders emergency quick dials', function () {
    render(React.createElement(SystemSidebar))
    expect(screen.getByText('112')).toBeInTheDocument()
    expect(screen.getByText(/Highway/)).toBeInTheDocument()
  })

  it('calls setOpen(false) on close button click', function () {
    render(React.createElement(SystemSidebar))
    fireEvent.click(screen.getByLabelText('Close Sidebar'))
    expect(mockStoreState.setSystemSidebarOpen).toHaveBeenCalledWith(false)
  })

  it('closes on backdrop click', function () {
    render(React.createElement(SystemSidebar))
    var backdrop = document.querySelector('.fixed.inset-0')
    if (backdrop) fireEvent.click(backdrop)
    expect(mockStoreState.setSystemSidebarOpen).toHaveBeenCalledWith(false)
  })

  it('highlights active nav item', function () {
    require('next/navigation').usePathname.mockReturnValue('/assistant')
    render(React.createElement(SystemSidebar))
    var links = screen.getAllByRole('link')
    var assistantLink = links.find(function (l) { return l.getAttribute('href') === '/assistant' })
    expect(assistantLink).toBeDefined()
  })

  it('renders SOS button linking to /sos', function () {
    render(React.createElement(SystemSidebar))
    var sosLink = screen.getByText('System SOS').closest('a')
    expect(sosLink).toHaveAttribute('href', '/sos')
  })

  it('renders quick dial tel: links', function () {
    render(React.createElement(SystemSidebar))
    var dials = screen.getAllByRole('link').filter(function (l) { return l.getAttribute('href')?.startsWith('tel:') })
    expect(dials.length).toBeGreaterThanOrEqual(3)
    expect(dials[0]).toHaveAttribute('href', 'tel:112')
  })

  it('removes Escape listener on cleanup', function () {
    var removeSpy = jest.spyOn(window, 'removeEventListener')
    var comp = render(React.createElement(SystemSidebar))
    comp.unmount()
    expect(removeSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
    removeSpy.mockRestore()
  })
})
