import { buildGoogleMapsRasterStyle, buildGoogleMapsSatelliteStyle, buildStyleCandidates } from '../map-styles';

describe('buildGoogleMapsRasterStyle', function() {
  it('returns light style', function() {
    var result = buildGoogleMapsRasterStyle(false);
    expect(result.name).toContain('Google Maps');
    expect(result.layers[0].paint['background-color']).toBe('#f0f4f8');
    expect(result.layers[1].paint).toEqual({});
  });
  it('returns dark style', function() {
    var result = buildGoogleMapsRasterStyle(true);
    expect(result.layers[0].paint['background-color']).toBe('#050a14');
    expect(result.layers[1].paint['raster-brightness-max']).toBe(0.8);
  });
});

describe('buildGoogleMapsSatelliteStyle', function() {
  it('returns satellite style', function() {
    var result = buildGoogleMapsSatelliteStyle();
    expect(result.name).toContain('Satellite');
    expect(result.layers[0].id).toBe('svai-google-satellite-layer');
  });
});

describe('buildStyleCandidates', function() {
  var originalMapStyle = process.env.NEXT_PUBLIC_MAP_STYLE_URL;
  var originalLight = process.env.NEXT_PUBLIC_MAPTILER_STYLE_LIGHT;
  var originalDark = process.env.NEXT_PUBLIC_MAPTILER_STYLE_DARK;

  afterEach(function() {
    process.env.NEXT_PUBLIC_MAP_STYLE_URL = originalMapStyle;
    process.env.NEXT_PUBLIC_MAPTILER_STYLE_LIGHT = originalLight;
    process.env.NEXT_PUBLIC_MAPTILER_STYLE_DARK = originalDark;
  });

  it('returns 3 candidates (light, non-satellite)', function() {
    var result = buildStyleCandidates('light', false);
    expect(result).toHaveLength(3);
    expect(result[0].kind).toBe('google-maps');
    expect(result[0].label).toBe('Google Maps (India)');
    expect(result[0].style).toBeDefined();
    expect(result[1].kind).toBe('maptiler-vector');
    expect(result[2].kind).toBe('openfreemap');
  });

  it('returns 3 candidates (dark, satellite)', function() {
    var result = buildStyleCandidates('dark', true);
    expect(result).toHaveLength(3);
    expect(result[0].label).toBe('Google Maps (Satellite)');
    expect(result[1].label).toBe('MapTiler (Satellite)');
  });

  it('uses default maptiler styles when env not set', function() {
    delete process.env.NEXT_PUBLIC_MAPTILER_STYLE_LIGHT;
    delete process.env.NEXT_PUBLIC_MAPTILER_STYLE_DARK;
    var result = buildStyleCandidates('dark', false);
    expect(result[1].style).toContain('dataviz-dark');
  });

});
