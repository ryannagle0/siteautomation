import type { Config } from "tailwindcss";

// Every value points at a CSS variable in src/tokens.css, so one set of
// classes renders correctly in all four presets. To change a colour, edit
// tokens.css — never add hex values here or in components.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)" },
        ink: "var(--text)",
        muted: "var(--muted)",
        line: "var(--border)",
        accent: {
          DEFAULT: "var(--accent)",
          fg: "var(--accent-fg)",
          ink: "var(--accent-ink)",
          soft: "var(--accent-soft)",
          line: "var(--accent-line)",
          hover: "var(--accent-hover)",
        },
        band: {
          DEFAULT: "var(--band)",
          ink: "var(--band-text)",
          muted: "var(--band-muted)",
          line: "var(--band-border)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
      },
      fontSize: {
        "step--2": "var(--step--2)",
        "step--1": "var(--step--1)",
        "step-small": "var(--step-small)",
        "step-0": "var(--step-0)",
        "step-1": "var(--step-1)",
        "step-2": "var(--step-2)",
        "step-3": "var(--step-3)",
        "step-4": "var(--step-4)",
        "step-5": "var(--step-5)",
      },
      borderRadius: {
        theme: "var(--radius)",
        "theme-lg": "var(--radius-lg)",
        btn: "var(--btn-radius)",
      },
      borderWidth: {
        theme: "var(--border-w)",
      },
      spacing: {
        section: "var(--section-y)",
        gutter: "var(--gutter)",
        "call-bar": "var(--call-bar-h)",
      },
      maxWidth: {
        content: "var(--maxw)",
        prose: "65ch",
      },
      transitionTimingFunction: {
        out: "var(--ease-out)",
      },
    },
  },
  plugins: [],
};
export default config;
