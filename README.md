# C++ Adventure

Windows 11 için çevrimdışı kullanılabilen, Türkçe/Rusça C++ öğrenme macerası. Masaüstü sürümü WebView2 penceresinde açılır; tarayıcı sekmesi gerekmez. G++ derleyicisi gerçek C++ kodunu çalıştırır.

## Hızlı başlatma

Önceden paketlenmiş uygulama `dist-stage29-cat-growth-stage3/CppAdventure/CppAdventure.exe` dosyasıdır; `start.bat` onu açar. Bu paket 2026-11-19 güvenlik ve müfredat güncellemelerinden ÖNCEKİ kodu içerir. Yeni kodu hemen denemek için proje klasöründe `.venv\bin\python.exe desktop.py` çalıştırın veya aşağıdaki gibi yeniden paketleyin. Eski sürüm klasörleri silinmiştir.

Kaynak koddan yeniden paketlemek için:

1. Windows 11, Python 3.10+, G++ (MSYS2 UCRT64 önerilir) ve WebView2 Runtime gerektiğini doğrulayın.
2. `build-windows.bat` dosyasını çalıştırın. İlk paketlemede `pywebview` ve `PyInstaller` proje içindeki `.venv` ortamına kurulur; bunun için internet gerekir.
3. Uygulama `dist/CppAdventure/CppAdventure.exe`, kullanıcı hesabına kurulum dosyası `dist/C++Adventure-Setup.exe` konumuna çıkar.

Normal uygulama kullanımı için Python, Node.js, npm veya internet bağlantısı gerekmez. G++ kod derleme için gereklidir. WebView2 Runtime Windows 11 bilgisayarında bulunmalıdır.

## En son görsel güncelleme

Kedi dükkânında yerel SVG katmanlarıyla baş, kulak, boyun, gövde, sırt ve oyuncak yuvalarına uygun aksesuar önizlemesi bulunur. Her yuvada bir aksesuar birlikte denenebilir; önizleme XP harcamaz. Sahip olunan eşyalar profilde giydirilebilir/çıkarılabilir ve kombinler kaydedilip yeniden uygulanabilir. Yeni arayüz Türkçe ve Rusça’dır. Ayrıntılar ve doğrulama sonuçları için [DEVAM.md](DEVAM.md) içindeki Ultimate Visual Learning & Cat Companion 2.0 Aşama 2 kaydına bakın.

## Bilgisayarda doğrulananlar

- Windows 11 (10.0.26300), Python 3.14.7, G++ 16.2.0 ve VS Code bulundu.
- 16 işlemci iş parçacığı ve 15.2 GB RAM görüldü; ayrı GPU gerekmez.
- WebView2 Runtime bulundu. WebView2 masaüstü penceresi uygulamayla birlikte başlatıldı.
- `dist/C++Adventure-Setup.exe` oluşturuldu ve geçici bir test konumuna kuruldu. Uygulama dosyası ile Başlat menüsü ve masaüstü kısayolları doğrulandı.

## Kullanım

- İlk açılışta profil oluşturun. İsteğe bağlı 4–8 rakamlı PIN tanımlayabilirsiniz.
- Açılış ekranı en az 3,5 saniye görünür. Yüzde yerel servis, SQLite, profiller ve seçili profil ilerlemesi gerçekten hazır oldukça güncellenir; erken hazır olursa gerçek %100 değerinde kısa süre bekler. Ekranda sürüm ve `Created by Ogulcanenes` bilgisi görünür.
- PIN korumalı profil seçimi veya silme, uygulama içindeki animasyonlu kedi PIN penceresini kullanır. PIN başlangıçta gizlidir; göz düğmesiyle gösterilebilir. Yanlış ve doğru denemelerde kedi farklı tepki verir. Enter ile gönderilir, Escape ile iptal edilir.
- Profil başına dil, avatar, XP, seviye, görevler, quiz denemeleri ve başarımlar bağımsız SQLite kaydı tutar.
- Bölüm seçince görevlerden önce konu anlatımı gösterilir. Quiz ve çıktı tahmini alanları boş başlar; doğru cevap hazır yazılı gelmez.
- Bilgi haritası konuların ön koşullarını gösterir. Ön koşul Boss görevleri bitmeden bölüm açılamaz; kilit denetimi hem ekranda hem görev gönderme servisinde uygulanır.
- Görev akışı mini quiz, çıktı tahmini, hata düzeltme, kodlama ve bölüm sonu Boss Challenge içerir. Kod görevleri gerçek G++ derlemesiyle değerlendirilir.
- Hata düzeltme, kodlama ve Boss görevlerinde önce bütün G++ test girdileri çalışır, ardından görevin C++ kavramı ayrı doğrulanır. Yalnızca ikisi de geçerse görev tamamlanır ve XP kazanılır. Clang kuruluysa `main` fonksiyonunun AST'siyle yapısal denetim yapılır; yalnızca G++ bulunan kurulumlarda yorum ve metin sabitlerini ayıklayan yapısal geri dönüş kullanılır.
- Her bölümün 4. kodlama görevi ile Boss Challenge'ı farklı senaryo, başlangıç kodu ve test girdilerine sahiptir. Boss'lar ayrıca daha kapsamlı, birden fazla girdiye dayalı görevlerdir.
- Kod editöründe öneriler C++ için hazırlanmış snippet’lerden gelir; sıradan kelime tamamlamaları kapalıdır. `Tab` ile seçili öneriyi ekleyin. `Ctrl+S` kayıt/yedekleme ekranını açar.
- Uygulama içindeki Çalıştır panelinde girdi alanını açıp program başlamadan önce bir veya birden fazla satır girebilirsiniz. Derleme durumu, stdout, program stderr’i, derleyici mesajları, çıkış kodu ve geçen süre ayrı gösterilir; derleme/çalıştırma için CMD penceresi açılmaz.
- Hata alınca test adı, beklenen ve alınan çıktı ile yerel derleyici açıklaması gösterilir. Ayarlardan çevrimdışı, Ollama, OpenAI veya AI kapalı seçilebilir.
- OpenAI’ye kod göndermek için her tanılama isteğinde ayrıca onay gerekir. API anahtarı `OPENAI_API_KEY` ortam değişkeninden okunur, veritabanına veya kaynak koda yazılmaz. Kodun yanı sıra görev metni ve sınırlı quiz geçmişi de onay ekranında açıklanır.
- Ollama yerel adreste aranır (`127.0.0.1:11434`). Kurulu model yoksa ayarlar ekranı çevrimdışı tanılamaya devam eder.
- Kayıt menüsü JSON dışa/içe aktarma ve manuel yedeklemeyi içerir. Veriler otomatik olarak kaydedilir.
- Öğrenme günlüğü her doğru/yanlış görev denemesini profil bazında kaydeder; konu başarısını, tekrar önerilerini ve son denemeleri gösterir. Günlük kayıtları JSON yedeklerine de dahil edilir.
- Kod laboratuvarında kaynak kod için yerel okunabilirlik sezgiselleri bulunur. Code Golf karşılaştırması iki çözümü aynı girdiyle gerçek G++ üzerinden derleyip çıktıları, kod boyutlarını ve yaklaşık derleme+çalışma sürelerini yan yana gösterir. Süre ölçümü algoritmik karmaşıklık analizi değildir.
- Görsel laboratuvarlar değişken, koşul, döngü, fonksiyon, dizi, pointer, güvenli bellek, OOP ve algoritmaları adım adım simüle eder; bubble/selection/insertion sort, linear/binary search ve factorial recursion adımlarını gösterir. Memory Playground stack, queue, linked list ve dinamik bellek yaşam döngüsünü güvenli sembolik simülasyonla gösterir. Oynat/duraklat/sıfırla/ileri/geri ve hız kontrolleri vardır. Laboratuvar başarı XP’si profil bazında bir kez SQLite’a yazılır ve JSON yedeğine alınır; simülasyon, kullanıcının gerçek C++ kodunu çalıştırmaz.
- Project Workshop mevcut eğitim görevlerine ek olarak çok dosyalı yerel çalışma alanlarını, Monaco dosya düzenlemeyi, G++ derleme/çalıştırmayı, standart girdi ve profile bağlı kaydetme/yedeklemeyi destekler. CMake kullanıcı hesabına kuruldu; uygulama PATH dışında kalan kullanıcı kurulumunu da bulur ve doğrulanmış kaynak listesinden güvenli build yapılandırması üretir.
- Kariyer paneli gerçek görev ve proje ilerlemesine göre basamak açar. Mülakat modu çevrimdışı Türkçe/Rusça C++ soruları ve G++ ile puanlanan kod görevleri sunar. Portföy kaydedilen proje durumlarını ve kullanıcının açıklamalarını içerir; Markdown olarak dışa aktarılabilir.
- Kedi dükkânındaki aksesuarlar artan XP fiyatlarına sahiptir ve seçili kedi görünümünde gösterilir.
- RPG loncası, kedi yoldaşı, ekipman ve bir defalık gizli görevler gerçek profil XP/öğrenme verisine dayanır. Offline Coding Arena günlük görevleri yerel G++ testleri ve profil bazlı kişisel rekorlarla çalışır.
- RPG içindeki C++ Dünya Haritası 20 müfredat bölgesini ilerlemeye göre açar; bölümlere ve Boss Challenge görevlerine doğrudan geçiş sunar. Gelişim paneli konu, hata, süre, görev ve XP istatistiklerini SQLite kayıtlarından hesaplar.
- İleri C++ modülü güvenli concurrency adım simülasyonu ve kod çalıştırmadan `-O0`/`-O2` Assembly üretimi sunar. Ders eklentileri yalnızca doğrulanmış JSON içerik manifestleridir; eklenti kodu çalıştırılmaz.
- Eklenti ekranındaki **Eklenti ekle** düğmesi iki dilde ders manifesti `.json` dosyası yükler. Örnek biçim `plugins/std_array_intro.json` içindedir; kendi dosyanızda benzersiz bir `id` kullanın. Eklentiler kullanıcıya özel yerel eklenti klasörüne kurulur; etkinleştirme her profil için ayrıdır. Yalnızca `lessons.read` izni desteklenir; 1–12 ders, en fazla 100 KB ve Türkçe/Rusça içerik zorunludur. Yeni sürüm yalnızca sürüm numarası yükseltilerek yüklenebilir. Uygulama içinden kaldırma eklentiyi yerel olarak siler ve bütün profillerdeki etkinleştirme kayıtlarını temizler. Script, bilinmeyen alan ve uygulama kodu çalıştırma desteklenmez.
- Dil değiştirildiğinde açık olan modül ekranları ortak dil olayıyla yeniden çizilir. Menü, istatistik ve geliştirici aracı etiketleri ile araç ipuçları merkezi `web/locales.json` kataloğundan anında güncellenir. Paketleme akışı örnek `std::array` eklentisini ve `web/assets/cpp-world-map.svg` yerel haritasını da masaüstü paketine ekler.

## Veri konumları

- Kaynak geliştirme çalıştırması: `data/adventure.db`, `backups/`, `student-work/`.
- Kurulu Windows uygulaması: `%LOCALAPPDATA%\CppAdventure\data\adventure.db`, `%LOCALAPPDATA%\CppAdventure\backups\` ve `%LOCALAPPDATA%\CppAdventure\student-work\`.
- Başlangıçta hata olursa kullanıcıya açıklama gösterilir; tanılama kaydı `%LOCALAPPDATA%\CppAdventure\logs\startup.log` konumuna yazılır.
- `start.bat` ile ilk masaüstü açılışında eski `data/adventure.db` içindeki profiller otomatik aktarılır. Hedefte ilerleme varsa üzerine yazılmaz; boş hedef değiştirilmeden önce `.pre-migration.bak` kopyası saklanır.
- JSON dışa aktarma profil bazlıdır; PIN özeti dışa aktarılmaz. İçe aktarma mevcut seçili profil ilerlemesinin yerini alır.

## Dersler ve görsel laboratuvar

- Her bölümde 5 konu anlatımı var: iki temel konu, kod örnekli adım adım anlatım, ✗/✓ işaretli sık yapılan hatalar ve kendini kontrol listesi (Türkçe ve Rusça).
- Her bölümde 8 görev var: iki kavram sorusu (tıklanabilir şıklı), iki çıktı tahmini, hata düzeltme, ısınma programı, pratik görevi ve boss. Yeni tahmin cevapları ve ısınma görevleri `tests/test_lesson_extra.py` içinde gerçek g++ ile doğrulanır.
- Konu anlatımlarında 36 "canlı anlatım" sahnesi var (`lesson_scenes.py`, `web/lesson-scenes.js`): sahne ekrana girince kendiliğinden oynar; kod satır satır yürür, değerler kod satırından bellekteki yerlerine uçar, bellek şeridi her değişkenin adresini ve kapladığı baytı gösterir. Derleme/dosya/istisna akışları, işlem sırası, koşul, döngü, çağrı yığını, dizi/string/map ve sınıf→nesne sahneleri Türkçe ve Rusça anlatılır.
- Görsel laboratuvarda kod satır satır vurgulanır; değişkenler stack/heap üzerinde adresleriyle belirir, pointer okları ve dereference ışığı, sıralamada yer değiştiren çubuklar, döngü izi, koşul çatalı, çağrı yığını, stack/queue ve sınıf→nesne animasyonları gösterilir (`web/lab-theater.js`). Zaman çizelgesine tıklayarak istenen adıma atlanır; ← → ile adım, Boşluk ile oynat/duraklat.

## Giriş, geliştirici araçları ve atölye

- Kayıt artık interaktif bir karakter seçicidir (`web/onboarding.js`): 7 kedi karakteri, canlı önizleme, isim ve isteğe bağlı PIN. Kayıttan sonra profil doğrudan açılır. PIN korumalı profiller mevcut PIN olmadan düzenlenemez.
- Geliştirici araçları: Git için görsel depo şeması (çalışma alanı → hazırlık → commit grafiği → origin) ve adım rehberi, çakışma işaretli dosyayla elle birleştirme, adım adım oluşan CMakeLists.txt, gerçek G++ test laboratuvarı ve geçmişli güvenli terminal. Tüm mesajlar Türkçe/Rusça.
- İleri C++: her thread için ayrı şerit, kaybolan güncellemelerin gösterildiği race condition/mutex simülasyonu; Compiler Explorer yalnızca kendi fonksiyonlarının assembly'sini gösterir ve O0/O2'yi karşılaştırır.
- Proje atölyesi: 8 proje (zorluk, kavramlar, çalışma planı, örnek girdi/çıktı) ve çok dosyalı alan için hazır şablonlar. Yeni projelerin çözümleri `tests/test_workshop_projects.py` ile doğrulanır.

## Ücretsiz AI öğretmen (Groq)

Hiçbir şey indirmeden ve ödeme yapmadan AI ipucu almak için:

1. console.groq.com adresinde ücretsiz hesap aç (kredi kartı gerekmez) ve **API Keys** bölümünden bir anahtar oluştur (`gsk_` ile başlar).
2. Uygulamada ⚙ Ayarlar > AI öğretmen sağlayıcısı > **Groq API anahtarı** kutusuna yapıştırıp **Anahtarı kaydet**'e bas. AI öğretmen otomatik olarak Groq'a geçer.

- Model `openai/gpt-oss-120b`; günlük ücretsiz sınır dolarsa `openai/gpt-oss-20b` denenir, o da doluysa çevrimdışı ipuçları gösterilir. Ücretsiz sınır aşıldığında para kesilmez.
- Anahtar Claude anahtarıyla aynı yerde (`%LOCALAPPDATA%\CppAdventure\secrets`) saklanır. `GROQ_API_KEY` ortam değişkeni de kullanılabilir.

## Claude ile AI öğretmen

Ayarlar (⚙) > AI öğretmen sağlayıcısı bölümünde Claude API anahtarını gir ve **Anahtarı kaydet**'e bas. Anahtar kaydedilince profilin AI öğretmeni Claude olur.

- Ucuz ve hızlı `claude-haiku-5-5` modeli kullanılır; yanıt en fazla 450 token ile sınırlıdır. Başka model için `CPP_ADVENTURE_CLAUDE_MODEL` ortam değişkeni kullanılabilir.
- Anahtar `%LOCALAPPDATA%\CppAdventure\secrets` içinde saklanır; proje klasörüne, veritabanına ve kayıt dosyasına yazılmaz. İstersen `ANTHROPIC_API_KEY` ortam değişkenini de kullanabilirsin.
- Kod yalnızca her istekte onay verirsen gönderilir; tam çözüm değil, ipucu istenir.

## Test paneli

Deneme yapmak için üst çubuktaki anahtar düğmesine bas ya da `Ctrl+Shift+A` kısayolunu kullan. Panel yalnızca etkin profili değiştirir:

- XP ekleme veya doğrudan ayarlama, seviye ve günlük seri ayarlama (seviye, kedinin büyüme aşamasını da değiştirir)
- tüm kedi eşyalarını verme veya silme, bölüm tamamlama, tüm başarımları verme, ilerlemeyi sıfırlama
- konfeti, kedi tepkileri, seviye atlama ve başarım bildirimi gibi animasyonları tetikleme

Paneli tamamen kapatmak için uygulamayı `CPP_ADVENTURE_ADMIN=0` ortam değişkeniyle başlat; o zaman düğme görünmez ve `/api/admin` 403 döner.

## Test

Proje kökünden:

```powershell
python -m py_compile server.py curriculum.py lesson_content.py desktop.py plugin_system.py
node --check web/app.js
python -m unittest discover -s tests -v
```

2026-11-19 güncellemesinden sonra tam regresyonda **118 otomatik test geçti, 0 başarısız** (Linux, Python 3.10, g++). Windows Job Object sınırları ve yeniden yazılan `build-windows.bat` bu ortamda çalıştırılamadı; Windows'ta ayrıca denenmelidir.

**Görsel masaüstü doğrulaması:** Altı atlas karakteri ayrı PNG'lere kırpıldı ve gerçek `CppAdventure.exe` penceresinde Türkçe ve Rusça ad, rol ve açıklamalarıyla altı büyük kart olarak kontrol edildi. Hata Avcısı kartının Rusça laboratuvar bağlantısı açılarak hedef ekranda karakter kılavuzu da doğrulandı.

## Mevcut kapsam ve sonraki aşamalar

Çalışan çekirdek müfredat 20 ana bölüm ve bölüm başına 5 görev (100 görev) içerir. İlk 15 bölüm temelleri, c16–c20 bölümleri pointer ve `new`/`delete`, akıllı işaretçiler ve RAII, kalıtım ve polimorfizm, şablonlar ve lambda'lar, `map`/`set` konteynerlerini kapsar. Ders, görev, quiz yanıtı, ipucu ve ana arayüz Türkçe/Rusça hazırlanmıştır. Yerel test/derleyici değerlendirmesi AI yanıtından bağımsızdır.

Geliştirici Araçları ekranında profil bazlı kalıcı sanal Git/branch/merge ve push/pull, conflict çözme, güvenli terminal simülatörü, sıralı CMake öğretim laboratuvarı ve gerçek G++ test laboratuvarı vardır. Keyfi terminal komutları ve kullanıcı CMake betikleri çalıştırılmaz. Project Workshop çok dosyalı G++ çalıştırma ve profile bağlı kayıt sunar; güvenli CMake derlemesi CMake kurulumuna bağlıdır. Uyarlanabilir öğrenme ve tekrar motoru profilin gerçek deneme geçmişini kullanır; en az üç gözlem olmadan tahmin üretmez. Bilgi haritası konu başarısını, istatistik paneli görünür uygulama süresi ve gerçek görev verilerini gösterir. Offline Arena, RPG loncası, concurrency/Assembly Explorer ve data-only eklenti sistemi de pakete dahildir. Multiplayer kapsam dışıdır.

## Kod çalıştırma güvenliği

Kod yalnızca yerel bilgisayarda G++ ile (`-Wall -Wextra` uyarılarıyla) derlenir. Kaynak kod boyutu sınırı, geçici derleme klasörü, derleme/çalıştırma zaman aşımı, program çıktısı için 64 KB sınırı ve bellek/alt süreç sınırları (`sandbox.py`; Windows'ta Job Object, Linux'ta rlimit) vardır. Yerel API yalnızca `127.0.0.1`/`localhost` Host başlığını kabul eder, çapraz site ve `Origin` uyuşmayan istekleri reddeder ve POST için `application/json` ister. Bu, tam izole bir işletim sistemi sandbox’ı değildir; güvenilmeyen C++ kodunu çalıştırmayın. AI’ye veri gönderimi çevrimdışı varsayılanda gerçekleşmez ve OpenAI isteği başına açık kullanıcı onayı gerektirir.

## Görseller ve lisans

Maskot ve arka plan çizimleri proje için üretilmiş, yerel `web/assets/` dosyalarıdır; yükleme sırasında internet gerekmez. Harici fotoğraf/meme alıntısı bu sürümde kullanılmadı.
