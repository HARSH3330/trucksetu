import {defineConfig,devices} from '@playwright/test'

export default defineConfig({
  testDir:'./e2e',testMatch:['**/public-navigation.spec.ts','**/public-widget.spec.ts','**/public-ux.spec.ts','**/public-followup.spec.ts'],workers:1,retries:0,
  reporter:[['list'],['html',{outputFolder:'playwright-public-report',open:'never'}]],outputDir:'test-results/public',
  use:{...devices['Desktop Chrome'],baseURL:'http://127.0.0.1:5190',trace:'retain-on-failure',screenshot:'only-on-failure'},
  // No database/auth/scanner reset. This suite checks public negative states
  // against a deliberately unreachable LOCAL API, never production.
  webServer:{command:'npm run dev -- --host 127.0.0.1 --port 5190 --strictPort',url:'http://127.0.0.1:5190',reuseExistingServer:false,env:{...process.env,VITE_API_URL:'http://127.0.0.1:9/api/v1',VITE_MSG91_WIDGET_ID:'fictional-browser-widget',VITE_MSG91_WIDGET_TOKEN_AUTH:'fictional-public-widget-token'}},
})
