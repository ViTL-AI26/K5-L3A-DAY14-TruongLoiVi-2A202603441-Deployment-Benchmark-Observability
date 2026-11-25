# Benchmark & Observability Report — Day 14

**Họ tên:** Trương Lợi Vĩ
**Ngày chạy:** 25/11/2026
**Môi trường:** MacBook Air, macOS, Python 3.11.3; local development environment; Mock LLM.

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---:|---|
| p95 latency `/ask` | ≤ 500 ms | Giữ phần lớn request phản hồi nhanh, đảm bảo trải nghiệm người dùng |
| Error rate `/ask` | ≤ 2% | Giới hạn tỷ lệ request thất bại ở mức thấp |
| Accuracy trên golden dataset | ≥ 80% | Đảm bảo agent trả lời đúng phần lớn câu hỏi trong bộ dữ liệu đánh giá |

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 5.37 | 189.6 | 212.5 | 222.3 | 3.00% | FAIL (error rate) |
| 10 | 32.88 | 189.3 | 220.7 | 1709.4 | 2.00% | PASS |
| 50 | 52.24 | 192.9 | 226.1 | 1714.7 | 0.00% | PASS |
| 100 | 57.38 | 233.3 | 369.4 | 1737.1 | 0.00% | PASS |

**Nhận xét:**

Throughput tăng đáng kể khi concurrency tăng từ 1 lên 100, từ 5.37 req/s lên 57.38 req/s. Tuy nhiên, mức tăng không tuyến tính. Khi concurrency tăng, hệ thống tận dụng khả năng xử lý đồng thời tốt hơn, nhưng throughput dần tăng chậm lại.

Ở concurrency 100, p95 đạt 369.4 ms, vẫn nằm trong ngưỡng SLO 500 ms. Tuy nhiên, p99 tăng lên 1737.1 ms, cho thấy vẫn tồn tại một số request có tail latency cao.

Ở concurrency 1, error rate là 3%, vượt ngưỡng 2%. Các lỗi HTTP 503 được Mock LLM mô phỏng.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---:|---:|---:|---:|
| 0 | 193.6 | 219.4 | 226.5 |
| 0.03 (mặc định) | 220.7 | 218.6 | 1695.0 |
| 0.1 | 327.7 | 1683.0 | 1711.8 |

**Nhận xét:**

Khi tỷ lệ request chậm tăng, tail latency có xu hướng tăng. Ở mức `MOCK_SLOW_RATE=0.03`, p99 tăng lên 1695 ms trong khi p95 vẫn ở mức 218.6 ms. Khi tỷ lệ tăng lên 0.1, p95 tăng lên 1683 ms và không đạt SLO 500 ms.

Các percentile cao như p95 và p99 giúp phát hiện những request chậm mà average latency có thể che giấu. Vì vậy, SLO không nên chỉ dựa trên latency trung bình.

### 2.3 Load test tổng thể

| Chỉ số | Kết quả |
|---|---:|
| Requests | 300 |
| Concurrency | 20 |
| Duration | 5.06 s |
| Throughput | 59.3 req/s |
| Error rate | 0.67% |
| Average latency | 251.0 ms |
| p50 | 191.3 ms |
| p95 | 223.3 ms |
| p99 | 1709.6 ms |
| Total cost | $0.010056 |

Kết quả: SLO p95 và SLO error rate đều PASS.

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 | Agent v2 final |
|---|---:|---:|---:|
| Accuracy | 4.3% | 91.3% | 100.0% |
| Passed | 1/23 | 21/23 | 23/23 |
| Avg tokens / câu | 57.1 | 109.3 | 118.8 |
| Tổng cost (USD) | 0.000404 | 0.000764 | 0.000835 |
| Cost / câu đúng (USD) | 0.00040395 | 0.00003639 | 0.00003629 |
| Latency p95 (ms) | 189.9 | 213.5 | 222.7 |
| Regression | - | 0 | 0 |
| Quality gate | FAIL | PASS | PASS |

**Các thay đổi Knowledge Base:**

- `security-02`: Bổ sung kiến thức JWT, Bearer token, xác minh chữ ký và thời hạn token.
- `scaling-03`: Bổ sung kiến thức Kubernetes HPA, CPU utilization, memory utilization và custom metrics.

Sau khi hoàn thiện Knowledge Base, agent v2 final đạt accuracy 100% (23/23). Có 22 câu được cải thiện so với v1 và không có regression.

Quality gate được cấu hình với accuracy tối thiểu 100%. Kết quả cuối cùng: PASS.

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:**

Agent v2 final cải thiện accuracy từ 4.3% lên 100%, tương ứng tăng 95.7 điểm phần trăm so với v1. Việc bổ sung retrieval context giúp agent trả lời chính xác hơn trên golden dataset.

Đổi lại, số token trung bình tăng từ 57.1 lên 118.8 và tổng chi phí tăng từ $0.000404 lên $0.000835. Tuy nhiên, cost trên mỗi câu trả lời đúng giảm từ $0.00040395 xuống $0.00003629.

Latency p95 tăng từ 189.9 ms lên 222.7 ms. Đây là trade-off giữa chất lượng trả lời, chi phí và độ trễ khi sử dụng retrieval.

## 4. Observability stack (production)

### 4.1 Screenshot và bằng chứng

Các ảnh minh chứng đã được lưu trong thư mục `screenshots/`:

- [x] `dashboard.png`: Grafana dashboard khi hệ thống có tải, hiển thị Golden Signals.
- [x] `grafana-dashboard.png`: Grafana dashboard tổng quan.
- [x] `jaeger-slow-trace.png`: Trace chậm trong Jaeger.
- [x] `jaeger-error-trace.png`: Trace lỗi HTTP 503 trong Jaeger.
- [x] `prometheus-alert-firing.png`: Trang Alerts của Prometheus với alert đang firing.

**Trạng thái:** Đã thực hiện và lưu screenshot.

Grafana ghi nhận 3 agent instances đang hoạt động, error rate hiện tại 0%, p95 latency khoảng 1.74 giây và LLM cost trong cửa sổ một giờ khoảng $0.7411.

Prometheus Targets xác nhận cả 3 agent instances đều UP.

### 4.2 Thí nghiệm "phá hệ thống"

Đã thực hiện thử nghiệm tăng đồng thời tỷ lệ lỗi và tỷ lệ request chậm để kiểm tra khả năng phát hiện sự cố của Prometheus.

| Thay đổi | Alert firing | Giá trị quan sát | Trạng thái |
|---|---|---|---|
| `MOCK_ERROR_RATE=0.10` | `AgentHighErrorRate` | Error rate 9.42% | FIRING |
| `MOCK_SLOW_RATE=0.10` | `AgentHighLatencyP95` | p95 latency 1.777 giây | FIRING |
| `LLM_MODEL=mock-llm-large` | Chưa kiểm tra | Chưa đo | Chưa thực hiện |
| `docker pause` 1 instance | Chưa kiểm tra | Chưa đo | Chưa thực hiện |
| `AGENT_VERSION=v1` | Chưa kiểm tra | Chưa đo | Chưa thực hiện |

Hai alert được kích hoạt sau khi chạy Locust với 30 users, tốc độ 5 requests/giây trong khoảng 3 phút. Prometheus hiển thị thời điểm Active Since khoảng 3 phút 26 giây đối với `AgentHighErrorRate` và 3 phút 28 giây đối với `AgentHighLatencyP95`. Đây là thời gian alert đã ở trạng thái active khi quan sát, không phải phép đo chính xác thời gian từ lúc thay đổi cấu hình đến lúc firing.

Sau thử nghiệm, các biến môi trường được khôi phục về:

- `MOCK_SLOW_RATE=0.03`
- `MOCK_ERROR_RATE=0.01`

Ba agent instances được recreate và xác nhận healthy.

### 4.3 Debug bằng trace

Đã sử dụng Jaeger để kiểm tra hai request đại diện:

**Slow trace:**
- Endpoint: `POST /ask`
- HTTP status: 200
- Tổng thời gian: khoảng 1.7 giây
- Số spans: 4
- Thời gian xử lý chủ yếu nằm ở bước gọi GenAI/LLM.

**Error trace:**
- Endpoint: `POST /ask`
- HTTP status: 503
- Tổng thời gian: khoảng 844 ms
- Số spans: 4
- Trace ghi nhận request thất bại do upstream LLM error được mô phỏng.

Hai trace được lưu lần lượt tại `screenshots/jaeger-slow-trace.png` và `screenshots/jaeger-error-trace.png`.

Kết quả cho thấy distributed tracing hỗ trợ xác định request chậm và phân tích đường đi của request khi xảy ra lỗi.

## 5. Benchmark scaling (production, Locust headless)

Thử nghiệm sử dụng Locust với 100 users, so sánh cấu hình 1 agent instance và 3 agent instances. Số liệu dưới đây được tổng hợp từ các file CSV Locust trong `benchmark-results/`.

| Số instance | Requests | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures | Error rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7,857 | 65.84 | 190 | 220 | 1,700 | 84 | 1.069% |
| 3 | 7,919 | 66.35 | 190 | 220 | 1,700 | 60 | 0.758% |

### Nhận xét

Khi tăng số agent instances từ 1 lên 3:

- Throughput tăng nhẹ từ 65.84 lên 66.35 requests/giây, tương đương khoảng 0.78%.
- Error rate giảm từ 1.069% xuống 0.758%.
- Average latency giảm từ 216.55 ms xuống 209.82 ms.
- p50, p95 và p99 gần như không thay đổi.

Kết quả cho thấy cấu hình 3 instances có cải thiện nhẹ về throughput và error rate trong thử nghiệm này. Tuy nhiên, mức cải thiện throughput chưa lớn, do đó chưa thể kết luận hệ thống scale tuyến tính theo số lượng instances.

Các file CSV được lưu trong `benchmark-results/`, gồm `scale_1_stats.csv`, `scale_3_stats.csv` và các file history/failures/exceptions tương ứng.