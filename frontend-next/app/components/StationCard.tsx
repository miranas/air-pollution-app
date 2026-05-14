'use client';

import { 
  formatLabel, 
  formatStationName,
  computeStationAqi, 
  getPollutants, 
  getPollutantLevel, 
  badgeClassForLevel, 
  levelLabel,
  type StationRecord,
  type ThresholdProfile 
} from '../utils/aqi';

interface StationCardProps {
  record: StationRecord;
  thresholdProfile: ThresholdProfile;
}

export default function StationCard({ record, thresholdProfile }: StationCardProps) {
  const stationName = formatStationName(record.info?.station_name);
  const stationId = record.info?.station_id || '-';
  const timeTo = String(record.measurements_list?.[0]?.time_to || '');
  const pollutants = getPollutants(record);
  const aqi = computeStationAqi(pollutants, thresholdProfile);

  return (
    <article className="rounded-lg border border-slate-400 bg-slate-100 p-5 md:p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-xl font-semibold text-slate-900 md:text-2xl">{stationName}</h3>
        <span className="text-base text-slate-600 font-mono">{stationId}</span>
      </div>

      <div className={`mb-4 rounded-xl border px-4 py-3 transition-colors duration-500 ${aqi.className}`}>
        <p className="text-xs font-semibold uppercase tracking-wider opacity-80 text-black/70">AQI Indeks</p>
        <div className="mt-1 flex items-end justify-between gap-3">
          <p className="text-4xl font-extrabold leading-none md:text-5xl text-black">
            {aqi.value ?? '--'}
          </p>
          <p className="text-sm font-bold md:text-base uppercase text-black/80">{aqi.category}</p>
        </div>
        <p className="mt-2 text-xs md:text-sm italic text-black/70">
          Glavno onesnaževalo: <span className="font-bold">{aqi.dominantPollutant ? formatLabel(aqi.dominantPollutant) : 'N/A'}</span>
        </p>
      </div>

      {pollutants.length > 0 ? (
        <div className="flex flex-wrap gap-2.5">
          {pollutants.map((item) => {
            const level = getPollutantLevel(item.key, item.value, thresholdProfile);
            return (
              <span
                key={`${stationId}-${item.key}`}
                className={`flex items-center rounded-full border px-3.5 py-2 text-sm font-bold ${badgeClassForLevel(level)}`}
              >
                {formatLabel(item.key)}: {String(item.value)}
                {level !== 'unknown' ? (
                  <span className="ml-2 rounded-md border border-black/10 bg-white/60 px-1.5 py-0.5 text-[10px] font-black uppercase">
                    {levelLabel(level)}
                  </span>
                ) : null}
              </span>
            );
          })}
        </div>
      ) : (
        <p className="text-sm italic text-slate-500">Ni podatkov o meritvah.</p>
      )}
    </article>
  );
}