# Rà soát local

Từ root dùng Python của backend sau `uv sync --locked`:

```powershell
& backend/.venv/Scripts/python.exe tests/security/review.py
& backend/.venv/Scripts/python.exe tests/security/dependencies.py
```

`review.py` quét file Git-visible (tracked + untracked không ignored) bằng pattern AWS access ID/private key/GitHub token và phát hiện private env bị lộ trong danh sách. Không in giá trị match. Không quét root.env/private ignored files, không tuyên bố đã rà Git history hoặc tất cả loại secret. Scan có thể cần phân loại false positives trước khi sửa.

`dependencies.py` đọc version registry packages từ backend/uv.lock rồi gửi tên/version package công khai tới OSV; không gửi source/credential. Finding thì exit1; lỗi mạng cũng là lỗi, không coi là PASS. Phải giữ report ngày kiểm vì dữ liệu advisory thay đổi.

Frontend dùng `npm audit --json` và `npm audit --omit=dev --json` trong frontend. Không dùng `--force`/major override để che findings. Kết quả11/11/2026 và rủi ro còn mở: [handoff.md](../../docs/handoff.md).
