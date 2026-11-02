# Spec 0002 — desktop shell (mini)

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0002-plan.md`
- Source: CR-2026-11-02-desktop-shell — bootstrap yeniden konumlandırma kararı (2026-11-02)
- Design: `docs/design/daily-planner-dashboard.html` (bu değişiklikle repoya giren 2026-11-02
  tarihli dışa aktarım; bu spec yalnızca kenar menü ve belirteç setini kullanır, tasarlanmış
  "Günlük Planlayıcı" ekranı kendi spec'ine aittir). Okuma kılavuzu: `docs/design/README.md`.
- Supersedes: 0001/AC-1, 0001/AC-2, 0001/AC-4, 0001/AC-5, 0001/AC-6, 0001/AC-9 (tamamen) ve
  0001/AC-12'nin tarayıcı ayağı. 0001/AC-3, AC-7, AC-8, AC-10, AC-11 ve AC-12'nin kaynak hijyeni
  ayağı korunur — aşağıdaki PB-* maddeleri. `specs/done/0001-app-skeleton.md` düzenlenmez.

## Intent
Ürün, izin yönetimi web uygulamasından tek kişilik yerel bir masaüstü çalışma alanına taşındı
(bootstrap, 2026-11-02). Bu değişiklik 0001'in HTTP iskeletini kaldırır ve yerine aynı işi gören
bir **masaüstü kabuğu** koyar: açılan bir pencere, kalıcı yerel veri ve sürümlenen bir şema.
Hiçbir ürün özelliği (görev, odak, not) bu spec'te yoktur — her biri kendi spec'iyle gelir. Şimdi
gerekiyor çünkü dokümanlar hedefi, kod hâlâ eski ürünü anlatıyor; bu fark kapanmadan ilk özellik
yazılamaz.

## Changed behavior
- [ ] CB-1 — Belgelenen tek komut çalıştırıldığında bir **masaüstü penceresi** açılır; pencere
  başlığı birebir `Notes&MJ`'dir. Ürün adının göründüğü her arayüz öğesinde `&` karakteri de
  görünür (kısayol işareti olarak yorumlanıp yutulmaz). Uygulama hiçbir ağ portu dinlemez ve
  tarayıcı gerektirmez.
- [ ] CB-2 — Pencere, kenar menüsünde tam olarak şu bölümleri gösterir: **Görev Panosu ·
  Notlarım & Belgeler · Günlük Planlayıcı · Projeler · Etiketler & Arşiv**. Senkronizasyon öğeleri,
  Ayarlar ve "Son Projeler" bulunmaz. Henüz yapılmamış her bölüm seçildiğinde **tek ortak bir boş
  durum şablonu** görünür; şablonda yalnızca bölüm adı değişkendir ve hizmetin hazır olmadığı
  Türkçe bildirilir. Uygulama hata vermez.
- [ ] CB-3 — İlk çalıştırmada kullanıcının yerel uygulama verisi dizininde (`docs/security.md`,
  Veri ve gizlilik) bir veri dosyası oluşturulur; sonraki çalıştırmalar aynı dosyayı yeniden
  kullanır, üzerine yazmaz.
- [ ] CB-4 — Veri dosyası bir şema sürümü taşır. Önceki sürüm numarasını taşıyan **sentetik olarak
  üretilmiş** bir dosya açıldığında şema ileri taşınır ve içindeki veri korunur — bu spec şemanın
  ilk sürümünü yarattığı için geçiş, gerçek bir eski dosyayla değil bu üretilmiş dosyayla
  kanıtlanır. Geçişi iki kez uygulamak veriyi bozmaz.
- [ ] CB-5 — Geçişten önce veri dosyasının bir yedeği, aynı dizine, kaynak şema sürümünü ve tarihi
  içeren bir adla alınır. (Yedeklerin temizlenmesi kapsam dışıdır.)
- [ ] CB-6 — Veri dosyası açılamadığında (bozuk dosya, yazma izni yok) uygulama sessizce boş
  başlamaz: ne olduğunu Türkçe anlatan açık bir hata ekranı gösterir.
- [ ] CB-7 — Beklenmeyen bir hata, genel bir Türkçe mesaj ve bir korelasyon kimliği taşıyan bir
  diyalogla gösterilir; bu kimlik, aynı hatanın PB-5'teki log kaydındaki kimliğin **aynısıdır**.
  Diyalogda istisna mesajı, yığın izi veya dosya yolu bulunmaz.
- [ ] CB-8 — Pencere kapatıldığında süreç temiz biter: arkada açık pencere, zamanlayıcı veya
  çalışan süreç kalmaz. (Bu, uygulamanın kendisiyle ilgilidir; test süreçlerinin hijyeni PB-3.)

## Preserved behavior
- [ ] PB-1 — `./scripts/check --fast` `ui` işaretli testleri çalıştırmaz, geri kalanını çalıştırır;
  `./scripts/check` tümünü çalıştırır; iki profilin test sayılarının toplamı tüm testlerin
  sayısına eşittir. (0001/AC-11)
- [ ] PB-2 — Bir modülün başka bir modülün iç paketini import etmesi, domain katmanının
  **`docs/architecture.md`'deki güncel yasak kümesinden** bir kütüphane import etmesi veya
  `app.shared`'in bir modülü import etmesi `./scripts/check`'i kırmızı yapar (her kural için
  tekrarlanabilir gözlem). Yasak küme bu değişiklikle yeni yığına göre güncellenir. (0001/AC-10)
- [ ] PB-3 — `./scripts/residue` ve `./scripts/residue --fast`, check'e ait hayatta kalan süreç
  raporlamaz; testler başarısız olduğunda veya zaman aşımına uğradığında da arkada süreç kalmaz.
  (0001/AC-12, kaynak hijyeni ayağı)
- [ ] PB-4 — Uygulama çalışırken kendi dışına hiçbir istek göndermez. (0001/AC-3, güçlenerek)
- [ ] PB-5 — Beklenmeyen hata, hata ayrıntısıyla birlikte bir korelasyon kimliği altında loga
  yazılır; iki ayrı hata iki farklı kimlik üretir. Logda yığın izi dışında dosya yolu, kullanıcı
  içeriği veya kişisel veri bulunmaz. (0001/AC-7, 0001/AC-8)

## User experience
**Akış:** kullanıcı uygulamayı başlatır → pencere açılır → kenar menüden bir bölüm seçer → bölüm
henüz yapılmadığı için boş durum metnini görür → pencereyi kapatır.

**Durumlar** (her biri bir kritere bağlı):

| Durum | Ne görünür | Kriter |
|---|---|---|
| İlk açılış | Pencere açılır, veri dosyası oluşur | CB-1, CB-3 |
| Sonraki açılışlar | Aynı veri dosyası kullanılır | CB-3 |
| Şema geçişi | Dosya ileri taşınır, önce yedek alınır | CB-4, CB-5 |
| Boş durum | Ortak şablon + bölüm adı | CB-2 |
| Hata — veri açılamıyor | Açık Türkçe hata ekranı | CB-6 |
| Hata — beklenmeyen | Türkçe diyalog + korelasyon kimliği | CB-7 |
| Kapanış | Süreç temiz biter | CB-8 |

**Tasarım bağı:** yukarıdaki `Design:` alanı. Bu spec tasarımdan yalnızca **kenar menü bölümlerini**
ve **renk/tipografi/boşluk belirteç setini** alır; tasarlanmış dashboard ekranı kapsam dışıdır.
Tasarım sonradan değişirse bu bir spec değişikliğidir (R-08).

**Erişilebilirlik:** kullanılan her metin/yüzey **belirteç çifti** için kontrast oranı ≥ 4.5:1.
Tema belirteçleri sabit olduğundan bu, ekran görüntüsüyle değil, çiftleri hesaplayan bir **birim
testiyle** kanıtlanır — ucuz, tekrarlanabilir ve tema değiştiğinde kendiliğinden yakalar.
(0001/AC-2'nin korunan ayağı.) Ayrıca kenar menüsünde klavyeyle (Tab/ok tuşları) gezinilebilir ve
odaklanan öğe görsel olarak bellidir.

## Out of scope
- Ürün özellikleri: görev, gün planı, zaman blokları, Eisenhower, odak modu/Pomodoro, notlar,
  projeler, etiketler, arşiv/çöp kutusu — her biri kendi spec'inde.
- Tasarımdaki "Günlük Planlayıcı & Akış" ekranının uygulanması.
- Paketleme ve kurulum (PyInstaller, `.exe`, kısayol, otomatik başlatma).
- Ayarlar ekranı, hızlı arama (⌘K), tepsi ikonu, sistem bildirimleri, klavye kısayolları.
- İçe/dışa aktarma, yedekleme arayüzü ve **yedeklerin temizlenmesi/sınırlanması** (şema geçişinin
  CB-5'te aldığı otomatik yedek hariç).
- Senkronizasyon ve çoklu cihaz (kalıcı olarak kapsam dışı — `docs/architecture.md`).
- Windows dışı platformlarda test ve paketleme.

## Definition of Done
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale
- [ ] Criterion ↔ evidence table complete for CB-* **and** PB-* (UI: before/after screenshots)
- [ ] Spec moved to `specs/done/` (immutable there)
