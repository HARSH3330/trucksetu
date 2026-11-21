type Props = {checked: boolean; onChange: (checked: boolean) => void}

/** Required at signup; the acknowledged privacy-notice version is recorded by the server. */
export default function SignupConsent({checked, onChange}: Props) {
  return <label className="signup-consent">
    <input type="checkbox" required checked={checked} onChange={e => onChange(e.target.checked)} />
    <span>I agree to the <a href="#terms" target="_blank" rel="noopener">Terms &amp; Conditions</a> and have read the <a href="#privacy" target="_blank" rel="noopener">Privacy notice</a>.</span>
  </label>
}
