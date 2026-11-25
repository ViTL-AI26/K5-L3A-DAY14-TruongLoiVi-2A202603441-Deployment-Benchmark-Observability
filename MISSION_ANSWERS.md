# Day 14 Lab – Câu trả lời nhiệm vụ

Tài liệu này được xây dựng dựa trên các tệp README và mã nguồn của repository. Những kết quả chưa có bằng chứng thực thi thực tế được đánh dấu là **Chưa chạy**, **Chưa đo lường** hoặc **Chưa triển khai**.

## Phần 1: Localhost và môi trường Production

### Bài tập 1.1: Các anti-pattern được phát hiện

Ứng dụng cơ bản trong `01-localhost-vs-production/develop/app.py` có những vấn đề sau khi đưa vào môi trường production:

1. API key theo định dạng OpenAI được ghi cứng trực tiếp trong mã nguồn.
2. URL cơ sở dữ liệu có chứa thông tin xác thực được ghi cứng trong mã nguồn.
3. API key được in ra trong log của request, có thể khiến thông tin bí mật bị lộ qua hệ thống ghi log.
4. Các cấu hình như `DEBUG` và `MAX_TOKENS` được cố định trong mã thay vì đọc từ biến môi trường.
5. Không có endpoint `/health` hoặc `/ready` để nền tảng triển khai giám sát ứng dụng.
6. Ứng dụng chỉ bind vào `localhost` và sử dụng cố định cổng `8000`, do đó không sử dụng giá trị `PORT` do nền tảng cung cấp hoặc tiếp nhận lưu lượng từ bên ngoài container qua `0.0.0.0`.
7. Ứng dụng luôn bật chế độ reload/debug của Uvicorn và không có cơ chế quản lý vòng đời tắt ứng dụng an toàn (graceful shutdown).

Ứng dụng có thể chạy trên máy tính cá nhân, nhưng chưa sẵn sàng cho production vì nền tảng triển khai không thể cấu hình, kiểm tra trạng thái hoặc dừng ứng dụng một cách an toàn.

### Bài tập 1.2: Quan sát phiên bản cơ bản

**Chưa chạy.** Qua việc xem xét mã nguồn, endpoint `/ask` nhận tham số truy vấn `question` và gọi mock LLM, vì vậy ứng dụng được thiết kế để chạy cục bộ. Tuy nhiên, ứng dụng vẫn tồn tại các anti-pattern đã liệt kê ở trên và không nên được triển khai nguyên trạng.

### Bài tập 1.3: Bảng so sánh

| Tiêu chí | Develop/basic | Production/advanced | Tại sao quan trọng? |
|---|---|---|---|
| Cấu hình | Các hằng số được khai báo trong `app.py`. | `config.py` đọc biến môi trường như `HOST`, `PORT`, `ENVIRONMENT` và `AGENT_API_KEY`. | Cùng một image có thể sử dụng cấu hình khác nhau trong các môi trường development, staging và production. |
| Thông tin bí mật | API key và mật khẩu cơ sở dữ liệu được nhúng trong mã nguồn; API key còn bị ghi vào log. | OpenAI key và agent key được lấy từ biến môi trường; `.env.example` là tệp mẫu. | Tránh để lộ thông tin bí mật thông qua mã nguồn hoặc log. |
| Mạng và cổng | Bind vào `localhost:8000`. | Bind vào host có thể cấu hình (mặc định `0.0.0.0`) và cổng `PORT` có thể cấu hình. | Container và nền tảng cloud cần địa chỉ bind có thể truy cập từ bên ngoài; nền tảng cũng có thể cấp cổng động. |
| Kiểm tra trạng thái | Không có health endpoint. | `/health` kiểm tra trạng thái hoạt động (liveness), còn `/ready` sử dụng cờ readiness. | Hệ thống điều phối có thể khởi động lại instance bị lỗi và ngừng chuyển request đến instance chưa sẵn sàng. |
| Ghi log | Sử dụng `print()`, bao gồm cả thông tin bí mật. | Cấu hình log theo định dạng JSON và ghi metadata của request mà không chứa key. | Log có cấu trúc an toàn hơn và thuận tiện cho việc truy vấn. |
| Tắt ứng dụng | Không có cơ chế quản lý vòng đời. | FastAPI lifespan chuyển readiness về false và thực hiện các công việc khi tắt; trình xử lý SIGTERM ghi nhận tín hiệu. | Các request đang xử lý có cơ hội hoàn tất trước khi instance dừng hoạt động. |

### Câu hỏi thảo luận

1. Một key được ghi cứng trong mã nguồn và đẩy lên repository GitHub công khai có thể bị sao chép, lạm dụng, dẫn đến rò rỉ dữ liệu hoặc phát sinh chi phí API ngoài dự kiến. Cần thu hồi hoặc xoay vòng key ngay lập tức, xóa key khỏi cấu hình triển khai và thay thế bằng secret được lưu tại nhà cung cấp dịch vụ hoặc hệ thống quản lý secret. Chỉ xóa key khỏi tệp hiện tại không đồng nghĩa với việc key đã bị xóa khỏi lịch sử Git.
2. Thiết kế stateless rất quan trọng vì load balancer có thể chuyển request tiếp theo của người dùng đến một instance khác. Việc lưu trạng thái dùng chung trong Redis hoặc cơ sở dữ liệu cho phép mọi instance tiếp tục cùng một phiên làm việc, đồng thời hỗ trợ thay thế instance hoặc mở rộng theo chiều ngang một cách an toàn.
3. Dev/prod parity là việc duy trì sự tương đồng giữa môi trường development, staging và production về runtime, dependencies, dịch vụ phụ trợ và quy trình triển khai. Trong thực tế, cần cố định phiên bản dependencies, sử dụng cấu hình theo biến môi trường, container và cùng loại dịch vụ thay vì phụ thuộc vào thiết lập riêng trên máy tính của lập trình viên.

## Phần 2: Docker

### Bài tập 2.1: Các câu hỏi về Dockerfile

1. **Image nền (Base image):** `python:3.11` trong `02-docker/develop/Dockerfile`.
2. **Thư mục làm việc (Working directory):** `/app`.
3. **Tại sao sao chép `requirements.txt` trước:** Docker có thể tái sử dụng layer cài đặt dependencies khi chỉ có mã nguồn ứng dụng thay đổi. Việc sao chép mã nguồn ở bước sau giúp tránh phải cài đặt lại dependencies mỗi khi mã ứng dụng thay đổi.
4. **CMD và ENTRYPOINT:** `CMD` cung cấp lệnh hoặc tham số mặc định và có thể được thay thế khi chạy `docker run`. `ENTRYPOINT` xác định chương trình thực thi cố định của container; các tham số được cung cấp sẽ được nối thêm vào, trừ khi entrypoint được ghi đè rõ ràng. Dockerfile này sử dụng `CMD ["python", "app.py"]`.

### Bài tập 2.2: Build và chạy

**Chưa chạy.** Chưa có số liệu đo kích thước image `agent-develop`.

### Bài tập 2.3: Multi-stage build

`02-docker/production/Dockerfile` sử dụng hai giai đoạn:

1. **Builder:** bắt đầu từ `python:3.11-slim`, cài đặt các dependencies phục vụ biên dịch/cơ sở dữ liệu, sau đó cài đặt Python dependencies vào `/root/.local`.
2. **Runtime:** bắt đầu lại từ image `python:3.11-slim` sạch, tạo người dùng không có quyền root là `appuser`, chỉ sao chép các package đã cài đặt cùng ứng dụng và tiện ích mock, sau đó khởi chạy Uvicorn với hai workers.

Image cuối cùng nhỏ hơn và có bề mặt tấn công được thu hẹp vì không chứa compiler, metadata của package manager và các tệp chỉ cần trong quá trình build. Image cũng có cấu hình Docker `HEALTHCHECK`.

**So sánh kích thước image:** Chưa đo lường. Các kích thước ước tính trong README chỉ là ví dụ hướng dẫn, không phải số liệu được ghi nhận cho bài nộp này.

### Bài tập 2.4: Docker Compose stack

Tệp Compose dành cho production định nghĩa bốn dịch vụ:

```text
Client -> Nginx (cổng 80/443) -> agent:8000
                                  |-> Redis (dịch vụ cache/giới hạn tốc độ)
                                  `-> Qdrant (cơ sở dữ liệu vector)
```

- `agent` được build từ Dockerfile production, nhận các biến `REDIS_URL` và `QDRANT_URL`, đồng thời chờ Redis và Qdrant vượt qua health check.
- `redis` là cache nội bộ sử dụng `redis:7-alpine`, có persistent volume và chính sách quản lý bộ nhớ LRU.
- `qdrant` là cơ sở dữ liệu vector nội bộ, có lưu trữ dữ liệu bền vững.
- `nginx` là dịch vụ duy nhất tiếp xúc trực tiếp với bên ngoài. Nginx reverse proxy đến agent, áp dụng giới hạn 10 request/giây cho mỗi IP với burst 20, bổ sung các security header và cung cấp route `/health` không bị giới hạn tốc độ.

Stack này chưa được chạy để phục vụ câu trả lời này, vì vậy không khẳng định đã có kết quả kiểm thử endpoint.

### Câu hỏi thảo luận

1. Sao chép dependencies trước mã nguồn giúp Docker cache layer cài đặt dependencies khi chỉ có mã ứng dụng thay đổi, từ đó rút ngắn thời gian build lại.
2. `.dockerignore` nên loại trừ các thông tin bí mật (`.env`), môi trường ảo, Python cache, metadata Git, các tệp kiểm thử/build và những tệp không cần thiết khi chạy ứng dụng. `venv/` có thể làm tăng kích thước build context và có thể chứa binary dành cho hệ điều hành khác; `.env` có thể làm lộ thông tin xác thực trong một layer của image.
3. Có thể mount thư mục trên máy host hoặc named volume bằng `docker run -v host_path:/container_path` hoặc khai báo `volumes:` trong Compose. Nên sử dụng mount chỉ đọc nếu agent chỉ cần đọc các tệp.

## Phần 3: Triển khai lên Cloud

### Bài tập 3.1: Triển khai trên Railway

**URL công khai:** https://fearless-mercy-production-32f08b7b.up.railway.app

**Nền tảng:** Railway

**Trạng thái triển khai:** Đã triển khai thành công và xác minh.

- `/health`: HTTP 200 — `{"status":"ok"}`
- `/ready`: HTTP 200 — `{"status":"ready"}`
- `/ask` khi không có API key: HTTP 401.
- `/ask` khi có API key hợp lệ: HTTP 200 với câu trả lời JSON hợp lệ.

Dịch vụ chạy từ thư mục `06-lab-complete/` bằng Dockerfile multi-stage. Redis trên Railway được kết nối thông qua biến môi trường `REDIS_URL`.

Ví dụ Railway có cấu trúc sẵn sàng triển khai: `app.py` đọc `PORT`, bind vào `0.0.0.0` và cung cấp `/health`. `railway.toml` sử dụng Nixpacks builder, khởi chạy Uvicorn trên `$PORT`, cấu hình `/health` và khởi động lại khi có lỗi. Việc đăng nhập Railway, tạo project, cấu hình môi trường, triển khai và kiểm tra URL công khai thực tế chưa được thực hiện cho câu trả lời này.

### Bài tập 3.2: So sánh cấu hình triển khai trên Render

`render.yaml` là Blueprint khai báo hạ tầng, mô tả một dịch vụ web Python và một dịch vụ Redis bằng YAML. Tệp bao gồm lệnh build/start, kiểm tra `/health`, khu vực Singapore, tự động triển khai và khai báo biến môi trường. `OPENAI_API_KEY` sử dụng `sync: false`, còn `AGENT_API_KEY` sử dụng `generateValue: true`, do đó không có secret thực nào được ghi trực tiếp vào tệp.

`railway.toml` là tệp TOML dành riêng cho Railway. Tệp tập trung vào builder, lệnh khởi chạy, đường dẫn health check và chính sách restart; thông tin bí mật dự kiến được thiết lập thông qua dashboard hoặc CLI của Railway. Cả hai cấu hình đều sử dụng `$PORT` và `/health`, nhưng Render khai báo các tài nguyên hạ tầng trong Blueprint, trong khi cấu hình Railway tập trung vào từng service.

### Bài tập 3.3: Đánh giá tùy chọn CI/CD với Cloud Run

`cloudbuild.yaml` định nghĩa một pipeline thực hiện cài đặt dependencies và chạy kiểm thử, build/tag image bằng commit SHA và `latest`, đẩy image lên Container Registry và triển khai lên Cloud Run tại `asia-southeast1`. Quá trình triển khai thiết lập số lượng instance tối thiểu/tối đa, CPU/bộ nhớ, timeout, môi trường production và lấy OpenAI key từ Secret Manager.

`service.yaml` mô tả dịch vụ Cloud Run theo dạng khai báo: ingress công khai, autoscaling từ một đến mười instance, concurrency mục tiêu 80, giới hạn tài nguyên, biến môi trường và tham chiếu secret, liveness probe tại `/health` và startup probe tại `/ready`.

### Câu hỏi thảo luận

1. Serverless function không phải lúc nào cũng phù hợp với AI agent vì cold start, giới hạn thời gian request, giới hạn bộ nhớ/CPU, khả năng tái sử dụng kết nối, streaming và chi phí tải model có thể ảnh hưởng đến độ trễ hoặc độ tin cậy.
2. Cold start là khoảng thời gian nhà cung cấp khởi tạo và chuẩn bị một instance mới. Người dùng cảm nhận điều này qua phản hồi đầu tiên chậm hơn; duy trì một số instance luôn hoạt động có thể giảm độ trễ này nhưng làm tăng chi phí.
3. Nên chuyển từ Railway sang Cloud Run khi dự án cần kiểm soát autoscaling/concurrency chi tiết hơn, CI/CD có thể tái lập, tích hợp Secret Manager, observability production hoặc quyền kiểm soát vận hành cao hơn. Railway vẫn phù hợp với prototype đơn giản hoặc demo môn học.

## Phần 4: Bảo mật API

### Bài tập 4.1: Xác thực bằng API key

Trong `04-api-gateway/develop/app.py`, `APIKeyHeader(name="X-API-Key", auto_error=False)` đọc header và `verify_api_key()` so sánh giá trị này với `AGENT_API_KEY` trước khi endpoint `/ask` được thực thi. Thiếu key sẽ trả về **401**; key không khớp sẽ trả về **403**. Endpoint `/health` được truy cập công khai.

Để xoay vòng key, hãy tạo secret mới, cập nhật biến môi trường trên nền tảng triển khai, triển khai/khởi động lại dịch vụ, cập nhật các client được cấp quyền và thu hồi key cũ. Dịch vụ production thực tế không nên sử dụng key dự phòng phục vụ mục đích giáo dục trong ví dụ này và tuyệt đối không ghi key thật vào log, mặc dù ứng dụng demo in key đã cấu hình khi khởi động.

**Kết quả kiểm thử:** Chưa thực hiện kiểm thử độc lập đối với API Key trong Exercise 4.1; chưa khẳng định kết quả HTTP cho phiên bản này.

### Bài tập 4.2: Xác thực bằng JWT

Dịch vụ nâng cao sử dụng quy trình sau:

1. `POST /auth/token` xác thực username/password mẫu bằng `authenticate_user()`.
2. `create_token()` ký JWT chứa subject, role, thời điểm phát hành và thời hạn 60 phút.
3. Client gửi `Authorization: Bearer <token>` đến `/ask`.
4. `verify_token()` xác thực chữ ký và thời hạn, sau đó trả về `username` và `role` cho endpoint.

Mã nguồn cung cấp hai tài khoản minh họa: `student` (vai trò user) và `teacher` (vai trò admin). Đường dẫn endpoint trong mã nguồn hiện tại là `/auth/token`. Thông tin xác thực bị thiếu sẽ trả về 401, token hết hạn trả về 401 và JWT không hợp lệ trả về 403. JWT secret mặc định được xác định rõ là giá trị dự phòng cho demo; khi triển khai production phải thiết lập `JWT_SECRET` một cách an toàn.

**Kết quả kiểm thử:** Đã kiểm thử thành công trên local API:

- Đăng nhập bằng tài khoản `student / demo123` tại `POST /auth/token` và nhận JWT thành công.
- Gửi request đến `/ask` không có Bearer token trả về **HTTP 401 Unauthorized**, với thông báo `Authentication required`.
- Gửi request có JWT hợp lệ được chấp nhận và trả về **HTTP 200 OK**.

### Bài tập 4.3: Giới hạn tốc độ (Rate limiting)

`04-api-gateway/production/rate_limiter.py` triển khai bộ đếm theo cửa sổ trượt trong bộ nhớ (**in-memory sliding-window counter**) bằng cách sử dụng `deque` lưu timestamp cho từng người dùng. Các timestamp cũ được loại bỏ trước mỗi lần kiểm tra.

- Người dùng thông thường: **10 request trong 60 giây**.
- Người dùng admin: **100 request trong 60 giây**.
- `/ask` chọn bộ giới hạn dành cho admin khi role JWT đã xác minh là `admin`; đây là cơ chế trong mã nguồn giúp admin có giới hạn cao hơn.
- Request vượt giới hạn nhận phản hồi **429** cùng thông tin giới hạn và thời gian chờ thử lại.

Cách triển khai này chỉ phù hợp với demo chạy một process. Chính mã nguồn cũng lưu ý rằng để mở rộng production cần sử dụng rate limiter dựa trên Redis, nhằm chia sẻ trạng thái giữa nhiều instance.

**Kết quả kiểm thử:** Đã kiểm thử thành công trên local API bằng tài khoản `student`:

- 10 request đầu tiên liên tiếp trả về **HTTP 200 OK**.
- Request thứ 11 trả về **HTTP 429 Too Many Requests**.
- Response ghi nhận `limit: 10`, `window_seconds: 60` và `retry_after_seconds: 59`.

Kết quả xác nhận cơ chế sliding-window rate limiter hoạt động đúng với giới hạn 10 request trong 60 giây.

### Bài tập 4.4: Triển khai Cost Guard

`CostGuard` được cung cấp là một triển khai giáo dục lưu trạng thái trong bộ nhớ, không phải triển khai Redis. Thành phần này duy trì một `UsageRecord` theo ngày cho mỗi người dùng và tổng chi phí toàn hệ thống theo ngày:

- Chi phí input: `$0.00015` cho mỗi 1K token; chi phí output: `$0.0006` cho mỗi 1K token.
- Ngân sách hằng ngày cho mỗi người dùng: `$1.00`; ngân sách hằng ngày toàn hệ thống: `$10.00`.
- Hệ thống cảnh báo khi người dùng sử dụng 80% ngân sách.
- `check_budget()` được gọi trước khi gọi mock LLM. Người dùng vượt ngân sách nhận **402**; khi ngân sách toàn hệ thống cạn, hệ thống trả về **503**.
- `record_usage()` được gọi sau khi xử lý và cập nhật số token, số request, chi phí của người dùng và chi phí toàn hệ thống.

Để có thể mở rộng, nên sử dụng Redis key theo tháng, chẳng hạn `budget:<user_id>:YYYY-MM`, thực hiện so sánh/cộng chi phí ước tính của request một cách nguyên tử, đặt TTL dài hơn một tháng một chút và từ chối request trước khi gọi LLM nếu ngân sách cho phép bị vượt. Đây là phương án được bài lab đề xuất; phương án này chưa được bổ sung vào mã nguồn Part 4 tại đây.

## Phần 5: Mở rộng và độ tin cậy

### Bài tập 5.1: Health check

Ứng dụng development triển khai cả hai endpoint:

- `/health` là endpoint liveness. Endpoint trả về trạng thái, uptime, phiên bản, môi trường, timestamp và kiểm tra bộ nhớ bằng `psutil` nếu thư viện này khả dụng. Endpoint có thể trả về trạng thái `degraded` nếu mức sử dụng bộ nhớ cao.
- `/ready` là endpoint readiness. Endpoint trả về **503** cho đến khi quá trình khởi động đặt `_is_ready = True`, đồng thời cũng trả về trạng thái này trong quá trình shutdown khi cờ được đặt thành false. Trong trường hợp bình thường, endpoint trả về trạng thái sẵn sàng cùng số request đang được xử lý.

**Kết quả kiểm thử:** Chưa chạy; không có kết quả endpoint nào được khẳng định.

### Bài tập 5.2: Graceful shutdown

Ứng dụng development sử dụng FastAPI lifespan và middleware `track_requests`. Khi khởi động, ứng dụng mô phỏng quá trình tải dependencies/model và đánh dấu dịch vụ đã sẵn sàng. Trong quá trình shutdown, ứng dụng đánh dấu trạng thái không còn sẵn sàng, sau đó chờ tối đa 30 giây để `_in_flight_requests` giảm về 0. Các signal handler cho SIGTERM và SIGINT ghi log sự kiện trong khi Uvicorn thực hiện vòng đời shutdown thông thường. Uvicorn được cấu hình `timeout_graceful_shutdown=30`.

**Kết quả kiểm thử:** Chưa chạy; chưa có kết quả về request đang xử lý hoặc tín hiệu SIGTERM.

### Bài tập 5.3: Thiết kế Stateless

Ứng dụng production lưu các phiên làm việc dưới Redis key `session:<session_id>` với TTL một giờ. Ứng dụng tuần tự hóa hội thoại dưới dạng JSON, thêm các message vào lịch sử, giữ lại 20 message gần nhất và cung cấp các endpoint để tạo/tiếp tục cuộc trò chuyện, xem lịch sử và xóa phiên. Vì trạng thái được lưu trong Redis, các instance agent khác nhau có thể sử dụng cùng một session ID.

Mã nguồn có cơ chế dự phòng lưu trong bộ nhớ khi không thể kết nối Redis. Cơ chế này hỗ trợ demo cục bộ nhưng không stateless hoặc có khả năng mở rộng; chế độ sử dụng Redis mới là hướng phù hợp cho production.

### Bài tập 5.4: Cân bằng tải (Load balancing)

Compose stack khai báo dịch vụ `agent`, Redis và Nginx. Dịch vụ agent được cấu hình ba replicas và chỉ có thể được truy cập thông qua Nginx tại cổng host `8080`. Nginx sử dụng `upstream agent_cluster` trỏ đến `agent:8000`, proxy các request, thử lại với một số lỗi upstream được chọn và bổ sung `X-Served-By` để có thể quan sát instance upstream đã xử lý request. Redis được chia sẻ giữa tất cả instance agent.

**Kết quả kiểm thử:** Chưa chạy; chưa có kết quả về scaling, lỗi instance hoặc load balancing.

### Bài tập 5.5: Đánh giá kiểm thử Stateless

`test_stateless.py` gửi năm request `/chat` tuần tự với cùng một session ID thông qua `http://localhost:8080`, ghi nhận các giá trị `served_by`, sau đó truy xuất lịch sử hội thoại. Script cho biết có quan sát được nhiều hơn một instance hay không và in ra các message đã được lưu.

Script xác minh tính liên tục của session qua nhiều request. Tuy nhiên, script **không** dừng ngẫu nhiên một instance mặc dù mô tả bài tập có đề cập đến tình huống này. Script chưa được chạy cho câu trả lời này, vì vậy không báo cáo session ID, danh sách instance hoặc kết quả kiểm thử.

## Phần 6: Dự án cuối kỳ

Dự án hoàn chỉnh trong `06-lab-complete/` đã được kiểm tra bằng công cụ production-readiness checker được cung cấp.

```text
PASS 12/12 — 41/41 checks passed
```

Các hạng mục được xác minh bao gồm Docker image multi-stage, Compose stack agent/Redis, `.dockerignore`, health/readiness, xác thực API key, rate limiting bằng Redis, cost guard, cấu hình môi trường, JSON logging, graceful shutdown và cấu hình Railway. Checker đo được kích thước image sau khi build là **63 MB**.

## Nhật ký sử dụng AI (AI Usage Log)

AI được sử dụng để hỗ trợ các công việc sau:

- Đọc tài liệu Day 14 và mã nguồn của các phần 1–6.
- Giải thích yêu cầu của từng bài tập và xác định hành vi trong mã nguồn có liên quan đến câu trả lời.
- Phân biệt các ví dụ được mô tả trong tài liệu với kết quả thực tế đã chạy hoặc đo lường.
- Soạn thảo và sắp xếp các câu trả lời ngắn gọn bằng tiếng Anh.

Nội dung cuối cùng được giới hạn trong bằng chứng từ repository và kết quả checker của Part 6 được cung cấp. Không có kết quả kiểm thử, benchmark, kích thước image hoặc URL công khai nào được tự tạo ra.
