export type ThresholdProfile = 'eu' | 'who';
export type Thresholds = Record<string, [number, number, number]>;
export type AqiInfo = {
  value: number | null;
  category: string;
  dominantPollutant: string | null;
  className: string;
};
export type StationRecord = {
  info?: {
    station_id?: string;
    station_name?: string;
  };
  measurements_list?: Array<Record<string, unknown>>;
};


export function getThresholds(profile: ThresholdProfile): Thresholds {
  const euThresholds: Thresholds = {
    // [goodMax, okMax, warnMax], everything above is bad
    // Approx bands around common EU legal targets/limits.
    pm25: [10, 20, 25],
    pm10: [20, 40, 50],
    no2: [20, 40, 60],
    o3: [80, 120, 180],
    so2: [40, 125, 350],
    co: [4, 7, 10],
    nox: [30, 60, 100],
  };

  // WHO AQG 2021 inspired baseline + two additional severity bands (stricter than EU bands).
  const whoThresholds: Thresholds = {
    pm25: [5, 10, 15],
    pm10: [15, 30, 45],
    no2: [10, 25, 40],
    o3: [50, 80, 120],
    so2: [20, 40, 80],
    co: [2, 4, 8],
    nox: [20, 40, 80],
  };

  return profile === 'who' ? whoThresholds : euThresholds;
}

export function toAqiBandScore(value: number, thresholds: [number, number, number]): number {
  const [goodMax, okMax, warnMax] = thresholds;

  if (value <= goodMax) {
    return Math.round((value / goodMax) * 50);
  }
  if (value <= okMax) {
    return Math.round(51 + ((value - goodMax) / (okMax - goodMax)) * 49);
  }
  if (value <= warnMax) {
    return Math.round(101 + ((value - okMax) / (warnMax - okMax)) * 49);
  }

  const hardCap = warnMax * 2;
  if (value >= hardCap) return 300;
  return Math.round(151 + ((value - warnMax) / (hardCap - warnMax)) * 149);
}

export function getAqiCategory(score: number): { label: string; className: string } {
  if (score <= 50) return { label: 'Odlicna', className: 'border-emerald-700 bg-emerald-200 text-emerald-950' };
  if (score <= 100) return { label: 'Sprejemljiva', className: 'border-yellow-700 bg-yellow-200 text-yellow-950' };
  if (score <= 150) return { label: 'Obcutljiva', className: 'border-orange-700 bg-orange-200 text-orange-950' };
  if (score <= 200) return { label: 'Slaba', className: 'border-rose-700 bg-rose-200 text-rose-950' };
  return { label: 'Zelo slaba', className: 'border-red-900 bg-red-300 text-red-950' };
}

export function computeStationAqi(
  pollutants: Array<{ key: string; value: unknown }>,
  profile: ThresholdProfile,
): AqiInfo {
  const thresholds = getThresholds(profile);
  let maxScore: number | null = null;
  let dominant: string | null = null;

  for (const pollutant of pollutants) {
    const numeric = toNumber(pollutant.value);
    const t = thresholds[pollutant.key];
    if (numeric === null || !t) continue;

    const subIndex = toAqiBandScore(numeric, t);
    if (maxScore === null || subIndex > maxScore) {
      maxScore = subIndex;
      dominant = pollutant.key;
    }
  }

  if (maxScore === null) {
    return {
      value: null,
      category: 'Ni dovolj podatkov',
      dominantPollutant: null,
      className: 'border-slate-400 bg-slate-200 text-slate-900',
    };
  }

  const category = getAqiCategory(maxScore);
  return {
    value: maxScore,
    category: category.label,
    dominantPollutant: dominant,
    className: category.className,
  };
}

export function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}


export function getPollutantLevel(
  key: string,
  value: unknown,
  profile: ThresholdProfile,
): 'good' | 'ok' | 'warn' | 'bad' | 'unknown' {
  const numeric = toNumber(value);
  if (numeric === null) return 'unknown';

  const thresholds = getThresholds(profile);

  const t = thresholds[key];
  if (!t) return 'unknown';
  if (numeric <= t[0]) return 'good';
  if (numeric <= t[1]) return 'ok';
  if (numeric <= t[2]) return 'warn';
  return 'bad';
}

export function formatLabel(key: string): string {
  const map: Record<string, string> = {
    pm10: 'PM10',
    pm25: 'PM2.5',
    no2: 'NO2',
    nox: 'NOx',
    o3: 'O3',
    so2: 'SO2',
    co: 'CO',
  };
  return map[key] || key.toUpperCase();
}

export function formatStationName(name?: string): string {
  if (!name) return 'Neznana postaja';

  const trimmed = name.trim().replace(/\s+/g, ' ');
  const match = trimmed.match(/^([A-Z]{2})\s+(.+)$/);

  if (!match) {
    return trimmed;
  }

  const [, prefix, suffix] = match;
  const cityByPrefix: Record<string, string> = {
    CE: 'Celje',
    LJ: 'Ljubljana',
    MB: 'Maribor',
    MS: 'Murska Sobota',
    NG: 'Nova Gorica',
  };

  const city = cityByPrefix[prefix];
  if (!city) {
    return trimmed;
  }

  const formattedSuffix = suffix
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');

  return `${city} ${formattedSuffix}`;
}

export function getPollutants(record: StationRecord): Array<{ key: string; value: unknown }> {
  const firstMeasurement = record.measurements_list?.[0] || {};
  const ignoredKeys = new Set(['station_id', 'station_name', 'time_from', 'time_to']);

  return Object.entries(firstMeasurement)
    .filter(([key, value]) => !ignoredKeys.has(key) && value !== null && value !== undefined)
    .map(([key, value]) => ({ key, value }));
}

export function levelLabel(level: 'good' | 'ok' | 'warn' | 'bad' | 'verybad' | 'unknown'): string {
  if (level === 'good') return 'DOBRO';
  if (level === 'ok') return 'ZMERNO';
  if (level === 'warn') return 'POVISANO';
  if (level === 'bad') return 'VISOKO';
  if (level === 'verybad') return 'ZELO SLABO';
  return 'NI PRAGA';
}

// Unified color palette for consistency across components
export type ColorLevel = 'good' | 'ok' | 'warn' | 'bad' | 'verybad' | 'unknown';

export const COLOR_PALETTE: Record<ColorLevel, { badge: string; chart: string }> = {
  good: {
    badge: 'border-emerald-900 bg-emerald-300 text-emerald-950 shadow-[0_0_0_1px_rgba(6,78,59,0.35)]',
    chart: '#047857', // emerald-700
  },
  ok: {
    badge: 'border-yellow-900 bg-yellow-300 text-yellow-950 shadow-[0_0_0_1px_rgba(113,63,18,0.35)]',
    chart: '#ca8a04', // yellow-600
  },
  warn: {
    badge: 'border-orange-900 bg-orange-300 text-orange-950 shadow-[0_0_0_1px_rgba(124,45,18,0.35)]',
    chart: '#c2410c', // orange-600
  },
  bad: {
    badge: 'border-rose-950 bg-rose-400 text-rose-950 shadow-[0_0_0_1px_rgba(76,5,25,0.35)]',
    chart: '#be185d', // rose-700
  },
  verybad: {
    badge: 'border-violet-900 bg-violet-400 text-violet-950 shadow-[0_0_0_1px_rgba(46,16,101,0.35)]',
    chart: '#6d28d9', // violet-700
  },
  unknown: {
    badge: 'border-slate-700 bg-slate-300 text-slate-900',
    chart: '#4b5563', // slate-600
  },
};

export function badgeClassForLevel(level: ColorLevel): string {
  return COLOR_PALETTE[level]?.badge || COLOR_PALETTE.unknown.badge;
}

export function chartColorForLevel(level: ColorLevel): string {
  return COLOR_PALETTE[level]?.chart || COLOR_PALETTE.unknown.chart;
}




