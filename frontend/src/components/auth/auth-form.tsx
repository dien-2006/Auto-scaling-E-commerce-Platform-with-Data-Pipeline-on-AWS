"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, type FormEvent } from "react";
import { AuthFailure, mutateAuth } from "@/lib/auth-client";
import {
  safeReturnPath,
  validRegistrationPassword,
  registrationPasswordHint,
} from "@/lib/auth-contract";
import { useSession } from "@/components/auth/session-provider";
import { RegisterReferenceArt } from "@/components/auth/register-reference-art";
import { LoginReferenceArt } from "@/components/auth/login-reference-art";
export function AuthForm({
  mode,
  returnTo,
  registered = false,
  phoneLogin = false,
}: {
  mode: "login" | "register";
  returnTo: string;
  registered?: boolean;
  phoneLogin?: boolean;
}) {
  const register = mode === "register";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
  const [show, setShow] = useState(false);
  const guard = useRef(false);
  const alert = useRef<HTMLParagraphElement>(null);
  const { refresh } = useSession();
  const router = useRouter();
  const destination = safeReturnPath(returnTo);
  const suffix = `?returnTo=${encodeURIComponent(destination)}`;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (guard.current) return;
    const form = event.currentTarget;
    setUncertain(false);
    const fields = Array.from(form.elements).filter((element): element is HTMLInputElement => element instanceof HTMLInputElement);
    const invalid = fields.find(field => !field.validity.valid);
    if (invalid) {
      const names: Record<string, string> = { email: "email", full_name: "họ và tên", phone: "số điện thoại", password: "mật khẩu", confirm: "mật khẩu xác nhận" };
      const name = names[invalid.name] ?? "thông tin";
      setError(invalid.validity.valueMissing ? `Vui lòng nhập ${name}.` : invalid.name === "password" && register ? registrationPasswordHint : `Vui lòng kiểm tra ${name}${invalid.name === "email" ? " (ví dụ: ten@example.com)" : ""}.`);
      requestAnimationFrame(() => alert.current?.focus());
      return;
    }
    const values = new FormData(form);
    const password = String(values.get("password") ?? "");
    if (register && !validRegistrationPassword(password)) {
      setError(registrationPasswordHint);
      requestAnimationFrame(() => alert.current?.focus());
      return;
    }
    if (register && password !== values.get("confirm")) {
      setError("Mật khẩu nhập lại chưa khớp.");
      requestAnimationFrame(() => alert.current?.focus());
      return;
    }
    guard.current = true;
    setBusy(true);
    setError("");
    try {
      const data: Record<string, string> = {
        [phoneLogin && !register ? "identifier" : "email"]: String(values.get("email") ?? "").trim(),
        password,
      };
      if (register) {
        data.full_name = String(values.get("full_name") ?? "").trim();
        const phone = String(values.get("phone") ?? "").trim();
        if (phone) data.phone = phone;
      }
      await mutateAuth(phoneLogin && !register ? "otp-login" : mode, data);
      form.reset();
      if (register) router.replace(`/dang-nhap${suffix}&registered=1`);
      else {
        const account = await refresh();
        if (!account)
          throw new Error(
            "Chưa thể kiểm tra phiên đăng nhập. Vui lòng thử lại.",
          );
        router.replace(destination);
        router.refresh();
      }
    } catch (failure) {
      setUncertain(register && failure instanceof AuthFailure && ["UNAVAILABLE", "NETWORK_ERROR", "REQUEST_TIMEOUT", "SERVER_ERROR", "DEPENDENCY_UNAVAILABLE"].includes(failure.code));
      setError(
        failure instanceof Error ? failure.message : "Chưa thể xác thực.",
      );
      requestAnimationFrame(() => alert.current?.focus());
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  return (
    <div
      className={`auth-scene ${register ? "auth-scene-register" : "auth-scene-login"}`}
    >
      {register ? <RegisterReferenceArt /> : <LoginReferenceArt />}
      <section className="auth-form-card" aria-labelledby="auth-form-title">
        <span className="auth-title-rays" aria-hidden="true">
          {
            <svg
              viewBox="0 0 36 50"
              width="36"
              height="50"
              fill="none"
              stroke="currentColor"
              strokeWidth="6"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="m25 4 8 12M5 21l17 6M8 44l15-5" />
            </svg>
          }
        </span>
        <h1 id="auth-form-title">
          {register ? "Đăng ký tài khoản" : "Đăng nhập vào COCO"}
        </h1>
        <p>
          {register
            ? "Tạo tài khoản để khám phá sản phẩm và kết nối với những gian hàng yêu thích."
            : "Truy cập tài khoản của bạn để tiếp tục hành trình mua sắm cùng coco."}
        </p>
        {registered && !register && (
          <p className="auth-success" role="status">
            <strong>Tạo tài khoản thành công!</strong>
            <span>Vui lòng đăng nhập bằng tài khoản vừa tạo.</span>
          </p>
        )}
        {error && (
          <p className="auth-error" role="alert" ref={alert} tabIndex={-1}>
            <strong>{uncertain ? "Chưa xác nhận được kết quả đăng ký" : register ? "Đăng ký chưa thành công" : "Đăng nhập chưa thành công"}</strong>
            <span>{error}</span>
            {uncertain && <span>Tài khoản có thể đã được tạo. Bạn có thể thử đăng nhập; nếu chưa có tài khoản, hãy đăng ký lại.</span>}
          </p>
        )}
        {busy && <p className="auth-pending" role="status">{register ? "Đang tạo tài khoản, vui lòng chờ…" : "Đang kiểm tra đăng nhập…"}</p>}
        <form onSubmit={submit} aria-busy={busy} noValidate>
          <fieldset disabled={busy}>
            <label htmlFor="auth-email">{phoneLogin && !register ? "Email hoặc số điện thoại" : "Email"}</label>
            <input
              id="auth-email"
              name="email"
              type={phoneLogin && !register ? "text" : "email"}
              autoComplete="email"
              required
              maxLength={255}
              placeholder={phoneLogin && !register ? "Email hoặc số điện thoại" : "Địa chỉ email"}
            />
            {register && (
              <>
                <label htmlFor="full-name">Họ và tên</label>
                <input
                  id="full-name"
                  name="full_name"
                  autoComplete="name"
                  required
                  maxLength={150}
                  pattern=".*\S.*"
                  placeholder="Họ và tên"
                />
              </>
            )}
            {register && (
              <details className="register-optional-phone">
                <summary>Thêm số điện thoại (không bắt buộc)</summary>
                <label htmlFor="auth-phone">
                  Số điện thoại <span>(không bắt buộc)</span>
                </label>
                <input
                  id="auth-phone"
                  name="phone"
                  type="tel"
                  autoComplete="tel"
                  minLength={3}
                  maxLength={30}
                  placeholder="Số điện thoại (không bắt buộc)"
                />
              </details>
            )}
            <label htmlFor="auth-password">Mật khẩu</label>
            <div className="auth-password-field">
              <input
                id="auth-password"
                name="password"
                type={show ? "text" : "password"}
                autoComplete={register ? "new-password" : "current-password"}
                required
                minLength={register ? 9 : 1}
                aria-describedby={register ? "password-hint" : undefined}
                placeholder="Mật khẩu"
              />
              <button
                type="button"
                onClick={() => setShow(!show)}
                aria-label={show ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                aria-pressed={show}
              >
                {
                  <svg
                    viewBox="0 0 24 24"
                    width="24"
                    height="24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    aria-hidden="true"
                  >
                    <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" />
                    <circle cx="12" cy="12" r="3" />
                    {!show && <path d="m3 3 18 18" />}
                  </svg>
                }
              </button>
            </div>
            {register && (
              <p id="password-hint" className="auth-field-hint">
                {registrationPasswordHint}
              </p>
            )}
            {register && (
              <>
                <label htmlFor="auth-confirm">Nhập lại mật khẩu</label>
                <input
                  id="auth-confirm"
                  name="confirm"
                  type={show ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  minLength={9}
                  placeholder="Xác nhận mật khẩu"
                />
              </>
            )}
            {!register && (
              <p className="login-password-help"><Link href={`/quen-mat-khau?returnTo=${encodeURIComponent(destination)}`}>Quên mật khẩu?</Link></p>
            )}
            <button className="auth-submit" type="submit">
              {busy ? "Đang xử lý…" : register ? "Đăng ký" : "Đăng nhập"}
            </button>
          </fieldset>
        </form>
        <div className="login-social-preview">
          <div className="login-social-divider">
            <span>{register ? "Hoặc đăng ký với" : "Hoặc đăng nhập với"}</span>
          </div>
          <div className="login-social-options">
            <button type="button" disabled>
              <span className="social-google" aria-hidden="true">
                G
              </span>
              Google
            </button>
            <button type="button" disabled>
              <span className="social-facebook" aria-hidden="true">
                f
              </span>
              Facebook
            </button>
            <button type="button" disabled>
              <svg
                viewBox="0 0 24 24"
                width="23"
                height="23"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M16.8 2c.2 2.1-1.4 4-3.4 4.3-.3-2 1.4-4 3.4-4.3ZM19.7 17.8c-.7 1.5-1.8 3.4-3.4 3.4-1.4 0-1.7-.8-3.4-.8s-2.1.8-3.5.8c-1.6 0-2.8-2.1-3.6-3.7C3.6 13 4.8 7.2 8.7 7.2c1.5 0 2.5.9 3.8.9 1.2 0 2.4-1 3.9-.9 1.3 0 2.7.7 3.5 1.8-3.3 1.8-2.8 6 .4 7.3l-.6 1.5Z" />
              </svg>
              Apple
            </button>
          </div>
          <p className="login-social-note">
            {register ? "Đăng ký" : "Đăng nhập"} mạng xã hội chưa được hỗ trợ.
          </p>
        </div>
        <p className="auth-switch">
          {register ? "Đã có tài khoản?" : "Chưa có tài khoản?"}{" "}
          <Link href={`${register ? "/dang-nhap" : "/dang-ky"}${suffix}`}>
            {register ? "Đăng nhập" : "Đăng ký ngay"}
          </Link>
        </p>
        <Link className="auth-browse-link" href="/san-pham">
          Tiếp tục khám phá sản phẩm →
        </Link>
      </section>
    </div>
  );
}
