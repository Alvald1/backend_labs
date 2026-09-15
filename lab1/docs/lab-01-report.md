# Лабораторная работа 1. HTTP-сервер на сокетах

Тема: каталог товаров. Реализованы техническая часть задач 1–4
и дополнительная задача 5.

Условие: [Part-1](https://git.digital.mephi.ru/Backend/Project/src/branch/main/Part-1),
коммит `b73de9660af574566f0891cc51a4b2efe4c7b446`.

## Окружение и запуск

Базовые HTTP-обмены записаны 13 сентября 2026 года на Linux-сервере `for-labs`
(локальный SSH-алиас `for-lab`): Python 3.13.15, uv 0.12.13, curl 8.5.0.
Для лабораторной использован отдельный каталог и адрес `127.0.0.1:18081`.
Работающие проекты сервера не останавливались.

```bash
uv sync --locked
uv run python -m rawhttp.server --port 18081
```

Восемь запросов выполнены последовательно после запуска с пустым словарём.
Вместо `/bookings` из примера используется ресурс выбранной темы — `/products`.
Флаги `-sS` убирают индикатор загрузки и сохраняют сообщения об ошибках.
При сборе вывода также использовались `-q` (не читать локальный curlrc)
и `--max-time 30`; они не меняют содержимое HTTP-запросов.

## Результаты команд

Коды первых восьми ответов: `200, 201, 204, 405, 404, 400, 404, 201`.
У ответа 204 отсутствуют тело, `Content-Type` и `Content-Length`.
У ответа 405 есть `Allow: GET`.
Последний JSON содержит 77 символов и занимает 87 байт в UTF-8:
десять букв в слове «Клавиатура» занимают по два байта.


### Команда 1

```bash
curl -sS -i http://127.0.0.1:18081/health
```

```text
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 66

{"status": "ok", "service": "product-catalog", "version": "0.1.0"}
```

### Команда 2

```bash
curl -sS -i -X POST http://127.0.0.1:18081/products -H 'Content-Type: application/json' -d '{"name": "Keyboard", "category_id": 1, "price": 2500, "stock": 10}'
```

```text
HTTP/1.1 201 Created
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 75
Location: /products/1

{"name": "Keyboard", "category_id": 1, "price": 2500, "stock": 10, "id": 1}
```

### Команда 3

```bash
curl -sS -i -X DELETE http://127.0.0.1:18081/products/1
```

```text
HTTP/1.1 204 No Content
Connection: close
```

### Команда 4

```bash
curl -sS -i -X PUT http://127.0.0.1:18081/health
```

```text
HTTP/1.1 405 Method Not Allowed
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 31
Allow: GET

{"error": "Method not allowed"}
```

### Команда 5

```bash
curl -sS -i http://127.0.0.1:18081/nothing-here
```

```text
HTTP/1.1 404 Not Found
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 22

{"error": "Not found"}
```

### Команда 6

```bash
curl -sS -i -X POST http://127.0.0.1:18081/products -H 'Content-Type: application/json' -d '{"name": "Keyboard",'
```

```text
HTTP/1.1 400 Bad Request
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 24

{"error": "Bad request"}
```

### Команда 7

```bash
curl -sS -i -X DELETE http://127.0.0.1:18081/products/999
```

```text
HTTP/1.1 404 Not Found
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 30

{"error": "Product not found"}
```

### Команда 8

```bash
curl -sS -i -X POST http://127.0.0.1:18081/products -H 'Content-Type: application/json' -d '{"name": "Клавиатура", "category_id": 1, "price": 2500, "stock": 10}'
```

```text
HTTP/1.1 201 Created
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 87
Location: /products/2

{"name": "Клавиатура", "category_id": 1, "price": 2500, "stock": 10, "id": 2}
```

### Команда 9

```bash
curl -sv http://127.0.0.1:18081/health
```

```text
*   Trying 127.0.0.1:18081...
* Connected to 127.0.0.1 (127.0.0.1) port 18081
> GET /health HTTP/1.1
> Host: 127.0.0.1:18081
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/1.1 200 OK
< Connection: close
< Content-Type: application/json; charset=utf-8
< Content-Length: 66
<
{ [66 bytes data]
* Closing connection
{"status": "ok", "service": "product-catalog", "version": "0.1.0"}
```

### Команда 10

```bash
curl -sv https://example.com/ -o /dev/null
```

```text
* Host example.com:443 was resolved.
* IPv6: 2a06:98c1:3122:8000::, 2a06:98c1:3123:8000::
* IPv4: 8.47.69.0, 8.6.112.0
*   Trying 8.47.69.0:443...
* Connected to example.com (8.47.69.0) port 443
* ALPN: curl offers h2,http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [512 bytes data]
*  CAfile: /etc/ssl/certs/ca-certificates.crt
*  CApath: /etc/ssl/certs
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Server hello (2):
{ [122 bytes data]
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
{ [19 bytes data]
* TLSv1.3 (IN), TLS handshake, Certificate (11):
{ [3686 bytes data]
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
{ [79 bytes data]
* TLSv1.3 (IN), TLS handshake, Finished (20):
{ [52 bytes data]
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
} [1 bytes data]
* TLSv1.3 (OUT), TLS handshake, Finished (20):
} [52 bytes data]
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519 / id-ecPublicKey
* ALPN: server accepted h2
* Server certificate:
*  subject: CN=example.com
*  start date: Jul 29 22:10:08 2026 GMT
*  expire date: Oct 27 22:17:21 2026 GMT
*  subjectAltName: host "example.com" matched cert's "example.com"
*  issuer: C=US; O=SSL Corporation; CN=Cloudflare TLS Issuing ECC CA 3
*  SSL certificate verify ok.
*   Certificate level 0: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA256
*   Certificate level 1: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 2: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 3: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384
} [5 bytes data]
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://example.com/
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: example.com]
* [HTTP/2] [1] [:path: /]
* [HTTP/2] [1] [user-agent: curl/8.5.0]
* [HTTP/2] [1] [accept: */*]
} [5 bytes data]
> GET / HTTP/2
> Host: example.com
> User-Agent: curl/8.5.0
> Accept: */*
>
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [230 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [230 bytes data]
* old SSL session ID is stale, removing
{ [5 bytes data]
< HTTP/2 200
< date: Sun, 13 Sep 2026 15:14:22 GMT
< content-type: text/html
< server: cloudflare
< last-modified: Fri, 11 Sep 2026 17:42:00 GMT
< allow: GET, HEAD
< accept-ranges: bytes
< age: 4586
< cf-cache-status: HIT
< cf-ray: a3a819ec39b6ec5b-DME
<
{ [5 bytes data]
* Connection #0 to host example.com left intact
```

### Команда 11

```bash
curl -sv --http1.1 --compressed https://example.com/ -o /dev/null
```

```text
* Host example.com:443 was resolved.
* IPv6: 2a06:98c1:3122:8000::, 2a06:98c1:3123:8000::
* IPv4: 8.47.69.0, 8.6.112.0
*   Trying 8.47.69.0:443...
* Connected to example.com (8.47.69.0) port 443
* ALPN: curl offers http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [512 bytes data]
*  CAfile: /etc/ssl/certs/ca-certificates.crt
*  CApath: /etc/ssl/certs
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Server hello (2):
{ [122 bytes data]
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
{ [25 bytes data]
* TLSv1.3 (IN), TLS handshake, Certificate (11):
{ [3686 bytes data]
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
{ [79 bytes data]
* TLSv1.3 (IN), TLS handshake, Finished (20):
{ [52 bytes data]
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
} [1 bytes data]
* TLSv1.3 (OUT), TLS handshake, Finished (20):
} [52 bytes data]
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519 / id-ecPublicKey
* ALPN: server accepted http/1.1
* Server certificate:
*  subject: CN=example.com
*  start date: Jul 29 22:10:08 2026 GMT
*  expire date: Oct 27 22:17:21 2026 GMT
*  subjectAltName: host "example.com" matched cert's "example.com"
*  issuer: C=US; O=SSL Corporation; CN=Cloudflare TLS Issuing ECC CA 3
*  SSL certificate verify ok.
*   Certificate level 0: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA256
*   Certificate level 1: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 2: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 3: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384
* using HTTP/1.x
} [5 bytes data]
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/8.5.0
> Accept: */*
> Accept-Encoding: deflate, gzip, br, zstd
>
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [230 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [230 bytes data]
* old SSL session ID is stale, removing
{ [5 bytes data]
< HTTP/1.1 200 OK
< Date: Sun, 13 Sep 2026 15:14:22 GMT
< Content-Type: text/html
< Transfer-Encoding: chunked
< Connection: keep-alive
< Server: cloudflare
< last-modified: Fri, 11 Sep 2026 17:42:00 GMT
< allow: GET, HEAD
< Age: 4586
< cf-cache-status: HIT
< Content-Encoding: br
< CF-RAY: a3a819ecbb57f143-DME
<
{ [318 bytes data]
* Connection #0 to host example.com left intact
```

## Разбор HTTP

### Что показывает curl

- `*` — сообщения самого curl: разрешение имени, подключение, TLS, выбор протокола.
- `>` — отправленные заголовки и представление стартовой строки запроса.
- `<` — полученные заголовки и строка состояния ответа.

Например, `GET /health HTTP/1.1`: `GET` — метод, `/health` — целевой путь,
`HTTP/1.1` — версия протокола. Разделители строк в HTTP/1.1 — `\r\n`,
после заголовков идёт пустая строка. В HTTP/2 curl тоже показывает удобную
для чтения строку `GET / HTTP/2`, но по сети передаются двоичные кадры
и псевдозаголовки `:method`, `:path`, `:scheme`, `:authority`.

Заголовки запросов:

| Заголовок | Кто добавил | Зачем |
|---|---|---|
| `Host` | curl по URL | Указывает серверу имя узла и нестандартный порт; один IP может обслуживать несколько сайтов |
| `User-Agent: curl/8.5.0` | curl | Сообщает, какой клиент отправил запрос |
| `Accept: */*` | curl | Клиент принимает любой тип ответа |
| `Content-Type: application/json` | Передан явно через `-H` в POST | Обозначает формат отправляемого тела |
| `Content-Length` | curl при отправке `-d` | Указывает число байт тела запроса |
| `Accept-Encoding: deflate, gzip, br, zstd` | curl из-за `--compressed` | Перечисляет поддерживаемые способы сжатия |

`HTTP/1.1 201 Created`: версия HTTP/1.1, числовой код 201 и поясняющая фраза
Created. Класс `2xx` означает успех: 200 — обычный успешный ответ,
201 — объект создан, 204 — успешно, тела ответа нет.
Класс `4xx` означает ошибку запроса клиента: 400 — неверный запрос,
404 — ресурс не найден, 405 — метод для этого пути не поддерживается.

Заголовки ответов:

| Заголовок | Значение в этих обменах |
|---|---|
| `Content-Type` | У своего сервера JSON в UTF-8, у example.com HTML |
| `Content-Length` | Длина закодированного тела в байтах; у `/health` — 66 |
| `Connection: close` | После одного ответа собственный сервер закрывает TCP-соединение |
| `Location: /products/1` | Адрес созданного товара |
| `Allow: GET` | Метод, допустимый для `/health`; обязателен при ответе 405 |
| `Transfer-Encoding: chunked` | В HTTP/1.1 ответ сайта разбит на чанки; нулевой чанк завершает тело |
| `Content-Encoding: br` | Тело сайта сжато Brotli; curl распаковывает его при `--compressed` |
| `Server: cloudflare` | Сообщает о ПО/посреднике, который обработал ответ; не раскрывает весь стек сайта |
| `cf-cache-status: HIT`, `Age: 4586` | Ответ выдан из кеша Cloudflare; Age показывает его возраст в секундах |

### Сравнение с example.com

1. Локальный сервер использует обычный HTTP, а сайт — HTTPS. В выводе сайта
   есть TLS 1.3, сертификат и проверка его подписи/имени. Это нужно для
   шифрования соединения и проверки подлинности сервера.
2. Локально используется HTTP/1.1. С сайтом curl согласовал HTTP/2 через ALPN
   при TLS-рукопожатии (`server accepted h2`). Флаг `--http1.1` ограничил
   выбор в третьем обмене, и сервер принял HTTP/1.1.
3. Локально границу тела задаёт `Content-Length`. В ответе сайта по HTTP/2
   нет ни `Content-Length`, ни `Transfer-Encoding`: тело передаётся кадрами
   DATA, завершение потока обозначается END_STREAM. HTTP/2 может содержать
   Content-Length, просто в этом ответе его нет. При принудительном HTTP/1.1
   сайт использовал `Transfer-Encoding: chunked`.
4. Собственный сервер отдаёт несжатый JSON. В последнем запросе curl объявил
   поддержку сжатия, сайт выбрал Brotli (`Content-Encoding: br`). Это
   уменьшает передаваемый объём. Chunked задаёт границы передачи, а Brotli
   сжимает содержимое — это разные механизмы.
5. Свой сервер закрывает соединение после каждого ответа. Сайт сохраняет его:
   в HTTP/1.1 есть `Connection: keep-alive`, а curl пишет `left intact`.
   В HTTP/2 постоянное соединение и потоки позволяют переиспользовать одно
   соединение. После завершения процесса curl оно всё равно закрывается.
6. У своего сервера нет `Server` и кеширующих заголовков. У сайта есть
   `Server: cloudflare`, `cf-cache-status: HIT` и `Age`: запрос прошёл через
   CDN, которая может отдавать сохранённую копию страницы.
7. Для `127.0.0.1` не нужен DNS. Для example.com curl получил IPv4- и
   IPv6-адреса, а в этом запуске подключился по IPv4.
8. В HTTP/2 имена заголовков в нижнем регистре — так требует протокол.
   HTTP/1.1 допускает разный регистр; наш парсер приводит имена к нижнему
   регистру, поэтому `Content-Length` и `cOnTeNt-LeNgTh` равнозначны.

### Заголовки и раскрытие реализации

`Server` и `X-Powered-By` могут раскрыть серверное ПО, фреймворк и их версии.
По этим сведениям атакующий может сузить поиск известных уязвимостей.
Наш сервер эти необязательные заголовки не отправляет: клиенту достаточно
статуса, типа и длины ответа. Их отсутствие само по себе не устраняет
уязвимости и не гарантирует, что реализацию нельзя определить иначе.

## Проверка кода

```bash
uv run ruff check .
uv run ruff format --check .
```

Для защиты от зависшего клиента установлен таймаут сокета 5 секунд.
В первоначальной версии клиенты обрабатываются последовательно.
Версии с потоками и asyncio и замеры описаны ниже.

## Задача 5. Модели обслуживания и нагрузка

Замеры выполнены 15 сентября 2026 года на `for-labs`: Linux 6.8.0-134-generic,
4 vCPU, около 8 ГиБ RAM, CPython 3.13.15. Клиент и сервер находились
на одной машине и общались через `127.0.0.1:18081`. Перед серией нагрузка
сервера была близка к нулю. Процессы лабораторной запускались с `nice=10`.

Лимит открытых файлов был 1024, для процессов замера установлен 4096.
Системный `somaxconn` равен 4096 и не менялся. Очередь по умолчанию во всех
трёх реализациях — 128. Каждая строка ниже — отдельный запуск свежего сервера;
прогоны выполнялись последовательно, каждый по одному разу.

Клиент создаёт N задач через `asyncio.gather`, без ограничения параллелизма.
Время соединения считается от начала подключения до получения всего ответа.
В режиме `--delay` в это время входят ожидание `100 Continue` и сама пауза.
Общее время включает завершение всех задач. Медиана и p95 считаются только
по успешным соединениям; p95 — элемент с индексом `ceil(0.95 * count) - 1`
в отсортированном списке. Ошибки и их типы выводятся отдельно. Таймаут
одного обмена, включая подключение, — 30 секунд.

Исходные результаты: [lab-01-load.json](lab-01-load.json).
`ListenOverflows` считывался из `/proc/net/netstat` непосредственно до и после
каждого прогона. Это счётчик всей сетевой среды хоста, поэтому его разность
теоретически может включать события других проектов; отдельной нагрузки
на них во время замера не создавалось.

### Основной прогон: GET /health, backlog=128

| Версия | N=100: всего, с | медиана, мс | p95, мс | ошибки | ΔListenOverflows | N=1000: всего, с | медиана, мс | p95, мс | ошибки | ΔListenOverflows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Последовательный | 0.017966 | 10.977 | 11.556 | 0 | 0 | 1.486470 | 1086.691 | 1268.523 | 0 | 1756 |
| Потоки | 0.031997 | 14.945 | 24.182 | 0 | 0 | 1.561730 | 1068.785 | 1346.195 | 0 | 1238 |
| asyncio | 0.019489 | 12.327 | 12.577 | 0 | 0 | 0.182384 | 116.218 | 120.391 | 0 | 0 |

### Контроль очереди: GET /health, N=1000, backlog=4096

| Версия | Всего, с | Медиана, мс | p95, мс | Ошибки | ΔListenOverflows |
|---|---:|---:|---:|---:|---:|---:|
| Последовательный | 0.181171 | 113.663 | 120.393 | 0 | 0 |
| Потоки | 0.327869 | 162.276 | 249.689 | 0 | 0 |
| asyncio | 0.194129 | 127.179 | 129.458 | 0 | 0 |

### Медленные клиенты: POST /products, N=50, delay=0.2, backlog=128

| Версия | Всего, с | Медиана, мс | p95, мс | Ошибки | ΔListenOverflows |
|---|---:|---:|---:|---:|---:|---:|
| Последовательный | 10.104222 | 5153.619 | 9696.915 | 0 | 0 |
| Потоки | 0.216598 | 211.133 | 214.160 | 0 | 0 |
| asyncio | 0.212917 | 208.605 | 209.244 | 0 | 0 |

### Объяснение результатов

При N=1000 и backlog=128 медиана последовательной и потоковой версий
получилась около секунды. Это не секунда вычислений над JSON: очередь
ожидающих `accept` соединений переполняется. Ядро отбрасывает пакеты при
переполнении, а TCP повторяет передачу по таймеру. Зафиксировано 1756 и 1238
событий `ListenOverflows`. Это число событий, а не число уникальных клиентов:
один клиент может вызвать несколько повторов.

Ошибок в этой серии не было. Повторная передача успела завершиться до
30-секундного таймаута клиента, поэтому переполнение превратилось в задержку,
а не в окончательный отказ. С backlog=4096 переполнения исчезли:
последовательная версия обработала тысячу запросов за 0,181 с вместо 1,486 с.
У каждого запроса очень мало работы, так что последовательное выполнение
само по себе здесь не требует секунды.

Когда очередь перестала мешать, стали видны затраты на потоки: 0,328 с
против 0,181 с у последовательного сервера при N=1000. На каждое соединение
создаётся поток ОС, выделяется стек, работает планировщик. В обычном CPython
GIL не позволяет исполнять Python-код одновременно в нескольких потоках,
хотя при ожидании сетевого ввода GIL освобождается. Изменение словаря товаров
защищено коротким Lock; сетевое ожидание находится снаружи блокировки.
Накладные расходы уже заметны при N=1000 в этом прогоне. При большом числе
одновременно живущих медленных соединений добавятся ограничения памяти,
числа потоков и дескрипторов. Точный N отказа не измерялся: он зависит от
лимитов ОС и того, сколько потоков одновременно остаются активными.

В asyncio ожидание сокета приостанавливает корутину, а цикл событий
обслуживает готовые соединения в одном потоке. В этом запуске он успевал
принимать соединения достаточно быстро, и даже с backlog=128 переполнений
не было. Увеличение очереди поэтому не дало выигрыша; небольшую разницу
0,182 и 0,194 с по одному прогону нельзя считать закономерностью.
Asyncio ограничат CPU, блокирующая операция внутри обработчика, память,
число дескрипторов или пропускная способность сети. Обычные функции
разбора HTTP и маршрутизации общие для всех трёх версий.

На GET /health без переполнений все варианты укладываются в доли секунды:
почти нечего ждать, и существенны накладные расходы клиента, TCP и
планировщика. На медленных клиентах разница принципиальная: последовательный
сервер сначала отвечает одному клиенту `100 Continue`, ждёт его 0,2 с,
завершает запрос и только затем принимает следующего. Поэтому получается
примерно `50 * 0.2 = 10` секунд. Потоки и asyncio совмещают эти ожидания:
получилось 0,217 и 0,213 с, примерно в 47 раз меньше. Это демонстрирует
перекрытие ожиданий, а не ускорение самой обработки JSON.

### Воспроизведение

Из папки `lab1`, в отдельных терминалах сервера и клиента установить
`ulimit -n 4096`. Запускать версии по одной, останавливая собственный
сервер через Ctrl+C между сериями:

```bash
uv run python -m rawhttp.server --port 18081
uv run python -m rawhttp.server_threads --port 18081
uv run python -m rawhttp.server_async --port 18081
```

Для каждой версии выполнить:

```bash
uv run python scripts/load.py 100 --port 18081
uv run python scripts/load.py 1000 --port 18081
uv run python scripts/load.py 50 --port 18081 --delay 0.2
```

Затем перезапустить ту же версию с `--backlog 4096` и повторить N=1000.
Для повторения условий замера можно запускать и сервер, и клиент через
`nice -n 10 uv run ...`. Следующая команда печатает счётчик; разность значений
до и после клиента — колонка ΔListenOverflows:

```bash
python3 - <<'PY'
from pathlib import Path
lines = Path('/proc/net/netstat').read_text().splitlines()
for index, line in enumerate(lines):
    if line.startswith('TcpExt:'):
        names = line.split()
        values = lines[index + 1].split()
        print(values[names.index('ListenOverflows')])
        break
PY
```

## Границы работы

Данные существуют только до остановки процесса. Нет базы данных,
авторизации и проверки остатков. Есть три модели обслуживания,
тело запроса читается по Content-Length.
Правило конкуренции за остаток и связи сущностей описаны в README для
следующих лабораторных. В этой работе реализованы только три требуемых маршрута.

Организационные пункты сдачи — регистрация темы в LMS, приватный репозиторий
Gitea и доступ преподавателям — не подтверждены этим отчётом.

## Источники

- [Условие лабораторной](https://git.digital.mephi.ru/Backend/Project/src/branch/main/Part-1).
- [RFC 9110: 204 No Content](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.5).
- [RFC 9112: длина тела HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html#section-6.3).
- [RFC 9113: обмен HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.1).
