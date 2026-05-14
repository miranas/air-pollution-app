'use client';

import { 
  formatStationName,
  type ThresholdProfile,
  type StationRecord,
} from './utils/aqi';

import StationCard from './components/StationCard';
import HistoryChart from './components/HistoryChart'; // Uvoz nove komponente
import { startTransition, useEffect, useState } from 'react';

const LATEST_REFRESH_MS = Number(process.env.NEXT_PUBLIC_LATEST_REFRESH_MS || 60000);

type HistoryPeriod = 'day' | 'week' | 'month' | 'year';

type HistoryStation = {
  info?: {
    station_id?: string;
    station_name?: string;
  };
  measurements_list?: Array<Record<string, unknown>>;
  total_points?: number;
};

type HistoryResponse = {
  period: string;
  from: string;
  to: string;
  stations: Record<string, HistoryStation>;
};

function formatDateTime(iso: string | null): string {
  if (!iso) return 'N/A';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat('sl-SI', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(date);
}

const formatLabel = (key: string) => key.toUpperCase().replace('PM', 'PM ');

export default function Home() {
  const [meritve, setMeritve] = useState<StationRecord[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [thresholdProfile, setThresholdProfile] = useState<ThresholdProfile>('eu');
  
  // Stanje za zgodovino
  const [historyPeriod, setHistoryPeriod] = useState<HistoryPeriod>('day');
  const [historyStationId, setHistoryStationId] = useState<string>('');
  const [historyPollutantKey, setHistoryPollutantKey] = useState<string>('');
  const [historyData, setHistoryData] = useState<HistoryResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 1. Pridobivanje zadnjih podatkov
  useEffect(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:5000`;
    async function fetchData() {
      try {
        const res = await fetch(`${apiBaseUrl}/api/latest?_t=${Date.now()}`, { cache: 'no-store' });
        if (res.ok) {
          const data = await res.json();
          setMeritve(Object.values(data));
        }
      } catch (e) { console.error("Fetch failed:", e); }
      setLoading(false);
    }
    fetchData();
    const interval = setInterval(fetchData, Math.max(10000, LATEST_REFRESH_MS));

    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchData();
      }
    };
    const onFocus = () => fetchData();

    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('focus', onFocus);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('focus', onFocus);
    };
  }, []);

  // 2. Pridobivanje zgodovine
  useEffect(() => {
    if (!historyStationId) return;
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:5000`;
    async function fetchHistory() {
      setHistoryLoading(true);
      try {
        const res = await fetch(`${apiBaseUrl}/api/history?period=${historyPeriod}&station_id=${encodeURIComponent(historyStationId)}`, { cache: 'no-store' });
        if (res.ok) setHistoryData(await res.json());
      } catch (error) { console.error('History fetch failed:', error); }
      finally { setHistoryLoading(false); }
    }
    fetchHistory();
  }, [historyPeriod, historyStationId]);

  // Pomožni podatki za prikaz
  const latestTime = meritve?.map(r => String(r.measurements_list?.[0]?.time_to || '')).filter(t => t.length > 0).sort().at(-1) || null;
  const stationOptions = meritve?.map(r => ({ stationId: r.info?.station_id || '', stationName: formatStationName(r.info?.station_name) })).filter(i => i.stationId.length > 0) || [];
  
  useEffect(() => {
    if (!historyStationId && stationOptions.length > 0) setHistoryStationId(stationOptions[0].stationId);
  }, [stationOptions, historyStationId]);

  const selectedHistoryStation = (historyData?.stations && historyStationId && historyData.stations[historyStationId]) || null;
  const historyRows = selectedHistoryStation?.measurements_list || [];
  const historyRowsChronological = [...historyRows].reverse();
  
  const historyPollutantKeys = ['aqi', ...Array.from(new Set(historyRows.flatMap(row => Object.keys(row).filter(key => !['station_id', 'station_name', 'time_to', 'time_from', 'aqi_eu', 'aqi_who'].includes(key)))))]
    .filter((key, index, array) => array.indexOf(key) === index);
  const selectedPollutant = historyPollutantKey && historyPollutantKeys.includes(historyPollutantKey) ? historyPollutantKey : historyPollutantKeys[0] || '';

  return (
    <main className="flex min-h-screen flex-col items-center bg-gradient-to-br from-[#0b1f3a] via-[#12345b] to-[#0e7490] text-white px-5 py-10 md:px-10 md:py-12">
      <h1 className="mb-10 text-5xl font-bold text-blue-500 font-mono md:text-6xl">
        AIR QUALITY APP <span className="text-white">ZRAKOMER</span>
      </h1>

      <div className="w-full max-w-7xl rounded-2xl border border-slate-400/60 bg-slate-100/90 p-7 text-slate-900 shadow-2xl md:p-10">
        <h2 className="mb-5 text-lg font-bold uppercase tracking-widest text-slate-800 md:text-xl">Zadnje meritve</h2>
        <p className="mb-5 text-base text-slate-700 md:text-lg">Zadnja meritev: <span className="font-semibold text-slate-900">{formatDateTime(latestTime)}</span></p>

        <div className="mb-5 flex flex-wrap items-center gap-3 text-sm md:text-base">
          <button onClick={() => setThresholdProfile('eu')} className={`rounded-full border px-4 py-1.5 font-semibold transition ${thresholdProfile === 'eu' ? 'bg-blue-700 text-white' : 'bg-slate-200 text-slate-700'}`}>EU zakonodaja</button>
          <button onClick={() => setThresholdProfile('who')} className={`rounded-full border px-4 py-1.5 font-semibold transition ${thresholdProfile === 'who' ? 'bg-blue-700 text-white' : 'bg-slate-200 text-slate-700'}`}>WHO priporočila</button>
        </div>

        <div className="max-h-[42rem] overflow-auto rounded-lg border border-slate-400 bg-slate-200/85 p-5 md:p-7 shadow-inner">
          {loading ? (
            <p className="animate-pulse text-lg font-bold text-blue-600">Nalagam podatke s postaj...</p>
          ) : meritve && meritve.length > 0 ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {meritve.map((record) => (
                <StationCard 
                  key={`${record.info?.station_id}-${record.measurements_list?.[0]?.time_to}`} 
                  record={record} 
                  thresholdProfile={thresholdProfile} 
                />
              ))}
            </div>
          ) : (
            <p className="text-red-700 font-bold">Podatki trenutno niso na voljo.</p>
          )}
        </div>

        {/* ANALIZA ZGODOVINE */}
        <div className="mt-8 rounded-lg border border-slate-400 bg-slate-200/80 p-5 md:p-7">
          <h3 className="mb-6 text-xl font-bold text-slate-900">Zgodovinska analiza trendov</h3>
          
          <div className="mb-6 flex flex-wrap gap-4">
             <div className="flex flex-col gap-1">
               <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Obdobje</label>
               <select className="rounded-md border bg-white p-2 text-sm font-medium shadow-sm" value={historyPeriod} onChange={(e) => setHistoryPeriod(e.target.value as HistoryPeriod)}>
                  <option value="day">Zadnjih 24 ur</option>
                  <option value="week">Zadnji teden</option>
                  <option value="month">Zadnji mesec</option>
                  <option value="year">Zadnje leto</option>
               </select>
             </div>

             <div className="flex flex-col gap-1">
               <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Merilno mesto</label>
               <select className="rounded-md border bg-white p-2 text-sm font-medium shadow-sm" value={historyStationId} onChange={(e) => setHistoryStationId(e.target.value)}>
                  {stationOptions.map(opt => <option key={opt.stationId} value={opt.stationId}>{opt.stationName}</option>)}
               </select>
             </div>
          </div>

          {historyLoading ? (
            <div className="flex h-64 items-center justify-center">
              <p className="animate-bounce font-bold text-blue-600">Pripravljam graf...</p>
            </div>
          ) : historyRows.length > 0 ? (
            <div className="space-y-6">
               <div className="flex flex-wrap gap-2">
                 {historyPollutantKeys.map(key => (
                   <button 
                    key={key} 
                    onClick={() => startTransition(() => setHistoryPollutantKey(key))} 
                    className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all shadow-sm ${selectedPollutant === key ? 'bg-blue-600 text-white ring-2 ring-blue-300' : 'bg-white border text-slate-600 hover:bg-slate-50'}`}
                   >
                     {formatLabel(key)}
                   </button>
                 ))}
               </div>

               {/* UPORABA NOVE PRO KOMPONENTE */}
               <HistoryChart 
                 pollutantKey={selectedPollutant} 
                 rows={historyRowsChronological} 
                 period={historyPeriod}
                 thresholdProfile={thresholdProfile}
               />
            </div>
          ) : (
            <div className="flex h-48 items-center justify-center rounded-xl border-2 border-dashed border-slate-300">
               <p className="text-slate-500 italic">Ni zgodovinskih podatkov za izbrano postajo.</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}