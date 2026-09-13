# SHUUD Web + App

**Уриа:** 2 минутын дотор замаа чөлөөл.

SHUUD нь замын жижиг тохиолдлыг мэдээлэх → SHIID шийдвэр → даатгалын баталгаа → зам чөлөөлөлт → төлбөр гэсэн нэг урсгалаар харуулах бүтээгдэхүүний интерфейс юм.

## Одоогийн MVP

- `index.html` — responsive Web + mobile/PWA interface
- `manifest.webmanifest` — гар утсанд суулгах PWA manifest
- `sw.js` — offline cache ба шинэ хувилбарын cache lifecycle
- `api.js` — escrow/payment backend adapter

## Demo flow

1. Тохиолдол мэдээлэх
2. Evidence бүрдүүлэх
3. SHIID шийдвэр
4. 120 секундийн явц
5. Зам чөлөөлөлтийг баталгаажуулах
6. Төлбөрийн баталгааг харуулах

## Backend connection

`api.js` нь same-origin `/api/v1` endpoint-уудыг ашиглахаар тохируулагдсан. Одоогийн GerChain API-ийн escrow урсгалтай:

- `POST /api/v1/escrows/create`
- `GET /api/v1/escrows/{escrow_id}`
- `POST /api/v1/escrows/{escrow_id}/action`

UI дээр backend-ийн нэрийг харуулах шаардлагагүй. SHUUD нь хэрэглэгчид харагдах бүтээгдэхүүн, backend нь дэд бүтэц байна.

## Хөгжүүлэх дараагийн шат

- Demo alert-уудыг бодит SHUUD state machine болгох
- Incident API нэмэх
- Evidence upload/storage холбох
- SHIID decision state холбох
- 120 секундийн сервер талын timer/event timeline
- Escrow lock/release-ийг UI action-тай холбох
- Sandbox analytics-ийг бодит event log-оос тооцох
