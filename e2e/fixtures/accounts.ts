export const providerAccount = {
  email: process.env.E2E_PROVIDER_EMAIL || 'provider.e2e@example.com',
  password: process.env.E2E_PROVIDER_PASSWORD || 'ProviderE2E123!',
}

export const adminAccount = {
  email: process.env.E2E_ADMIN_EMAIL || 'admin.e2e@example.com',
  password: process.env.E2E_ADMIN_PASSWORD || 'AdminE2E123!Secure',
}
