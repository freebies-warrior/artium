'use client';

import { useEffect, useMemo, useState } from 'react';
import '../global.css';

interface CountdownTimerProps {
  /** Accept either a Date OR an ISO string (e.g. "2026-01-28T10:00:00Z") */
  targetDate?: Date | string;
}

type TimeLeft = {
  hours: number;
  minutes: number;
  seconds: number;
};

function clamp(n: number) {
  return Number.isFinite(n) ? n : 0;
}

function computeTimeLeft(target: Date | null): TimeLeft {
  if (!target) return { hours: 0, minutes: 0, seconds: 0 };

  const diffMs = target.getTime() - Date.now();
  const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return { hours: clamp(hours), minutes: clamp(minutes), seconds: clamp(seconds) };
}

export default function CountdownTimer({ targetDate }: CountdownTimerProps) {
  const target = useMemo(() => {
    if (!targetDate) return null;
    if (targetDate instanceof Date) return targetDate;

    const d = new Date(targetDate); // ISO from backend (time_end)
    return Number.isNaN(d.getTime()) ? null : d;
  }, [targetDate]);

  const [timeLeft, setTimeLeft] = useState<TimeLeft>(() => computeTimeLeft(target));

  useEffect(() => {
    // Update immediately when target changes
    setTimeLeft(computeTimeLeft(target));

    const timer = setInterval(() => {
      setTimeLeft(computeTimeLeft(target));
    }, 1000);

    return () => clearInterval(timer);
  }, [target]);

  const formatNumber = (num: number) => String(num).padStart(2, '0');

  const isEnded = timeLeft.hours === 0 && timeLeft.minutes === 0 && timeLeft.seconds === 0;

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 lg:p-6">
      <p className="text-neutral-400 text-sm mb-4 text-center">
        {isEnded ? 'Auction ended' : 'Auction ends in:'}
      </p>

      <div className="flex items-center justify-center gap-2 lg:gap-4">
        {/* Hours */}
        <div className="text-center flex flex-col items-center">
          <div className="bg-neutral-850 border border-neutral-800 rounded-lg px-3 py-2 lg:px-4 lg:py-3">
            <span className="text-2xl lg:text-4xl font-bold text-white">
              {formatNumber(timeLeft.hours)}
            </span>
          </div>
          <span className="text-xs text-neutral-400 mt-2 block">Hours</span>
        </div>

        <span className="text-2xl lg:text-4xl font-bold text-neutral-500">:</span>

        {/* Minutes */}
        <div className="text-center flex flex-col items-center">
          <div className="bg-neutral-850 border border-neutral-800 rounded-lg px-3 py-2 lg:px-4 lg:py-3">
            <span className="text-2xl lg:text-4xl font-bold text-white">
              {formatNumber(timeLeft.minutes)}
            </span>
          </div>
          <span className="text-xs text-neutral-400 mt-2 block">Minutes</span>
        </div>

        <span className="text-2xl lg:text-4xl font-bold text-neutral-500">:</span>

        {/* Seconds */}
        <div className="text-center flex flex-col items-center">
          <div className="bg-neutral-850 border border-neutral-800 rounded-lg px-3 py-2 lg:px-4 lg:py-3">
            <span className="text-2xl lg:text-4xl font-bold text-white">
              {formatNumber(timeLeft.seconds)}
            </span>
          </div>
          <span className="text-xs text-neutral-400 mt-2 block">Seconds</span>
        </div>
      </div>

      {!target && (
        <p className="mt-3 text-center text-xs text-neutral-500">
          No end time provided.
        </p>
      )}
    </div>
  );
}
