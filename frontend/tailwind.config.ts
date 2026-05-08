import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        chrome: {
          950: '#05080d',
          900: '#0b111b',
          850: '#121b28',
          800: '#152130',
        },
        signal: {
          teal: '#3de2d2',
          amber: '#f6a12d',
          coral: '#ff7262',
          sky: '#6ecbff',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Segoe UI"', 'sans-serif'],
        display: ['"Sora"', '"IBM Plex Sans"', 'sans-serif'],
      },
      boxShadow: {
        panel: '0 18px 80px rgba(2, 8, 22, 0.42)',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        rise: 'rise 500ms ease-out both',
      },
    },
  },
  plugins: [],
} satisfies Config;

