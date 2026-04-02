# Aria Intelligence - 4 Haftalik Sprint Haritasi

**Baslangic:** 2026-04-02 (Hafta 1)
**Bitis:** 2026-04-30 (Hafta 4)
**Ekip Yapisi:** 3 paralel track — AI/ML (Python), Backend (Go), Frontend (React)

---

## Tamamlanan Isler (Sprint Oncesi)

| Track | Tamamlanan |
|-------|-----------|
| AI/ML | Spotify client, bge-m3 embedding, Qdrant store, batch pipeline CLI, FastAPI (recommend/search/moods) |
| Backend | — |
| Frontend | — |

---

## Hafta 1 — 02-08 Nisan

### AI/ML (Python)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Qwen model entegrasyonu (local inference, vLLM/llama.cpp) | Yuksek | 2 |
| RAG prompt template tasarimi (mood + tracks -> dogal dil oneri) | Yuksek | 1 |
| `/recommend` endpointini RAG ciktisiyla guncelleme | Yuksek | 1 |
| Unit testler (embedder, vector store, RAG chain) | Orta | 1 |

**Cikti:** `/recommend` Qwen uzerinden kisisellestirilmis oneri donecek.

### Backend (Go)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Go proje bootstrapping (Gin/Echo, proje yapisi) | Yuksek | 1 |
| PostgreSQL + migration setup (golang-migrate) | Yuksek | 1 |
| Kullanici modeli (users tablosu, CRUD) | Yuksek | 1 |
| Auth sistemi (JWT issuing + middleware) | Yuksek | 2 |

**Cikti:** Register/login calisan, JWT token donebilen bir Go API.

### Frontend (React)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| React proje bootstrapping (Vite + TypeScript) | Yuksek | 1 |
| Proje yapisi (components, pages, hooks, services) | Yuksek | 0.5 |
| UI kit / design system secimi (Tailwind + shadcn/ui) | Orta | 0.5 |
| Login / Register sayfalari (form + validasyon) | Yuksek | 2 |
| Auth context + token yonetimi (axios interceptor) | Yuksek | 1 |

**Cikti:** Login/register calisan, token saklayan bir frontend iskeleti.

---

## Hafta 2 — 09-15 Nisan

### AI/ML (Python)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Kullanici-sarki etkilesim veri modeli (like, skip, listen suresi) | Yuksek | 1 |
| Collaborative filtering modulu (user-item matrix, ALS/SVD) | Yuksek | 2 |
| Hibrit skorlama: CF skor + vector similarity birlestirme | Yuksek | 1 |
| Sentetik etkilesim verisi olusturma (test icin) | Orta | 0.5 |
| CF cold-start fallback mantigi | Orta | 0.5 |

**Cikti:** Hibrit oneri sistemi (content-based + collaborative filtering). Cold-start'ta sadece content-based.

### Backend (Go)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Go -> Python ML service HTTP client | Yuksek | 1 |
| `/api/recommend` proxy endpointi | Yuksek | 1 |
| Kullanici etkilesim endpointleri (POST like/skip/listen) | Yuksek | 1 |
| Kullanici gecmisi endpointi (GET /history) | Orta | 1 |
| Request validation + error handling middleware | Orta | 1 |

**Cikti:** Go backend, ML servisini cagiriyor; kullanici etkilesimleri DB'ye kaydediliyor.

### Frontend (React)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Ana sayfa / mood secim ekrani | Yuksek | 2 |
| Mood kartlari UI (emoji/icon + renk paleti) | Yuksek | 1 |
| Oneri sonuc sayfasi (sarki listesi + Qwen aciklamasi) | Yuksek | 1.5 |
| Sarki karti komponenti (album art, isim, artist, like butonu) | Orta | 0.5 |

**Cikti:** Kullanici mood seciyor -> oneriler listeleniyor.

---

## Hafta 3 — 16-22 Nisan

### AI/ML (Python)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| CF model offline training pipeline (batch job) | Yuksek | 1.5 |
| Model performans degerlendirmesi (precision@k, recall@k, NDCG) | Yuksek | 1.5 |
| Embedding cache layer (tekrar embed etmeyi onleme) | Orta | 1 |
| Spotify katalog genisletme (daha fazla genre/playlist) | Dusuk | 1 |

**Cikti:** CF modeli offline egitiliyor, metrikler raporlaniyor.

### Backend (Go)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Kullanici profil endpointleri (GET/PUT /profile) | Yuksek | 1 |
| Favori sarkilar endpointi (GET /favorites) | Orta | 1 |
| Rate limiting middleware | Orta | 1 |
| API dokumantasyonu (Swagger/OpenAPI) | Orta | 1 |
| Loglama ve hata izleme (structured logging) | Orta | 1 |

**Cikti:** Tam API dokumantasyonu, rate limiting, profil yonetimi.

### Frontend (React)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Sarki detay / onizleme (Spotify embed veya 30s preview) | Yuksek | 1.5 |
| Like/skip etkilesim butonlari + API baglantisi | Yuksek | 1 |
| Kullanici profil sayfasi | Orta | 1 |
| Gecmis oneriler sayfasi (/history) | Orta | 1 |
| Responsive tasarim (mobile uyumluluk) | Orta | 0.5 |

**Cikti:** Etkilesim butonlari calisiyor, profil ve gecmis sayfalari hazir.

---

## Hafta 4 — 23-29 Nisan

### AI/ML (Python)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| End-to-end test senaryolari (mood -> oneri -> feedback dongusu) | Yuksek | 1 |
| Caching katmani (Redis - sik sorgulanan mood'lar) | Orta | 1 |
| RAG prompt iyilestirme (cikti kalitesi tuneleme) | Orta | 1.5 |
| Performans optimizasyonu (inference latency) | Orta | 1 |
| Dokumantasyon (model kartlari, API spec) | Dusuk | 0.5 |

**Cikti:** Optimize edilmis, test edilmis ML pipeline.

### Backend (Go)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Integration testler (Go <-> Python service) | Yuksek | 1.5 |
| Redis cache entegrasyonu | Orta | 1 |
| Health check + readiness endpointleri | Orta | 0.5 |
| Docker Compose (tum servisler: Go, Python, Qdrant, Postgres, Redis) | Yuksek | 1.5 |
| CI pipeline (GitHub Actions: lint + test) | Dusuk | 0.5 |

**Cikti:** Tek komutla ayaga kalkan, test edilen sistem.

### Frontend (React)

| Gorev | Oncelik | Gun |
|-------|---------|-----|
| Loading / error state'leri (skeleton, toast) | Yuksek | 1 |
| End-to-end flow testi (login -> mood -> oneri -> like) | Yuksek | 1 |
| Animasyonlar ve mikro-etkilesimler (Framer Motion) | Dusuk | 1 |
| PWA / favicon / meta tag'ler | Dusuk | 0.5 |
| Son bug fix'ler ve polish | Orta | 1.5 |

**Cikti:** Demo'ya hazir, cilali bir frontend.

---

## Sprint Sonu Hedefi (30 Nisan)

Calisan uctan uca demo:
1. Kullanici login olur
2. Mood secer (ornek: "huzunlu", "enerjik")
3. Sistem hibrit oneri uretir (content-based + collaborative filtering)
4. Qwen dogal dilde aciklama yazar ("Bu sarkilari sectim cunku...")
5. Kullanici like/skip yapar -> gelecek onerileri iyilesir

---

## Riskler ve Notlar

| Risk | Etki | Onlem |
|------|------|-------|
| Qwen local inference GPU gereksinimleri | Yuksek | Quantized model (GGUF/Q4) veya API fallback |
| CF cold-start (yeterli kullanici verisi yok) | Orta | Sentetik veri + sadece content-based fallback |
| Go <-> Python service iletisim latency | Orta | gRPC'ye gecis opsiyonu, connection pooling |
| Frontend scope creep | Dusuk | MVP odakli, ekstra feature'lar backlog'a |
| Spotify API rate limit | Dusuk | Batch fetching + local cache |
