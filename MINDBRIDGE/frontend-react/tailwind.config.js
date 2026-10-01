/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        calm: {
          blue: "#DCEEFF",
          lavender: "#E9E2FF",
          mint: "#DFF5EC",
          beige: "#F8F3EA",
          slate: "#2D3748",
          charcoal: "#1A202C",
          surface: "rgba(255, 255, 255, 0.72)",
          glass: "rgba(255, 255, 255, 0.85)",
          border: "rgba(226, 232, 240, 0.8)",
        },
        emergency: {
          soft: "#FFF1F0",
          border: "#FFA39E",
          red: "#E53E3E",
          darkRed: "#9B1C1C",
          hover: "#C53030",
        },
        accent: {
          teal: "#0D9488",
          indigo: "#4F46E5",
          rose: "#E11D48",
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Poppins", "Nunito Sans", "sans-serif"],
        bengali: ["Noto Sans Bengali", "sans-serif"],
        hindi: ["Noto Sans Devanagari", "sans-serif"],
      },
      boxShadow: {
        'soft-glow': '0 0 50px rgba(186, 215, 255, 0.45)',
        'calm-card': '0 10px 30px -5px rgba(0, 0, 0, 0.04), 0 20px 25px -5px rgba(0, 0, 0, 0.02)',
        'elevated': '0 20px 40px -15px rgba(37, 99, 235, 0.08)',
      },
      animation: {
        'breath-slow': 'breathe 5s ease-in-out infinite',
      },
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(0.95)', opacity: '0.75' },
          '50%': { transform: 'scale(1.05)', opacity: '1.0' },
        }
      }
    },
  },
  plugins: [],
}
