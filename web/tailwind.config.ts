import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#07140F',
          secondary: '#0B1F16',
          elevated: '#102A1E',
          surface: 'rgba(16,42,30,0.72)',
        },
        emerald: {
          950: '#032B20',
          900: '#064B38',
          800: '#086A4E',
          700: '#0A8763',
          500: '#19A974',
          300: '#5BD6A3',
        },
        gold: {
          500: '#C8A55A',
          400: '#D9BA70',
          300: '#E8D19A',
        },
        content: {
          primary: '#F5F2E8',
          secondary: '#C6D2CA',
          muted: '#81978B',
        },
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'royal-pulse': 'royalPulse 5s ease-in-out infinite',
        'orbit': 'orbit 3s linear infinite',
        'shimmer': 'shimmer 1.2s ease-out forwards',
        'bloom': 'bloom 8s ease-in-out infinite alternate',
      },
      keyframes: {
        royalPulse: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.05)' },
        },
        orbit: {
          from: { transform: 'rotate(0deg) translateX(60px) rotate(0deg)' },
          to: { transform: 'rotate(360deg) translateX(60px) rotate(-360deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        bloom: {
          '0%': { opacity: '0.05', transform: 'scale(0.95)' },
          '100%': { opacity: '0.15', transform: 'scale(1.05)' },
        },
      },
      backdropBlur: {
        xs: '4px',
      },
    },
  },
  plugins: [],
}

export default config
