/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: '1rem', lg: '2rem' },
      screens: { '2xl': '1280px' }
    },
    extend: {
      colors: {
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81'
        },
        ink: '#0f172a'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif']
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '0.625rem',
        xl: '0.75rem'
      },
      boxShadow: {
        card: '0 1px 2px rgba(15,23,42,.06), 0 1px 3px rgba(15,23,42,.08)',
        pop: '0 10px 30px rgba(15,23,42,.12)'
      },
      keyframes: {
        'fade-in': { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        'slide-up': { '0%': { opacity: 0, transform: 'translateY(8px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        shimmer: { '100%': { transform: 'translateX(100%)' } }
      },
      animation: {
        'fade-in': 'fade-in .2s ease-out',
        'slide-up': 'slide-up .25s ease-out'
      }
    }
  },
  plugins: []
};
