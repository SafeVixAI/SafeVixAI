// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('axios', () => ({
  __esModule: true,
  default: (() => {
    const post = jest.fn();
    const get = jest.fn();
    const requestUse = jest.fn();
    const responseUse = jest.fn();
    return {
      __post: post,
      __get: get,
      __requestUse: requestUse,
      __responseUse: responseUse,
      create: jest.fn(function() {
        return {
          get,
          post,
          interceptors: {
            request: { use: requestUse },
            response: { use: responseUse },
          },
        }
      }),
    }
  })(),
}));

jest.mock('../../lib/public-env', () => ({
  PUBLIC_API_BASE_URL: 'https://api.safevix.test',
  PUBLIC_CHATBOT_BASE_URL: 'https://chat.safevix.test',
}));

jest.mock('../../lib/reverse-geocode', () => ({
  getAddressFromGPS: jest.fn(),
}));

import { triggerSos } from '../../lib/api';

const axiosMock = jest.requireMock('axios').default;

describe('SOS API helper', function() {
  beforeEach(function() {
    jest.clearAllMocks();
  });

  it('dispatches SOS with an authenticated-safe POST request', async function() {
    axiosMock.__post.mockResolvedValueOnce({
      data: {
        services: [],
        count: 0,
        radius_used: 0,
        source: 'api',
        numbers: {
          universal: { service: '112', coverage: 'India' },
        },
      },
    });

    const response = await triggerSos({ lat: 13.0827, lon: 80.2707 });

    expect(axiosMock.__post).toHaveBeenCalledWith('/api/v1/emergency/sos', null, {
      params: { lat: 13.0827, lon: 80.2707 },
    });
    expect(response.numbers.universal.service).toBe('112');
  });
});



