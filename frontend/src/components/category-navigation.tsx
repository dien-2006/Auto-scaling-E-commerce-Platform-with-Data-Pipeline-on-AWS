import Link from "next/link";
import { beautyCategories } from "@/lib/categories";
import { CategoryIcon } from "@/components/category-icon";
export function CategoryNavigation() {
 return <nav className="home-category-menu" aria-label="Danh mục sản phẩm"><h2><span aria-hidden="true">☰</span>Danh mục sản phẩm</h2><ul>{beautyCategories.map(category=><li key={category.key}><Link href={`/san-pham?danh-muc=${category.slug}`}><CategoryIcon category={category.key}/><span>{category.name}</span><span className="category-chevron" aria-hidden="true">›</span></Link></li>)}</ul><Link className="home-category-all" href="/san-pham">Tất cả sản phẩm →</Link></nav>;
}
