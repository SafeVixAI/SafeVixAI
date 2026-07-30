// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

jest.mock('@gsap/react', function() {
  return { useGSAP: jest.fn() };
});

jest.mock('@/lib/gsap', function() {
  return { gsap: { fromTo: jest.fn(), to: jest.fn() } };
});

jest.mock('next/dynamic', function() {
  return function() {
    return function MockDynamic() { return React.createElement('div', null, 'Camera'); };
  };
});

jest.mock('@/lib/analytics', function() {
  return { track: { firstAidViewed: jest.fn(), emergencyCallMade: jest.fn() } };
});

jest.mock('@/lib/store', function() {
  return { useAppStore: jest.fn(function(s) { return typeof s === 'function' ? {} : {}; }) };
});

jest.mock('react-i18next', function() {
  return {
    useTranslation: function() {
      return {
        t: function(key: string, fb?: unknown) {
          if (fb && typeof fb === 'object' && 'defaultValue' in fb) return (fb as Record<string, string>).defaultValue;
          return (fb as string) || key;
        },
        i18n: { language: 'en' },
      };
    },
  };
});

const GUIDE_DATA = {
  cpr: { id: 'cpr', title: 'CPR', subtitle: 'Chest compressions', accent: 'red', icon: 'HeartPulse', iconType: 'filled' as const, steps: ['Check responsiveness', 'Call 112', 'Start compressions'] },
  choking: { id: 'choking', title: 'Choking', subtitle: 'Airway obstruction', accent: 'orange', icon: 'Activity', iconType: 'outlined' as const, steps: ['Encourage coughing', 'Back blows'] },
  burns: { id: 'burns', title: 'Burns', subtitle: 'Thermal injury', accent: 'yellow', icon: 'Flame', iconType: 'filled' as const, steps: ['Cool under running water'] },
  fractures: { id: 'fractures', title: 'Fractures', subtitle: 'Bone injury', accent: 'blue', icon: 'Bone', iconType: 'outlined' as const, steps: ['Immobilize the area'] },
  bleeding: { id: 'bleeding', title: 'Bleeding', subtitle: 'Severe bleeding', accent: 'red', icon: 'Droplets', iconType: 'filled' as const, steps: ['Apply pressure', 'Elevate'] },
};

function renderFirstAid() {
  const FirstAidClient = require('../first-aid/FirstAidClient').FirstAidClient;
  return render(React.createElement(FirstAidClient, { guides: GUIDE_DATA }));
}

describe('FirstAidClient', function() {
  it('renders HUD title and emergency guide label', function() {
    renderFirstAid();
    expect(screen.getByText('First Aid HUD')).toBeTruthy();
    expect(screen.getByText('Emergency Guide')).toBeTruthy();
  });

  it('renders search input in normal mode', function() {
    renderFirstAid();
    expect(screen.getByPlaceholderText('Search emergency protocol...')).toBeTruthy();
  });

  it('renders protocol cards', function() {
    renderFirstAid();
    expect(screen.getByText('CPR')).toBeTruthy();
    expect(screen.getByText('Choking')).toBeTruthy();
    expect(screen.getByText('Burns')).toBeTruthy();
    expect(screen.getByText('Fractures')).toBeTruthy();
  });

  it('filters guides by search query', function() {
    renderFirstAid();
    const searchInput = screen.getByPlaceholderText('Search emergency protocol...');
    fireEvent.change(searchInput, { target: { value: 'cpr' } });
    expect(screen.getByText('CPR')).toBeTruthy();
    expect(screen.queryByText('Burns')).toBeNull();
  });

  it('shows empty state when no guides match', function() {
    renderFirstAid();
    const searchInput = screen.getByPlaceholderText('Search emergency protocol...');
    fireEvent.change(searchInput, { target: { value: 'zzzzzxyz' } });
    expect(screen.getByText(/No protocols match/)).toBeTruthy();
  });

  it('shows Start Guide buttons on cards', function() {
    renderFirstAid();
    const startButtons = screen.getAllByText('Start Guide');
    expect(startButtons.length).toBeGreaterThanOrEqual(4);
  });

  it('opens guide modal on card click', function() {
    renderFirstAid();
    fireEvent.click(screen.getByText('CPR'));
    expect(screen.getByText('Live Protocol')).toBeTruthy();
    expect(screen.getByText('Instructions')).toBeTruthy();
    expect(screen.getByText('Check responsiveness')).toBeTruthy();
  });

  it('closes guide modal on Escape key', function() {
    renderFirstAid();
    fireEvent.click(screen.getByText('CPR'));
    expect(screen.getByText('Live Protocol')).toBeTruthy();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByText('Live Protocol')).toBeNull();
  });

  it('marks steps as completed on click', function() {
    renderFirstAid();
    fireEvent.click(screen.getByText('CPR'));
    fireEvent.click(screen.getByText('Check responsiveness'));
    expect(screen.getByLabelText('Step 1: Check responsiveness')).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows normal mode toggle and switches to emergency mode', function() {
    renderFirstAid();
    const modeBtn = screen.getByText('Normal Mode');
    expect(modeBtn).toBeTruthy();
    fireEvent.click(modeBtn);
    expect(screen.getByText('Emergency Active')).toBeTruthy();
  });

  it('shows Invoke Scan button and activates camera on click', function() {
    renderFirstAid();
    expect(screen.getByText('Invoke Full Scan')).toBeTruthy();
    fireEvent.click(screen.getByText('Invoke Full Scan'));
    expect(screen.getByText('Camera')).toBeTruthy();
  });

  it('shows Call 112 button in guide modal', function() {
    renderFirstAid();
    fireEvent.click(screen.getByText('CPR'));
    const call112Buttons = screen.getAllByText('Call 112');
    expect(call112Buttons.length).toBeGreaterThanOrEqual(1);
  });

  it('shows Terminate Protocol and Emergency Hotline in modal footer', function() {
    renderFirstAid();
    fireEvent.click(screen.getByText('CPR'));
    expect(screen.getByText('Terminate Protocol')).toBeTruthy();
    expect(screen.getByText('Emergency Hotline')).toBeTruthy();
  });
});
