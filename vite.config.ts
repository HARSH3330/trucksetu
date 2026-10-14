import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins:[react()],
  test: {include: ['src/**/*.test.{ts,tsx}', 'e2e/**/*.spec.ts'], exclude: ['e2e/kyc*.spec.ts', 'e2e/public-*.spec.ts']},
});
