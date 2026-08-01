import React from 'react';
import { render } from '@testing-library/react';
import DashboardContent from '../DashboardContent';

// Mock the child components
jest.mock('../TopSearch', () => function MockTopSearch() { return <div data-testid="top-search" />; });
jest.mock('../FloatingSidebarControls', () => function MockFloatingSidebarControls() { return <div data-testid="floating-sidebar" />; });
jest.mock('../RecentAlertsOverlay', () => function MockRecentAlertsOverlay() { return <div data-testid="recent-alerts" />; });
jest.mock('../DashboardMapBootstrap', () => function MockDashboardMapBootstrap() { return <div data-testid="dashboard-map-bootstrap" />; });

describe('DashboardContent', () => {
  it('renders all components without crashing', () => {
    const { getByTestId } = render(<DashboardContent />);
    
    expect(getByTestId('top-search')).toBeInTheDocument();
    expect(getByTestId('floating-sidebar')).toBeInTheDocument();
    expect(getByTestId('recent-alerts')).toBeInTheDocument();
    expect(getByTestId('dashboard-map-bootstrap')).toBeInTheDocument();
  });
});
