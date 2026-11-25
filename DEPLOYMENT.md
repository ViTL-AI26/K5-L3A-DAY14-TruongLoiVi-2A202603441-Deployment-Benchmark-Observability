# HƯỚNG DẪN TRIỂN KHAI — DAY 14

## 1. Thông tin triển khai

- **Nền tảng:** Railway
- **Tên Project:** day14-ai-agent
- **Tên Service:** fearless-mercy
- **Môi trường:** production
- **Public URL:** https://fearless-mercy-production-32f08b7b.up.railway.app

## 2. Các API Endpoint trên môi trường production

| Endpoint | Phương thức | Xác thực | Kết quả kiểm tra |
|---|---|---|---|
| `/health` | GET | Không yêu cầu | HTTP 200 |
| `/ready` | GET | Không yêu cầu | HTTP 200 |
| `/ask` | POST | X-API-Key | HTTP 200 khi API key hợp lệ |
| `/ask` | POST | X-API-Key | HTTP 401 khi thiếu API key |

## 3. Các biến môi trường

| Biến môi trường | Mục đích |
|---|---|
| `AGENT_API_KEY` | Khóa xác thực API |
| `REDIS_URL` | Địa chỉ kết nối Redis trên Railway |
| `RATE_LIMIT_PER_MINUTE` | Giới hạn số request trên mỗi API key trong một phút |
| `DAILY_BUDGET_USD` | Ngân sách chi phí tối đa mỗi ngày |
| `PORT` | Cổng chạy ứng dụng do Railway cung cấp |
| `ENVIRONMENT` | Môi trường triển khai, sử dụng giá trị `production` |

Các thông tin bí mật được cấu hình trực tiếp trong Railway Variables, không lưu trong mã nguồn hoặc GitHub.

## 4. Kết quả kiểm thử triển khai

### 4.1. Kiểm tra Health Check

- Gửi GET request đến `/health`.
- Kết quả thực tế: HTTP 200.
- Response: `{"status":"ok"}`.

### 4.2. Kiểm tra Readiness Check

- Gửi GET request đến `/ready`.
- Kết quả thực tế: HTTP 200.
- Response: `{"status":"ready"}`.

### 4.3. Kiểm tra API Key Authentication

- Gửi POST request đến `/ask` không có API key: HTTP 401.
- Gửi POST request đến `/ask` với API key hợp lệ: HTTP 200.
- Request hợp lệ nhận được câu trả lời JSON từ AI Agent.

## 5. Quy trình triển khai

Ứng dụng được triển khai từ thư mục `06-lab-complete/` bằng Railway CLI.

Quy trình triển khai sử dụng Dockerfile multi-stage để xây dựng Docker image và khởi chạy FastAPI application.

Redis được triển khai dưới dạng một database service riêng trên Railway. AI Agent kết nối đến Redis thông qua biến môi trường `REDIS_URL`.

## 6. Kết luận

AI Agent đã được triển khai thành công trên Railway và có thể truy cập thông qua Public URL.

Các kiểm tra Health Check, Readiness Check và API Key Authentication đều đạt kết quả mong đợi. Ứng dụng đã sẵn sàng phục vụ các request trên môi trường production.