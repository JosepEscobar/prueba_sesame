/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f0fdf4',
                    100: '#dcfce7',
                    200: '#bbf7d0',
                    300: '#86efac',
                    400: '#4ade80',
                    500: '#22c55e',
                    600: '#16a34a',
                    700: '#15803d',
                    800: '#166534',
                    900: '#14532d',
                },
                secondary: {
                    50: '#f5f7fa',
                    100: '#ebeef5',
                    200: '#d2dae7',
                    300: '#afbcd4',
                    400: '#8898bc',
                    500: '#6879a6',
                    600: '#4f5c8a',
                    700: '#414b71',
                    800: '#36405f',
                    900: '#2e364f',
                },
            },
        },
    },
    plugins: [],
} 