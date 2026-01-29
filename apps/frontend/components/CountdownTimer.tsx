'use client'

import { useState, useEffect } from 'react'
import '../global.css'

interface CountdownTimerProps {
  targetDate?: Date
}

export default function CountdownTimer({ targetDate }: CountdownTimerProps) {
  const [timeLeft, setTimeLeft] = useState({
    hours: 59,
    minutes: 59,
    seconds: 59,
  })

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        let { hours, minutes, seconds } = prev

        if (seconds > 0) seconds--
        else if (minutes > 0) {
          minutes--
          seconds = 59
        } else if (hours > 0) {
          hours--
          minutes = 59
          seconds = 59
        }

        return { hours, minutes, seconds }
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const formatNumber = (num: number) => num.toString().padStart(2, '0')

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 lg:p-6">
      {/* Center title */}
      <p className="text-neutral-400 text-sm mb-4 text-center">
        Auction ends in:
      </p>

      {/* Center the whole timer row */}
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

        <span className="text-2xl lg:text-4xl font-bold text-neutral-500">
          :
        </span>

        {/* Minutes */}
        <div className="text-center flex flex-col items-center">
          <div className="bg-neutral-850 border border-neutral-800 rounded-lg px-3 py-2 lg:px-4 lg:py-3">
            <span className="text-2xl lg:text-4xl font-bold text-white">
              {formatNumber(timeLeft.minutes)}
            </span>
          </div>
          <span className="text-xs text-neutral-400 mt-2 block">Minutes</span>
        </div>

        <span className="text-2xl lg:text-4xl font-bold text-neutral-500">
          :
        </span>

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
    </div>
  )
}
