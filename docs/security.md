# Security

Her plan ve review'ın uyması gereken temel kurallar. Bu uygulamanın tehdit modeli alışılmışın
dışındadır: sunucu, hesap ve ağ yoktur — saldırı yüzeyi makinenin kendisi ve uygulamaya verilen
dosyalardır.

## Veri ve gizlilik
- Tüm veri yalnızca yerel makinede, tek bir SQLite dosyasında: `%LOCALAPPDATA%\Notes-MJ\`.
  **Şifreleme yoktur**; koruma işletim sisteminin kullanıcı dosya izinleridir (bootstrap kararı,
  2026-11-02). Dizüstü hırsızlığı gibi senaryolar için disk şifrelemesi (BitLocker) işletim
  sistemi katmanının sorumluluğudur. Bu kararın değişmesi ADR ister.
- **Uygulama ağa çıkmaz.** Telemetri, kullanım istatistiği, kilitlenme raporu, güncelleme kontrolü
  ve bulut yedekleme yoktur. Bu bir özelliktir, eksiklik değil (`docs/architecture.md`, yasak 5–6).
- Kullanıcı içeriği (not metni, görev başlığı, proje adı) loglara **yazılmaz**; loglarda yalnızca
  ID, olay adı ve korelasyon ID'si bulunur. **Tek istisna yığın izidir:** beklenmeyen bir hatanın
  yığın izi, içindeki istisna metniyle birlikte loga yazılır — onsuz tek kişilik ve ağsız bir
  uygulamada hata teşhis edilemez (spec 0002/PB-5; review 0002/F-6, 2026-11-03). İstisna metnine
  kullanıcı içeriği konulmaz; log dosyası veri dosyasıyla aynı dizinde, aynı kullanıcı izinleriyle
  durur ve makineden çıkmaz.
- Yedekleme kullanıcının sorumluluğundadır; uygulama yalnızca şema geçişinden önce veritabanı
  dosyasının bir kopyasını alır (`docs/conventions.md`, Data rules).

## Secrets
- Repoda secret yoktur ve olmayacaktır: uygulama hiçbir servise bağlanmaz, API anahtarı taşımaz.
  Bir plan secret ihtiyacı doğuruyorsa, önce ağ yasağının neden delindiği tartışılır.
- Ajanlar secret değerlerini yazdırmaz, hata ayıklarken bile.

## Input & output
- Veritabanı erişimi yalnızca **parametreli `sqlite3` sorgularıyla**; string birleştirmeyle SQL
  kurmak yasaktır.
- Kullanıcıdan gelen ad veya yol dosya yoluna doğrudan birleştirilmez; uygulama kendi veri dizini
  dışına yazmaz (path traversal).
- İçe aktarma (ileride): dosyadan okunan içerik **veri** olarak işlenir — hiçbir koşulda
  çalıştırılmaz, formül olarak değerlendirilmez veya HTML/zengin metin olarak yorumlanmaz.
- Qt tarafında kullanıcı içeriği zengin metin olarak basılmaz: `setText` ile düz metin kullanılır,
  `setHtml` kullanıcı içeriği için yasaktır (etiket enjeksiyonu).
- Hata mesajları stack trace, SQL, dosya yolu ve kullanıcı içeriği göstermez
  (`docs/conventions.md`, Error handling).

## AuthN / AuthZ
Yoktur ve **bilinçli olarak kapsam dışıdır**: uygulama tek kullanıcılıdır ve işletim sistemi
oturumunun arkasındadır. Rol, oturum, parola ve yetki kontrolü kavramları bu üründe mevcut değildir.
Çok kullanıcılı veya paylaşımlı bir özellik gündeme gelirse, kod yazılmadan önce ADR yazılır.

## Dependencies
- Yeni paket yalnızca **onaylanmış bir planın içinde**, gerekçesiyle eklenir; insan onaylar.
- Lisans: MIT, BSD, Apache-2.0, PSF veya eşdeğer izin verici. GPL/AGPL yok.
  - **İstisna — LGPL (PySide6).** PySide6 LGPLv3'tür ve arayüz kütüphanesi olarak kullanılır
    (bootstrap kararı, 2026-11-02). Koşullar: kütüphane **dinamik bağlanır**, kaynağı
    değiştirilmez, dağıtımda statik bağlama yapılmaz ve lisans metni ürünle birlikte verilir.
    Yeni bir LGPL bağımlılığı ayrı bir karar gerektirir.
- Son 12 ayda bakım görmüş olmalı; sürümler `uv.lock` ile kilitli.
- Güvenlik açığı taraması (`pip-audit`) CI'da ayrı bir job'da çalışır, `scripts/check` içinde değil
  (ağ gerektirir; check deterministik ve çevrimdışı kalır).

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase. Bu üründe review'ın özellikle baktığı yer: ağ yasağının delinmesi,
kullanıcı içeriğinin loga veya hata mesajına sızması, ve parametresiz SQL.
