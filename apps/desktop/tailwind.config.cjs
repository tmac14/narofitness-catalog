/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      /**
       * UX 3.0 semantic platform screens (Phase 0).
       * Default Tailwind breakpoints sm/md/lg/xl/2xl are NOT replaced.
       *
       * Semantics (each alias applies ONLY within its band unless noted):
       * - mobile:  max-width 639px  → mobile band only (0–639px)
       * - tablet:  min 640px, max 1023px → tablet band only
       * - desktop: min 1024px, max 1279px → desktop band only
       * - wide:    min-width 1280px → wide band and above (1280px+)
       *
       * For min-width “and up”, continue using sm (640+), lg (1024+), xl (1280+).
       * Canonical TS constants: src/lib/responsive/breakpoints.ts
       */
      screens: {
        mobile: { max: "639px" },
        tablet: { min: "640px", max: "1023px" },
        desktop: { min: "1024px", max: "1279px" },
        wide: "1280px",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
      colors: {
        narofitness: {
          black: "var(--nr-black)",
          graphite: "var(--nr-graphite)",
          surface: "var(--nr-surface)",
          "surface-2": "var(--nr-surface-2)",
          border: "var(--nr-border)",
          "border-soft": "var(--nr-border-soft)",
          text: "var(--nr-text)",
          "text-muted": "var(--nr-text-muted)",
          "text-subtle": "var(--nr-text-subtle)",
          white: "var(--nr-white)",
          green: "var(--nr-green)",
          "green-bright": "var(--nr-green-bright)",
          "green-dark": "var(--nr-green-dark)",
          "green-soft-bg": "var(--nr-green-soft-bg)",
        },
        "preview-canvas": "var(--preview-canvas)",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        row: {
          warning: "hsl(var(--row-warning-bg))",
          error: "hsl(var(--row-error-bg))",
          infoA: "hsl(var(--row-info-a-bg))",
          infoB: "hsl(var(--row-info-b-bg))",
          selected: "hsl(var(--row-selected-bg))",
          hover: "hsl(var(--row-hover-bg))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      spacing: {
        4.5: "1.125rem",
        18: "4.5rem",
        "touch-target": "var(--touch-target-min)",
        "touch-gap": "var(--touch-target-gap)",
      },
      fontSize: {
        "2xs": ["0.65rem", { lineHeight: "1rem" }],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
