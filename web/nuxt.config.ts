// https://nuxt.com/docs/api/configuration/nuxt-config
const favicon =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23e4f222'/%3E%3Ctext x='16' y='22' font-family='Arial' font-weight='700' font-size='16' text-anchor='middle' fill='%231b1b16'%3EC%3C/text%3E%3C/svg%3E"

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  ssr: false,
  devServer: { port: 3100 },
  nitro: {
    devProxy: {
      '/api': { target: 'http://127.0.0.1:8600/api', changeOrigin: true },
    },
  },
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      title: 'ContractCop',
      htmlAttrs: { lang: 'en' },
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
      link: [
        { rel: 'icon', href: favicon },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap',
        },
      ],
    },
  },
})
