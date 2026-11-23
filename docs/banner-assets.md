# Banner coco — UI-05

## UI-07 — Banner trang danh sách sản phẩm

- Asset sử dụng: `frontend/public/images/coco-catalog-banner.png`.
- Component: `frontend/src/components/catalog-banner.tsx`, chỉ render tại `/san-pham`.
- Công cụ: built-in image_gen, không CLI fallback. Đây là artwork editorial, không gán vào ảnh catalog thật. Giữ nguyên ảnh/bố cục banner homepage UI-05.
- Prompt nguyên văn:

Create one original premium beauty e-commerce campaign background, very wide landscape aspect ratio 3:1. Photorealistic luxury studio still life. Warm ivory, apricot-peach and fresh powder-blue color palette, youthful and airy, modern editorial art direction. LEFT 52 percent clean creamy background with subtle sunlight and a very soft peach gradient reserved for HTML copy. RIGHT half a group of three unbranded cosmetics: a sculptural frosted sky-blue serum dropper, a matte ivory pump bottle, and a translucent peach cream jar, displayed on a curved ivory pedestal with one sliced peach and a delicate white flower. Gentle curved translucent fabric and a soft peach-colored arch behind the products. Beautiful realistic glass, premium diffuse light, gentle natural shadows. NO text, NO typography, NO logos or brand labels, NO price or discounts, NO people, NO watermark. Not a website mockup. Horizontal original photograph for a beauty collection banner, no medical claims. Opaque background.

## Bộ ảnh trang chủ UI-05

Hai ảnh dưới đây là artwork editorial tạo mới bằng built-in `image_gen` theo skill imagegen, dùng cho banner trang chủ. Không phải ảnh sản phẩm thật của nhà bán, không gán vào catalog/DB và không chứa giá/giảm giá/claim thương hiệu khác. Ảnh gốc còn giữ ở thư mục generated_images của Codex; bản được dùng đã copy vào repository. Chưa dùng CLI/API fallback.

| File trong repository | Sử dụng |
| --- | --- |
| frontend/public/images/coco-skincare-campaign.png | Banner lớn và banner nhỏ chăm sóc da |
| frontend/public/images/coco-fragrance-campaign.png | Banner nhỏ nước hoa |

Component `frontend/src/components/home/campaign-banners.tsx` đặt chữ Việt bằng HTML và dùng Next Image để phục vụ ảnh local. Giữ nhãn “Hình minh họa bộ sưu tập”, không bịa freeship/discount hoặc lấy ảnh này thay ảnh thật. Các banner link tới bộ lọc danh mục thật trên homepage.

## Prompt skincare — nguyên văn

Create one premium wide landscape ecommerce beauty campaign background photograph, aspect ratio approximately 3:1. Photorealistic studio still life, pastel sky blue and soft peach palette, contemporary Vietnamese beauty marketplace visual direction. Composition: left 50 percent mostly clean pale powder-blue background with subtle flowing silk and soft light, intended for HTML text overlay; RIGHT half a beautifully composed group of unbranded generic cosmetic packaging: frosted peach pump lotion bottle, tall ivory cleanser tube, pale blue glass serum dropper and small white cream jar on a low sculptural stone pedestal, a single delicate peach flower and fresh leaves, realistic glossy/refraction textures, soft daylight, polished advertising photo quality. No text, no letters, no logos, no brand labels, no prices, no discount badges, no watermark, no people. Original campaign artwork, not a screenshot or website mockup. Wide horizontal framing, cosmetics occupy right half, generous clear space left. Opaque background.

## Prompt fragrance — nguyên văn

One ultra-wide horizontal 3:1 photorealistic premium beauty ecommerce banner background. Original editorial photograph for a brand called coco but NO text or branding anywhere. Pale lavender and sky-blue softly lit studio background. On far RIGHT a single elegant round clear glass perfume bottle with subtle pale pink liquid, brushed silver cap, resting beside one peach flower on smooth pale stone. Left 55 percent clean uncluttered lavender-blue background for later HTML typography. Beautiful glass reflections, soft shadows, realistic studio photography. No letters, logos, watermark, prices, promotional badges, people, website UI. Opaque background.

## BRAND-02 — Logo transparent (10/11/2026)

Nguồn: C:/Users/ADMIN/Downloads/loho.png, giữ nguyên nguồn và asset BRAND-01. Built-in image_gen theo skill imagegen, use case background-extraction, transparent_background=true. Output gốc: C:/Users/ADMIN/.codex/generated_images/01a1c514-2e8b-7161-8954-1704a4d96e28/exec-3914b2a9-580c-4ed3-843c-f281a1252dbf.png; copy thành frontend/public/images/coco-logo-transparent.png (2193×717 RGBA, alpha0..255, corners0).

Prompt: Remove ONLY the off-white/white outer background to actual transparent alpha. Preserve exactly the blue bag, woman silhouette and leaf inside the bag, blue gradient lowercase text coco, all blue rays and sparkles, proportions and smooth edges. Keep intentional white shapes INSIDE the shopping bag intact. Make empty counters in letter o transparent. No redesign, new outlines, shadows or frame. Crop transparent outer margins tightly around full logo with small3% padding; wide landscape; transparent PNG for website header.

BrandLogo/favicons dùng asset mới; CSS cao84px desktop,58px mobile,50px auth/Seller,40px shipping nhỏ. Không dùng logo làm ảnh catalog/DB hoặc upload storage.
