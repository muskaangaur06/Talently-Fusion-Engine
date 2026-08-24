/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
      },
      colors: {
        paper: "#f4f3ee",
        card: "#fdfcf8",
        ink: {
          DEFAULT: "#23272b",
          soft: "#5b6370",
          faint: "#8b93a1",
        },
        line: {
          DEFAULT: "#e2dfd4",
          soft: "#eceada",
        },
        primary: {
          DEFAULT: "#0e7466",
          deep: "#0a574d",
          soft: "#dcede9",
          faint: "#eef5f3",
        },
        accent: {
          DEFAULT: "#c2711d",
          soft: "#f7ead8",
        },
        night: {
          DEFAULT: "#21252a",
          soft: "#2d3339",
        },
        success: {
          DEFAULT: "#1d7a46",
          soft: "#e2f0e6",
        },
        warning: {
          DEFAULT: "#a16207",
          soft: "#f6ecd4",
        },
        danger: {
          DEFAULT: "#b3402e",
          soft: "#f7e4df",
        },
        // Legacy brand alias kept pointing at the new primary so any
        // not-yet-migrated bg-brand-*/text-brand-* usages still resolve sensibly.
        brand: {
          50: "#eef5f3",
          100: "#dcede9",
          500: "#0e7466",
          600: "#0e7466",
          700: "#0a574d",
          900: "#21252a",
        },
      },
    },
  },
  plugins: [],
};
