export const PRIVACY_VERSION = 'privacy-v1-20261104'
export const PRIVACY_CONTACT = 'harshagarwal244@gmail.com'

export type PrivacySection = {heading: string; paragraphs?: string[]; items?: string[]}

export const PRIVACY_SECTIONS: PrivacySection[] = [
  {heading: '1. Who we are', paragraphs: [
    'TransivoX (www.transivox.in) is operated by TransivoX Private Limited (“we”, “us”). TransivoX is a marketplace that connects customers with independent transport providers.',
    `Contact and grievance: ${PRIVACY_CONTACT}.`]},
  {heading: '2. What we collect', items: [
    'Account details: name, email address, mobile number (if you add one), password (stored only as a secure hash) and your role (customer, provider or driver).',
    'Transport requirements: routes, pickup and delivery details, cargo information, schedules and map pins if you choose to use map search.',
    'Verification documents: for customers, your PAN; for providers and drivers, identity, business and vehicle documents (for example registration, insurance, fitness, pollution and permit).',
    'Payments: payments are processed by Razorpay. We receive the payment status and reference, not your card or bank details.',
    'Technical data: IP address, device and browser details and security logs.']},
  {heading: '3. Your PAN', paragraphs: [
    'We ask customers for their PAN only to verify the customer account and reduce misuse before a transport requirement is published. Your document is not shown to providers, is not published with your requirement and is viewed only by authorised reviewers.']},
  {heading: '4. Why we use your data', paragraphs: [
    'To create and secure your account; to verify customers and providers; to publish requirements and show bids; to process the platform connection fee and refunds; to send account and booking emails; to prevent fraud and misuse; to resolve disputes; and to meet legal obligations. We rely on your consent, which you can withdraw (see section 8).']},
  {heading: '5. Who processes your data for us', items: [
    'Amazon Web Services (Mumbai): private encrypted storage of verification documents and malware scanning.',
    'Neon (database, United States region): our database, which holds account and booking records. Some data is therefore stored outside India.',
    'Vercel: website and application hosting.',
    'Razorpay: payments.',
    'Brevo: transactional emails such as verification codes.',
    'Google (Maps and Places): only if you choose to load map search; your map searches are shared with Google.'],
   paragraphs: ['We do not sell your personal data.']},
  {heading: '6. Security', paragraphs: [
    'Documents are stored in a private, encrypted bucket with no public access, are scanned for malware, and are opened only through short-lived authorised links by authorised reviewers. No system is perfectly secure.']},
  {heading: '7. How long we keep data', items: [
    'Verification documents (PAN): kept while your account is active; deleted, including all stored versions, within 30 days after you close your account or withdraw consent.',
    'Rejected or abandoned submissions: deleted within 30 days of rejection if you do not resubmit.',
    'Account data: kept while your account is active; deleted or anonymised within 90 days after closure.',
    'Payment, invoice and tax records: kept for the period required by Indian tax and accounting law.',
    'Security and audit logs: kept for 12 months.']},
  {heading: '8. Your rights', paragraphs: [
    `You may ask to access, correct or erase your data, withdraw consent, or raise a grievance by emailing ${PRIVACY_CONTACT}. Withdrawing consent for verification means you can no longer publish requirements. We will respond within 30 days.`]},
  {heading: '9. Children', paragraphs: ['TransivoX is not for anyone under 18.']},
  {heading: '10. Changes', paragraphs: ['We will publish changes on this page with a new version number.']},
]
