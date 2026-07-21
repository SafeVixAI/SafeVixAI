// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import type { AsyncDuckDB } from '@duckdb/duckdb-wasm';
import { OFFLINE_CHALLAN_LOOKUP_DELAY_MS } from './safety-constants';
import { logClientError, logClientWarning } from './client-logger';

let dbInstance: AsyncDuckDB | null = null;

// Clean CSV parser for Javascript fallback
function parseCSV(text: string): Record<string, string>[] {
  const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
  if (lines.length === 0) return [];
  
  const splitCSVLine = (line: string) => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  const headers = splitCSVLine(lines[0]);
  return lines.slice(1).map(line => {
    const values = splitCSVLine(line);
    const row: Record<string, string> = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    return row;
  });
}

// Lazy-loads DuckDB-Wasm and overrides CORS Worker restriction using Blobs
async function getDuckDB() {
  if (dbInstance) return dbInstance;
  /* istanbul ignore next */if (typeof window === 'undefined') return null;

  const duckdb = await import('@duckdb/duckdb-wasm');
  
  const DUCKDB_BUNDLES = {
    mvp: {
      mainModule: '/duckdb/duckdb-mvp.wasm',
      mainWorker: '/duckdb/duckdb-browser-mvp.worker.js',
    },
    eh: {
      mainModule: '/duckdb/duckdb-eh.wasm',
      mainWorker: '/duckdb/duckdb-browser-eh.worker.js',
    }
  };

  const bundle = await duckdb.selectBundle(DUCKDB_BUNDLES);
  
  // CORS workaround for Web Worker script
  const workerResponse = await fetch(bundle.mainWorker!);
  const workerBlob = new Blob([await workerResponse.text()], { type: 'application/javascript' });
  const workerUrl = URL.createObjectURL(workerBlob);
  const worker = new Worker(workerUrl);
  
  const logger = new duckdb.ConsoleLogger();
  const db = new duckdb.AsyncDuckDB(logger, worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  dbInstance = db;
  return db;
}

async function calculateWithDuckDB(
  violationCode: string, 
  vehicleClass: string, 
  isRepeat: boolean, 
  stateCode: string
) {
  /* istanbul ignore next */if (typeof window === 'undefined') return null;
  
  // Sanitization
  const cleanViolation = violationCode.replace(/[^a-zA-Z0-9_]/g, '');
  const cleanVehicle = vehicleClass.replace(/[^a-zA-Z0-9_]/g, '');
  const cleanState = stateCode.replace(/[^a-zA-Z]/g, '').toUpperCase();

  const db = await getDuckDB();
  if (!db) return null;
  const conn = await db.connect();
  
  try {
    let tablesLoaded = false;
    try {
      await conn.query('SELECT count(*) FROM violations LIMIT 1');
      await conn.query('SELECT count(*) FROM state_overrides LIMIT 1');
      tablesLoaded = true;
    } catch {
      // Tables do not exist, need to create them
    }
    
    if (!tablesLoaded) {
      const violationsText = await fetch('/offline-data/violations.csv').then(r => r.text());
      const overridesText = await fetch('/offline-data/state_overrides.csv').then(r => r.text());
      
      await db.registerFileText('violations.csv', violationsText);
      await db.registerFileText('state_overrides.csv', overridesText);
      
      await conn.query(`
        CREATE TABLE violations AS SELECT * FROM read_csv_auto('violations.csv');
        CREATE TABLE state_overrides AS SELECT * FROM read_csv_auto('state_overrides.csv');
      `);
    }
    
    const normalizedClassMap: Record<string, string> = {
      '4W': 'LMV',
      '2W': '2W',
      'HTV': 'HMV',
      'BUS': 'BUS'
    };
    const normClass = normalizedClassMap[cleanVehicle] || cleanVehicle;
    
    const possibleOverrideCodes = [
      cleanViolation,
      `${cleanViolation}${normClass}`,
      !isRepeat ? `${cleanViolation}FIRST` : `${cleanViolation}REPEAT`
    ];
    
    const sql = `
      SELECT 
        v.violation_code,
        COALESCE(o.section, v.section) AS section,
        COALESCE(o.description, v.description) AS description,
        COALESCE(CAST(o.base_fine AS INTEGER), 
                 CASE '${cleanVehicle}' 
                   WHEN '2W' THEN COALESCE(CAST(v.base_fine_2w AS INTEGER), CAST(v.base_fine AS INTEGER))
                   WHEN '4W' THEN COALESCE(CAST(v.base_fine_4w AS INTEGER), CAST(v.base_fine AS INTEGER))
                   WHEN 'HTV' THEN COALESCE(CAST(v.base_fine_htv AS INTEGER), CAST(v.base_fine AS INTEGER))
                   WHEN 'BUS' THEN COALESCE(CAST(v.base_fine_bus AS INTEGER), CAST(v.base_fine AS INTEGER))
                   ELSE CAST(v.base_fine AS INTEGER)
                 END) AS base_fine,
        COALESCE(CAST(o.repeat_fine AS INTEGER),
                 CASE '${cleanVehicle}' 
                   WHEN '2W' THEN COALESCE(CAST(v.repeat_fine_2w AS INTEGER), CAST(v.repeat_fine AS INTEGER))
                   WHEN '4W' THEN COALESCE(CAST(v.repeat_fine_4w AS INTEGER), CAST(v.repeat_fine AS INTEGER))
                   WHEN 'HTV' THEN COALESCE(CAST(v.repeat_fine_htv AS INTEGER), CAST(v.repeat_fine AS INTEGER))
                   WHEN 'BUS' THEN COALESCE(CAST(v.repeat_fine_bus AS INTEGER), CAST(v.repeat_fine AS INTEGER))
                   ELSE CAST(v.repeat_fine AS INTEGER)
                 END) AS repeat_fine
      FROM violations v
      LEFT JOIN state_overrides o 
        ON v.violation_code = o.violation_code 
        AND o.state_code = '${cleanState}'
        AND (o.vehicle_class = '${normClass}' OR o.vehicle_class IS NULL OR o.vehicle_class = '')
      WHERE v.violation_code = '${cleanViolation}' 
         OR v.violation_code IN (${possibleOverrideCodes.map(c => `'${c}'`).join(',')})
      LIMIT 1;
    `;
    
    const queryResult = await conn.query(sql);
    const rows = queryResult.toArray();
    
    if (rows.length > 0) {
      const row = rows[0].toJSON();
      return {
        base_fine: Number(row.base_fine || 0),
        repeat_fine: row.repeat_fine != null ? Number(row.repeat_fine) : null,
        section: String(row.section || ''),
        description: String(row.description || ''),
      };
    }
    return null;
  } finally {
    await conn.close();
  }
}

export async function initOfflineChallanDB() {
  try {
    await getDuckDB();
    return true;
  } catch {
    return false;
  }
}

/** @internal — test helper to reset module-level singleton between tests */
export function __testResetDbInstance() {
  if (typeof dbInstance !== 'undefined') dbInstance = null;
}

export async function calculateOfflineChallan(
  violationCode: string, 
  vehicleClass: string, 
  isRepeat: boolean,
  stateCode = 'TN'
) {
  // Simulate standard network lookup latency for realism
  await new Promise(r => setTimeout(r, OFFLINE_CHALLAN_LOOKUP_DELAY_MS));

  // 1. Attempt DuckDB Wasm
  try {
    const result = await calculateWithDuckDB(violationCode, vehicleClass, isRepeat, stateCode);
    if (result) return result;
  } catch (err) {
    logClientWarning('SafeVixAI: DuckDB Wasm run failed. Falling back to client-side CSV parser.', { error: String(err) });
  }

  // 2. Fetch and parse offline CSVs directly
  try {
    const violationsResp = await fetch('/offline-data/violations.csv');
    const overridesResp = await fetch('/offline-data/state_overrides.csv');
    
    if (!violationsResp.ok || !overridesResp.ok) {
      throw new Error('Fallback CSV file fetch returned not OK status');
    }
    
    const violationsText = await violationsResp.text();
    const overridesText = await overridesResp.text();
    
    const violations = parseCSV(violationsText);
    const overrides = parseCSV(overridesText);
    
    const violation = violations.find(v => v.violation_code === violationCode);
    if (!violation) {
      throw new Error(`Violation code ${violationCode} not found in offline CSV`);
    }
    
    const vClassLower = vehicleClass.toLowerCase();
    const baseCol = `base_fine_${vClassLower}`;
    const repeatCol = `repeat_fine_${vClassLower}`;
    
    let baseFine = Number(violation[baseCol] || violation.base_fine || 0);
    let repeatFine = violation[repeatCol] || violation.repeat_fine ? Number(violation[repeatCol] || violation.repeat_fine) : null;
    let section = violation.section || '';
    let description = violation.description || '';
    
    const normalizedClassMap: Record<string, string> = {
      '4W': 'LMV',
      '2W': '2W',
      'HTV': 'HMV',
      'BUS': 'BUS'
    };
    const normClass = normalizedClassMap[vehicleClass] || vehicleClass;
    
    const possibleOverrideCodes = [
      violationCode,
      `${violationCode}${normClass}`,
      !isRepeat ? `${violationCode}FIRST` : `${violationCode}REPEAT`
    ];

    const override = overrides.find(o => 
      o.state_code === stateCode && 
      possibleOverrideCodes.includes(o.violation_code) &&
      (o.vehicle_class === normClass || !o.vehicle_class)
    );
    
    if (override) {
      if (override.base_fine) baseFine = Number(override.base_fine);
      if (override.repeat_fine) repeatFine = Number(override.repeat_fine);
      if (override.section) section = override.section;
      if (override.description) description = override.description;
    }
    
    return {
      base_fine: baseFine,
      repeat_fine: repeatFine,
      section,
      description,
    };
  } catch (err) {
    logClientError('SafeVixAI: Fallback CSV parsing failed. Defaulting to in-memory dictionary.', { error: String(err) });
    
    // 3. Last-resort in-memory lookup dictionary (zero network / zero parser dependency)
    const db = {
      '177':  { base: 500,   repeat: 1500,  desc: 'General Provision',                      section: '177'    },
      '177A': { base: 500,   repeat: 1000,  desc: 'Violation of road regulations',           section: '177A'   },
      '178':  { base: 500,   repeat: 500,   desc: 'Traveling without ticket on bus',          section: '178(1)' },
      '179':  { base: 2000,  repeat: 2000,  desc: 'Disobedience of orders of authorities',   section: '179(1)' },
      '180':  { base: 5000,  repeat: 5000,  desc: 'Allowing unauthorized person to drive',   section: '180'    },
      '181':  { base: 5000,  repeat: 5000,  desc: 'Driving without license',                 section: '181'    },
      '182_3':{ base: 10000, repeat: 10000, desc: 'Driving despite disqualification',        section: '182(3)' },
      '182_4':{ base: 10000, repeat: 10000, desc: 'Driving over size/weight limit',          section: '182(4)' },
      '183':  { base: vehicleClass === '4W' || vehicleClass === 'LMV' ? 1000 : 2000, repeat: vehicleClass === '4W' || vehicleClass === 'LMV' ? 2000 : 4000, desc: 'Over-speeding', section: '183(1)' },
      '184':  { base: 5000,  repeat: 10000, desc: 'Dangerous driving',                       section: '184'    },
      '185':  { base: 10000, repeat: 15000, desc: 'Drunken driving',                         section: '185'    },
      '194D': { base: 1000,  repeat: 1000,  desc: 'Driving without helmet',                  section: '194D'   },
      '194B': { base: 1000,  repeat: 1000,  desc: 'Driving without seat belt',               section: '194B'   },
    };

    const result = db[violationCode as keyof typeof db];
    if (!result) return { base_fine: 0, repeat_fine: null, section: 'Unknown', description: 'Violation not found' };

    return {
      base_fine: result.base,
      repeat_fine: result.repeat,
      section: result.section,
      description: result.desc,
    };
  }
}
