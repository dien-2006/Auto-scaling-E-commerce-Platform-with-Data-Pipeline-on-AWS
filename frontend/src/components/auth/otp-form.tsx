"use client";

import Link from "next/link";
import {useEffect,useRef,useState,type FormEvent,type ReactNode} from "react";
import {AuthFailure} from "@/lib/auth-client";
import {requestOTP,otpMutation,verifyEmailOTP,type OTPOptions,type Challenge,type EmailProof} from "@/lib/otp-client";
import {accountFrom,validRegistrationPassword,registrationPasswordHint,safeReturnPath} from "@/lib/auth-contract";
import {ResetReferenceArt} from "./reset-reference-art";
import {RegisterReferenceArt} from "./register-reference-art";

function FieldIcon({kind}:{kind:"mail"|"lock"|"user"|"shield"}){
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">{kind==="mail"?<><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 6 8 7 8-7"/></>:kind==="lock"?<><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/></>:kind==="user"?<><circle cx="12" cy="8" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/></>:<><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/></>}</svg>;
}
function InputField({id,label,kind,children}:{id:string;label:string;kind:"mail"|"lock"|"user"|"shield";children:ReactNode}){
  return <div className="otp-field-group"><label htmlFor={id}>{label}</label><div className="otp-input-field"><FieldIcon kind={kind}/>{children}</div></div>;
}
function PasswordFields({register}:{register:boolean}){
  const [show,setShow]=useState(false);
  return <><InputField id="otp-password" label={register?"Mật khẩu":"Mật khẩu mới"} kind="lock"><input id="otp-password" name="password" placeholder={register?"Mật khẩu":"Mật khẩu mới"} type={show?"text":"password"} required minLength={9} maxLength={128} autoComplete="new-password" aria-describedby="otp-password-hint"/><button className="otp-password-toggle" type="button" aria-label={show?"Ẩn mật khẩu":"Hiện mật khẩu"} aria-pressed={show} onClick={()=>setShow(!show)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>{!show&&<path d="m3 3 18 18"/>}</svg></button></InputField><p id="otp-password-hint" className="auth-field-hint">{registrationPasswordHint}</p><InputField id="otp-confirm" label="Xác nhận mật khẩu" kind="lock"><input id="otp-confirm" name="confirm" placeholder="Xác nhận mật khẩu" type={show?"text":"password"} required minLength={9} maxLength={128} autoComplete="new-password"/></InputField></>;
}

export function OTPForm({purpose,options,returnTo="/"}:{purpose:"REGISTER"|"RESET_PASSWORD";options:OTPOptions;returnTo?:string}){
  const register=purpose==="REGISTER";
  const [target,setTarget]=useState("");
  const [challenge,setChallenge]=useState<Challenge|null>(null);
  const [proof,setProof]=useState<EmailProof|null>(null);
  const [until,setUntil]=useState(0),[proofUntil,setProofUntil]=useState(0),[now,setNow]=useState(0);
  const [action,setAction]=useState<"send"|"verify"|"complete"|null>(null);
  const [error,setError]=useState(""),[notice,setNotice]=useState(""),[done,setDone]=useState(false);
  const guard=useRef(false),emailInput=useRef<HTMLInputElement>(null),codeInput=useRef<HTMLInputElement>(null),alert=useRef<HTMLParagraphElement>(null);
  const busy=action!==null;
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[]);
  useEffect(()=>{if(error)alert.current?.focus();},[error]);
  const remaining=Math.max(0,Math.ceil((until-now)/1000));
  const proofRemaining=Math.max(0,Math.ceil((proofUntil-now)/1000));
  const loginURL=`/dang-nhap?returnTo=${encodeURIComponent(safeReturnPath(returnTo))}`;
  function failure(error:unknown){setError(error instanceof Error?error.message:"Chưa xử lý được yêu cầu. Vui lòng thử lại.");}
  function changeEmail(value:string){setTarget(value);setChallenge(null);setProof(null);setUntil(0);setNotice("");setError("");if(codeInput.current)codeInput.current.value="";}
  function restart(){setChallenge(null);setProof(null);setUntil(0);setNotice("");setError("");}
  async function send(){
    if(guard.current||!emailInput.current?.reportValidity())return;
    guard.current=true;setAction("send");setError("");setNotice("");
    try{const next=await requestOTP({purpose,channel:"EMAIL",target:target.trim()});setChallenge(next);setProof(null);const current=Date.now();setNow(current);setUntil(current+60000);if(codeInput.current)codeInput.current.value="";setNotice("Nếu email hợp lệ, mã xác minh sẽ được gửi. Kiểm tra hộp thư và thư rác; mã có hiệu lực 1 phút.");}
    catch(error){failure(error);}finally{guard.current=false;setAction(null);}
  }
  async function verifyCode(){
    if(!challenge||!remaining||!codeInput.current?.reportValidity())return null;
    const next=await verifyEmailOTP(challenge,codeInput.current.value,purpose);
    const current=Date.now();setNow(current);setProof(next);setProofUntil(current+next.expires_in*1000);setNotice(register?"Email đã được xác minh.":"Email đã được xác minh. Bạn có thể đặt mật khẩu mới.");return next;
  }
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(guard.current)return;
    const form=event.currentTarget,values=new FormData(form);
    if(!register&&!proof&&!challenge){await send();return;}
    if(register||proof){
      const password=String(values.get("password")||"");
      if(password!==values.get("confirm")||!validRegistrationPassword(password)){setError(password!==values.get("confirm")?"Mật khẩu xác nhận chưa khớp.":registrationPasswordHint);return;}
    }
    if(!proof&&(!challenge||!remaining)){setError("Vui lòng gửi và nhập mã xác minh còn hiệu lực.");return;}
    if(proof&&!proofRemaining){setError("Phiên xác minh đã hết hạn. Vui lòng lấy mã mới.");return;}
    guard.current=true;setAction(!proof?"verify":"complete");setError("");
    let completing=false;
    try{
      const verified=proof||await verifyCode();if(!verified)return;
      if(!register&&!proof)return; // The reset password fields only appear AFTER server verification.
      completing=true;setAction("complete");
      const result=await otpMutation(register?"otp-register":"password-reset",{verification_token:verified.verification_token,...(register?{full_name:String(values.get("full_name")||"").trim(),password:String(values.get("password")||"")}:{new_password:String(values.get("password")||"")})});
      if(result.purpose!==purpose||(register&&!accountFrom(result.user)))throw new AuthFailure("UNAVAILABLE");
      form.reset();setProof(null);setDone(true);setNotice("");
    }catch(error){
      if(completing){setProof(null);setChallenge(null);setUntil(0);setNotice("");const uncertain=error instanceof AuthFailure&&["UNAVAILABLE","NETWORK_ERROR","OTP_UNAVAILABLE","SERVER_ERROR"].includes(error.code);setError(`${error instanceof Error?error.message:"Chưa xác nhận được kết quả."}${uncertain?" Hãy thử đăng nhập bằng mật khẩu vừa đặt trước khi yêu cầu mã mới.":" Vui lòng xác minh email lại."}`);}
      else failure(error);
    }finally{guard.current=false;setAction(null);}
  }
  const emailField=<InputField id="otp-target" label="Email" kind="mail"><input ref={emailInput} id="otp-target" name="target" type="email" value={target} onChange={event=>changeEmail(event.target.value)} placeholder="Email" autoComplete="email" required maxLength={255} readOnly={!register&&!!challenge}/></InputField>;
  const codeField=<InputField id="otp-code" label="Mã xác minh" kind="shield"><input ref={codeInput} id="otp-code" name="code" placeholder="Mã xác minh" inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} autoComplete="one-time-code" required disabled={!challenge||remaining===0}/></InputField>;
  return <div className={`auth-scene otp-scene ${register?"auth-scene-register otp-register-scene":"otp-reset-scene"}`}>
    {register?<RegisterReferenceArt/>:<ResetReferenceArt/>}
    <section className="auth-form-card otp-form-card" aria-labelledby="otp-title">
      <div className={register?"otp-register-title":"otp-reset-title"}>{<span className="auth-title-rays" aria-hidden="true"><svg viewBox="0 0 36 50" width="30" height="42" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round"><path d="m25 4 8 12M5 21l17 6M8 44l15-5"/></svg></span>}
      <h1 id="otp-title">{register?"Đăng ký tài khoản":"Quên mật khẩu"}</h1></div>
      {!register&&!done&&<p className="otp-reset-description">Nhập email để nhận mã xác minh và đặt lại mật khẩu.</p>}
      {!register&&!done&&<ol className="otp-steps" aria-label="Các bước khôi phục"><li aria-current={!challenge&&!proof?"step":undefined}>1. Email</li><li aria-current={challenge&&!proof?"step":undefined}>2. Xác minh</li><li aria-current={proof?"step":undefined}>3. Mật khẩu mới</li></ol>}
      {error&&<p className="auth-error" role="alert" ref={alert} tabIndex={-1}>{error}</p>}
      {notice&&!done&&<p className="otp-notice" role="status">{notice}</p>}
      {done?<><p className="auth-success" role="status"><strong>{register?"Tạo tài khoản thành công!":"Đổi mật khẩu thành công!"}</strong><span>Vui lòng đăng nhập bằng mật khẩu của bạn.</span></p><Link href={loginURL} className="primary-button">Đăng nhập</Link></>:!options.email?<p role="status">Dịch vụ gửi OTP chưa được cấu hình. Vui lòng thử lại sau.</p>:<form onSubmit={submit} aria-busy={busy}><fieldset disabled={busy}>
        {register?<>
          {emailField}
          <div className="otp-inline-code">{codeField}<button className="otp-send-button" type="button" onClick={()=>void send()} disabled={busy||!!challenge&&remaining>0}>{action==="send"?"Đang gửi…":challenge&&remaining>0?`Gửi lại (${remaining}s)`:challenge?"Gửi lại mã":"Gửi mã"}</button></div>
          {challenge&&<p className="otp-clock" role="timer">{remaining?`Mã hết hạn sau ${remaining} giây`:"Mã đã hết hạn. Vui lòng gửi lại mã."}</p>}
          <InputField id="otp-name" label="Họ và tên" kind="user"><input id="otp-name" name="full_name" required maxLength={150} autoComplete="name" placeholder="Họ và tên"/></InputField>
          <PasswordFields register/>
          <button className="auth-submit" type="submit" disabled={!challenge||!remaining}>{busy?"Đang xử lý…":"Đăng ký"}</button>
        </>:proof?<>
          <p className="otp-verified-address">Đã xác minh: {target}</p>
          <PasswordFields register={false}/>
          <p className="otp-clock" role="timer">{proofRemaining?`Đặt mật khẩu trong ${Math.floor(proofRemaining/60)}:${String(proofRemaining%60).padStart(2,"0")}`:"Phiên xác minh đã hết hạn."}</p>
          <button className="auth-submit" type="submit" disabled={!proofRemaining}>{busy?"Đang đặt lại mật khẩu…":"Đặt lại mật khẩu"}</button>
          <button className="secondary-button" type="button" onClick={restart}>Xác minh lại email</button>
        </>:<>
          {emailField}
          <div className="otp-inline-code">{codeField}<button className="otp-send-button" type="button" onClick={()=>void send()} disabled={busy||!!challenge&&remaining>0}>{action==="send"?"Đang gửi…":challenge&&remaining>0?`Gửi lại (${remaining}s)`:challenge?"Gửi lại mã":"Gửi mã"}</button></div>
          {challenge&&<p className="otp-clock" role="timer">{remaining?`Mã hết hạn sau ${remaining} giây`:"Mã đã hết hạn. Vui lòng gửi lại mã."}</p>}
          <button className="auth-submit" type="submit" disabled={!challenge||!remaining}>{action==="verify"?"Đang xác minh…":"Xác minh mã OTP"}</button>
          {challenge&&<div className="otp-actions"><button className="secondary-button" type="button" onClick={restart}>Đổi email</button></div>}
        </>}
      </fieldset></form>}
      {register&&!done&&options.email&&<div className="otp-social-preview"><div className="login-social-divider"><span>Hoặc đăng ký với</span></div><div className="login-social-options"><button type="button" disabled title="Chưa hỗ trợ"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="#4285f4" d="M21.6 12.2c0-.7-.1-1.4-.2-2.1H12v4h5.4a4.6 4.6 0 0 1-2 3v2.6h3.3c1.9-1.8 2.9-4.4 2.9-7.5Z"/><path fill="#34a853" d="M12 22c2.7 0 4.9-.9 6.6-2.4l-3.3-2.6c-.9.6-2 1-3.3 1-2.6 0-4.8-1.8-5.6-4.2H3v2.7A10 10 0 0 0 12 22Z"/><path fill="#fbbc05" d="M6.4 13.8a6 6 0 0 1 0-3.6V7.5H3a10 10 0 0 0 0 9l3.4-2.7Z"/><path fill="#ea4335" d="M12 6c1.5 0 2.8.5 3.9 1.5l2.9-2.9A9.6 9.6 0 0 0 12 2a10 10 0 0 0-9 5.5l3.4 2.7C7.2 7.8 9.4 6 12 6Z"/></svg>Google</button><button type="button" disabled title="Chưa hỗ trợ"><span className="social-facebook" aria-hidden="true">f</span>Facebook</button><button type="button" disabled title="Chưa hỗ trợ"><svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="M16.8 2c.2 2.1-1.4 4-3.4 4.3-.3-2 1.4-4 3.4-4.3ZM19.7 17.8c-.7 1.5-1.8 3.4-3.4 3.4-1.4 0-1.7-.8-3.4-.8s-2.1.8-3.5.8c-1.6 0-2.8-2.1-3.6-3.7C3.6 13 4.8 7.2 8.7 7.2c1.5 0 2.5.9 3.8.9 1.2 0 2.4-1 3.9-.9 1.3 0 2.7.7 3.5 1.8-3.3 1.8-2.8 6 .4 7.3l-.6 1.5Z"/></svg>Apple</button></div><p className="login-social-note">Đăng ký mạng xã hội chưa được hỗ trợ.</p></div>}
      {!done&&<p className="auth-switch">{register?"Bạn đã có tài khoản? ":""}<Link href={loginURL}>{register?"Đăng nhập":"Quay lại đăng nhập"}</Link></p>}
    </section>
  </div>;
}
