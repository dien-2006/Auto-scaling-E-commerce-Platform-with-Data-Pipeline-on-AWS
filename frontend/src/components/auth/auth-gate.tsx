"use client";
import {useEffect,useState} from "react";
import {otpOptions,type OTPOptions} from "@/lib/otp-client";
import {AuthForm} from "@/components/auth/auth-form";
import {OTPForm} from "@/components/auth/otp-form";
export function AuthGate({mode,returnTo="/",registered=false}:{mode:"login"|"register"|"reset";returnTo?:string;registered?:boolean}){
  const [options,setOptions]=useState<OTPOptions|null>(null),[error,setError]=useState("");
  useEffect(()=>{let active=true;otpOptions().then(value=>{if(active)setOptions(value);}).catch(()=>{if(active)setError("Không kiểm tra được dịch vụ xác thực. Vui lòng tải lại trang.");});return()=>{active=false;};},[]);
  if(error)return <p className="shell auth-error" role="alert">{error}</p>;
  if(!options)return <p className="shell" role="status">Đang kiểm tra dịch vụ xác thực…</p>;
  if(mode==="reset")return <OTPForm purpose="RESET_PASSWORD" options={options} returnTo={returnTo}/>;
  if(mode==="register"&&options.enabled)return <OTPForm purpose="REGISTER" options={options} returnTo={returnTo}/>;
  return <AuthForm mode={mode} returnTo={returnTo} registered={registered}/>;
}
