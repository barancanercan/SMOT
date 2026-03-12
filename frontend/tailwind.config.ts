import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Party colors
        chp: "#e31b23",
        akp: "#ffa500",
        mhp: "#c8102e",
        bbp: "#1e3a8a",
        yrp: "#006400",
        bagimsiz: "#808080",
      },
    },
  },
  plugins: [],
};

export default config;
