import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Page from '../app/page'

jest.mock('next/link', () => {
  return ({ children }: { children: React.ReactNode }) => {
    return children
  }
})

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

describe('Home Page structural verification', function() {
  it('renders the SafeVixAI app shell', function() {
    render(<Page />)
    expect(screen.getByPlaceholderText(/Ask Maps or Search/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Enable Location/i).length).toBeGreaterThan(0)
  })

  it('renders the emergency protocol surface', function() {
    render(<Page />)
    expect(screen.getByText(/Emergency Protocols/i)).toBeInTheDocument()
    expect(screen.getAllByTitle(/Geolocation not supported/i).length).toBeGreaterThan(0)
  })

  it('renders with proper heading structure', function() {
    render(<Page />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })
})
