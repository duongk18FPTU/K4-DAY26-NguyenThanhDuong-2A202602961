# Chạy bài lab trên Windows / PowerShell

## Nội dung bài học

| Phần | Mục tiêu | API key |
|---|---|---|
| 01-function-calling | Gemini chọn hàm; ứng dụng tự thực thi hàm và gửi kết quả lại model | Gemini |
| 02-mcp-basics | Client khám phá và gọi tool trên server qua stdio | Không cần |
| 03-production | Bearer token, tìm tool qua registry, tương thích giữa v1/v2 | Không cần key dịch vụ; dùng token demo |
| 04-lab | ADK điều phối Gemini gọi MCP server qua HTTP; server lấy thời tiết thật | Gemini + WeatherAPI |

Luồng Lab 04: trình duyệt → ADK/Gemini → MCP `http://localhost:8085/mcp`
→ WeatherAPI → kết quả tool → Gemini trả lời.

Function Calling là khả năng model yêu cầu gọi công cụ; MCP chuẩn hóa việc
kết nối, khám phá và gọi công cụ. ADK xử lý vòng lặp gọi tool cho Lab 04.

## Môi trường

Máy đã có Python **3.12.10** tại
`C:\Users\duong\AppData\Local\Programs\Python\Python312\python.exe`.
Lệnh `python` hiện trỏ tới Python 3.10, vì vậy dùng interpreter trong môi trường
riêng hoặc đường dẫn Python 3.12 rõ ràng.

- `.venv`: các bài 01–03 và công cụ `uv`.
- `04-lab/mcp-server/.venv`: dependencies server theo `uv.lock`.
- `04-lab/mcp-client/.venv`: dependencies ADK client theo `uv.lock`.

Các bài 01–03 yêu cầu MCP SDK v2, còn hai lockfile Lab 04 dùng MCP SDK v1.
Giữ ba môi trường riêng để tránh xung đột.

Để cài lại từ thư mục gốc repo:

```powershell
& 'C:\Users\duong\AppData\Local\Programs\Python\Python312\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install uv
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
.\.venv\Scripts\uv.exe pip install --python .\.venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\uv.exe sync --directory 04-lab/mcp-server --locked --python 'C:\Users\duong\AppData\Local\Programs\Python\Python312\python.exe'
.\.venv\Scripts\uv.exe sync --directory 04-lab/mcp-client --locked --python 'C:\Users\duong\AppData\Local\Programs\Python\Python312\python.exe'
```

Không cần activate venv hay thay đổi PATH hệ thống.

Đã kiểm tra trên máy ngày 14/10/2026:

- Cả ba môi trường đều dùng Python 3.12.10; `uv pip check` không báo xung đột.
- Bài 02 khám phá tool và gọi thời tiết mock cho ba thành phố thành công.
- Bài 03 chạy thành công auth client, versioning và registry.
- Lab 04 khám phá đủ ba tool qua MCP và gọi `health_check` thành công.
- ADK web trả HTTP 200, liệt kê `weather_agent`; ADK khám phá đủ ba MCP tool.
- WeatherAPI đã trả thành công thời tiết Hà Nội và dự báo Tokyo qua MCP.
- Forecast từ chối `days=0` và `days=4`, giới hạn hợp lệ là 1–3 ngày.
- Luồng Gemini → ADK → MCP → WeatherAPI đã trả lời thành công bằng tiếng Việt,
  với cả `get_current_weather` và `get_forecast` do Gemini chọn.
- API chat của ADK web đã gọi `get_current_weather` thật và trả lời thành công.

Log kiểm tra cục bộ: `.cache/lab04-live-check.log` và
`.cache/lab04-web-check.log` (không chứa API key, không được commit).

Model `gemini-2.5-flash` của mã mẫu trả 404 với key mới. Lab 04 đã chuyển
mặc định sang `gemini-3.5-flash-lite`, theo
[hướng dẫn về model của Google](https://ai.google.dev/gemini-api/docs/deprecations/).
Gemini 3.8 Flash trả 503 do quá tải lúc kiểm tra; `gemini-3.5-flash-lite`
đã chạy thành công và được chọn làm cấu hình mặc định cho lab.

## Điền API key cho Lab 04

Hai file `.env` trên máy đã được điền key. Nếu cài lại repo, sao chép
`.env.example` sang `.env` trong từng thư mục (không ghi đè file đang có key).

- `04-lab/mcp-client/.env`: điền Gemini key vào `GOOGLE_API_KEY=`.
- `04-lab/mcp-server/.env`: điền WeatherAPI key vào `WEATHERAPI_KEY=`.

Client dùng `GOOGLE_GENAI_USE_VERTEXAI=FALSE` và
`MCP_SERVER_URL=http://localhost:8085/mcp`. Server dùng `PORT=8085`.
Model mặc định là `gemini-3.5-flash-lite`; có thể đặt `GEMINI_MODEL` trong client `.env`.
Các file `.env` được Git bỏ qua. Điền key trực tiếp vào file trên máy.

## Chạy Lab 04

Mở hai terminal PowerShell tại thư mục gốc repo.

Terminal 1:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\04-lab\start.ps1 -Target Server
```

Terminal 2:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\04-lab\start.ps1 -Target Client
```

Mở `http://localhost:8000`, chọn `weather_agent`, hỏi ví dụ:
“Thời tiết Hà Nội hiện tại thế nào?” hoặc “Dự báo Tokyo trong 3 ngày tới”.
Nhấn Ctrl+C tại mỗi terminal để dừng.

Server tự đọc `.env` cạnh `weather.py` và mặc định chạy HTTP, kể cả terminal
không tương tác. Muốn stdio, chạy `weather.py --transport stdio`.
Nếu thay cổng server, sửa cả `PORT` và `MCP_SERVER_URL` tương ứng.

Kiểm tra cấu hình khi server đang chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\04-lab\start.ps1 -Target Verify
powershell -NoProfile -ExecutionPolicy Bypass -File .\04-lab\start.ps1 -Target Verify -Live
```

Thiếu Gemini key sẽ báo lỗi cấu hình, dù dependencies đã cài xong.
Lệnh Verify thực hiện MCP handshake, kiểm tra ba tool, health và ADK discovery.
Thêm `-Live` để gọi WeatherAPI và Gemini thật, kiểm tra Gemini chọn cả tool thời
tiết hiện tại và dự báo, rồi in câu trả lời cuối bằng tiếng Việt. Lệnh này dùng
quota API. Key không được in ra màn hình.

Nếu Gemini báo 503, model đang quá tải: thử lại sau hoặc đổi `GEMINI_MODEL` sang
model khả dụng khác và khởi động lại client. Lỗi 429 cần kiểm tra quota/rate limit.

## Chạy các bài 01–03

```powershell
$env:PYTHONUTF8 = '1'
Push-Location 02-mcp-basics
..\.venv\Scripts\python.exe weather_client.py
Pop-Location

Push-Location 03-production
..\.venv\Scripts\python.exe versioned_client.py
..\.venv\Scripts\python.exe registry_client.py
Pop-Location
```

Phần auth cần server và client ở hai terminal, cùng thư mục `03-production`:
`..\.venv\Scripts\python.exe auth_server.py` và
`..\.venv\Scripts\python.exe auth_client.py`.
Auth server dùng cổng 8000, nên dừng ADK web trước khi chạy ví dụ auth.

Bài 01 đọc key từ biến môi trường `GEMINI_API_KEY` (khác tên biến của ADK):

```powershell
$env:GEMINI_API_KEY = 'dien_key_trong_terminal_cua_ban'
Push-Location 01-function-calling
..\.venv\Scripts\python.exe weather_function_calling.py
Pop-Location
```
