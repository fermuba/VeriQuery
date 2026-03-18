/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        background:  'hsl(var(--background))',
        foreground:  'hsl(var(--foreground))',
        primary:     'hsl(var(--primary))',
        'primary-foreground': 'hsl(var(--primary-foreground))',
        muted:       'hsl(var(--muted))',
        'muted-foreground': 'hsl(var(--muted-foreground))',
        border:      'hsl(var(--border))',
        card:        'hsl(var(--card))',
        accent:      'hsl(var(--accent))',
        destructive: 'hsl(var(--destructive))',
        success:     'hsl(var(--success))',
        warning:     'hsl(var(--warning))',
      },
    },
  },
  plugins: [],
}
