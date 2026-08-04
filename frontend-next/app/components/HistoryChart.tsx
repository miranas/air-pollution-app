'use client';

import { 
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
} from 'recharts';
import { useMemo } from 'react';
import { format } from 'date-fns';
import { sl } from 'date-fns/locale';
import {
  computeStationAqi,
  getPollutants,
  getPollutantLevel,
  levelLabel,
  getThresholds,
  chartColorForLevel,
  type ThresholdProfile,
  type ColorLevel,
} from '../utils/aqi';

interface HistoryChartProps {
  pollutantKey: string;
  rows: any[];
  period: string;
  thresholdProfile: ThresholdProfile;
}

const AQI_THRESHOLDS = [50, 100, 150, 200] as const;

type ChartPoint = {
  time: number;
  value: number;
};

type ChartSegment = {
  color: string;
  points: ChartPoint[];
};

type SeriesLevel = 'good' | 'ok' | 'warn' | 'bad' | 'very bad' | 'unknown';

function getAqiLevel(value: number): SeriesLevel {
  if (value <= AQI_THRESHOLDS[0]) return 'good';
  if (value <= AQI_THRESHOLDS[1]) return 'ok';
  if (value <= AQI_THRESHOLDS[2]) return 'warn';
  if (value <= AQI_THRESHOLDS[3]) return 'bad';
  return 'very bad';
}

function getSeriesLevel(
  pollutantKey: string,
  value: number,
  thresholdProfile: ThresholdProfile,
): SeriesLevel {
  if (pollutantKey === 'aqi') {
    return getAqiLevel(value);
  }

  return getPollutantLevel(pollutantKey, value, thresholdProfile);
}

function getSeriesLabel(
  pollutantKey: string,
  level: SeriesLevel,
): string {
  if (pollutantKey === 'aqi') {
    if (level === 'good') return 'DOBRO';
    if (level === 'ok') return 'ZMERNO';
    if (level === 'warn') return 'POVIŠANO';
    if (level === 'bad') return 'SLABO';
    if (level === 'verybad') return 'ZELO SLABO';
    return 'NI PRAGA';
  }

  if (level === 'very bad') {
    return 'ZELO SLABO';
  }

  return levelLabel(level);
}

function getChartTitle(pollutantKey: string): string {
  return pollutantKey === 'aqi' ? 'AQI indeks' : pollutantKey.toUpperCase();
}

function getYAxisDomain(pollutantKey: string): [number, number] | undefined {
  return pollutantKey === 'aqi' ? [0, 300] : undefined;
}

function downsamplePoints<T extends ChartPoint>(points: T[], maxPoints: number): T[] {
  if (points.length <= maxPoints) return points;

  const step = Math.ceil(points.length / maxPoints);
  const sampled: T[] = [];
  for (let index = 0; index < points.length; index += step) {
    sampled.push(points[index]);
  }

  const last = points[points.length - 1];
  if (sampled[sampled.length - 1] !== last) {
    sampled.push(last);
  }

  return sampled;
}

function getXAxisTickCount(period: string): number {
  if (period === 'day') return 12;
  if (period === 'week') return 10;
  if (period === 'month') return 10;
  return 12;
}

function interpolatePoint(start: ChartPoint, end: ChartPoint, threshold: number): ChartPoint {
  if (end.value === start.value) {
    return {
      time: start.time,
      value: threshold,
    };
  }

  const ratio = (threshold - start.value) / (end.value - start.value);
  return {
    time: start.time + (end.time - start.time) * ratio,
    value: threshold,
  };
}

function buildColoredSegments(
  points: ChartPoint[],
  pollutantKey: string,
  thresholdProfile: ThresholdProfile,
): ChartSegment[] {
  if (points.length < 2) {
    return [];
  }

  const thresholds = pollutantKey === 'aqi'
    ? AQI_THRESHOLDS
    : getThresholds(thresholdProfile)[pollutantKey];
  const segments: ChartSegment[] = [];

  const appendSegment = (color: string, startPoint: ChartPoint, endPoint: ChartPoint) => {
    const last = segments[segments.length - 1];
    if (!last || last.color !== color) {
      segments.push({ color, points: [startPoint, endPoint] });
      return;
    }

    const tail = last.points[last.points.length - 1];
    if (tail.time === startPoint.time && tail.value === startPoint.value) {
      last.points.push(endPoint);
      return;
    }

    segments.push({ color, points: [startPoint, endPoint] });
  };

  for (let i = 0; i < points.length - 1; i += 1) {
    const start = points[i];
    const end = points[i + 1];

    const minValue = Math.min(start.value, end.value);
    const maxValue = Math.max(start.value, end.value);
    const crossingThresholds = thresholds
      ? thresholds.filter((threshold) => threshold > minValue && threshold < maxValue)
      : [];

    const splitPoints = crossingThresholds
      .sort((a, b) => (start.value <= end.value ? a - b : b - a))
      .map((threshold) => interpolatePoint(start, end, threshold));

    const chain = [start, ...splitPoints, end];

    for (let j = 0; j < chain.length - 1; j += 1) {
      const pieceStart = chain[j];
      const pieceEnd = chain[j + 1];
      const midValue = (pieceStart.value + pieceEnd.value) / 2;
      const level = getSeriesLevel(pollutantKey, midValue, thresholdProfile);
      const color = chartColorForLevel(level);

      appendSegment(color, pieceStart, pieceEnd);
    }
  }

  return segments;
}

export default function HistoryChart({ pollutantKey, rows, period, thresholdProfile }: HistoryChartProps) {
  const rawData: Array<ChartPoint & { category: string }> = useMemo(() => {
    const points = rows.map((row) => {
      const time = row.time_to ? new Date(row.time_to).getTime() : Date.now();

      if (pollutantKey === 'aqi') {
        const aqiKey = thresholdProfile === 'who' ? 'aqi_who' : 'aqi_eu';
        const precomputedAqi = Number(row[aqiKey]);

        if (Number.isFinite(precomputedAqi)) {
          return {
            time,
            value: precomputedAqi,
            category: '',
          };
        }

        const pollutants = getPollutants({ measurements_list: [row] });
        const aqi = computeStationAqi(pollutants, thresholdProfile);
        return {
          time,
          value: aqi.value ?? NaN,
          category: aqi.category,
        };
      }

      return {
        time,
        value: Number(row[pollutantKey]),
        category: '',
      };
    }).filter((item) => !Number.isNaN(item.time) && Number.isFinite(item.value))
      .sort((a, b) => a.time - b.time);

    return downsamplePoints(points, 420);
  }, [rows, pollutantKey, thresholdProfile]);

  const segments = useMemo(
    () => buildColoredSegments(rawData, pollutantKey, thresholdProfile),
    [rawData, pollutantKey, thresholdProfile],
  );

  const pointByTime = useMemo(() => {
    const byTime = new Map<number, { value: number; category: string }>();
    for (const point of rawData) {
      byTime.set(point.time, { value: point.value, category: point.category });
    }
    return byTime;
  }, [rawData]);

  const TooltipContent = ({ active, label, payload }: any) => {
    if (!active || !payload?.length) return null;

    const labelTime = Number(label);
    const fromSeries = pointByTime.get(labelTime);
    const first = payload.find((item: any) => item?.payload?.value !== undefined) || payload[0];
    const value = Number(fromSeries?.value ?? first?.payload?.value ?? first?.value ?? NaN);
    if (!Number.isFinite(value)) return null;
    const level = getSeriesLevel(pollutantKey, value, thresholdProfile);
    const categoryFromData = (fromSeries?.category || first?.payload?.category || '').trim();
    const category = categoryFromData || getSeriesLabel(pollutantKey, level);

    return (
      <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {(() => {
            try {
              return format(new Date(Number(label)), 'd. MMMM yyyy, p', { locale: sl });
            } catch {
              return String(label);
            }
          })()}
        </p>
        <p className="mt-1 text-sm font-bold text-slate-900">
          {pollutantKey === 'aqi' ? `AQI ${Math.round(value)}` : `${value.toFixed(1)} µg/m³`}
        </p>
        <p className="text-xs font-semibold uppercase" style={{ color: chartColorForLevel(level) }}>
          {category}
        </p>
      </div>
    );
  };

  return (
    <div className="h-[350px] w-full rounded-xl border border-slate-200 bg-white p-4 shadow-inner">
      <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-slate-500">
        Analiza trenda: {getChartTitle(pollutantKey)}
      </h4>
      
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rawData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          
          {/* TUKAJ JE MANJKAJOČA MREŽA */}
          <CartesianGrid 
            strokeDasharray="3 3" 
            vertical={false} 
            stroke="#e2e8f0" 
          />
          
          <XAxis 
            dataKey="time" 
            type="number"
            domain={['dataMin', 'dataMax']}
            tickCount={getXAxisTickCount(period)}
            minTickGap={8}
            tickFormatter={(unixTime) => {
              try {
                const date = new Date(unixTime);
                if (period === 'day') return format(date, 'HH:mm');
                if (period === 'week') return format(date, 'ccc d.', { locale: sl });
                return format(date, 'd. MMM', { locale: sl });
              } catch {
                return '';
              }
            }}
            stroke="#94a3b8"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          
          <YAxis 
            domain={getYAxisDomain(pollutantKey)}
            stroke="#94a3b8" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
          />
          
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            content={<TooltipContent />}
            isAnimationActive={false}
          />

          <Line
            data={rawData}
            type="linear"
            dataKey="value"
            stroke="transparent"
            strokeWidth={10}
            dot={false}
            activeDot={false}
            legendType="none"
            isAnimationActive={false}
          />

          {segments.map((segment, index) => (
            <Line
              key={`${segment.color}-${index}`}
              data={segment.points}
              type="linear"
              dataKey="value"
              stroke={segment.color}
              strokeWidth={6}
              dot={false}
              isAnimationActive={false}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}