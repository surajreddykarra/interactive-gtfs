/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Open Sans"', 'sans-serif'],
      },
      colors: {
        metro: '#E91E63',
        rail: '#9C27B0',
        bus: '#FFC107',
        'selection-yellow': 'rgba(255, 235, 59, 0.3)',
      },
    },
  },
  plugins: [],
};
