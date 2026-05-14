/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Cream / paper tones (saree base, mill-floor paper)
        cream: {
          50: '#fbf8f1',
          100: '#f4ead6',
          200: '#e9dcbe',
          300: '#d9c598',
        },
        // Deep inks (drafting ink, woven warp)
        ink: {
          900: '#1a1814',
          800: '#2a2620',
          700: '#3d362b',
          600: '#5a4f3e',
          500: '#7d6f58',
          400: '#a08f74',
        },
        // Madder red (traditional dye accent)
        madder: {
          500: '#b12a32',
          600: '#971f26',
          700: '#7c1820',
        },
        // Zari gold (metallic thread)
        zari: {
          400: '#d4af5c',
          500: '#b8943f',
          600: '#9a7a30',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'Georgia', 'serif'],
        body: ['"Inter Tight"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.04em',
      },
    },
  },
  plugins: [],
};
