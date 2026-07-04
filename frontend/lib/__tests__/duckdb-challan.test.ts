var mockDuckDBModule = { selectBundle: jest.fn(), ConsoleLogger: jest.fn(), AsyncDuckDB: jest.fn() };

jest.mock('../client-logger', function() { return { logClientError: jest.fn(), logClientWarning: jest.fn() } })

// Helper to create fresh mock instances — prevents once-queue pollution across tests
function createFreshMocks() {
  return {
    conn: { query: jest.fn(), close: jest.fn().mockResolvedValue(undefined) },
    db: { connect: jest.fn(), instantiate: jest.fn(), registerFileText: jest.fn() },
  };
}
var mocks = createFreshMocks();

jest.mock('@duckdb/duckdb-wasm', function() { return mockDuckDBModule });

// JSDOM lacks Worker and URL.createObjectURL — provide polyfills for DuckDB instantiation path
if (typeof URL.createObjectURL !== 'function') {
  (globalThis as any).URL.createObjectURL = function() { return 'blob:http://localhost/mock-' + Date.now(); };
  (globalThis as any).URL.revokeObjectURL = function() {};
}
var MockWorker = function MockWorker(this: any, _url: string) {
  this.postMessage = jest.fn();
  this.terminate = jest.fn();
  this.addEventListener = jest.fn();
  this.removeEventListener = jest.fn();
} as unknown as { new(url: string): Worker };
if (typeof Worker === 'undefined' || (globalThis as any).Worker.toString().includes('[native code]')) {
  (globalThis as any).Worker = MockWorker;
}

import { initOfflineChallanDB, calculateOfflineChallan, __testResetDbInstance } from '../duckdb-challan';

var VIOLATIONS_CSV = 'violation_code,section,description,base_fine,base_fine_2w,base_fine_4w,repeat_fine,repeat_fine_2w,repeat_fine_4w\n' +
  'MVA_185,185,Drunken driving,10000,8000,12000,15000,12000,18000\n' +
  'MVA_183,183(1),Over-speeding,2000,1500,2500,4000,3000,5000\n';
var OVERRIDES_CSV = 'violation_code,state_code,vehicle_class,base_fine,repeat_fine,section,description\n' +
  'MVA_185,TN,LMV,15000,20000,185-A,Enhanced TN fine\n' +
  'MVA_183,KA,,3000,6000,183(2),KA override\n';

describe('duckdb-challan', function() {
  beforeEach(function() {
    jest.clearAllMocks();

    // Reset module-level dbInstance to bypass cache across tests
    __testResetDbInstance();

    // Reset mocks to prevent once-queue pollution
    mocks = createFreshMocks();

    global.fetch = jest.fn();
    mockDuckDBModule.selectBundle.mockResolvedValue({
      mainModule: '/duckdb/test.wasm',
      mainWorker: '/duckdb/test.worker.js',
      pthreadWorker: '/duckdb/test.worker.js',
    });
    mockDuckDBModule.ConsoleLogger.mockReturnValue({ log: jest.fn() });
    mockDuckDBModule.AsyncDuckDB.mockImplementation(function() {
      mocks.db.connect.mockResolvedValue(mocks.conn);
      mocks.conn.query.mockResolvedValue([]);   // default: empty result
      mocks.db.instantiate = jest.fn().mockResolvedValue(undefined);
      return mocks.db;
    });
  });

  describe('parseCSV (internal — tested via calculateOfflineChallan fallback)', function() {
    it('parses CSV and finds correct violation with DuckDB failed', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return VIOLATIONS_CSV } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return OVERRIDES_CSV } });

      var result = await calculateOfflineChallan('MVA_185', '4W', false, 'TN');

      expect(result).toBeTruthy();
      expect(result!.section).toBe('185-A');
      expect(result!.description).toBe('Enhanced TN fine');
    });

    it('falls back to base fine when no state override', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return VIOLATIONS_CSV } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,state_code,vehicle_class,base_fine\n' } });

      var result = await calculateOfflineChallan('MVA_183', '2W', false, 'MH');

      expect(result).toBeTruthy();
      expect(result!.base_fine).toBe(1500);
    });
  });

  describe('initOfflineChallanDB', function() {
    it('returns true when DuckDB initializes successfully', async function() {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true, text: async function() { return 'worker script'; } });
      var ok = await initOfflineChallanDB();
      expect(ok).toBe(true);
    });

    it('returns false when DuckDB init throws', async function() {
      mockDuckDBModule.selectBundle.mockRejectedValue(new Error('bundle failed'));
      var ok = await initOfflineChallanDB();
      expect(ok).toBe(false);
    });
  });

  describe('DuckDB wasm success path', function() {
    function workerFetch() {
      return { ok: true, text: async function() { return 'worker script'; } };
    }

    it('returns correct result when DuckDB succeeds with existing tables', async function() {
      mocks.conn.query
        .mockResolvedValueOnce({}) // SELECT count(*) FROM violations
        .mockResolvedValueOnce({}) // SELECT count(*) FROM state_overrides
        .mockResolvedValueOnce({   // Main SQL query
          toArray: function() {
            return [{
              toJSON: function() {
                return { base_fine: 15000, repeat_fine: 20000, section: '185-A', description: 'Enhanced TN fine' };
              },
            }];
          },
        });
      (global.fetch as jest.Mock).mockResolvedValue(workerFetch());

      var result = await calculateOfflineChallan('MVA_185', '4W', false, 'TN');
      expect(result).toBeTruthy();
      expect(result!.section).toBe('185-A');
      expect(result!.description).toBe('Enhanced TN fine');
      expect(result!.base_fine).toBe(15000);
      expect(result!.repeat_fine).toBe(20000);
    });

    it('creates tables when check fails and then returns query result', async function() {
      // Sync throw triggers the try-catch for table creation path
      mocks.conn.query
        .mockImplementationOnce(function() { throw new Error('not found'); })
        .mockImplementationOnce(function() { return Promise.resolve({}); })
        .mockImplementationOnce(function() {
          return Promise.resolve({
            toArray: function() {
              return [{
                toJSON: function() {
                  return { base_fine: 1000, repeat_fine: 2000, section: '183(1)', description: 'Over-speeding' };
                },
              }];
            },
          });
        });
      var csvText = 'violation_code,section,description,base_fine\nMVA_183,183(1),Over-speeding,1000';
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce(workerFetch())           // getDuckDB worker
        .mockResolvedValueOnce({ ok: true, text: async function() { return csvText; } })  // violations.csv
        .mockResolvedValueOnce({ ok: true, text: async function() { return ''; } });      // state_overrides.csv

      var result = await calculateOfflineChallan('MVA_183', '2W', false, 'KA');
      expect(result).toBeTruthy();
      expect(result!.section).toBe('183(1)');
      expect(result!.description).toBe('Over-speeding');
      expect(result!.base_fine).toBe(1000);
    });

    it('falls to CSV when DuckDB query returns no rows', async function() {
      mocks.conn.query
        .mockResolvedValueOnce({})                         // check violations
        .mockResolvedValueOnce({})                         // check overrides
        .mockResolvedValueOnce({ toArray: function() { return []; } });  // empty result
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce(workerFetch())           // getDuckDB worker
        .mockResolvedValueOnce({ ok: true, text: async function() { return VIOLATIONS_CSV; } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return OVERRIDES_CSV; } });

      var result = await calculateOfflineChallan('MVA_185', '4W', false, 'TN');
      expect(result).toBeTruthy();
      expect(result!.section).toBe('185-A');
      expect(result!.description).toBe('Enhanced TN fine');
      expect(result!.base_fine).toBe(15000);
    });
  });

  describe('in-memory dictionary fallback (last resort)', function() {
    it('returns correct values for MVA_185 from dictionary', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,section,description,base_fine\n' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,state_code\n' } });

      var result = await calculateOfflineChallan('185', '4W', false);

      expect(result).toBeTruthy();
      expect(result!.base_fine).toBe(10000);
      expect(result!.repeat_fine).toBe(15000);
      expect(result!.description).toContain('Drunken driving');
    });

    it('returns 0/null for unknown violation code', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,section,description,base_fine\n' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,state_code\n' } });

      var result = await calculateOfflineChallan('UNKNOWN_CODE', '4W', false);

      expect(result).toBeTruthy();
      expect(result!.base_fine).toBe(0);
      expect(result!.description).toBe('Violation not found');
    });

    it('uses vehicle-specific fine for LMV on speed violation', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,section,description,base_fine\n' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,state_code\n' } });

      var result = await calculateOfflineChallan('183', '4W', false);

      expect(result).toBeTruthy();
      expect(result!.base_fine).toBe(1000);
    });
  });

  describe('error handling', function() {
    it('falls back to in-memory dict on network error', async function() {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('net error'));
      var result = await calculateOfflineChallan('185', '4W', false);
      expect(result).toBeTruthy();
      expect(result!.description).toContain('Drunken driving');
    });

    it('throws error when CSV fetch returns !ok status', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: false, text: async function() { return '' } })
        .mockResolvedValueOnce({ ok: false, text: async function() { return '' } });

      var result = await calculateOfflineChallan('185', '4W', false);
      expect(result).toBeTruthy();
      expect(result!.description).toContain('Drunken driving');
    });
  });

  describe('parseCSV edge cases', function() {
    it('handles empty input', async function() {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return '' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return '' } });

      var result = await calculateOfflineChallan('MVA_185', '4W', false);
      expect(result).toBeTruthy();
      expect(result!.description).toBe('Violation not found');
    });

    it('parses quoted CSV fields correctly', async function() {
      var quotedCSV = 'violation_code,section,description,base_fine\n"185","Section 185","Drunken, driving",10000\n';
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'not-a-wasm' } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return quotedCSV; } })
        .mockResolvedValueOnce({ ok: true, text: async function() { return 'violation_code,state_code\n' } });

      var result = await calculateOfflineChallan('185', '4W', false);
      expect(result).toBeTruthy();
      expect(result!.description).toBe('Drunken, driving');
      expect(result!.section).toBe('Section 185');
      expect(result!.base_fine).toBe(10000);
    });
  });
});
