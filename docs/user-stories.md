# Aria Intelligence - User Stories & Requirements

---

## US-01: Mood Secimi ile Muzik Onerisi Alma

**Kullanici olarak,** ruh halimi secerek bana uygun sarki onerileri almak istiyorum, boylece nasil hissettigime gore muzik dinleyebilirim.

### Acceptance Criteria

| # | Kriter | Dogrulama |
|---|--------|-----------|
| AC-1 | Kullanici en az 8 farkli mood seceneginden birini secebilir | UI'da 8+ mood karti render ediliyor |
| AC-2 | Mood secildikten sonra en az 5, en fazla 20 sarki onerisi doner | API response'unda `tracks.length >= 5 && <= 20` |
| AC-3 | Her oneri icin sarki adi, artist, album ve album kapagi gosterilir | Response body'de `name, artist, album, cover_url` alanlari dolu |
| AC-4 | Qwen tarafindan olusturulan dogal dilde bir aciklama metni yer alir | Response'da `explanation` alani bos degil ve min 50 karakter |
| AC-5 | Sonuclar 3 saniye icinde gosterilir (UI'da loading state dahil) | Performans testi: p95 latency < 3s |

---

## US-02: Kullanici Kayit ve Giris

**Kullanici olarak,** hesap olusturup giris yapmak istiyorum, boylece onerilerim ve gecmisim kisisellestirilsin.

### Acceptance Criteria

| # | Kriter | Dogrulama |
|---|--------|-----------|
| AC-1 | Email + sifre ile kayit olunabilir | POST `/auth/register` 201 doner, DB'de user olusur |
| AC-2 | Kayit sirasinda email formati ve sifre uzunlugu (min 8 karakter) dogrulanir | Gecersiz inputlarda 400 + hata mesaji doner |
| AC-3 | Basarili giriste JWT token doner | POST `/auth/login` response'unda `access_token` alani var |
| AC-4 | Yanlis sifre ile giris denendiginde anlamli hata mesaji gosterilir | 401 + `"invalid credentials"` mesaji |
| AC-5 | Token suresi doldugunda kullanici login sayfasina yonlendirilir | Frontend expired token'da `/login`'e redirect eder |

---

## US-03: Sarkiyi Begeni / Gec ile Degerlendirme

**Kullanici olarak,** onerilen sarkilari begenebilmek veya gecebilmek istiyorum, boylece sistem gelecekte bana daha iyi oneriler sunabilsin.

### Acceptance Criteria

| # | Kriter | Dogrulama |
|---|--------|-----------|
| AC-1 | Her sarki kartinda like ve skip butonlari goruntulenir | UI'da her `TrackCard`'da iki buton render ediliyor |
| AC-2 | Like/skip aksiyonu backend'e kaydedilir | POST `/interactions` 201 doner, DB'de kayit olusur |
| AC-3 | Ayni sarki icin tekrar like yapildiginda toggle olur (unlike) | Ikinci POST'ta etkilesim silinir veya guncellenir |
| AC-4 | Etkilesim kaydedildikten sonra UI'da gorsel geri bildirim verilir | Like buton rengi degisir, toast/animasyon gosterilir |
| AC-5 | Etkilesim verileri collaborative filtering modeline girdi olur | CF training pipeline etkilesim tablosunu okuyor |

---

## US-04: Oneri Gecmisini Goruntuleme

**Kullanici olarak,** daha once aldigi onerileri ve begendigi sarkilari gorebilmek istiyorum, boylece hosuma giden sarkilara tekrar ulasabileyim.

### Acceptance Criteria

| # | Kriter | Dogrulama |
|---|--------|-----------|
| AC-1 | Gecmis sayfasinda son 30 gune ait oneriler listelenir | GET `/history` son 30 gun verisi doner |
| AC-2 | Her gecmis kaydinda tarih, mood ve onerilen sarkilar goruntulenir | Response'da `date, mood, tracks` alanlari mevcut |
| AC-3 | Begendigi sarkilar ayri bir "Favoriler" sekmesinde listelenir | GET `/favorites` sadece like'lanan sarkilari doner |
| AC-4 | Liste sayfalama (pagination) destekler | `?page=1&limit=20` parametreleri calisir |
| AC-5 | Bos gecmis durumunda anlamli bir bos state gosterilir | 0 kayitta UI'da "Henuz oneri almadiniz" mesaji |

---

## US-05: Collaborative Filtering ile Kisisellestirilmis Oneri

**Kullanici olarak,** benzer muzik zevkine sahip diger kullanicilarin dinlediklerinden faydalanan oneriler almak istiyorum, boylece kesfetmedigim sarkilari bulabileyim.

### Acceptance Criteria

| # | Kriter | Dogrulama |
|---|--------|-----------|
| AC-1 | En az 5 etkilesimi olan kullanicilara CF tabanli oneriler sunulur | 5+ etkilesimli user'da response `source: "hybrid"` icerir |
| AC-2 | 5'ten az etkilesimi olan kullanicilara sadece content-based oneri sunulur | <5 etkilesimli user'da response `source: "content-based"` icerir |
| AC-3 | Hibrit skor, CF ve content-based skorlarin agirlikli ortalamasi olarak hesaplanir | Skor hesabi: `final = w1*cf_score + w2*cb_score`, w1+w2=1 |
| AC-4 | CF modeli en az haftada 1 kez yeniden egitilir | Batch job haftalik schedule'da calisir |
| AC-5 | Begendigi sarkilar tekrar onerilmez | Liked track ID'leri oneri listesinden filtrelenir |

---

## US-06: Sarki Onizleme ve Spotify Yonlendirme

**Kullanici olarak,** onerilen sarkilarin kisa bir onizlemesini dinlemek ve begendigim sarkiyi Spotify'da acabilmek istiyorum.

### Acceptance Criteria

| # | Kriter | Dogrulama |
|---|--------|-----------|
| AC-1 | Sarki kartinda 30 saniyelik preview play/pause butonu vardir | Preview URL'i olan sarkilarda audio player renderlanir |
| AC-2 | Preview URL'i olmayan sarkilarda buton disabled gosterilir | `preview_url: null` olan kartlarda buton disabled |
| AC-3 | "Spotify'da Ac" butonu sarki sayfasina yonlendirir | Buton `external_urls.spotify` linkini yeni sekmede acar |
| AC-4 | Ayni anda sadece 1 sarki onizlemesi oynatilabilir | Baska sarkiya basildiginda onceki durur |
| AC-5 | Onizleme mobilde de sorunsuz calisir | iOS Safari ve Android Chrome'da audio oynatilir |

---

## Dependency Diagram

Asagidaki diagram, user story'ler arasindaki bagimliliklari gosterir. Bir story'nin baslamasi icin bagimli oldugu story'lerin tamamlanmis olmasi gerekir.

```
                    +------------------+
                    |     US-02        |
                    | Kayit ve Giris   |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
     +--------+------+ +----+----------+ +-+---------------+
     |    US-01       | |    US-03      | |     US-04       |
     | Mood ile Oneri | | Like / Skip   | | Oneri Gecmisi   |
     +--------+-------+ +----+---------+ +-----------------+
              |              |
              |              v
              |    +---------+---------+
              |    |      US-05        |
              |    | Collab. Filtering |
              |    +---------+---------+
              |              |
              +---------+----+
                        |
                        v
              +---------+---------+
              |      US-06        |
              | Onizleme/Spotify  |
              +-------------------+
```

### Bagimlilk Tablosu

| Story | Bagimli Oldugu Story'ler | Aciklama |
|-------|--------------------------|----------|
| US-01 | US-02 | Oneri almak icin kullanicinin giris yapmis olmasi gerekir |
| US-02 | — | Bagimsiz, ilk yapilmasi gereken story |
| US-03 | US-01, US-02 | Oneri alindiktan sonra like/skip yapilabilir |
| US-04 | US-02 | Gecmisi gorebilmek icin giris gerekir |
| US-05 | US-03 | CF icin yeterli etkilesim verisi (like/skip) gerekir |
| US-06 | US-01 | Onizleme icin once oneri sonuclarinin gosterilmesi gerekir |

### Kritik Yol (Critical Path)

```
US-02 -> US-01 -> US-03 -> US-05
```

Bu zincir projenin en uzun bagimlilik yoludur. Bu yoldaki herhangi bir gecikme, sprint bitisini dogrudan etkiler. Oncelik bu sirayla verilmelidir.

### Sprint-Story Eslemesi

| Story | Sprint Haftasi | Track |
|-------|---------------|-------|
| US-02 | Hafta 1 | Backend + Frontend |
| US-01 | Hafta 1-2 | AI/ML + Frontend |
| US-03 | Hafta 2-3 | Backend + Frontend |
| US-04 | Hafta 3 | Backend + Frontend |
| US-05 | Hafta 2-3 | AI/ML + Backend |
| US-06 | Hafta 3-4 | Frontend |

---

## Non-Functional Requirements (NFR)

### NFR-01: Guvenlik

| # | Gereksinim | Olcum |
|---|-----------|-------|
| NFR-1.1 | Tum API endpointleri (auth haric) JWT ile korunur | Auth middleware olmadan 401 doner |
| NFR-1.2 | Sifreler bcrypt (cost >= 12) ile hashlenir, plaintext saklanmaz | DB'de sifre alani `$2b$` prefix ile baslar |
| NFR-1.3 | JWT token suresi maksimum 24 saat olur | Token decode edildiginde `exp - iat <= 86400` |
| NFR-1.4 | SQL injection ve XSS'e karsi input sanitizasyonu yapilir | OWASP ZAP taramasi critical/high bulgu uretmez |
| NFR-1.5 | API rate limiting uygulanir (IP basina dakikada max 60 istek) | 61. istekte 429 Too Many Requests doner |
| NFR-1.6 | CORS policy sadece izin verilen originlere aciktir | Farkli origin'den istek 403 doner |

### NFR-02: Performans

| # | Gereksinim | Olcum |
|---|-----------|-------|
| NFR-2.1 | Mood -> oneri akisi p95 latency < 3 saniye | Load test (k6/locust): p95 < 3000ms |
| NFR-2.2 | API ayni anda en az 50 concurrent kullaniciyi destekler | 50 concurrent user'da error rate < %1 |
| NFR-2.3 | Vector similarity search < 200ms (Qdrant) | Qdrant query log: avg < 200ms |
| NFR-2.4 | Sik sorgulanan mood'lar icin cache hit orani > %70 | Redis monitoring: hit ratio > 0.7 |
| NFR-2.5 | Frontend ilk sayfa yuklemesi (LCP) < 2 saniye | Lighthouse LCP < 2000ms |

### NFR-03: Erisilebilirlik ve Sureklilik

| # | Gereksinim | Olcum |
|---|-----------|-------|
| NFR-3.1 | Tum servisler Docker Compose ile tek komutla ayaga kalkar | `docker compose up` ile tum servisler healthy olur |
| NFR-3.2 | Health check endpointleri mevcut (/health, /ready) | GET `/health` 200 doner, dependency check yapar |
| NFR-3.3 | Structured JSON loglama tum servislerde aktif | Log ciktisi JSON formatinda, `timestamp, level, message` alanlari var |
| NFR-3.4 | Veritabani migration'lari versiyonlu ve geri alinabilir | `migrate up` ve `migrate down` basarili calisir |
| NFR-3.5 | CI pipeline her PR'da lint + unit test calistirir | GitHub Actions: PR'da pipeline basarili tamamlanir |
