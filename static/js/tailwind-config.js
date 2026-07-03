tailwind.config = {
    theme: {
        extend: {
            colors: {
                brand: {
                    DEFAULT: '#1D5D73',
                    dark: '#0F2D38',
                    light: '#C8C275',
                },
                wine: '#731D33',
                olive: '#736D1D',
                'old-gold': '#C8C275',
                'pastel-pink': '#F2B6C6',
                'hero-green': '#57984F',
                'glass-bg': 'rgba(29, 93, 115, 0.25)',
                'glass-hover': 'rgba(29, 93, 115, 0.35)',
                'glass-border': 'rgba(200, 220, 240, 0.12)',
                'glass-border-hover': 'rgba(200, 220, 240, 0.25)',
                'glass-modal': 'rgba(29, 93, 115, 0.35)',
                'glass-modal-border': 'rgba(200, 220, 240, 0.2)',
                'glass-footer': 'rgba(29, 93, 115, 0.15)',
                'glass-footer-border': 'rgba(200, 220, 240, 0.08)',
            },
            spacing: {
                'phi': '1.618rem',
                'phi-2': '2.618rem',
                'phi-3': '4.236rem',
                'phi-4': '6.854rem',
                'phi-5': '11.089rem',
            },
            fontSize: {
                'phi-base': ['1rem', { lineHeight: '1.618' }],
                'phi-1': ['1.618rem', { lineHeight: '1.2' }],
                'phi-2': ['2.618rem', { lineHeight: '1.2' }],
                'phi-3': ['4.236rem', { lineHeight: '1.1' }],
                'phi-4': ['6.854rem', { lineHeight: '1.1' }],
            },
            fontFamily: {
                'sans': ['Satoshi', 'system-ui', '-apple-system', 'sans-serif'],
                'heading': ['archivo-black', 'system-ui', '-apple-system', 'sans-serif'],
            },
            maxWidth: {
                'phi': '61.8%',
                'phi-container': '1200px',
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.5s ease-out',
                'hx-fade-in': 'hxFadeIn 0.4s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                hxFadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(0.618rem)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
            },
        },
    },
}
