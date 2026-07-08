/** @type {import('tailwindcss').Config} */
// Electro design system: primary #F28B00 (orange), secondary #F92400 (red),
// dark #484848, light #F5F5F5. Brand colors resolve to CSS variables so the
// platform admin can re-theme the whole site at runtime (see :root in main.css).

// Map every shade to its CSS variable, keeping Tailwind's alpha support.
const shadeVar = (name) =>
  Object.fromEntries(
    [50, 100, 200, 300, 400, 500, 600, 700, 800, 900].map((s) => [
      s,
      `rgb(var(--c-${name}-${s}) / <alpha-value>)`
    ])
  );

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  darkMode: 'class',
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: '1rem', lg: '2rem' },
      screens: { '2xl': '1400px' }
    },
    extend: {
      colors: {
        // Brand palette via CSS variables (see :root in main.css) so the platform
        // admin can re-theme the whole site at runtime. Defaults = the q-shop brand.
        primary: shadeVar('primary'),
        secondary: shadeVar('secondary'),
        ink: '#484848',
        muted: '#6d6d6d',
        lightbg: 'rgb(var(--c-bg) / <alpha-value>)'
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Cairo', '"Open Sans"', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Tahoma', 'Arial', 'sans-serif'],
        heading: ['var(--font-heading)', 'Cairo', 'Roboto', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Arial', 'sans-serif']
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
