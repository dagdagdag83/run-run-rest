/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'run-run-rest-base': '#0C0F0A',
        'run-run-rest-surface': '#242325',
        'run-run-rest-primary': '#58A4B0',
        'run-run-rest-accent': '#D64933',
        'run-run-rest-muted': '#BAC1B8',
      },
      fontFamily: {
        sans: ['"IBM Plex Mono"', 'monospace'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
