export type AdminCategory = {
  category_id: string;
  parent_category_id: string | null;
  category_name: string;
  category_slug: string;
  is_active: boolean;
  depth: number;
  effective_active: boolean;
  path: string;
};
export type CategoryInput = {
  category_name: string;
  category_slug: string;
  parent_category_id: string | null;
  is_active: boolean;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const validId = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
function categoryValue(
  value: unknown,
): (CategoryInput & { category_id: string; children: unknown[] }) | null {
  if (
    !record(value) ||
    !validId(value.category_id) ||
    !(value.parent_category_id === null || validId(value.parent_category_id)) ||
    typeof value.category_name !== "string" ||
    !value.category_name.trim() ||
    value.category_name.length > 120 ||
    typeof value.category_slug !== "string" ||
    value.category_slug.length > 140 ||
    !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value.category_slug) ||
    typeof value.is_active !== "boolean" ||
    !Array.isArray(value.children)
  )
    return null;
  return {
    category_id: value.category_id,
    category_name: value.category_name,
    category_slug: value.category_slug,
    parent_category_id: value.parent_category_id,
    is_active: value.is_active,
    children: value.children,
  };
}
export function categoryTreeFrom(value: unknown): AdminCategory[] | null {
  if (!record(value) || !Array.isArray(value.items)) return null;
  const rows: AdminCategory[] = [],
    ids = new Set<string>(),
    slugs = new Set<string>();
  const pending = value.items
    .map((v) => ({
      value: v as unknown,
      parent: null as string | null,
      depth: 0,
      active: true,
      path: "",
    }))
    .reverse();
  while (pending.length) {
    const item = pending.pop()!,
      node = categoryValue(item.value);
    if (
      !node ||
      node.parent_category_id !== item.parent ||
      item.depth >= 100 ||
      ids.has(node.category_id) ||
      slugs.has(node.category_slug)
    )
      return null;
    ids.add(node.category_id);
    slugs.add(node.category_slug);
    const path = item.path
        ? `${item.path} / ${node.category_name}`
        : node.category_name,
      active = item.active && node.is_active;
    rows.push({
      category_id: node.category_id,
      category_name: node.category_name,
      category_slug: node.category_slug,
      parent_category_id: node.parent_category_id,
      is_active: node.is_active,
      depth: item.depth,
      effective_active: active,
      path,
    });
    for (const child of [...node.children].reverse())
      pending.push({
        value: child,
        parent: node.category_id,
        depth: item.depth + 1,
        active,
        path,
      });
  }
  return rows;
}
export function blockedParents(rows: AdminCategory[], id: string): Set<string> {
  const blocked = new Set([id]),
    children = new Map<string, string[]>();
  for (const row of rows)
    if (row.parent_category_id)
      children.set(row.parent_category_id, [
        ...(children.get(row.parent_category_id) ?? []),
        row.category_id,
      ]);
  const queue = [id];
  while (queue.length) {
    for (const child of children.get(queue.pop()!) ?? [])
      if (!blocked.has(child)) {
        blocked.add(child);
        queue.push(child);
      }
  }
  return blocked;
}
export class AdminCategoryFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          SLUG_EXISTS: "Đường dẫn danh mục đã được sử dụng.",
          CATEGORY_CYCLE:
            "Danh mục cha không được là chính nó hoặc danh mục con. Hãy tải lại cây.",
          CATEGORY_TOO_DEEP: "Cây danh mục không được vượt quá 100 cấp.",
          INVALID_CATEGORY_TREE:
            "Cây danh mục có liên kết không hợp lệ. Hãy kiểm tra lại dữ liệu.",
          INVALID_PARENT: "Không tìm thấy danh mục cha. Hãy tải lại cây.",
          VALIDATION_ERROR: "Kiểm tra tên, đường dẫn và danh mục cha.",
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập không hợp lệ.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          FORBIDDEN: "Chỉ quản trị viên được quản lý danh mục.",
          NOT_FOUND: "Không tìm thấy danh mục.",
          CSRF_FAILED: "Phiên xác thực đã thay đổi. Hãy tải lại trang.",
        } as Record<string, string>
      )[code] ??
        "Chưa xác minh được kết quả. Hãy tải lại cây danh mục để kiểm tra.",
    );
  }
}
async function request(
  path: string,
  signal: AbortSignal,
  init?: RequestInit,
): Promise<unknown> {
  try {
    const response = await fetch(path, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.any([signal, AbortSignal.timeout(20000)]),
    });
    const value: unknown = await response.json();
    if (!response.ok)
      throw new AdminCategoryFailure(
        record(value) &&
          record(value.error) &&
          typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof AdminCategoryFailure) throw e;
    throw new AdminCategoryFailure("UNAVAILABLE");
  }
}
export async function fetchAdminCategories(
  signal: AbortSignal,
): Promise<AdminCategory[]> {
  const value = categoryTreeFrom(
    await request("/api/v1/admin/categories", signal),
  );
  if (!value) throw new AdminCategoryFailure("UNAVAILABLE");
  return value;
}
export async function saveCategory(
  input: CategoryInput,
  id: string | null,
  signal: AbortSignal,
): Promise<string> {
  const data = {
    category_name: input.category_name.trim(),
    category_slug: input.category_slug.trim(),
    parent_category_id: input.parent_category_id,
    is_active: input.is_active,
  };
  if (
    (id !== null && !validId(id)) ||
    !data.category_name ||
    data.category_name.length > 120 ||
    data.category_slug.length > 140 ||
    !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(data.category_slug) ||
    (data.parent_category_id !== null && !validId(data.parent_category_id)) ||
    typeof data.is_active !== "boolean"
  )
    throw new AdminCategoryFailure("VALIDATION_ERROR");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new AdminCategoryFailure("UNAVAILABLE");
  const response = await request(
    `/api/v1/admin/categories${id ? `/${id}` : ""}`,
    signal,
    {
      method: id ? "PATCH" : "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
      },
      body: JSON.stringify(data),
    },
  );
  const node = categoryValue(record(response) ? response.data : null);
  if (
    !node ||
    (id !== null && node.category_id !== id) ||
    node.category_name !== data.category_name ||
    node.category_slug !== data.category_slug ||
    node.parent_category_id !== data.parent_category_id ||
    node.is_active !== data.is_active
  )
    throw new AdminCategoryFailure("UNAVAILABLE");
  return node.category_id;
}
