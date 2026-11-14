export type SignupForm={name:string;email:string;mobile:string;password:string;role:string}

/** The signup tick covers the Terms version loaded with the form; without it the Terms are asked again before publishing. */
export function signupBody(form:SignupForm,privacyVersion:string,termsVersion:string|null){
  return {full_name:form.name,email:form.email,mobile:form.mobile.trim()||null,password:form.password,role:form.role,privacy_notice_version:privacyVersion,...(termsVersion?{terms_version:termsVersion}:{})}
}
