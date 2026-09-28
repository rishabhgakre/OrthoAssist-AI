/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // ---- Brand ----
        // Exact requested brand ink — the ONE dark surface color used across
        // sidebar, login panel, dark cards and buttons, so every dark surface
        // in the app is provably the same color rather than eyeballed shades.
        ink: "rgb(3 26 7)",
        "ink-raised": "#0A2C12", // one step lighter than ink, for cards/rows sitting on top of it
        "ink-line": "#153420",   // hairline borders/dividers on dark surfaces
        lightbox: "rgb(3 26 7)", // alias so any legacy reference still matches the brand ink
        gold: {
          DEFAULT: "#C9A66B",
          bright: "#DCC28F",
          light: "#DCC28F",
          dim: "rgba(201,166,107,0.5)",
          bg: "#F5EEDD",
        },
        // Secondary pillar accent — used consistently for anything tied to
        // Functional/Gait recovery, mirroring gold's role for Structural.
        amethyst: {
          DEFAULT: "#6B4C9A",
          bright: "#9B7FC4",
          bg: "#EFE9F6",
        },

        // ---- Surfaces ----
        page: "#F2F0EA",
        card: "#FAF8F4",
        "card-alt": "#F3EFE3",
        border: {
          DEFAULT: "#E2DED2",
          strong: "#CCC6B6",
        },

        // ---- Text ----
        body: "#1C231F",
        muted: "#8A8478",
        faint: "#ABA79A",

        // ---- Gemstone recovery-status system ----
        // malachite = strong/good, topaz = moderate, garnet = needs attention.
        // garnet doubles as the app's one red accent (alerts, destructive).
        malachite: { DEFAULT: "#1E7A5C", bright: "#3FAF8A", bg: "#E1EFE8" },
        topaz: { DEFAULT: "#A8752E", bright: "#D9A857", bg: "#F3EAD6" },
        garnet: { DEFAULT: "#8B2635", bright: "#C85E6E", bg: "#F3E0E2" },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,30,20,0.05)",
        "card-hover": "0 8px 24px rgba(20,30,20,0.08)",
        panel: "0 20px 60px rgba(3,26,7,0.25)",
        gold: "0 0 0 1px rgba(201,166,107,0.35), 0 8px 24px rgba(201,166,107,0.15)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      keyframes: {
        "fade-in": { from: { opacity: 0 }, to: { opacity: 1 } },
        "slide-up": { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        "slide-in-right": { from: { opacity: 0, transform: "translateX(16px)" }, to: { opacity: 1, transform: "translateX(0)" } },
        shimmer: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
      },
      animation: {
        "fade-in": "fade-in .2s ease-out",
        "slide-up": "slide-up .25s cubic-bezier(.16,1,.3,1)",
        "slide-in-right": "slide-in-right .25s cubic-bezier(.16,1,.3,1)",
        shimmer: "shimmer 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
}
