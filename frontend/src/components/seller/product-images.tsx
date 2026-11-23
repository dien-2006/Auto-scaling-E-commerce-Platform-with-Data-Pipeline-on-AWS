"use client";
import Image from "next/image";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import {
  ImageFailure,
  readImages,
  updateImage,
  uploadImage,
  type SellerImage,
} from "@/lib/product-images-client";

export function ProductImages({
  productId,
  shopId,
  name,
  enabled,
  onClose,
}: {
  productId: string;
  shopId: string;
  name: string;
  enabled: boolean;
  onClose: () => void;
}) {
  const { refresh } = useSession();
  const [images, setImages] = useState<SellerImage[] | null>(null),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false),
    [retry, setRetry] = useState(0),
    [remove, setRemove] = useState<string | null>(null);
  const mounted = useRef(false),
    submitting = useRef(false),
    write = useRef<AbortController | null>(null),
    form = useRef<HTMLFormElement>(null);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      write.current?.abort();
    };
  }, []);
  function failure(e: unknown) {
    setError(e instanceof Error ? e.message : "Chưa tải được ảnh.");
    if (
      e instanceof ImageFailure &&
      [
        "AUTH_REQUIRED",
        "TOKEN_EXPIRED",
        "INVALID_TOKEN",
        "USER_LOCKED",
        "FORBIDDEN",
        "SHOP_NOT_APPROVED",
      ].includes(e.code)
    ) {
      setImages(null);
      void refresh();
    }
  }
  useEffect(() => {
    const c = new AbortController();
    void readImages(productId, shopId, c.signal)
      .then((value) => {
        if (!c.signal.aborted) {
          setImages(value);
          setUncertain(false);
        }
      })
      .catch((e: unknown) => {
        if (!c.signal.aborted) {
          setError(e instanceof Error ? e.message : "Chưa tải được ảnh.");
          if (
            e instanceof ImageFailure &&
            [
              "AUTH_REQUIRED",
              "TOKEN_EXPIRED",
              "INVALID_TOKEN",
              "USER_LOCKED",
              "FORBIDDEN",
              "SHOP_NOT_APPROVED",
            ].includes(e.code)
          )
            void refresh();
        }
      });
    return () => c.abort();
  }, [productId, shopId, retry, refresh]);
  function reload() {
    if (submitting.current) return;
    setImages(null);
    setError("");
    setNotice("");
    setRemove(null);
    setRetry((v) => v + 1);
  }
  async function run(operation: (signal: AbortSignal) => Promise<void>) {
    if (submitting.current || uncertain || !images) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const c = new AbortController();
    write.current = c;
    try {
      await operation(c.signal);
      if (!mounted.current) return;
      setNotice("Đã cập nhật ảnh sản phẩm.");
      setImages(null);
      setRemove(null);
      form.current?.reset();
      setRetry((v) => v + 1);
    } catch (e) {
      if (!mounted.current) return;
      failure(e);
      if (
        !(e instanceof ImageFailure) ||
        ["UNAVAILABLE", "DEPENDENCY_UNAVAILABLE", "IMAGE_EXISTS"].includes(
          e.code,
        )
      )
        setUncertain(true);
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  function upload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget),
      file = data.get("file");
    if (!(file instanceof File) || !file.size) {
      setError("Hãy chọn ảnh sản phẩm.");
      return;
    }
    void run((signal) =>
      uploadImage(productId, file, data.get("primary") === "on", signal),
    );
  }
  return (
    <section
      className="seller-card seller-images"
      aria-labelledby="seller-images-title"
    >
      <header className="seller-heading">
        <div>
          <h2 id="seller-images-title">Ảnh sản phẩm — {name}</h2>
          <p>
            JPEG, PNG, WebP · tối đa 5 MiB, 16 triệu điểm ảnh · mỗi chiều không
            quá 4096 px.
          </p>
        </div>
        <button
          className="seller-outline-button"
          disabled={busy}
          onClick={onClose}
        >
          Đóng quản lý ảnh
        </button>
      </header>
      {error && (
        <p role="alert" className="seller-form-error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="seller-form-success">
          {notice}
        </p>
      )}
      {!enabled && (
        <p className="seller-storage-notice" role="status">
          Kho ảnh chưa được cấu hình. Tải ảnh lên sẽ mở sau khi quản trị viên
          hoàn tất thiết lập.
        </p>
      )}
      {uncertain && (
        <p role="status">
          Kết quả chưa rõ. Tải lại danh sách ảnh và kiểm tra trước khi thao tác
          tiếp.
        </p>
      )}
      <button
        className="seller-outline-button"
        disabled={busy}
        onClick={reload}
      >
        Tải lại danh sách ảnh
      </button>
      {!images ? (
        !error && <p role="status">Đang tải ảnh…</p>
      ) : (
        <>
          <form ref={form} className="seller-image-upload" onSubmit={upload}>
            <fieldset disabled={!enabled || busy || uncertain}>
              <legend>Tải ảnh mới</legend>
              <label htmlFor="seller-image-file">Chọn ảnh sản phẩm</label>
              <input
                id="seller-image-file"
                type="file"
                name="file"
                accept="image/jpeg,image/png,image/webp"
                required
              />
              <label>
                <input
                  type="checkbox"
                  name="primary"
                  defaultChecked={!images.length}
                />{" "}
                Đặt làm ảnh chính
              </label>
              <button
                className="primary-button"
                disabled={!enabled || busy || uncertain}
              >
                {busy ? "Đang xử lý…" : "Tải ảnh lên"}
              </button>
            </fieldset>
          </form>
          {!images.length ? (
            <p>Chưa có ảnh được liên kết với sản phẩm.</p>
          ) : (
            <ul className="seller-image-grid">
              {images.map((image) => (
                <li key={image.product_image_id}>
                  <ImagePreview image={image} name={name} />
                  <strong>
                    {image.is_primary ? "Ảnh chính" : "Ảnh sản phẩm"}
                  </strong>
                  <small>#{image.product_image_id}</small>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const value = Number(
                        new FormData(e.currentTarget).get("sort_order"),
                      );
                      void run((signal) =>
                        updateImage(productId, image.product_image_id, signal, {
                          sort_order: value,
                        }),
                      );
                    }}
                  >
                    <label>
                      Thứ tự ảnh
                      <input
                        type="number"
                        name="sort_order"
                        min={0}
                        max={2147483647}
                        step={1}
                        defaultValue={image.sort_order}
                        required
                        disabled={busy || uncertain}
                      />
                    </label>
                    <button
                      className="seller-outline-button"
                      disabled={busy || uncertain}
                    >
                      Lưu thứ tự
                    </button>
                  </form>
                  {!image.is_primary && (
                    <button
                      className="seller-outline-button"
                      disabled={busy || uncertain}
                      onClick={() =>
                        void run((signal) =>
                          updateImage(
                            productId,
                            image.product_image_id,
                            signal,
                            { is_primary: true },
                          ),
                        )
                      }
                    >
                      Chọn làm ảnh chính
                    </button>
                  )}
                  {remove === image.product_image_id ? (
                    <div>
                      <p>
                        Bỏ ảnh khỏi sản phẩm? File gốc vẫn được giữ trong kho
                        ảnh.
                      </p>
                      <button
                        className="seller-outline-button"
                        disabled={busy || uncertain}
                        onClick={() =>
                          void run((signal) =>
                            updateImage(
                              productId,
                              image.product_image_id,
                              signal,
                              null,
                            ),
                          )
                        }
                      >
                        Xác nhận bỏ ảnh
                      </button>
                      <button
                        className="seller-outline-button"
                        disabled={busy}
                        onClick={() => setRemove(null)}
                      >
                        Giữ ảnh
                      </button>
                    </div>
                  ) : (
                    <button
                      className="seller-outline-button"
                      disabled={busy || uncertain}
                      onClick={() => setRemove(image.product_image_id)}
                    >
                      Bỏ ảnh
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
function ImagePreview({ image, name }: { image: SellerImage; name: string }) {
  const [failed, setFailed] = useState(false);
  return image.url && !failed ? (
    <Image
      src={image.url}
      alt={name}
      width={180}
      height={180}
      unoptimized
      onError={() => setFailed(true)}
    />
  ) : (
    <span className="seller-image-placeholder">
      {failed ? "Chưa tải được ảnh" : "Ảnh chưa có URL phân phối"}
    </span>
  );
}
