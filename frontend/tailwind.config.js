/** @type {import('tailwindcss').Config} */
// Electro design system: primary #F28B00 (orange), secondary #F92400 (red),
// dark #484848, light #F5F5F5. Headings Roboto, body Open Sans.
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: '1rem', lg: '2rem' },
      screens: { '2xl': '1400px' }
    },
    extend: {
      colors: {
        primary: {
          50: '#fff8ee',
          100: '#ffe9cc',
          200: '#fdcf94',
          300: '#fbb35c',
          400: '#f79e2f',
          500: '#f79115',
          600: '#F28B00',
          700: '#c66f00',
          800: '#9e5900',
          900: '#7a4500'
        },
        secondary: {
          50: '#fff1ee',
          100: '#ffddd6',
          200: '#ffb8a8',
          300: '#ff8f78',
          400: '#fd5a3c',
          500: '#F92400',
          600: '#e01f00',
          700: '#bb1a00',
          800: '#961700',
          900: '#7a1600'
        },
        ink: '#484848',
        muted: '#6d6d6d',
        lightbg: '#F5F5F5'
      },
      fontFamily: {
        sans: ['"Open Sans"', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Helvetica', 'Arial', 'sans-serif'],
        heading: ['Roboto', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Arial', 'sans-serif']
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '0.625rem',
        xl: '0.75rem'
      },
      boxShadow: {
        card: '0 1px 2px rgba(72,72,72,.06), 0 1px 3px rgba(72,72,72,.08)',
        pop: '0 10px 30px rgba(72,72,72,.15)'
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
