# UI design reference

Arayüzün görsel kaynağı burasıdır. Spec'lerin "tasarım bağı" (`docs/testing.md`, Evidence for UI
criteria) bu klasöre işaret eder.

| Dosya | Ne |
|---|---|
| `daily-planner-dashboard.html` | **Günlük Planlayıcı & Akış** ekranı — tek tasarlanmış ekran. Tarayıcıda açılarak incelenir. |

## Nasıl okunur

Tasarım, HTML + Tailwind olarak üretilmiş statik bir makettir; **uygulanacak kod değildir**.
Arayüz PySide6 (Qt Widgets + QSS) ile yazılır (`docs/architecture.md`, bootstrap kararı
2026-11-02), tasarım yalnızca görsel referanstır.

Taşınırken kaynak alınacak şey, dosyanın `<script>` içindeki `tailwind.config` bloğunda duran
**Material 3 belirteç setidir**: ~45 renk belirteci (`surface`, `primary`, `on-surface-variant`…),
tipografi ölçeği (Inter / JetBrains Mono) ve boşluk ölçeği. Bunlar tek bir QSS tema dosyasına
çevrilir; widget'lara doğrudan renk veya piksel yazılmaz (`docs/conventions.md`, UI conventions).

## Tasarımla ürün arasındaki bilinçli farklar

Tasarım, ürün kapsamıyla birebir aynı değildir. Bootstrap'ta (2026-11-02) kararlaştırılan farklar:

1. **Ürün adı.** Tasarımda "FlowCraft" yazar; ürünün adı **Notes&MJ**'dir.
2. **Senkronizasyon çıkar.** Kenar çubuğundaki "Senkronize Edildi" ve üstteki "Senkronize"
   düğmesi uygulanmaz — ürün tamamen yereldir ve ağa çıkmaz (`docs/architecture.md`, kapsam dışı).
3. **Ağ bağımlılıkları yerelleşir.** Tasarım Tailwind CDN, Google Fonts ve uzak görseller kullanır;
   uygulamada font, ikon ve tema `app/resources/` içine gömülür (`docs/architecture.md`, yasak 6).
4. **Çizilmemiş ekranlar.** Kenar menüdeki *Görev Panosu*, *Notlarım & Belgeler*, *Projeler*,
   *Etiketler & Arşiv* ve *Ayarlar* henüz tasarlanmamıştır. Bu ekranların tasarımı, kendi
   spec'leriyle birlikte gelir; o zamana kadar bu dosyadaki belirteç seti ve düzen dili esas alınır.
5. **Gömülü veriler örnektir.** Tasarımdaki tarihler, görevler ve sayılar (örn. "24 Ekim 2024",
   "%48 Odak oranı") yer tutucudur, kabul kriteri değildir.
