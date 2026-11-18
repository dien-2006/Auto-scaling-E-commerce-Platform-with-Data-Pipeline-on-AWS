-- Review before applying. Only replaces the view, no base table changes.
BEGIN;
SET LOCAL lock_timeout = '5s';
CREATE OR REPLACE VIEW marketplace.v_deal_today AS
SELECT p.product_id, p.product_name, p.shop_id, s.shop_name,
       p.price AS original_price,
       ROUND(p.price * (1 - c.discount_percent / 100), 2)::numeric(14,2) AS sale_price,
       ROUND(c.discount_percent)::integer AS discount_percent,
       pi.image_key, i.quantity AS stock, p.created_at,
       c.code AS coupon_code, c.expires_at AS ends_at
FROM marketplace.products p
JOIN marketplace.shops s ON s.shop_id = p.shop_id
JOIN marketplace.inventory i ON i.product_id = p.product_id
LEFT JOIN LATERAL (
    SELECT img.image_key FROM marketplace.product_images img
    WHERE img.product_id = p.product_id
    ORDER BY img.is_primary DESC, img.sort_order, img.product_image_id LIMIT 1
) pi ON true
JOIN LATERAL (
    SELECT cp.code, cp.discount_percent, cp.expires_at
    FROM marketplace.coupons cp
    WHERE cp.is_active AND now() >= cp.starts_at AND now() < cp.expires_at
      AND cp.used_count < cp.usage_limit
      AND cp.discount_percent > 0 AND cp.discount_percent < 30
      AND (cp.shop_id = p.shop_id OR cp.shop_id IS NULL)
      AND p.price >= cp.min_order_amount
    ORDER BY cp.discount_percent DESC, cp.expires_at, cp.coupon_id
    LIMIT 1
) c ON true
WHERE p.is_active AND s.shop_status::text = 'APPROVED' AND i.quantity > 0;
COMMIT;
