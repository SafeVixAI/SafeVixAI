import React from 'react';
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

jest.mock('../lib/store', () => {
  const actual = jest.requireActual('../lib/store');
  return {
    ...actual,
    useAppStore: (selector: any) => {
      const state = { isAuthenticated: true };
      // If the selector requests isAuthenticated, return true
      if (selector.toString().includes('isAuthenticated')) return true;
      return actual.useAppStore(selector);
    }
  }
})


describe('Home Page structural verification', function() {
  it('renders the SafeVixAI app shell', async function() {
    render(<Page />)
    expect(await screen.findByPlaceholderText(/Ask Maps or Search/i)).toBeInTheDocument()
    expect((await screen.findAllByText(/Enable Location/i)).length).toBeGreaterThan(0)
  })

  it('renders the emergency protocol surface', async function() {
    render(<Page />)
    expect(await screen.findByText(/Emergency Protocols/i)).toBeInTheDocument()
    expect((await screen.findAllByTitle(/Geolocation not supported/i)).length).toBeGreaterThan(0)
  })

  it('renders with proper heading structure', async function() {
    render(<Page />)
    expect(await screen.findByRole('heading', { level: 1 })).toBeInTheDocument()
  })
})
