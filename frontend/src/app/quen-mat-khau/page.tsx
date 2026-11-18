import {AuthGate} from "@/components/auth/auth-gate";
import {safeReturnPath} from "@/lib/auth-contract";
export const metadata={title:"Quên mật khẩu | COCO",robots:{index:false}};
export default async function Page({searchParams}:{searchParams:Promise<{returnTo?:string}>}){const params=await searchParams;return <AuthGate mode="reset" returnTo={safeReturnPath(params.returnTo)}/>;}
