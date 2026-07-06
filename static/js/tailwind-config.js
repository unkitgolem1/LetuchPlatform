tailwind.config = {
    theme: {
        extend: {
            colors: {
                'lotus-dark': '#0A3323',
                'lotus-moss': '#839958',
                'lotus-beige': '#F7F4D5',
                'lotus-rosy': '#D3968C',
                'lotus-midnight': '#105666',
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
                'sans': ['Inter', 'Helvetica Neue', 'system-ui', 'sans-serif'],
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
