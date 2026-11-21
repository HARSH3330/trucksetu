import {defineConfig,devices} from '@playwright/test'

export default defineConfig({
  testDir:'./e2e',testMatch:'public-design.spec.ts',workers:1,retries:0,
  reporter:[['list'],['html',{outputFolder:'playwright-design-report',open:'never'}]],
  outputDir:'test-results/design',
  use:{...devices['Desktop Chrome'],baseURL:'http://127.0.0.1:5191',trace:'retain-on-failure',screenshot:'only-on-failure'},
  webServer:{command:'npm run build && npm run preview -- --host 127.0.0.1 --port 5191 --strictPort',url:'http://127.0.0.1:5191',reuseExistingServer:false,env:{...process.env,VITE_API_URL:'http://127.0.0.1:9/api/v1',VITE_MSG91_WIDGET_ID:'',VITE_MSG91_WIDGET_TOKEN_AUTH:''}},
})
