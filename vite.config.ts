import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins:[react()],
  cacheDir: process.env.TRANSIVOX_VITE_CACHE_DIR || 'node_modules/.vite',
  test: {include: ['src/**/*.test.{ts,tsx}', 'e2e/**/*.spec.ts'], exclude: ['e2e/kyc*.spec.ts', 'e2e/public-*.spec.ts', 'e2e/release-*.spec.ts', 'e2e/demand-*.spec.ts', 'e2e/customer-verification.spec.ts']},
});
