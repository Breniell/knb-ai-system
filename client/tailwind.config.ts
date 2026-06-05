import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm editorial neutrals
        paper: "#FBFAF7",
        surface: "#FFFFFF",
        "surface-2": "#F4F2EC",
        "surface-3": "#ECE9E1",
        line: "#E6E3DA",
        "line-strong": "#D8D4C8",
        ink: "#1B1A16",
        "ink-soft": "#3D3B34",
        muted: "#6E6B61",
        faint: "#9A968A",
        // Brand — jewel teal/green (honours KNB blue→green identity, refined)
        brand: {
          50: "#ECFBF5",
          100: "#D2F4E6",
          200: "#A7E8CF",
          300: "#6FD4B2",
          400: "#36B98F",
          500: "#129E76",
          600: "#0E7C66",
          700: "#0C6253",
          800: "#0C4E43",
          900: "#0A3F38",
        },
        // Secondary accent — warm clay/amber for data + highlights
        clay: {
          100: "#FBEEDD",
          300: "#EEC79A",
          500: "#D08A3C",
          600: "#B5712A",
          700: "#8F5620",
        },
        // Status
        ok: "#0E7C66",
        warn: "#B5712A",
        danger: "#C0453B",
        info: "#2563A8",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "Georgia", "serif"],
        sans: ['"Public Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.375rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(27,26,22,0.04), 0 1px 3px rgba(27,26,22,0.06)",
        lift: "0 4px 16px -4px rgba(27,26,22,0.10), 0 2px 6px -2px rgba(27,26,22,0.06)",
        pop: "0 12px 40px -8px rgba(27,26,22,0.18)",
      },
      keyframes: {
        "fade-in": { from: { opacity: "0", transform: "translateY(4px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        "scale-in": { from: { opacity: "0", transform: "scale(0.97)" }, to: { opacity: "1", transform: "scale(1)" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        "fade-in": "fade-in 0.4s cubic-bezier(0.16,1,0.3,1)",
        "scale-in": "scale-in 0.3s cubic-bezier(0.16,1,0.3,1)",
      },
    },
  },
  plugins: [],
} satisfies Config;
