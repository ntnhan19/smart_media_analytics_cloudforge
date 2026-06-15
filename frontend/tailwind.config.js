/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sma-purple': '#7B5CF5',
        'sma-blue': '#4F8EF7',
        'sma-bg': '#0E0B1F',
        'sma-surface': '#16132A',
        'sma-green': '#4ADE80',
      }
    },
  },
  plugins: [],
}
