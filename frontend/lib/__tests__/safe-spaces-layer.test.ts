import { addSafeSpacesLayer } from '../safe-spaces-layer';

jest.mock('../public-env', () => ({
  PUBLIC_API_BASE_URL: 'https://api.safevix.test',
}));

describe('addSafeSpacesLayer', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  it('loads backend places response and adds a map layer', async function() {
    const fetchMock = global.fetch as jest.Mock;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        places: [
          {
            name: 'City Hospital',
            type: 'hospital',
            lat: 13.0827,
            lon: 80.2707,
            phone: '108',
          },
        ],
        count: 1,
        source: 'openstreetmap',
      }),
    });

    const map = {
      getSource: jest.fn(() => undefined),
      addSource: jest.fn(),
      addLayer: jest.fn(),
    };

    await addSafeSpacesLayer(map as any, 13.0827, 80.2707);

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.safevix.test/api/v1/emergency/safe-spaces?lat=13.0827&lon=80.2707&radius=1000'
    );
    expect(map.addSource).toHaveBeenCalledWith('safe-spaces', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [80.2707, 13.0827] },
            properties: { name: 'City Hospital', type: 'hospital', phone: '108' },
          },
        ],
      },
    });
    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'safe-spaces-circles' }));
    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'safe-spaces-labels' }));
  });

  it('throws when API returns non-ok status (line 42)', async function() {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    const map = {
      getSource: jest.fn(() => undefined),
      addSource: jest.fn(),
      addLayer: jest.fn(),
    };

    await expect(addSafeSpacesLayer(map as any, 10, 20)).rejects.toThrow('Safe spaces request failed with 500');
  });

  it('updates existing source via setData when source already exists (lines 54-58)', async function() {
    const setData = jest.fn();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => [
        { name: 'Police Station', type: 'police', lat: 13.0, lon: 80.0, phone: '100' },
      ],
    });

    const map = {
      getSource: jest.fn(() => ({ setData } as any)),
      addSource: jest.fn(),
      addLayer: jest.fn(),
    };

    await addSafeSpacesLayer(map as any, 13.0, 80.0);

    expect(setData).toHaveBeenCalledWith({
      type: 'FeatureCollection',
      features: expect.arrayContaining([
        expect.objectContaining({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [80.0, 13.0] },
        }),
      ]),
    });
    expect(map.addSource).not.toHaveBeenCalled();
    expect(map.addLayer).not.toHaveBeenCalled();
  });

  it('handles array response format from backend', async function() {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => [
        { name: 'Fire Station', type: 'fire', lat: 14.0, lon: 78.0, phone: '101' },
      ],
    });

    const map = {
      getSource: jest.fn(() => undefined),
      addSource: jest.fn(),
      addLayer: jest.fn(),
    };

    await addSafeSpacesLayer(map as any, 14.0, 78.0);

    expect(map.addSource).toHaveBeenCalledWith('safe-spaces', expect.objectContaining({
      data: expect.objectContaining({
        features: expect.arrayContaining([
          expect.objectContaining({
            geometry: { type: 'Point', coordinates: [78.0, 14.0] },
          }),
        ]),
      }),
    }));
  });
});



