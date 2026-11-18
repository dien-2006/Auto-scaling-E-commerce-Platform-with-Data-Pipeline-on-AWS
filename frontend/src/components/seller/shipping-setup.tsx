"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { SellerIcon } from "@/components/seller/seller-icon";
import {
  shippingCarriers,
  shippingDraftError,
  type CarrierCode,
  type ShippingDraft,
} from "@/lib/seller-shipping";

export function ShippingSetup() {
  const [draft, setDraft] = useState<ShippingDraft>({
    carriers: ["GHN", "GHTK"],
    feeMode: "PLATFORM",
    customFee: "",
    processingDays: 1,
  });
  const issue = shippingDraftError(draft);
  function toggle(code: CarrierCode) {
    setDraft((value) => ({
      ...value,
      carriers: value.carriers.includes(code)
        ? value.carriers.filter((item) => item !== code)
        : [...value.carriers, code],
    }));
  }
  return (
    <div className="seller-shipping-page">
      <div className="shipping-page-inner">
        <header className="shipping-page-heading">
          <h1>
            <SellerIcon name="shop" />
            Đăng ký bán hàng trên COCO
          </h1>
          <p>
            Hoàn thành 4 bước đơn giản để mở gian hàng và bắt đầu kinh doanh
          </p>
        </header>
        <ol
          className="shipping-progress"
          aria-label="Thiết kế quy trình đăng ký bán hàng"
        >
          <li className="shipping-step-complete">
            <span>
              <SellerIcon name="check" />
            </span>
            <strong>01 Thông tin shop</strong>
          </li>
          <li aria-current="step">
            <span>02</span>
            <strong>Cài đặt vận chuyển</strong>
          </li>
          <li>
            <span>
              <SellerIcon name="shield" />
            </span>
            <strong>03 Admin phê duyệt</strong>
          </li>
          <li>
            <span>
              <SellerIcon name="shop" />
            </span>
            <strong>04 Sẵn sàng bán hàng</strong>
          </li>
        </ol>
        <section
          className="shipping-setup-card"
          aria-labelledby="shipping-setup-title"
        >
          <div className="shipping-setup-art">
            <Image
              src="/images/coco-shipping-truck.png"
              alt="Xe giao hàng COCO xanh trắng, bản đồ và các kiện hàng"
              fill
              sizes="(max-width: 800px) 80vw, 36vw"
              priority
            />
          </div>
          <div className="shipping-setup-content">
            <header className="shipping-card-heading">
              <div>
                <SellerIcon name="truck" />
                <h2 id="shipping-setup-title">
                  <span>02</span> Cài đặt vận chuyển
                </h2>
              </div>
              <p>
                Thiết lập phương thức và phí vận chuyển cho gian hàng của bạn.
              </p>
            </header>
            <form
              className="shipping-settings-form"
              onSubmit={(event) => event.preventDefault()}
            >
              <fieldset className="shipping-methods-panel">
                <legend>
                  <SellerIcon name="box" />
                  <span>Phương thức vận chuyển</span>
                </legend>
                <p>Chọn đơn vị vận chuyển hỗ trợ</p>
                <div className="shipping-carrier-grid">
                  {shippingCarriers.map((carrier) => (
                    <label
                      key={carrier.code}
                      className={`shipping-carrier carrier-${carrier.code.toLowerCase()}`}
                    >
                      <input
                        type="checkbox"
                        checked={draft.carriers.includes(carrier.code)}
                        onChange={() => toggle(carrier.code)}
                        aria-label={carrier.name}
                      />
                      {carrier.code === "EXPRESS" ? (
                        <>
                          <SellerIcon name="bolt" />
                          <strong>Hỏa tốc</strong>
                        </>
                      ) : (
                        <span>
                          <strong>{carrier.name}</strong>
                          <span
                            className="shipping-carrier-wordmark"
                            aria-hidden="true"
                          >
                            {carrier.wordmark}
                          </span>
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="shipping-options-row">
                <fieldset className="shipping-fees-panel">
                  <legend>
                    <SellerIcon name="truck" />
                    <span>Phí vận chuyển</span>
                  </legend>
                  <label className="shipping-radio">
                    <input
                      type="radio"
                      name="shipping-fee-mode"
                      checked={draft.feeMode === "PLATFORM"}
                      onChange={() =>
                        setDraft((value) => ({ ...value, feeMode: "PLATFORM" }))
                      }
                    />
                    <span>Theo bảng giá sàn (khuyến nghị)</span>
                    <span
                      className="shipping-fee-info"
                      title="Bảng giá và phí vận chuyển chưa được áp dụng trong giao diện xem trước."
                      aria-label="Bảng giá chưa được áp dụng"
                    >
                      <SellerIcon name="info" />
                    </span>
                  </label>
                  <label className="shipping-radio">
                    <input
                      type="radio"
                      name="shipping-fee-mode"
                      checked={draft.feeMode === "CUSTOM"}
                      onChange={() =>
                        setDraft((value) => ({ ...value, feeMode: "CUSTOM" }))
                      }
                    />
                    <span>Tự thiết lập phí vận chuyển</span>
                  </label>
                  {draft.feeMode === "CUSTOM" && (
                    <div className="shipping-custom-fee">
                      <label htmlFor="shipping-custom-fee">
                        Phí cố định (VND)
                      </label>
                      <input
                        id="shipping-custom-fee"
                        type="text"
                        inputMode="decimal"
                        value={draft.customFee}
                        onChange={(event) =>
                          setDraft((value) => ({
                            ...value,
                            customFee: event.target.value,
                          }))
                        }
                        placeholder="Ví dụ: 25000"
                        aria-invalid={!!issue}
                        aria-describedby={
                          issue ? "shipping-draft-error" : undefined
                        }
                      />
                    </div>
                  )}
                </fieldset>
                <fieldset className="shipping-processing-panel">
                  <legend>
                    <SellerIcon name="calendar" />
                    <label htmlFor="shipping-processing-days">
                      Thời gian xử lý đơn
                    </label>
                  </legend>
                  <select
                    id="shipping-processing-days"
                    value={draft.processingDays}
                    onChange={(event) =>
                      setDraft((value) => ({
                        ...value,
                        processingDays: Number(event.target.value),
                      }))
                    }
                  >
                    {[1, 2, 3, 5, 7].map((days) => (
                      <option key={days} value={days}>
                        Trong {days} ngày
                      </option>
                    ))}
                  </select>
                </fieldset>
              </div>
              {issue && (
                <p
                  className="shipping-draft-error"
                  id="shipping-draft-error"
                  role="alert"
                >
                  {issue}
                </p>
              )}
              <p
                className="shipping-preview-notice"
                id="shipping-preview-notice"
              >
                <strong>Xem trước giao diện.</strong> Lựa chọn chưa được lưu
                hoặc áp dụng cho đơn hàng. Chức năng lưu đang được chuẩn bị.
              </p>
              <div className="shipping-form-actions">
                <Link className="shipping-back" href="/kenh-nguoi-ban">
                  <SellerIcon name="arrow-left" />
                  Quay lại
                </Link>
                <button
                  className="shipping-next"
                  type="submit"
                  disabled
                  aria-describedby="shipping-preview-notice"
                >
                  Tiếp tục
                  <SellerIcon name="arrow-right" />
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
