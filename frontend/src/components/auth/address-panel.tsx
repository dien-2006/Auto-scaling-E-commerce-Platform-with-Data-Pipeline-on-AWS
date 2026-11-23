"use client";
import Link from "next/link";
import { CommerceRestriction } from "@/components/auth/commerce-restriction";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import { listAddresses, saveAddress } from "@/lib/address-client";
import type { AddressInput, ShippingAddress } from "@/lib/address-contract";

const empty: AddressInput = {
  recipient_name: "",
  phone: "",
  address_line: "",
  ward: null,
  district: null,
  city: "",
  is_default: false,
};
export function AddressPanel({returnTo = "/tai-khoan"}: {returnTo?: string}) {
  const { account, loading, error } = useSession();
  if (loading)
    return (
      <div className="shell account-page" role="status">
        Đang kiểm tra phiên đăng nhập…
      </div>
    );
  if (!account)
    return (
      <section className="shell account-page">
        <h1>Địa chỉ giao hàng</h1>
        <p role={error ? "alert" : "status"}>
          {error || "Đăng nhập để quản lý địa chỉ của bạn."}
        </p>
        <Link
          className="primary-button"
          href={`/dang-nhap?returnTo=${encodeURIComponent(`/tai-khoan/dia-chi?returnTo=${encodeURIComponent(returnTo)}`)}`}
        >
          Đăng nhập
        </Link>
      </section>
    );
  if (account.user_role === "ADMIN") return <CommerceRestriction />;
  return <AddressBook key={account.user_id} returnTo={returnTo} />;
}
function AddressBook({returnTo}: {returnTo: string}) {
  const [items, setItems] = useState<ShippingAddress[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState<AddressInput>(empty);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const guard = useRef(false);
  const generation = useRef(0);
  const formRef = useRef<HTMLFormElement>(null);
  const alertRef = useRef<HTMLParagraphElement>(null);
  async function reload() {
    const current = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const result = await listAddresses();
      if (generation.current === current) setItems(result);
    } catch (e) {
      if (generation.current === current) {
        setItems([]);
        setError(e instanceof Error ? e.message : "Không tải được địa chỉ.");
      }
    } finally {
      if (generation.current === current) setLoading(false);
    }
  }
  useEffect(() => {
    let active = true;
    const current = ++generation.current;
    void listAddresses().then(
      (result) => {
        if (active && generation.current === current) {
          setItems(result);
          setLoading(false);
        }
      },
      (e) => {
        if (active && generation.current === current) {
          setError(e instanceof Error ? e.message : "Không tải được địa chỉ.");
          setLoading(false);
        }
      },
    );
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    if (error) alertRef.current?.focus();
  }, [error]);
  useEffect(() => {
    if (editing !== null)
      formRef.current?.querySelector<HTMLInputElement>("input")?.focus();
  }, [editing]);
  async function mutate(
    method: "POST" | "PATCH" | "DELETE",
    id?: string,
    data?: Partial<AddressInput>,
  ) {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await saveAddress(method, id, data);
      setEditing(null);
      setConfirmDelete(null);
      setNotice("Đã lưu thay đổi địa chỉ.");
      await reload();
    } catch (e) {
      setError(
        `${e instanceof Error ? e.message : "Chưa xác nhận được thay đổi."} Nếu kết nối bị gián đoạn, hãy tải lại danh sách trước khi gửi lại.`,
      );
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editing === null) return;
    const values = {
      ...form,
      recipient_name: form.recipient_name.trim(),
      phone: form.phone.trim(),
      address_line: form.address_line.trim(),
      city: form.city.trim(),
      ward: form.ward?.trim() || null,
      district: form.district?.trim() || null,
    };
    if (!values.recipient_name || !values.address_line || !values.city) {
      setError("Vui lòng điền đầy đủ thông tin bắt buộc.");
      return;
    }
    void mutate(
      editing === "new" ? "POST" : "PATCH",
      editing === "new" ? undefined : editing,
      values,
    );
  }
  return (
    <div className="shell account-page address-page">
      <Link href={returnTo}>{returnTo.startsWith("/thanh-toan") ? "← Quay lại thanh toán" : "← Tài khoản của tôi"}</Link>
      <section className="address-book">
        <div className="address-heading">
          <div>
            <span className="auth-step">TÀI KHOẢN COCO</span>
            <h1>Địa chỉ giao hàng</h1>
            <p>Lưu thông tin người nhận để chuẩn bị cho bước thanh toán.</p>
          </div>
          <button
            className="primary-button"
            disabled={busy || loading}
            onClick={() => {
              setForm(empty);
              setEditing("new");
              setConfirmDelete(null);
            }}
          >
            + Thêm địa chỉ
          </button>
        </div>
        {error && (
          <p
            className="address-error"
            role="alert"
            tabIndex={-1}
            ref={alertRef}
          >
            {error}
          </p>
        )}
        {notice && <p role="status">{notice}</p>}
        <button
          className="account-retry"
          disabled={busy || loading}
          onClick={() => {
            setEditing(null);
            setConfirmDelete(null);
            void reload();
          }}
        >
          Tải lại danh sách
        </button>
        {loading ? (
          <p role="status">Đang tải địa chỉ…</p>
        ) : error && !items.length ? (
          <p>
            Danh sách chưa tải được. Vui lòng thử tải lại hoặc đăng nhập lại khi
            phiên hết hạn.
          </p>
        ) : items.length === 0 ? (
          <div className="address-empty">
            <h2>Bạn chưa có địa chỉ nào</h2>
            <p>Thêm người nhận và địa chỉ giao hàng đầu tiên của bạn.</p>
          </div>
        ) : (
          <ul className="address-list">
            {items.map((item) => (
              <li key={item.address_id}>
                <div>
                  <h2>
                    {item.recipient_name}{" "}
                    {item.is_default && (
                      <span className="address-default">Mặc định</span>
                    )}
                  </h2>
                  <p>{item.phone}</p>
                  <p>
                    {[item.address_line, item.ward, item.district, item.city]
                      .filter(Boolean)
                      .join(", ")}
                  </p>
                </div>
                <div className="address-actions">
                  <button
                    disabled={busy || loading}
                    onClick={() => {
                      setForm({
                        recipient_name: item.recipient_name,
                        phone: item.phone,
                        address_line: item.address_line,
                        ward: item.ward,
                        district: item.district,
                        city: item.city,
                        is_default: item.is_default,
                      });
                      setEditing(item.address_id);
                      setConfirmDelete(null);
                    }}
                  >
                    Sửa
                    <span className="sr-only">
                      {" "}
                      địa chỉ của {item.recipient_name}
                    </span>
                  </button>
                  {!item.is_default && (
                    <button
                      disabled={busy || loading}
                      onClick={() =>
                        void mutate("PATCH", item.address_id, {
                          is_default: true,
                        })
                      }
                    >
                      Đặt mặc định
                    </button>
                  )}
                  <button
                    disabled={busy || loading}
                    onClick={() => setConfirmDelete(item.address_id)}
                  >
                    Xóa
                    <span className="sr-only">
                      {" "}
                      địa chỉ của {item.recipient_name}
                    </span>
                  </button>
                </div>
                {confirmDelete === item.address_id && (
                  <div
                    className="address-delete"
                    role="group"
                    aria-label="Xác nhận xóa địa chỉ"
                  >
                    <p>
                      Xóa địa chỉ này? Thông tin trên đơn hàng cũ được giữ
                      nguyên.
                    </p>
                    <button
                      disabled={busy}
                      onClick={() => void mutate("DELETE", item.address_id)}
                    >
                      Xác nhận xóa
                    </button>
                    <button
                      disabled={busy}
                      onClick={() => setConfirmDelete(null)}
                    >
                      Giữ lại
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
        {editing !== null && (
          <form className="address-form" ref={formRef} onSubmit={submit}>
            <h2>{editing === "new" ? "Thêm địa chỉ mới" : "Sửa địa chỉ"}</h2>
            <fieldset disabled={busy || loading}>
              <div className="address-fields">
                {(
                  [
                    ["recipient_name", "Họ tên người nhận", 150, true, "name"],
                    ["phone", "Số điện thoại", 30, true, "tel"],
                    [
                      "address_line",
                      "Số nhà, tên đường",
                      2000,
                      true,
                      "street-address",
                    ],
                    ["ward", "Phường / xã", 120, false, "address-level3"],
                    ["district", "Quận / huyện", 120, false, "address-level2"],
                    ["city", "Tỉnh / thành phố", 120, true, "address-level1"],
                  ] as const
                ).map(([key, label, max, required, auto]) => (
                  <label key={key} htmlFor={`address-${key}`}>
                    {label}
                    {required ? " *" : " (không bắt buộc)"}
                    <input
                      id={`address-${key}`}
                      name={key}
                      value={form[key] || ""}
                      autoComplete={auto}
                      maxLength={max}
                      minLength={key === "phone" ? 3 : 1}
                      required={required}
                      type={key === "phone" ? "tel" : "text"}
                      pattern={
                        key === "phone" ? "\\+?[0-9 \\(\\)\\-]+" : undefined
                      }
                      onChange={(event) =>
                        setForm({ ...form, [key]: event.target.value })
                      }
                    />
                  </label>
                ))}
              </div>
              <label className="address-checkbox">
                <input
                  type="checkbox"
                  checked={form.is_default}
                  onChange={(event) =>
                    setForm({ ...form, is_default: event.target.checked })
                  }
                />
                Đặt làm địa chỉ mặc định
              </label>
              <p className="auth-field-hint">
                Có thể không có địa chỉ mặc định. Xóa địa chỉ mặc định sẽ không
                tự chọn địa chỉ khác.
              </p>
              <div className="address-actions">
                <button className="primary-button" type="submit">
                  {busy ? "Đang lưu…" : "Lưu địa chỉ"}
                </button>
                <button type="button" onClick={() => setEditing(null)}>
                  Hủy
                </button>
              </div>
            </fieldset>
          </form>
        )}
        {busy && <p role="status">Đang cập nhật địa chỉ…</p>}
      </section>
    </div>
  );
}
