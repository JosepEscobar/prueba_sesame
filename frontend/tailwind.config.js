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
                    50: '#f0f7ff',
                    100: '#e0efff',
                    200: '#c0dfff',
                    300: '#7ab7ff',
                    400: '#48aaff',
                    500: '#2a8af6',
                    600: '#2a4a6d',
                    700: '#1a416a',
                    800: '#193f69',
                    900: '#1e3a5f',
                },
                gray: {
                    100: '#f3f4f6',
                    200: '#e5e7eb',
                    300: '#d1d5db',
                    400: '#9ca3af',
                    500: '#6b7280',
                    600: '#4b5563',
                    700: '#374151',
                    750: '#1a1a1a',
                    800: '#1f2937',
                    900: '#111827',
                },
                chatgpt: {
                    background: '#212121e6',
                    surface: '#323232d9',
                    composer: '#303030',
                    sidebar: '#2b2b2b',
                    userBubble: '#2a4a6d',
                    userBubbleHover: '#1a416a',
                    error: '#f93a37',
                },
            },
            typography: {
                DEFAULT: {
                    css: {
                        maxWidth: 'none',
                        color: 'inherit',
                        a: {
                            color: '#7ab7ff',
                            '&:hover': {
                                color: '#5e83b3',
                            },
                        },
                        strong: {
                            color: 'inherit',
                            fontWeight: '700',
                        },
                        h1: {
                            color: 'inherit',
                            fontWeight: '700',
                        },
                        h2: {
                            color: 'inherit',
                            fontWeight: '700',
                        },
                        h3: {
                            color: 'inherit',
                            fontWeight: '700',
                        },
                        code: {
                            color: 'inherit',
                            fontWeight: '500',
                        },
                        pre: {
                            backgroundColor: '#323232d9',
                            color: '#f3f4f6',
                        },
                    },
                },
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
} 