/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F5F6F3",
        panel: "#FFFFFF",
        ink: "#12181A",
        muted: "#5C6B69",
        line: "#DEE3E1",
        teal: {
          DEFAULT: "#0E6E66",
          dim: "#0E6E661A",
          deep: "#0A4F49",
        },
        amber: { DEFAULT: "#B7791F", bg: "#FBF0DD" },
        green: { DEFAULT: "#1F7A4D", bg: "#E6F4EB" },
        red: { DEFAULT: "#B3261E", bg: "#FBEAE9" },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
