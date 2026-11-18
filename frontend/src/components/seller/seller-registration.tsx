"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import { SellerIcon } from "@/components/seller/seller-icon";
import { suggestedShopSlug } from "@/lib/seller-registration";
import { shopInputError, type ShopInput } from "@/lib/seller-shop-client";

type Props = {
  guest?: boolean;
  loading?: boolean;
  busy?: boolean;
  uncertain?: boolean;
  error?: string;
  phone?: string | null;
  onSave: (input: ShopInput) => Promise<void>;
  onReload?: () => void;
};
export function SellerRegistration({
  guest = false,
  loading = false,
  busy = false,
  uncertain = false,
  error = "",
  phone = null,
  onSave,
  onReload,
}: Props) {
  const [name, setName] = useState(""),
    [description, setDescription] = useState(""),
    [email, setEmail] = useState(""),
    [customSlug, setCustomSlug] = useState<string | null>(null),
    [issue, setIssue] = useState("");
  const slug = customSlug ?? suggestedShopSlug(name),
    disabled = loading || busy || uncertain;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled) return;
    const input: ShopInput = {
      shop_name: name.trim(),
      shop_slug: slug.trim(),
      description: description.trim() || null,
      contact_email: email.trim() || null,
    };
    // Guests can proceed to sign in without submitting a shop or persisting PII.
    if (!guest) {
      const message = shopInputError(input, true);
      if (message) {
        setIssue(message);
        return;
      }
    }
    setIssue("");
    await onSave(input);
  }
  return (
    <div className="seller-signup-page">
      <section className="seller-signup-scene">
        <div className="seller-signup-grid">
          <div className="seller-signup-intro">
            <h1>
              <span className="seller-heading-sparks" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>
              Đăng ký bán hàng
              <br />
              cùng COCO
            </h1>
            <p>
              Bắt đầu mở gian hàng ngay hôm nay,
              <br />
              dễ dàng gia nhập và kinh doanh hiệu quả trên COCO!
            </p>
            <div className="seller-signup-art-row">
              <div className="seller-signup-art">
                <Image
                  src="/images/coco-seller-store.png"
                  alt="Cửa hàng COCO Seller xanh trắng với quầy hàng và kiện hàng"
                  fill
                  sizes="(max-width: 700px) 80vw, (max-width: 1100px) 45vw, 33vw"
                  priority
                />
              </div>
              <ul className="seller-signup-perks">
                <li>
                  <SellerIcon name="users" />
                  <span>
                    Kết nối
                    <br />
                    với khách hàng
                  </span>
                </li>
                <li>
                  <SellerIcon name="shield" />
                  <span>
                    Thông tin
                    <br />
                    được bảo vệ
                  </span>
                </li>
                <li>
                  <SellerIcon name="growth" />
                  <span>
                    Mở gian hàng
                    <br />
                    thật dễ dàng
                  </span>
                </li>
              </ul>
            </div>
          </div>
          <section
            className="seller-signup-card"
            aria-labelledby="seller-signup-title"
          >
            <h2 id="seller-signup-title">Đăng ký bán hàng trên COCO</h2>
            <p className="seller-signup-subtitle">
              Hoàn tất hồ sơ để bắt đầu bán hàng trên COCO
            </p>
            <ol
              className="seller-signup-steps"
              aria-label="Quy trình mở gian hàng"
            >
              {[
                "Thông tin shop",
                "Gửi hồ sơ",
                "Admin phê duyệt",
                "Sẵn sàng bán hàng",
              ].map((label, index) => (
                <li key={label} aria-current={index === 0 ? "step" : undefined}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{label}</strong>
                </li>
              ))}
            </ol>
            {(issue || error) && (
              <p className="seller-form-error" role="alert">
                {issue || error}
              </p>
            )}
            {loading && (
              <p role="status" className="seller-signup-hint">
                Đang kiểm tra phiên đăng nhập…
              </p>
            )}
            {uncertain && (
              <div className="seller-uncertain">
                <p>
                  Chưa xác minh được kết quả lần gửi hồ sơ. Kiểm tra lại trước
                  khi tiếp tục.
                </p>
                <button
                  type="button"
                  className="seller-outline-button"
                  onClick={onReload}
                >
                  Kiểm tra hồ sơ đã lưu
                </button>
              </div>
            )}
            <form className="seller-signup-form" onSubmit={submit}>
              <fieldset disabled={disabled}>
                <legend className="sr-only">Đăng ký gian hàng</legend>
                <div className="seller-signup-field">
                  <SellerIcon name="shop" />
                  <label htmlFor="seller-signup-name" className="sr-only">
                    Tên shop
                  </label>
                  <input
                    id="seller-signup-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Tên shop"
                    autoComplete="organization"
                    required={!guest}
                  />
                </div>
                <div className="seller-signup-field seller-signup-textarea">
                  <SellerIcon name="message" />
                  <label
                    htmlFor="seller-signup-description"
                    className="sr-only"
                  >
                    Mô tả shop
                  </label>
                  <textarea
                    id="seller-signup-description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Mô tả shop"
                    rows={2}
                  />
                </div>
                <div className="seller-signup-field">
                  <SellerIcon name="email" />
                  <label htmlFor="seller-signup-email" className="sr-only">
                    Email liên hệ
                  </label>
                  <input
                    id="seller-signup-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email"
                    maxLength={255}
                    autoComplete="email"
                  />
                </div>
                <div className="seller-signup-field seller-signup-phone">
                  <SellerIcon name="phone" />
                  <label htmlFor="seller-signup-phone" className="sr-only">
                    Số điện thoại tài khoản
                  </label>
                  <input
                    id="seller-signup-phone"
                    type="tel"
                    value={phone ?? ""}
                    placeholder={
                      guest ? "SĐT" : "Tài khoản chưa có số điện thoại"
                    }
                    readOnly
                    aria-describedby="seller-signup-phone-hint"
                  />
                </div>
                <small
                  id="seller-signup-phone-hint"
                  className="seller-signup-phone-hint"
                >
                  Số điện thoại từ tài khoản, không hiển thị cho người mua.
                </small>
                {!guest && (
                  <details className="seller-signup-slug">
                    <summary>Tùy chỉnh đường dẫn shop</summary>
                    <label htmlFor="seller-signup-slug">
                      Đường dẫn cố định sau đăng ký
                    </label>
                    <div>
                      <span>/gian-hang/</span>
                      <input
                        id="seller-signup-slug"
                        value={slug}
                        onChange={(e) => setCustomSlug(e.target.value)}
                        maxLength={160}
                        placeholder="ten-shop-cua-ban"
                      />
                    </div>
                    <small>Chữ thường không dấu, số và dấu gạch nối.</small>
                  </details>
                )}
                <button
                  type="submit"
                  className="seller-signup-submit"
                  aria-describedby={
                    guest && !loading ? "seller-signup-login-hint" : undefined
                  }
                  disabled={disabled}
                >
                  {busy ? "Đang gửi hồ sơ…" : "Tiếp tục"}
                </button>
                {guest && !loading && (
                  <p className="sr-only" id="seller-signup-login-hint">
                    Đăng nhập để gửi hồ sơ.
                  </p>
                )}
              </fieldset>
            </form>
            <Link
              href="/kenh-nguoi-ban/van-chuyen"
              className="shipping-preview-link"
            >
              Xem trước bước 02 — Cài đặt vận chuyển →
            </Link>
          </section>
        </div>
      </section>
      <SellerRegistrationBenefits />
    </div>
  );
}

function SellerRegistrationBenefits() {
  return (
    <div className="seller-signup-benefits">
      <div>
        {(
          [
            ["shop", "Tạo gian hàng miễn phí", "Đăng ký nhanh, không mất phí"],
            [
              "support",
              "Hỗ trợ người bán",
              "Hướng dẫn mở và quản lý gian hàng",
            ],
            ["shield", "Thanh toán COD", "Thanh toán khi nhận hàng"],
            ["growth", "Phát triển bền vững", "Xây dựng gian hàng của bạn"],
          ] as const
        ).map(([icon, title, description]) => (
          <section key={title}>
            <SellerIcon name={icon} />
            <div>
              <h2>{title}</h2>
              <p>{description}</p>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
