import { render, screen } from '@testing-library/react'
import React from 'react'
import { MunicipalityCard } from '../guide/MunicipalityCard'

jest.mock('next/link', function() {
  return function MockLink(props) {
    return React.createElement('a', Object.assign({}, props, { 'data-testid': 'next-link' }), props.children)
  }
})

describe('MunicipalityCard', function () {
  const baseMuni = {
    slug: 'chennai',
    name: 'Chennai',
    shortName: 'Chennai',
    city: 'Chennai',
    stateCode: 'TN',
    municipalityType: 'Corporation',
    wardCount: 200,
    population: 12000000,
    helplinePhone: '1913',
    centroidLat: 13.08,
    centroidLon: 80.27,
    distanceKm: 0,
  }

  it('renders municipality name', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    expect(screen.getByText('Chennai')).toBeInTheDocument()
  })

  it('renders helpline phone', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    expect(screen.getByText('1913')).toBeInTheDocument()
  })

  it('renders city and state code', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    expect(screen.getByText('Chennai, TN')).toBeInTheDocument()
  })

  it('formats large population in Crores', function () {
    render(React.createElement(MunicipalityCard, { municipality: Object.assign({}, baseMuni, { population: 12000000 }) }))
    expect(screen.getByText('1.2 Cr')).toBeInTheDocument()
  })

  it('formats population in Lakhs', function () {
    render(React.createElement(MunicipalityCard, { municipality: Object.assign({}, baseMuni, { population: 500000 }) }))
    expect(screen.getByText('5.0 L')).toBeInTheDocument()
  })

  it('formats population in Thousands', function () {
    render(React.createElement(MunicipalityCard, { municipality: Object.assign({}, baseMuni, { population: 5000 }) }))
    expect(screen.getByText('5K')).toBeInTheDocument()
  })

  it('renders dash for null population', function () {
    const muni = Object.assign({}, baseMuni, { population: null })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    expect(screen.queryByText('Cr')).not.toBeInTheDocument()
    expect(screen.queryByText('L')).not.toBeInTheDocument()
    expect(screen.queryByText('K')).not.toBeInTheDocument()
  })

  it('renders ward count', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    expect(screen.getByText('200 wards')).toBeInTheDocument()
  })

  it('does not render ward count when zero', function () {
    const muni = Object.assign({}, baseMuni, { wardCount: 0 })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    expect(screen.queryByText('wards')).not.toBeInTheDocument()
  })

  it('renders distance when not null', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    expect(screen.getByText('0.0 km')).toBeInTheDocument()
  })

  it('does not render distance when null', function () {
    const muni = Object.assign({}, baseMuni, { distanceKm: null })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    expect(screen.queryByText('km')).not.toBeInTheDocument()
  })

  it('does not render helpline when missing', function () {
    const muni = Object.assign({}, baseMuni, { helplinePhone: null })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    expect(screen.queryByText('1913')).not.toBeInTheDocument()
  })

  it('renders Corp badge for municipal_corporation', function () {
    const muni = Object.assign({}, baseMuni, { municipalityType: 'municipal_corporation' })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    expect(screen.getByText('Corp')).toBeInTheDocument()
  })

  it('renders Muni badge for municipality', function () {
    const muni = Object.assign({}, baseMuni, { municipalityType: 'municipality' })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    expect(screen.getByText('Muni')).toBeInTheDocument()
  })

  it('has correct Link href to /guide/{slug}', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    const link = screen.getByTestId('next-link')
    expect(link.getAttribute('href')).toBe('/guide/chennai')
  })

  it('applies known state color class', function () {
    render(React.createElement(MunicipalityCard, { municipality: baseMuni }))
    const badge = screen.getByText('TN')
    expect(badge.className).toMatch(/emerald/)
  })

  it('applies fallback state color for unknown state', function () {
    const muni = Object.assign({}, baseMuni, { stateCode: 'XX' })
    render(React.createElement(MunicipalityCard, { municipality: muni }))
    const badge = screen.getByText('XX')
    expect(badge.className).toMatch(/brand/)
  })
})
