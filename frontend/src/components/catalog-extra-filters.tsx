/** Unconfigured capabilities: don't send unsupported fields to the public catalog API. */
export function CatalogExtraFilters() {
  return (
    <div className="catalog-extra-filters">
      <fieldset disabled aria-describedby="shipping-unavailable">
        <legend>
          Đơn vị vận chuyển <span>Chưa kết nối</span>
        </legend>
        <label>
          <input type="checkbox" />
          Giao Hàng Nhanh
        </label>
        <label>
          <input type="checkbox" />
          Giao Hàng Tiết Kiệm
        </label>
        <label>
          <input type="checkbox" />
          Viettel Post
        </label>
        <p id="shipping-unavailable">
          Các lựa chọn dự kiến, chưa có đơn vị được kết nối.
        </p>
      </fieldset>
      <fieldset disabled aria-describedby="services-unavailable">
        <legend>
          Dịch vụ & khuyến mãi <span>Sắp có</span>
        </legend>
        <label>
          <input type="checkbox" />
          Ưu đãi vận chuyển
        </label>
        <label>
          <input type="checkbox" />
          Sản phẩm khuyến mãi
        </label>
        <label>
          <input type="checkbox" />
          Giao hàng nhanh
        </label>
        <p id="services-unavailable">
          Bộ lọc sẽ mở khi có thông tin dịch vụ và chương trình ưu đãi.
        </p>
      </fieldset>
    </div>
  );
}
