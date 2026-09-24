import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "#FAFAF8",
        navy: {
          DEFAULT: "#0A1628",
          light: "#132238",
        },
        blue: {
          DEFAULT: "#1D4ED8",
          dark: "#1E3A8A",
        },
        grey: {
          line: "#E5E5E5",
          section: "#F4F4F2",
          muted: "#8A93A3",
        },
        ink: "#080808",
        background: "#FAFAF8",
        foreground: "#0A1628",
        "muted-foreground": "#8A93A3",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sharp: "4px",
      },
      letterSpacing: {
        tightest: "-0.02em",
        wide: "0.08em",
      },
      maxWidth: {
        content: "1280px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
