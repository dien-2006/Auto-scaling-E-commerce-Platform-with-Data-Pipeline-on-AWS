import { AuthFailure } from "@/lib/auth-client";
export type OTPOptions={enabled:boolean;email:boolean;sms:boolean};
export type Challenge={challenge_id:string;expires_in:number;resend_after:number};
export async function otpOptions():Promise<OTPOptions>{
  const response=await fetch("/api/v1/auth/otp-options",{cache:"no-store",credentials:"same-origin",signal:AbortSignal.timeout(10000)});
  const value=await response.json();
  if(!response.ok || typeof value.enabled!=="boolean" || typeof value.email!=="boolean" || typeof value.sms!=="boolean")throw new AuthFailure("UNAVAILABLE");
  return value;
}
export async function otpMutation(endpoint:"otp-request"|"otp-verify"|"otp-register"|"password-reset",data:Record<string,unknown>):Promise<Record<string,unknown>> {
  try{
    const csrf=await fetch("/api/v1/auth/csrf",{cache:"no-store",credentials:"same-origin",signal:AbortSignal.timeout(10000)});
    const token=await csrf.json();
    if(!csrf.ok || typeof token?.data?.csrf_token!=="string")throw new AuthFailure("CSRF_FAILED");
    const response=await fetch(`/api/v1/auth/${endpoint}`,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-CSRF-Token":token.data.csrf_token},body:JSON.stringify(data),signal:AbortSignal.timeout(20000)});
    const value=await response.json().catch(()=>null);
    if(!response.ok)throw new AuthFailure(typeof value?.error?.code==="string"?value.error.code:response.status===429?"RATE_LIMITED":"UNAVAILABLE");
    if(!value?.data || typeof value.data!=="object")throw new AuthFailure("UNAVAILABLE");
    return value.data;
  }catch(error){if(error instanceof AuthFailure)throw error;throw new AuthFailure("NETWORK_ERROR");}
}
export async function requestOTP(data:Record<string,unknown>):Promise<Challenge>{
  const value=await otpMutation("otp-request",data);
  if(typeof value.challenge_id!=="string" || !/^[0-9a-f-]{36}$/i.test(value.challenge_id) || value.expires_in!==60 || value.resend_after!==60)throw new AuthFailure("UNAVAILABLE");
  return value as Challenge;
}

export type EmailProof={purpose:"REGISTER"|"RESET_PASSWORD";verification_token:string;expires_in:number};
export async function verifyEmailOTP(challenge:Challenge,code:string,purpose:EmailProof["purpose"]):Promise<EmailProof>{
  const value=await otpMutation("otp-verify",{challenge_id:challenge.challenge_id,code});
  if(value.purpose!==purpose || typeof value.verification_token!=="string" || !/^[0-9a-f]{64}$/.test(value.verification_token) || value.expires_in!==300)throw new AuthFailure("UNAVAILABLE");
  return value as EmailProof;
}
