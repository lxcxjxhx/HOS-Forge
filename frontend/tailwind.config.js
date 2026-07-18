/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react";
import typography from "@tailwindcss/typography";
export default {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        modal: {
          background: "#171717",
          input: "#27272A",
          primary: "#F3CE49",
          secondary: "#737373",
          muted: "#A3A3A3",
        },
        org: {
          border: "#171717",
          background: "#262626",
          divider: "#525252",
          button: "#737373",
          text: "#A3A3A3",
        },
        /* ── 安全风信子 HOS-Forge 主题色 ── */
        hyacinth: {
          deep:      "#2D1A36",
          deeper:    "#1E0F26",
          base:      "#392A40",
          light:     "#8C6E9F",
          lighter:   "#B49BC4",
          glow:      "#C9B0DB",
          crimson:   "#862C3B",
          'crimson-light': "#B33F4E",
          stem:      "#6CCB4C",
          'stem-dark': "#3B7A28",
          metal:     "#2C2D2F",
          'metal-dark': "#1A1A1C",
        },
        hos: {
          'bg-primary':   "#1E1F1D",
          'bg-secondary': "#272822",
          'bg-tertiary':  "#2C2D2F",
          'text-primary': "#B49BC4",
          'text-secondary': "#8C6E9F",
          'text-muted':   "#6B6F72",
          accent:         "#8C6E9F",
          danger:         "#B33F4E",
          success:        "#6CCB4C",
          warning:        "#D4A040",
          border:         "#2C2D2F",
          'border-light': "#3C3E42",
        },
      },
      fontFamily: {
        sans: ['Outfit', '-apple-system', 'SF Pro', 'Segoe UI', 'sans-serif'],
        mono: ['IBM Plex Mono', 'Fira Code', 'JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        hos: {
          sm:  '6px',
          md:  '10px',
          lg:  '16px',
          xl:  '24px',
        },
      },
      boxShadow: {
        'hos-glow':     '0 0 20px rgba(134, 44, 59, 0.4)',
        'hos-stem-glow':'0 0 15px rgba(108, 203, 76, 0.3)',
        'hos-md':       '0 4px 12px rgba(26, 26, 28, 0.8)',
      },
      animation: {
        'hos-glow':   'hos-glow 3s ease-in-out infinite',
        'hos-breathe':'hos-breathe 4s ease-in-out infinite',
      },
      keyframes: {
        'hos-glow': {
          '0%, 100%': { boxShadow: '0 0 5px rgba(134, 44, 59, 0.4)' },
          '50%':      { boxShadow: '0 0 20px rgba(140, 110, 159, 0.5)' },
        },
        'hos-breathe': {
          '0%, 100%': { opacity: '0.6' },
          '50%':      { opacity: '1' },
        },
      },
    },
  },
  plugins: [typography],
};
