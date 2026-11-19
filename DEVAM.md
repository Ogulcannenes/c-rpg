# C++ Adventure — Geliştirme Durumu

Son güncelleme: 2026-11-14

## Aşama 1 — Mevcut projeyi inceleme ve güvenli yedek

Durum: **Tamamlandı. Sonraki aşamaya kullanıcı onayı olmadan geçilmedi.**

### İncelenen mimari

- Masaüstü kabuğu: Python `pywebview` ile WebView2 penceresi; yerel HTTP sunucusu ve HTML/CSS/JavaScript arayüzü.
- Servis ve iş mantığı: `server.py`; SQLite profiller, görevler ve ilerleme verileri için yerel kayıt kullanıyor.
- Müfredat: `curriculum.py` ve `lesson_content.py`; 15 bölüm, toplam 75 görev, her bölümde quiz/çıktı tahmini/hata düzeltme/kodlama/boss görevleri ve 21 ön koşul bağlantısı.
- Kod editörü: `web/` altında yerel arayüz ve vendored Monaco dosyaları.
- Derleme: bulunan G++/Clang++ derleyicisi; geçici çalışma klasörü, kaynak boyutu sınırı ve derleme/çalıştırma zaman aşımı.
- Paketleme: PyInstaller çıktısı ve kullanıcı hesabına kurulum yapan Windows yükleyici dosyaları mevcut.

### Korunan başlangıç yedeği

- Klasör: `C:\Users\user\OneDrive\Desktop\adel1\C++ Adventure.backup-2026-11-14`
- Kopya doğrulaması: 6.699 dosya kaynak ve yedekte aynı; toplam boyut her iki tarafta 252.165.483 bayt.
- SQLite başlangıç veritabanı yedekte tutuldu. Kaynak ve yedek kopyada `integrity_check=ok`; iki yerel profil, beş görev tamamlama kaydı ve sıfır yabancı anahtar ihlali görüldü. Profil adları ve içerikleri bu rapora dahil edilmedi.

### Başlangıç testleri

- `python -m unittest discover -s tests -v`: **21 test geçti, 0 başarısız**.
- Testler arasında gerçek G++ ile stdin/stdout, derleme hataları, kavram ve edge-case doğrulama, profil izolasyonu/XP, quiz ve günlük kayıtları, içe/dışa aktarma, ön koşullar, laboratuvar simülasyonları, kod kalite/Code Golf, AI onay sınırı ve proje atölyesi bulunuyor.
- `dist/C++Adventure-Setup.exe` ve `dist/CppAdventure/CppAdventure.exe` mevcut. Bu aşamada GUI uygulaması başlatılmadı; başlatma veritabanı şemasını uygulama koduyla değiştirebileceğinden mevcut gerçek kullanıcı verisine dokunmamak için uçtan uca GUI açılışını sonraki onaylı aşamada doğrulamak üzere bıraktım.

### İncelemede görülen açıklar ve riskler

- Kod çalıştırma zaman aşımı ve geçici klasör var; işletim sistemi seviyesinde süreç, bellek ve dosya sistemi yalıtımı yok.
- AI sağlayıcılarının gerçek ağ bağlantısı ve OpenAI anahtarı bu aşamada uçtan uca denenmedi; mevcut otomatik test çevrimdışı varsayılanı ve onay gereksinimini doğruluyor.
- Splash screen ve PIN kedi animasyonları, akıllı tüm-müfredat kavram denetimi, ayrıntılı öğrenme analitiği, görsel algoritma/memory araçları, Git/CMake/terminal modülleri, kariyer/portföy, Concurrency/Compiler Explorer ve güvenli eklenti sistemi henüz doğrulanmış mevcut özellikler değil.
- README genişletilmiş modüllerin bir kısmını açıkça tamamlanmamış olarak listeliyor.
- Kullanıcının bu talimattaki son kapsamı tek oyunculu; multiplayer ve çevrimiçi eşleştirme kapsam dışı tutulacak.

### Bu aşamadaki değişiklikler

- Uygulama kaynak kodunda veya kullanıcı verisinde değişiklik yapılmadı.
- Bu durum dosyası, aşama kaydı olarak yedek alındıktan sonra oluşturuldu.

## Aşama 2 — Kod çalıştırma sistemi ve CMD sorunu

Durum: **Tamamlandı ve test edildi.**

### Yapılan değişiklikler

- G++/Clang++ ve derlenen program Windows'ta `CREATE_NO_WINDOW` ile başlatılıyor; uygulamanın önünde CMD penceresi açılmıyor.
- Derleme ve çalışma hataları ayrı fazlar olarak raporlanıyor. API yanıtı `compile_ok`, derleyici mesajları, stdout, program stderr'i, çıkış kodu ve toplam süre/derleme/çalışma sürelerini taşıyor.
- Boş kaynak kod ve 2.000 karakterden uzun/geçersiz girdi açıkça reddediliyor. Derleme ve çalışma zaman aşımı mesajları ayrıştırıldı.
- Ders editörü ve Project Workshop aynı yerel çalıştırma servisini kullanıyor; Türkçe ve Rusça sonuç paneli bu iki ekranda da aynı bilgileri gösteriyor.
- README'deki çalıştırma bilgisi güncellendi.

### Düzenlenen dosyalar

- `server.py`
- `web/app.js`
- `web/index.html`
- `web/run-panel.css` (yeni)
- `tests/test_core.py`
- `README.md`
- `DEVAM.md`

### Test ve çalışma sonucu

- Otomatik testler: **25 geçti, 0 başarısız** (başlangıçtaki 21 test de dahil).
- Python bytecode derleme kontrolü ve `node --check web/app.js`: başarılı.
- Gerçek Windows paketleme: başarılı; `dist/CppAdventure/CppAdventure.exe` ve 24.832.698 baytlık `dist/C++Adventure-Setup.exe` üretildi.
- Paketlenmiş masaüstü uygulaması izole test veri klasörüyle açıldı; pencere ve yerel HTML/CSS servis edildi. Uygulamanın yerel API'sinden string girişiyle `Hello Luna` ve ikinci satır `Ready` çıktısı alındı (çıkış kodu 0). Bilerek hatalı C++ gönderiminde derleyici tanıları ayrı alanda görüldü.
- Derleme/çalıştırma isteği sırasında yeni CMD işlemi oluşmadı. Test veritabanı geçici konumdaydı ve testten sonra temizlendi; gerçek `data/adventure.db` değiştirilmedi.
- İlk yeniden paketleme denemesi test uygulaması açık olduğu için DLL kilidine takıldı; test örneği kapatıldıktan sonra paketleme tekrarlandı ve başarılı oldu.

### Kalan riskler

- G++ zaman ve kod boyutu sınırları var; uygulama seviyesinde ayrıcalıksız işlem/Job Object ile kaynak sınırı ve dosya sistemi yalıtımı henüz yok. Güvenli kod sandbox'ı bu aşamada tamamlanmış sayılmıyor.
- Program girdisi çalıştırmadan önce giriliyor; canlı stdin akışı, program çalışırken etkileşimli terminal girdisi olarak uygulanmadı.

## Aşama 3 — Bütün görevlerde kavram doğrulaması ve Boss Challenge düzenlemesi

Durum: **Tamamlandı ve kullanıcı onayıyla test edildi. Sonraki aşama için onay bekleniyor.**

### Yapılan değişiklikler

- 15 bölümün hata düzeltme, kodlama ve Boss görevleri konuya özel içerikle yenilendi; 45 göreve ayrı C++ kavram ölçütleri eklendi.
- Görev başına birden fazla G++ test girdisi ve değişken sınırlarını kapsayan senaryolar eklendi. Sabit çıktı, yorum, string içeriği veya kullanılmayan değişkenler konu kavramını karşılamıyor.
- Clang varsa öğrencinin `main` AST'si inceleniyor. Clang yoksa G++ derlemesi/testlerine ek olarak yorum ve sabitleri ayıklayan yapısal belirteç denetimi çalışıyor. Bu geri dönüş AST kadar güçlü değil.
- Görev ancak gerçek derleme/çalıştırma testleri ve kavram kriterleri birlikte geçince tamamlanıyor; kavram başarısızlığında iki dilde geri bildirim veriliyor ve XP yazılmıyor.
- Her bölümün 4. görevi ve Boss'u ayrı senaryo, başlangıç kodu ve testlerle yeniden tasarlandı.
- Öğrenme ekranı, başarısız test ve kavram kriterlerini ayrı gösteriyor.

### Düzenlenen dosyalar

- `concept_checker.py` (yeni)
- `mission_contracts.py` (yeni)
- `curriculum.py`
- `server.py`
- `web/app.js`
- `tests/test_core.py`
- `tests/test_mission_contracts.py` (yeni)
- `README.md`
- `DEVAM.md`

### Test ve paketleme sonucu

- `python -m py_compile concept_checker.py mission_contracts.py curriculum.py server.py tests/test_core.py tests/test_mission_contracts.py`: başarılı.
- `node --check web/app.js`: başarılı.
- `python -m unittest discover -s tests -v`: **31 geçti, 0 başarısız** (165,8 saniye).
- 45 farklı hata düzeltme/kodlama/Boss çözümü gerçek G++ ile derlendi; görevlerin her birindeki tüm girdi/çıktı vakaları geçti.
- Clang AST testleri 15 kavram kuralının iki dilli kriterlerini, aldatıcı yorum/string ve kullanılmayan değişken örneklerinin reddini doğruladı.
- API entegrasyon testi sabit çıktının görev başarı/XP vermediğini; kavramı kullanan geçerli çözümün XP aldığını doğruladı.
- Windows paketlemesi bu güncellemeden sonra yeniden oluşturuldu: `dist/CppAdventure/CppAdventure.exe` (5.521.618 bayt) ve `dist/C++Adventure-Setup.exe` (24.862.594 bayt).
- Paketlenmiş masaüstü uygulaması bu aşamada açıldı; uygulama penceresi yanıt verdi, yerel arayüz HTTP 200 ile yüklendi ve pencere normal biçimde kapandı. Bu açılış kontrolünde kullanıcı profili veya ilerleme API'sine yazma yapılmadı.
- PyInstaller, isteğe bağlı `pycparser.lextab` ve `pycparser.yacctab` hidden import'ları bulunamadı uyarısı verdi; paketleme başarıyla tamamlandı ve uygulama açılış duman testi geçti.

### Bilinen sınırlamalar

- Clang bulunmayan bilgisayarlarda yapısal geri dönüş kontrolü AST analizinden daha az kapsamlıdır; G++ çalıştırma testleri zorunlu kalır.
- C++ çalıştırma için işletim sistemi seviyesinde sandbox mevcut değildir (Aşama 2'de kaydedilmiş güvenlik sınırı).

## Aşama 4 — Splash Screen ve Cat Password Interaction

Durum: **Tamamlandı ve kullanıcı onayıyla test edildi. Sonraki aşama için onay bekleniyor.**

### Yapılan değişiklikler

- Masaüstü uygulaması ana ekrandan önce koyu RPG temalı, özgün SVG kedi maskotlu açılış ekranı gösteriyor. Kod parçacıkları ve parçacıklar animasyonlu; `Created by Ogulcanenes` ve uygulama sürümü görünür.
- İlerleme yüzdesi sahte sayaç değil; sürüm/veritabanı metaverisi, profil listesi ve seçili profil kaydı gerçekten yüklendikçe ilerliyor. Başlangıç hatasında ekran hata mesajı ve tekrar dene seçeneği sunuyor.
- Splash, ana içerik daha önce hazır olsa bile en az **3.500 ms** gösteriliyor. Gerçek yükleme tamamlanınca yüzde 100’de kalıp kalan görünürlük süresini tamamlıyor; hazır olmadan yapay yüzde artışı yapılmıyor.
- Sunucuya `/api/meta` sürüm ve veritabanı hazırlık yanıtı eklendi; sürüm `0.4.0` olarak tanımlandı.
- Profil seçme ve PIN korumalı profil silme artık uygulama içi PIN modalını kullanıyor. PIN gizli başlıyor, göz düğmesiyle görünür/gizli yapılabiliyor, Enter ile gönderiliyor ve Escape ile iptal ediliyor.
- Aynı özgün SVG kedi dört PIN durumunu canlandırıyor: gözleri kapalı, tek gözüyle bakan, yanlış PIN’de şaşkın/üzgün, doğru PIN’de sevinçli. Hatalı PIN’de giriş sarsılıyor; animasyon sonrası görünürlük önceki duruma dönüyor.
- Sunucunun mevcut PBKDF2 tabanlı profil PIN denetimi değişmedi. Başlangıç sorunları profil/kod içeriği taşımadan `%LOCALAPPDATA%\CppAdventure\logs\startup.log` dosyasına yazılıyor; beklenmeyen başlangıç hatası kullanıcıya gösteriliyor.

### Düzenlenen dosyalar

- `desktop.py`
- `server.py`
- `web/index.html`
- `web/app.js`
- `web/splash.js` (yeni)
- `web/pin-cat.js` (yeni)
- `web/startup-pin.css` (yeni)
- `tests/test_core.py`
- `tests/test_startup_pin.py` (yeni)
- `README.md`
- `DEVAM.md`

### Test ve paketleme sonucu

- Python bytecode derleme kontrolü ve `node --check` (app, splash, PIN): başarılı.
- `python -m unittest discover -s tests -v`: **35 geçti, 0 başarısız** (120,5 saniye); mevcut tam test seti, yerel metaveri endpoint testi, mevcut PBKDF2 PIN yanlış/doğru seçme testi, splash/PIN arayüz sözleşme testleri ve minimum görünürlük zaman testi içeriyor.
- Paketlenmiş masaüstü uygulaması izole `%LOCALAPPDATA%` klasörüyle açıldı. Başlangıç kaydı DB init, loopback HTTP listener ve masaüstü pencere adımlarının tamamlandığını gösterdi.
- Paketlenmiş uygulamanın splash HTML içeriği ve `/api/meta` yanıtı HTTP 200 ile doğrulandı: `app_version=0.4.0`, veritabanı hazır. Uygulama penceresi normal kapatıldı; gerçek profil veya ilerleme API'sine yazılmadı.
- Son Windows kurulum `.exe` paketi yeniden üretildi: `CppAdventure.exe` 5.522.976 bayt, `C++Adventure-Setup.exe` 24.873.246 bayt. PyInstaller, önceki aşamadaki gibi isteğe bağlı `pycparser.lextab` / `pycparser.yacctab` import uyarısı verdi; üretim başarılı.
- Kedi durum animasyonlarının piksel/görsel karşılaştırması otomatikleştirilmedi; testler CSS/DOM durumlarını ve sunucu PIN akışını kapsıyor.
- Geri dönüş kopyası son 3,5 saniye splash değişikliği ve kurulum paketiyle eşitlendi ve kaynakla karşılaştırıldı: **6.726 dosya, 252.941.186 bayt**.

### Bilinen sınırlamalar

- Splash ölçümü temel masaüstü başlatması ve profil/ilerleme yüklemesine dayanıyor; Monaco editörünü açılış için zorunlu bekletmiyor.
- İşletim sistemi seviyesinde C++ sandbox sınırı Aşama 2'de kaydedilen risk olarak duruyor.

## Aşama 5 — Git, Git Conflict, CMake, Testing ve Terminal Simulator

Durum: **Tamamlandı ve test edildi.**

### Yapılan değişiklikler

- Yeni Geliştirici Araçları ekranı Türkçe/Rusça arayüzle eklendi; Git, Conflict, CMake, Testing ve Terminal laboratuvarları ayrı sekmelerde.
- Git laboratuvarı init, sanal dosya yazma, stage/add, commit, branch oluşturma/geçme, merge ve sanal remote push/pull akışlarını destekliyor. Yol dışına çıkan dosya adları kabul edilmiyor; gerçek proje dosyaları değişmiyor.
- Ayrı conflict laboratuvarı iki dalın çakışan değişikliğini gösteriyor; yalnızca sunulan iki geçerli sürümden biri seçilince çözüm tamamlanıyor.
- CMake laboratuvarı CMakeLists, proje/standart, executable ve configure/build/run adımlarını sırayla öğretiyor. Bu aşamada keyfi CMakeLists çalıştırmıyor; gerçek çok dosyalı CMake build Aşama 9 Project Workshop kapsamına bırakıldı.
- Testing laboratuvarı kullanıcının C++ kodunu, stdin ve beklenen çıktıyı mevcut sınırlı gerçek G++ çalıştırıcısına gönderiyor; derleme, çıkış ve test karşılaştırması sonucu gösteriliyor.
- Terminal laboratuvarı izole sanal dosya alanında help/pwd/ls/cd/mkdir/touch/cat/echo, Git/CMake ve derleyici tanıtım komutlarını destekliyor. İzin listesi dışındaki komutlar işletim sisteminde çalıştırılmıyor.
- Yeni laboratuvar durumları SQLite’ta profil bazında kalıcı; dışa/içe aktarma ve profil ayrımıyla uyumlu.

### Değişen dosyalar

- `server.py`, `devtools.py` (yeni), `web/index.html`, `web/app.js`, `web/devtools-ui.js` (yeni), `web/devtools.css` (yeni)
- `tests/test_core.py`, `tests/test_devtools.py` (yeni), `README.md`, `DEVAM.md`

### Test sonucu

- Python bytecode derlemesi ve `node --check` (app.js, devtools-ui.js): başarılı.
- Yeni birim ve API hedefli testler: **9 geçti, 0 başarısız**.
- Tam regresyon: **44 geçti, 0 başarısız** (112,9 saniye). 45 gerçek G++ müfredat çözümü, eski profil/yedek akışları, Aşama 5 laboratuvarlarının SQLite profil ayrımı, JSON geri yükleme ve G++ test laboratuvarı dahil.
- İlk hedefli API koşusu ortamın yerel soket iznine takıldı; yerel döngüsel test izniyle yeniden çalıştırıldığında bir JSON yedek test hatası bulundu ve düzeltildi. Son hedefli ve tam koşu başarılıdır.
- Aşama 5’in yeni GUI’si paketlenmiş exe içinde henüz görsel kullanıcı testi almadı; paketleme ve uygulama smoke testi altı aşama tamamlandıktan sonra yapılacak.

## Sıradaki aşama — Aşama 6

Adaptive Learning, Spaced Repetition ve gerçek öğrenme kayıtlarına dayalı Knowledge Prediction. Aşama 5 kaynak durumu bu aşamaya geçmeden kaydedildi.

## Aşama 6 — Adaptive Learning, Spaced Repetition ve Knowledge Prediction

Durum: **Tamamlandı ve test edildi.**

### Yapılan değişiklikler

- Aralıklı tekrar yalnızca quizlere bağlı kalmıyor; kodlama, hata düzeltme ve Boss denemeleri de öğrenme olayları üzerinden kişisel tekrar planına giriyor.
- Başarısız kod görevi bir günlük aralıkla, başarılı tekrar üç günlükten başlayıp 30 güne kadar artan aralıkla planlanıyor. Quizlerin mevcut 1→3→9 günlük davranışı korunuyor.
- Zamanı gelmiş tekrarlar, günlük görev seçilirken yeni görevlerden önce değerlendiriliyor.
- Knowledge Prediction gerçek profile ait en az üç deneme olmadan tahmin üretmiyor. Son beş deneme ve toplam başarı oranına göre yüksek/izlemeye değer tekrar ihtiyacı belirliyor; tahmin kesin sonuç gibi sunulmuyor.
- Uyarlanabilir yol sırasıyla zamanı gelen tekrarı, zorlanılan konuyu veya sıradaki tamamlanmamış konuyu öneriyor. Ana sayfada ve öğrenme günlüğünde iki dilli kişisel öneri alanı bulunuyor.

### Değişen dosyalar

- `server.py`, `learning_engine.py` (yeni), `web/index.html`, `web/learning-ui.js` (yeni), `web/learning.css` (yeni)
- `tests/test_core.py`, `tests/test_learning_engine.py` (yeni), `README.md`, `DEVAM.md`

### Test sonucu

- `py_compile` ve `node --check`: başarılı.
- Hedefli tahmin, zamanlama ve RU/TR izolasyon testleri: **6 geçti, 0 başarısız**.
- Tam regresyon: **49 geçti, 0 başarısız** (113,1 saniye); Aşama 5 ve G++ müfredat testleri dahil.
- Tahmin algoritması yerel ve deterministiktir; AI veya internet kullanmaz. Yeni görsel alanın paketlenmiş exe üzerindeki GUI testi son paketlemede yapılacak.

## Aşama 7 — Knowledge Map ve Advanced Statistics Dashboard

Durum: **Tamamlandı ve test edildi.**

### Yapılan değişiklikler

- Bilgi haritası tamamlanma ve ön koşul kilitlerine ek olarak gerçek denemelerden yeterli kanıt varsa konuyu sağlam, tekrar önerilir veya çalışılıyor olarak işaretliyor; boş konular ayrı gösteriliyor.
- Yeni istatistik ekranı XP, görev ilerlemesi, son 30 gündeki aktif süre, doğruluk, günlük seri, proje/başarım sayısı, günlük süre grafiği, konu başarısı ve hata türlerini gösteriyor.
- Aktif süre yalnızca uygulama görünürken sayılıyor. Gizli/arka plan penceresi ölçülmüyor. İstemci heartbeat'i artan toplam süre olarak gönderdiği için tekrar gelen istekler çift sayılmıyor.
- Süre SQLite’ta profil/session bazında saklanıyor; JSON dışa/içe aktarma ve profil ayrımıyla uyumlu.
- İstatistik görünümü ve bilgi haritası etiketleri Türkçe/Rusça.

### Değişen dosyalar

- `server.py`, `web/index.html`, `web/app.js`, `web/study-tracker.js` (yeni), `web/stats-ui.js` (yeni), `web/stats.css` (yeni)
- `tests/test_core.py`, `tests/test_stats_ui.py` (yeni), `README.md`, `DEVAM.md`

### Test sonucu

- Python derleme kontrolü ve yeni JavaScript dosyalarının `node --check` doğrulaması: başarılı.
- Hedefli istatistik/API/arayüz testleri: **7 geçti, 0 başarısız**.
- Tam regresyon: **56 geçti, 0 başarısız** (114,6 saniye); profiller, backup/import, C++ derleme ve görev değerlendirmeleri dahil.
- İstatistik ekranı henüz paketlenmiş exe’de görsel olarak kontrol edilmedi; son paketleme/smoke aşamasında yapılacak.

## Sıradaki aşama — Aşama 8

Algorithm Visualizer ve Memory Playground. Aşama 7 dosyaları bu geçiş öncesinde geri dönüş kopyasına kaydedildi.

## Aşama 8 — Algorithm Visualizer ve Memory Playground

Durum: **Tamamlandı ve otomatik test edildi.**

### Yapılan değişiklikler

- Algoritma görselleştirici bubble, selection ve insertion sort; linear ve binary search; ayrıca factorial recursion/call-stack simülasyonlarını adım adım gösteriyor. Adımlarda karmaşıklık bilgisi ve ara durumlar bulunuyor.
- Memory Playground güvenli sembolik modelle stack, queue, linked list, dynamic allocation/free, leak ve dangling pointer senaryolarını kapsıyor. Gerçek süreç belleğinde tehlikeli işlem yapılmıyor.
- Algoritma seçimi ve bellek senaryosu mevcut ileri/geri, oynat/duraklat, sıfırla ve hız kontrollerine bağlandı; seçenekler Türkçe/Rusça.
- Tamamlanan laboratuvarlar gerçek profil kaydı üzerinden bir defa XP veriyor; diğer profilin ilerlemesi etkilenmiyor.

### Değişen dosyalar

- `visual_labs.py`, `web/index.html`, `web/algorithm-labs.js` (yeni), `web/algorithm-labs.css` (yeni)
- `tests/test_algorithm_labs.py` (yeni), `tests/test_core.py`, `README.md`, `DEVAM.md`

### Test sonucu

- Laboratuvar birim testleri: **4 geçti, 0 başarısız**.
- Yeni XP/profil API testi: **1 geçti, 0 başarısız**.
- Tam regresyon: **61 geçti, 0 başarısız** (117,15 saniye); G++ gerçek derleme görevleri, profil ayrımı, JSON yedek/geri yükleme, AI onay politikası, aşama 5–7 ekranları ve yeni laboratuvarlar dahil.
- Python ve JavaScript sözdizimi kontrolleri başarılı. Paketlenmiş exe üzerinde görsel kullanıcı testi henüz yapılmadı.
- Aşama 8 geri dönüş kopyası `restore-points/stage8` altında; dosyalar `MANIFEST.sha256` ile doğrulanabilir.

## Sıradaki aşama — Aşama 9

Project Workshop ve Real Developer Missions: çok dosyalı yerel proje alanı, proje kalıcılığı, G++ testleri ve izin verilen yerde gerçek CMake yapılandırma/build/test akışı.

## Aşama 9 — Project Workshop ve Real Developer Missions

Durum: **G++ atölyesi tamamlandı ve test edildi; CMake yolu uygulanmış fakat bu bilgisayarda CMake olmadığı için gerçek yapılandırma/build çalıştırması doğrulanamadı.**

### Yapılan değişiklikler

- Mevcut tek dosyalı proje görevleri korunarak aynı atölye ekranına kalıcı çok dosyalı proje alanı eklendi. Kullanıcı proje oluşturabilir, adını düzenleyebilir, `.cpp`/header/metin dosyaları ve alt klasörler ekleyip silebilir, Monaco’da dosya değiştirebilir, kaydedebilir ve profil bazında projeler arasında geçiş yapabilir.
- Çok dosyalı G++ build, standart girdi, stdout/stderr, çıkış kodu ve süre sınırıyla geçici çalışma klasöründe gerçekten çalışır. Desteklenen kaynak/header uzantıları, 24 dosya, dosya başına 20.000, toplam 100.000 karakter sınırı ve yol geçişi engeli uygulanır.
- Yeni çalışma alanları SQLite’ta ayrı profillere kaydolur; JSON profil yedeğine dahil edilir ve geri yüklenir.
- CMake modu kuruluysa doğrulanmış kaynak listesine göre uygulama kontrollü `CMakeLists.txt` üretip configure/build/run yapar. Kullanıcının yazdığı CMake betiği çalıştırılmaz. Bu bilgisayarda `cmake` bulunmadı; eksik araç mesajı ve G++ alternatifi test edildi.
- Eski görev tabanlı atölyedeki proje teslimi ve tek seferlik XP sistemi korunmuştur. Özel boş çalışma alanı build’i tek başına XP vermiyor; XP değerlendirmesi mevcut kriterli proje görevlerinde kalıyor.

### Değişen dosyalar

- `server.py`, `project_workshop.py` (yeni), `web/index.html`, `web/project-workshop.js` (yeni), `web/project-workshop.css` (yeni)
- `tests/test_core.py`, `tests/test_project_workshop.py` (yeni), `tests/test_project_workshop_ui.py` (yeni), `README.md`, `DEVAM.md`

### Test sonucu

- Yeni atölye hedefli kontroller: **6 geçti, 0 başarısız**; gerçek 3 dosyalı G++ derleme/çalıştırma, dosya yolu güvenliği, UI bağlantısı, profil ayrımı ve JSON yedek/geri yükleme dahil.
- Tam regresyon: **67 geçti, 0 başarısız** (117,79 saniye).
- Python derleme ve yeni JavaScript sözdizimi kontrolleri başarılı.
- CMake build başarı yolu test edilmedi; CMake kurulu değil. Mevcut uygulama içi Git/CMake eğitim laboratuvarı ise sanal öğretim simülasyonudur.
- Aşama 9 geri dönüş noktası `restore-points/stage9` altında saklandı.

## Sıradaki aşama — Aşama 10

Profil verilerinden kariyer seviyesi, kalıcı mülakat oturumları/değerlendirmesi ve tamamlanan projelerden dışa aktarılabilir portföy.

## Aşama 10 — Career Mode, Interview Mode ve Portfolio Builder

Durum: **Tamamlandı ve otomatik test edildi.**

### Yapılan değişiklikler

- Kariyer ekranı profilin gerçek tamamlanan görev ve proje kayıtlarından Beginner, Intermediate, Advanced ve Professional basamaklarını belirliyor. XP tek başına yeterlilik ölçütü değil. Bir sonraki basamak için görev/proje hedefleri gösteriliyor.
- Mülakat modu Türkçe/Rusça, süre sınırı 15 dakika olan kalıcı oturumlar sunuyor: her oturumda dört C++/algoritma/bellek çoktan seçmeli sorusu ve gerçek G++ ile test edilen bir kodlama görevi bulunuyor. Kod soruları çoklu girdilerle kontrol ediliyor; puan, süre, yanıtlar ve oturum geçmişi profil bazında SQLite’ta saklanıyor. Yarıda kalan oturum sürdürülebiliyor.
- Portföy, atölyede gerçekten kaydedilmiş proje teslimlerini listeliyor; devam eden/tamamlanan durumu ile test skoru ayrılıyor. Açıklama ve teknoloji bilgileri düzenlenip profile kaydediliyor; yerel Markdown dosyası dışa aktarılabiliyor. Kod parçaları 4.000 karakterle sınırlandırılıyor.
- Mülakat sonuçlarından güçlü ve tekrar önerilen konular gerçek oturum yanıtlarından türetiliyor. Interview ve portfolio verileri profil JSON yedeklerine eklenip güvenli biçimde geri yükleniyor.
- Yeni ekranlar Türkçe/Rusça; gerçek C++ testi çevrimdışı, harici AI’ye veri gönderimi yok.

### Değişen dosyalar

- `server.py`, `career_system.py` (yeni), `web/index.html`, `web/app.js`, `web/career-ui.js` (yeni), `web/career.css` (yeni)
- `tests/test_core.py`, `tests/test_career_system.py` (yeni), `tests/test_career_ui.py` (yeni), `README.md`, `DEVAM.md`

### Test sonucu

- Kariyer eşikleri, iki dilde soru seçimi ve arayüz bağlantısı: **3 geçti, 0 başarısız**.
- Profil/API entegrasyon testi: **1 geçti, 0 başarısız**; 5 soruluk mülakatın G++ kod sınaması, profil ayrımı, portföy notları ve dışa/içe aktarma dahil.
- Tam regresyon: **71 geçti, 0 başarısız** (119,48 saniye). Önceki aşamalar, gerçek G++ müfredat testleri, çok dosyalı proje, laboratuvar, yedekleme ve yeni kariyer modülleri dahil.
- Python derleme, JavaScript sözdizimi kontrolleri başarılı. Paketlenmiş `.exe` içinde görsel smoke testi bu aşamada yapılmadı.
- Aşama 10 geri dönüş noktası `restore-points/stage10` altında saklandı.

## Aşama 5–10 durumu

- Aşama 5 — Git/conflict/CMake öğretim laboratuvarları, güvenli sanal terminal ve G++ test alanı: **tamamlandı, test edildi**. CMake/terminal/Git simülasyonları ana bilgisayarda keyfi komut çalıştırmaz.
- Aşama 6 — Adaptive Learning, Spaced Repetition ve Knowledge Prediction: **tamamlandı, test edildi**.
- Aşama 7 — Knowledge Map ve gerçek verilere dayalı Advanced Statistics: **tamamlandı, test edildi**.
- Aşama 8 — Algorithm Visualizer ve güvenli Memory Playground: **tamamlandı, test edildi**.
- Aşama 9 — çok dosyalı Project Workshop ve G++: **tamamlandı, test edildi**. CMake build özelliği mevcut ama bilgisayarda CMake kurulu olmadığından gerçek CMake build başarı yolu test edilmedi.
- Aşama 10 — Career Mode, Interview Mode ve Portfolio Builder: **tamamlandı, test edildi**.
- Bu altı aşamanın yeni ekranları paketlenmiş Windows exe içinde henüz görsel kullanıcı smoke testi almadı. Test edilmeyen özellikler, entegrasyon testlerini geçti diye GUI açısından doğrulanmış sayılmamalıdır.

### CMake kurulum ve entegrasyon düzeltmesi

- `winget` bu Windows kurulumunda çalışmadığı için CMake 4.4.4, Kitware'ın `cmake` Python dağıtımı üzerinden kullanıcı hesabına kuruldu. CMake yürütülebiliri kullanıcı Python site-packages konumunda; varsayılan PATH içinde değil.
- Project Workshop artık `APPDATA\Python\PythonXY\site-packages\cmake\data\bin\cmake.exe` yolunu çözüyor. Böylece masaüstü uygulaması ve paketlenmiş Python çalışma zamanı PATH değiştirilmeden CMake'i bulabiliyor.
- Windows'ta MinGW Makefiles, mevcut MSYS2 `g++` ve `mingw32-make` ile açıkça seçiliyor. CMake configure → build → çalıştır adımı 3 dosyalı projede geçti; API ve CMake laboratuvarı durum ekranı da bağımlılığı algıladı.
- Kurulum sonrası hedefli CMake/G++/API kontrolleri: **6 geçti, 0 başarısız**.
- Kurulum ve düzeltme sonrasındaki tam regresyon: **72 geçti, 0 başarısız**. Gerçek CMake configure/build/run, G++ build, güvenli CMake durumu, profil kayıtları, yedekleme ve önceki modüller bu turda çalıştı.

## Son Windows paketleme kontrolü — 14.11.2026

- Güncel CMake düzeltmelerini içeren paket `dist/CppAdventure/CppAdventure.exe` konumuna alındı. Önceki uygulama klasörü geri dönüş için `restore-points/pre-final-package/CppAdventure` altında tutuldu.
- Windows kurulum paketi `dist/C++Adventure-Setup.exe` yeniden oluşturuldu. Kurulum arşivinin içindeki exe ile dağıtım klasöründeki exe SHA-256 üzerinden eşleşti.
- `start.bat` çalıştırıldı. Güncel exe, SQLite başlangıcını ve yerel servisi başlattı; `startup.log` kaydında masaüstü penceresinin oluşturulduğu ve başlatma hatası olmadan normal kapandığı görüldü. Erken kontrolde işlem çalışır durumdaydı. Bu oturumda pencereyi CUA pencereler listesinde görsel olarak yakalayamadım; bu nedenle görsel smoke testi tamamlanmış sayılmıyor.
- Önceden CMake düzeltmesi sonrası çalıştırılmış regresyon sonucu: **72 geçti, 0 başarısız**. Bu son turda aynı testleri tekrar çalıştırmadım; yalnızca paket ve açılış kaydını doğruladım.

## Aşama 11 — RPG loncası, kedi ekipmanı ve gizli görevler

Durum: **Tamamlandı ve hedefli otomatik test edildi.**

- Gerçek XP ile ilerleyen beş lonca rütbesi ve yoldaş gelişim kademeleri eklendi.
- Dört gizli görev gerçek boss, tamamlanmış proje, satın alınmış aksesuar ve öğrenme süresi verilerinden açılıyor. Ödül tek seferlik ve profil başarımlarına yazılıyor; XP tekrar kazanılamıyor.
- Satın alınmış aksesuarı kedi yoldaşına giydirme/çıkarma ve profil ayrımı eklendi. Yerel kedi illüstrasyonu kullanılıyor; yeni ekran Türkçe/Rusça.
- `rpg_system.py`, `server.py`, `web/index.html`, `web/rpg-ui.js`, `web/rpg.css`, `tests/test_core.py` değişti. Aşama geri dönüş kopyası `restore-points/stage11` altında.
- Testler: RPG API profil izolasyonu, gizli görev ödülü ve mükerrer ödül engeli, ekipman doğrulaması ve iki dilli ekran: **2 geçti, 0 başarısız**. `py_compile` ve `node --check` geçti. İlk kısıtlı ortam denemesinde loopback erişimi engellendi; izinli yerel test çalıştırmasıyla iki test de geçti.

## 10–15 ilerleme durumu

- 10 Kariyer/Mülakat/Portföy: önceden tamamlanmış; bu istekte tekrar geliştirilmedi.
- 11 RPG: tamamlandı ve test edildi.
- 12 İleri C++/Compiler Explorer/Code Golf, 13 Coding Arena/Eklentiler, 14 genel QA ve 15 paketleme: sırada.

## Aşama 12 — Concurrency, Compiler Explorer ve Code Quality/Code Golf

Durum: **Tamamlandı ve hedefli otomatik test edildi.**

- Yarış koşulu ve Mutex farkını iş parçacığı adımlarıyla anlatan, güvenli yerel simülasyon eklendi. İşletim sistemi thread’i başlatmaz; Play/Pause/Reset, ileri/geri adım ve hız kontrolleri bulunur.
- Compiler Explorer yerel G++/Clang++ ile C++ kodunu gerçek `-O0` ve `-O2` Assembly çıktısına dönüştürüyor. Kod çalıştırılmaz; 20 KB kaynak sınırı ve 12 saniyelik derleme zaman aşımı var.
- Önceden çalışan Code Golf ve heuristik Kod Kalitesi ekranı korunup İleri C++ ekranından bağlandı. Ölçümlerin gerçek compile/run veya sezgisel kontrol olduğu arayüzde ayrılıyor.
- `advanced_cpp.py`, `server.py`, `web/index.html`, `web/advanced-cpp-ui.js`, `web/advanced-cpp.css`, `tests/test_core.py` değişti. Aşama kopyası `restore-points/stage12` altında.
- `py_compile` ve `node --check` geçti. Concurrency race/mutex modeli, G++ ile iki gerçek Assembly çıktısı, API profil kontrolü ve iki dil bağlantısı: **3 geçti, 0 başarısız** (test filtresine uyan Advanced Statistics regresyonu da dahil).

- Aşama 12 tamamlandı; sıradaki aşama: 13 — Offline Coding Arena ve güvenli Plugin System.

## Aşama 13 — Offline Coding Arena ve güvenli Plugin System

Durum: **Tamamlandı ve otomatik test edildi.**

- Günlük görev üç çevrimdışı C++ challenge arasından tarihe göre seçilir. Uygulama gerçek G++ ile dört test girdisini derleyip çalıştırır; puan, çözüm süresi, günlük/kişisel rekor ve XP profil bazında saklanır. Kusursuz ödül aynı gün aynı görev için yalnızca bir kez verilir.
- Arena denemeleri JSON yedeklerine eklenip geri yüklenir. Çoklu profil testinde diğer oyuncunun denemesi ve ödülü ayrıdır.
- Eklenti sistemi yalnızca izin listesi doğrulanmış JSON ders manifestleri okur. Python/JavaScript çalıştırma, dosya sistemi veya işletim sistemi izinleri yoktur; symlink, fazla boyut, bilinmeyen alan, hatalı JSON ve tekrarlı kimlikler reddedilir. Profil başına etkinleştirme yedeklenir. Örnek `std::array` dersi `plugins/std_array_intro.json` içindedir.
- Kullanıcı eklentileri kurulu uygulamada `%LOCALAPPDATA%\\CppAdventure\\plugins` klasörüne JSON olarak eklenir. Paketleme aşamasında örnek dersin dağıtım paketine dahil edilmesi doğrulanacak.
- Değişenler: `server.py`, `arena_system.py`, `plugin_system.py`, `plugins/std_array_intro.json`, `web/index.html`, `web/arena-ui.js`, `web/arena.css`, `tests/test_core.py`. Aşama kopyası `restore-points/stage13` altında.
- Testler: günün challenge seçimi/API, gerçek G++ gizli testleri, tek seferlik XP, profil ayrımı, arena yedek geri yükleme, plugin izin reddi, etkinleştirme/yedek geri yükleme, iki dilli UI ve mevcut Debugging Arena regresyonu: **4 geçti, 0 başarısız**. Python derleme ve ilgili JavaScript syntax kontrolleri geçti.

- Aşama 13 tamamlandı; sıradaki aşama: 14 — genel güvenlik, performans, dil ve regresyon kalite kontrolü.

## Aşama 14 — Genel güvenlik, performans ve regresyon kalite kontrolü

Durum: **Kontroller tamamlandı; mevcut sınırlar aşağıda açıkça listelenmiştir.**

- Dil anında değiştirildiğinde RPG, Arena ve İleri C++ ekranlarının açık görünümü ve gezinme başlıkları da güncelleniyor. İlgili üç iki dilli arayüz testi eklendi.
- Windows paket yapılandırması örnek JSON eklentisini de ekleyecek şekilde güncellendi; aksi durumda kaynak modunda bulunan ders kurulu uygulamada görünmezdi.
- Python modüllerinin soğuk import ölçümü: **282 ms**. `py_compile` ve dört ilgili `node --check` geçti.
- Hedefli ekran/dil testleri: **3 geçti, 0 başarısız**. Tam regresyon: **80 geçti, 0 başarısız** (147.217 saniye). G++ müfredat derlemeleri, CMake, profil ayrımı, kayıt/yedekleme, AI rıza kontrolü ve önceki UI testleri pakete dahildi.
- Güvenlik incelemesinde kod boyutu (20.000 karakter), derleme (15 sn) ve çalışma (3 sn) sınırları ile geçici klasör doğrulandı. Sınır: Windows kod çalıştırıcısı işlem başına işletim sistemi Job Object bellek limiti veya güçlü dosya sistemi sandbox’ı uygulamıyor; güvenilmeyen kod için tam izolasyon sağlandığı iddia edilmemelidir. Assembly aracı da yalnızca derler, programı çalıştırmaz; 20 KB ve 12 sn sınırları vardır.
- Aşama 14 geri dönüş kopyası `restore-points/stage14` altında saklanacak.

## Aşama 15 — Windows son paketleme ve teslim

Durum: **Paket oluşturuldu; çalışma kaydı doğrulandı. Görsel pencere incelemesi sınırlı kaldı.**

- PyInstaller Windows 11'de yeni `dist/CppAdventure/CppAdventure.exe` masaüstü paketini oluşturdu. `plugins/std_array_intro.json` paket içinde `_internal/plugins/` yolunda doğrulandı.
- `dist/C++Adventure-Setup.exe` oluşturuldu (**25,446,144 bayt**). Kurulum payload’undaki `.exe` ile dağıtım exe’sinin SHA-256 değeri aynı: `276893AADCE52FE0748772C9D06CE84079062B98E888488534E720AFC713D594`.
- Önceki dağıtım klasörü ve kurulum dosyası `restore-points/stage14-package` altında geri dönüş için tutuldu. Aşama 14 kaynak snapshot’ı `restore-points/stage14` altında.
- `start.bat` üzerinden güncel paket açıldı; gerçek çalışan süreç `dist/CppAdventure/CppAdventure.exe` konumundan geldi. Yerel startup kaydı SQLite başlangıcı, `127.0.0.1` servisi ve masaüstü penceresinin oluşturulmasını gösterdi. Codex pencereler listesinde uygulama penceresi görünmediği için piksel düzeyinde görsel smoke doğrulaması yapılamadı; uygulamanın başlaması doğrulandı.
- Son otomatik regresyon: **80 geçti, 0 başarısız**. Installer exe özeti ve payload dosyaları eşleşti. Masaüstü test uygulaması bu teslim sonunda açık bırakıldı.

## 10–15 sonuç özeti

- 10 Kariyer/Mülakat/Portföy: önceden tamamlanmış.
- 11 RPG loncası/kedi ekipmanı/gizli görev: tamamlandı; hedefli testler geçti.
- 12 Concurrency/Compiler Explorer: tamamlandı; güvenli simülasyon ve gerçek yerel Assembly üretimi test edildi.
- 13 Offline Arena/data-only eklentiler: tamamlandı; G++ testleri, profil/yedek izolasyonu ve manifest güvenliği test edildi.
- 14 kalite kontrol: 80/80 regresyon ve dil/UI/derleme kontrolleri geçti. Gerçek Windows OS seviyesinde sandbox/işlem bellek sınırı mevcut değil; bu güvenlik sınırı README’de açıklandı.
- 15 masaüstü exe ve setup paketi: üretildi ve açılış kaydı doğrulandı. Görsel pencere incelemesi otomasyon penceresi görünürlüğü nedeniyle tamamlanamadı.

## Maddeler 16–20 — mevcut özelliklerin doğrulanması

Bu maddeler son kapsamlı talimattaki sıra ile eşleştirildi: 16 Terminal Simulator, 17 Concurrency/Compiler Explorer, 18 Career Mode, 19 Interview Mode, 20 Portfolio Builder. Mevcut uygulamada daha önce geliştirilmiş oldukları için kodu tekrar yazmadım; hedefli testleri yeniden çalıştırdım.

- **16 Terminal Simulator:** Komutlar sanal dosya alanında çalışır; ana bilgisayarda komut çalıştırma engellenir. `test_virtual_terminal_blocks_host_commands` geçti.
- **17 Concurrency/Compiler Explorer:** Race/Mutex adım simülasyonu ve gerçek G++ ile `-O0`/`-O2` Assembly üretimi test edildi. İki test geçti.
- **18 Career Mode:** Kariyer seviyesi görev ve proje kilometre taşlarından hesaplanır; seviye ve iki dilli ekran testleri geçti.
- **19 Interview Mode:** Türkçe/Rusça soru seçimi, kalıcı oturum, G++ ile kod sorusu, profil ayrımı ve yedek geri yükleme entegrasyon testi geçti.
- **20 Portfolio Builder:** Proje notu/teknolojilerinin profile kaydı ve JSON yedekleme/geri yüklemesi Interview/Career API entegrasyon testinde doğrulandı.
- Hedefli test paketi: `test_devtools`, `test_career_system`, `test_career_ui` ve üç gerçek API/G++ senaryosu — **13 geçti, 0 başarısız (3.663 saniye)**.
- Bu doğrulama turunda uygulama kodu değiştirilmedi; mevcut Stage 15 Windows paketi geçerli kaldı. Test/doğrulama kaydı `restore-points/stage16-20-checkpoint` altında saklandı.
- Multiplayer bu projenin bağlayıcı tek oyunculu kapsamı dışında kalır; çevrim içi oyuncu eşleştirme veya yarışma eklenmedi.

## Maddeler 21–25 — RPG, Offline Arena ve istatistikler

Durum: **Mevcut özellikler doğrulandı; 23. maddedeki ayrı RPG Dünya Haritası tamamlandı.**

- **21 Cat Companion:** Yerel kedi illüstrasyonu ve XP ile gelişen yoldaş kademesi mevcut. Ekipman/companion ekranı ve profil verisi doğrulandı.
- **22 Guild, Equipment, Secret Quests:** Beş gerçek XP lonca rütbesi, satın alınan aksesuarı giydirme ve boss/proje/aksesuar/çalışma süresi koşullu, bir defalık gizli ödüller mevcut. Profil izolasyonu ve yinelenen ödül engeli test edildi.
- **23 World Map ve Boss Battles:** Önceki uygulamada müfredat bilgi haritası ve Boss görevleri vardı, ancak RPG dünya bölgeleri ayrı gösterilmiyordu. RPG karargâhına 15 konulu, Türkçe/Rusça C++ Dünya Haritası eklendi: Variables Forest, Loop Dungeon, Pointer Abyss · Memory Realm, OOP Castle, STL Kingdom ve Final Boss Arena dahil. Gerçek chapter ön koşulları bölge kilitlerini belirler; görev ilerlemesi ve boss yenilme durumu gösterilir; açık bölgeye veya ayrı Boss Challenge görevine tıklanabilir.
- **24 Offline Coding Arena:** Günlük C++ meydan okumaları gerçek G++ gizli testleriyle çevrimdışı çalışır; XP bir kez verilir, kişisel skor/rekor ve kayıtlar profil bazında tutulur.
- **25 Advanced Statistics:** Görev denemeleri, doğruluk, konu performansı, hata türleri, XP, proje ve görünür çalışma süresi gerçek yerel kayıtlardan hesaplanır.
- Son odaklı regresyon: **9 geçti, 0 başarısız (5.313 saniye)**. RPG/ekipman/gizli ödül API’si, Arena’da gerçek G++ ve tek seferlik XP, profil/yedek ayrımı, istatistikler, bilgi haritası, iki dilli ekranlar ve Boss görevlerinin farklılığı kapsandı. `node --check web/rpg-ui.js` ve `py_compile` başarılı. Bu değişiklikten sonra tam 80 testlik paket yeniden çalıştırılmadı.
- Dünya haritası `dist/CppAdventure` ve Setup paketine yeniden alındı. Setup boyutu **25,448,852 bayt**; kurulum arşivindeki exe dağıtım exe’siyle aynı SHA-256 değerinde: `47187C1EC76AA66FA814C382FCD7C476CAE23C463CD3E39D1BD3399528A0F3F6`.
- `start.bat` güncel masaüstü exe’sini başlattı; SQLite, yerel servis ve WebView masaüstü penceresi başlangıç kaydı doğrulandı. Masaüstü penceresi otomasyon envanterinde görünmediğinden Dünya Haritası için görsel tıklama testi yapılmadı.
- Geri dönüş noktası `restore-points/pre-world-map-package` altında; aşama kaynak ve test kaydı `restore-points/stage21-25-checkpoint` altında.

## Kapsamlı kalite denetimi — maddeler 5–25, 2026-11-14

**Kapsam sınırı:** Bu denetim, ana talimatın 5–25 numaralı özelliklerini ve önceki geliştirme kayıtlarını kapsar. 26. aşama başlatılmadı. Kullanıcı veritabanı ve ilerlemesi sıfırlanmadı. Değişiklikten önce `restore-points/pre-audit-5-25` tam proje geri dönüş kopyası alındı; önceki paket klasörleri yerinde bırakıldı.

### Başlangıçta bulunan eksikler

- Aşama kayıtlarındaki API/birim testleri her modülün görsel kullanıcı testi yapıldığını kanıtlamıyordu; harita ve bazı ekranların gerçek GUI smoke test kapsamı dardı.
- Canlı Rusça profil ekranında İstatistikler etiketi Türkçe, Geliştirici Araçları etiketi ham `devtoolsNav` anahtarı olarak kalmıştı. Üst araç çubuğunda da Türkçe sabit başlıklar vardı.
- C++ Dünya Haritası bölgeleri ayrı görsel bir dünyayla temsil edilmiyordu; başlık/bağlantı görünümü yetersizdi.
- `dist-stage15` ve `dist-stage21-25` boş klasörlerini başarılı paketleme kanıtı saymak mümkün değildi.
- Uygulamada yerel kedi çizimleri/arka planları var, ancak açık lisanslı harici kedi fotoğrafı veya meme görselleri yok. Bu kısım tamamlanmış değil.

### Yapılan düzeltmeler

- `web/locales.json` içine merkezi Türkçe/Rusça istatistik, geliştirici araçları ve araç ipucu çevirileri eklendi. `web/index.html` bu çeviri anahtarlarına bağlandı. `web/app.js` dil değiştirince metinleri ve başlık ipuçlarını güncelliyor.
- İnternet gerektirmeyen özgün `web/assets/cpp-world-map.svg` eklendi: farklı bölgeler, bağlantı yolları, NPC ve boss çizimleri var. Harita `web/rpg-ui.js`/`web/rpg.css` üzerinden sürükleme, yakınlaştırma, durum gösterimi ve ilgili bölüm/boss açma davranışına bağlı.
- Windows'ta derleyici geçici exe'leri temizlerken karşılaşılan kısa süreli dosya kilitleri için sınırlı tekrar denemesi eklendi (`server.py`).
- Yerelleştirme ve harita regresyon testleri eklendi/güncellendi (`tests/test_i18n_catalog.py`, `tests/test_core.py`).
- Düzenlenen dosyalar: `server.py`, `web/app.js`, `web/index.html`, `web/i18n.js`, `web/locales.json`, `web/rpg-ui.js`, `web/rpg.css`, `tests/test_i18n_catalog.py`, `tests/test_core.py`, `README.md`, `start-desktop.bat`. Yeni SVG yerel pakete eklendi.

### Aşama 5–25 durum değerlendirmesi

- **5–10:** Git/CMake/Testing/Terminal laboratuvarları, learning journal/adaptive learning, knowledge map/istatistik, algoritma ve bellek laboratuvarları, Project Workshop, Career/Interview/Portfolio mevcuttu. Son regresyonda gerçek HTTP/API, G++ derleme ve kayıt işlevleri sınandı. Her ekranın elle GUI kullanımı yapılmadı.
- **11–13:** Guild/equipment/gizli görevler, concurrency/assembly/Code Golf ve offline arena/güvenli JSON eklentileri mevcut. Profil izolasyonu, tek seferlik XP, manifest güvenliği ve gerçek derleyici davranışı regresyonda geçti.
- **14–15:** kalite kontrolleri ve Windows paketi yeniden üretildi. Tam işletim sistemi sandbox'ı/Job Object bellek limiti yok; README'deki güvenlik sınırı geçerlidir. Yeni temiz build `dist-audit-final` içinde; standart `dist` çalışan OneDrive uygulamasının dosya kilidi nedeniyle üzerine yazılamadı. Başlatıcı son denetim sürümünü önce açacak şekilde güncellendi. Önceki standart dağıtım ve ara klasörler silinmedi.
- **16–20:** Terminal, concurrency/compiler explorer, Career, Interview ve Portfolio regresyon testleriyle tekrar doğrulandı.
- **21–25:** Cat Companion, Guild/Equipment, Boss, Offline Arena ve gerçek verili Advanced Statistics otomatik test kapsamından geçti. C++ Dünya Haritası artık yerel illüstrasyon ve görev bağlantılarına sahip. GUI'de tüm kontroller tek tek elle kullanılmadı.

### Dil ve görsel kalite

- Katalog testi Türkçe/Rusça içerik anahtarlarının eksiksiz ve paralel olduğunu; runtime testi yeniden başlatmadan dil değiştirmeyi doğruladı. Gerçek masaüstü penceresindeki Rusça profil ekranı incelendi ve kalan iki gezinme etiketi ile üst araç ipuçları düzeltildi.
- C++ kodu, komutlar, G++, Git/CMake gibi teknik ürün/terimler özgün biçimde kalabilir. OpenAI/Ollama'nın çevrimiçi yanıtları bu turda servis bağlantısı olmadan test edilmedi.
- Yerel görseller `web/assets/cpp-world-map.svg`, `web/assets/cat-companion.png` ve `web/assets/coding-cats-room.png`. Harici fotoğraf/meme yok; kedi animasyonları ve tüm modül görselleri kapsamlı görsel GUI testinden geçmiş sayılmaz.

### Boş build/dist klasörleri

- Gizli dosyalar dahil taramada `dist-cmake-validation`, `dist-stage15`, `dist-stage21-25`: **0 girdi, 0 dosya**. Silinmediler. İlk iki klasör OneDrive reparse-point niteliğinde.
- `build-cmake-validation`, `build-stage15`, `build-stage21-25`: boş değil, her birinde 16 dosya. Bunlar ara PyInstaller build çıktılarıdır; tek başlarına installer üretildiğini göstermez.
- Önceki kayıtlar aşama çıktılarının standart `dist` içine taşındığını söylüyor. Ancak boş `dist-stage15`/`dist-stage21-25` klasörlerini oluşturan veya boşaltan kesin komut için kayıt/log yok; dolayısıyla bunun taşıma sonrası staging kalıntısı olduğu yalnızca olası açıklamadır. `dist-cmake-validation` için kesin oluşturma nedeni doğrulanamadı.
- Yeni denetim build'inde uygulama: `dist-audit-final/CppAdventure/CppAdventure.exe` (**5,596,196 bayt**, SHA-256 `48BB34AF80FBB4CD6B023B8C4C14CF4EC24C3E29688B5F0B03A2394C89054882`). Kurulum paketi: `dist-audit-final/C++Adventure-Setup.exe` (**24,994,339 bayt**, SHA-256 `488B3A39DDDD375A28268AADB12AF82458A4AC8C15F2874B03402361D8249310`). Setup payload'undaki exe hash'i dağıtım exe'siyle aynı; 297 dosya arasında son locale kataloğu ve harita SVG'si doğrulandı. Paket oluşturma komutu başarılı; installer'ın mevcut kuruluma uygulanması bu turda yapılmadı.

### Gerçek test sonuçları ve sınırlar

- `python -m unittest discover -s tests -v`: **86 geçti, 0 başarısız (164.569 saniye)**. İlk kısıtlı denemede Windows loopback bağlantısı engellendi; loopback'e izin verilen tam tekrar başarıyla tamamlandı.
- Yerelleştirme ve profil seçici testleri tam regresyona dahil edildi. Python `py_compile` ve `node --check` (`app.js`, `rpg-ui.js`, `i18n.js`) geçti.
- Tam regresyon gerçek G++ stdin/stdout, hata ve timeout, müfredat kavram denetimi/Boss farklılığı, CMake ve çok dosyalı proje, profil/XP, yedekleme, AI rızası, harita/laboratuvar, TR/RU katalogları ve mevcut modülleri içerdi.
- `start.bat` ile son `dist-audit-final` uygulaması açıldı ve gerçek pencere CUA'da görüntülendi. Profil seçmeden dili Rusça'ya çevirdim; ilk anlık karede eski profil içeriği kısa süre görünse de yenilenme tamamlandıktan sonra profil listesi, seçim düğmeleri, liderlik tablosu ve gezinme tümüyle Rusçaydı; ekranda Türkçe UI sızıntısı kalmadı. Gerçek kullanıcı veritabanı açılmadı/değiştirilmedi; Codex çalıştırma ortamı `LOCALAPPDATA` değerini geçici klasöre yönlendiriyor. Tüm modül ekranları elle gezilmedi.
- AI servis bağlantı testleri: **yapılmadı** (OpenAI API anahtarı/harici onay yok; Ollama/model erişimi doğrulanmadı). Installer yeni sürüm olarak mevcut kuruluma uygulanmadı.

### Başlatma ve geri dönüş

- `start.bat` → `start-desktop.bat` → `dist-audit-final/CppAdventure/CppAdventure.exe`.
- Güncel kurulum dosyası `dist-audit-final/C++Adventure-Setup.exe`.
- Tam kaynak/proje geri dönüş kopyası: `restore-points/pre-audit-5-25`. Önceki `dist` ve build klasörleri değişiklik sonrası temizlenmedi/silinmedi.
- **Sonuç:** aşama 5–25 kapsamı denetlendi ve doğrulanabilen bazı eksikler düzeltildi; bütün görsel/AI/elle GUI istekleri tamamlandı değildir. 26. aşamaya geçilmedi.

## Aşama 26 — Plugin System, 2026-11-14

### Geri dönüş noktası ve kapsam

- Değişikliklerden önce `restore-points/stage26-before` altında **292 dosya / 79.605.976 bayt** tam geri dönüş kopyası oluşturuldu. Bu aşamada gerçek kullanıcı veritabanı değiştirilmedi.
- Bu aşama eklentileri güvenli, yerel ve veri odaklı ders paketleriyle sınırlar. Eklenti kaynak kodu çalıştıran genel amaçlı yürütülebilir bir eklenti API'si yoktur; bu kasıtlı bir güvenlik sınırıdır.

### Yapılan değişiklikler

- `plugin_system.py`: Türkçe/Rusça zorunlu manifest ve ders alanları, katı SemVer, tek `lessons.read` izni, 12 ders ve 100 KB boyut sınırı, bilinmeyen/script alanlarını reddetme, symlink/reparse-point ve dosya yolu kontrolleri, bozuk dosya başına hata izolasyonu eklendi.
- Yerel `.json` eklentileri sabit kullanıcı eklenti klasörüne geçici dosya ve atomik değiştirme ile kuruluyor. Yerleşik eklentiler değiştirilemiyor veya kaldırılamıyor. Güncelleme yalnızca daha yüksek sürüm numarasıyla yapılabiliyor. Kaldırma, bütün profillerde o eklentiye ait etkinleştirme ayarlarını temizliyor.
- `server.py`: kurulum/güncelleme/kaldırma API uçları eklendi; profil doğrulaması ve büyük manifest için ayrı istek boyutu limiti var. Kaynak çalıştırma ile paketlenmiş uygulama yerleşik ve kullanıcı eklenti klasörlerini ayrı kullanıyor.
- `web/arena-ui.js`, `web/arena.css`, `web/locales.json`: TR/RU eklenti yükleme, sürüm/kaynak etiketi, kullanıcıya açık izin bildirimi, eklenti kaldırma onayı ve hata açıklamaları eklendi.
- `tests/test_core.py`: kurulum, yükseltme, eski sürüm reddi, 30 KB üzeri istek, profil bazlı etkinleştirme, yerleşik eklentiyi koruma, kaldırma, script alanını reddetme ve bozuk manifest yalıtımı testleri eklendi.
- `start-desktop.bat` artık `dist-stage26` uygulamasını önce açar. README ve bu aşama kaydı güncellendi.
- Değişen kaynak/dokümanlar: `plugin_system.py`, `server.py`, `web/arena-ui.js`, `web/arena.css`, `web/locales.json`, `tests/test_core.py`, `start-desktop.bat`, `README.md`, `DEVAM.md`; PyInstaller `CppAdventure.spec` dosyasını da yeniden oluşturdu. Yeni paket `dist-stage26/` altında.

### Testler ve paket doğrulaması

- Python derleme kontrolü (`plugin_system.py`, `server.py`), `node --check web/arena-ui.js` ve JSON katalog okuma: başarılı.
- Türkçe/Rusça katalog testleri: **5 geçti, 0 başarısız**.
- Eklenti hedef testleri: **3 geçti, 0 başarısız**. İlk çalıştırmada yerel loopback kısıtı testleri engelledi; izinli tekrar kurulum yanıtındaki bir HTTP durum kodu hatasını yakaladı. Düzeltmeden sonra hedef testler geçti.
- Tam regresyon: `python -m unittest discover -s tests -v` → **88 geçti, 0 başarısız (136,804 saniye)**. G++/CMake, profil ve kayıt, öğrenme sistemleri, dil katalogları, eklenti API'leri ve önceki modüller kapsandı.
- PyInstaller Windows 11 / Python 3.14.7 dağıtım build'i başarılı. Kurulum paketi üretimi başarılı: `dist-stage26/C++Adventure-Setup.exe`, **25.001.673 bayt**, SHA-256 `23A4EB21BDD739ED427D6A255812241D986F4EA1E291B5A1249BA63C9191B8B9`.
- Masaüstü uygulaması `dist-stage26/CppAdventure/CppAdventure.exe` açıldı; WebView içeriği ve profil seçici görünür oldu. Dağıtım exe'si **5.601.406 bayt**, SHA-256 `1E11EB1C2C231E2ACDDD041B2A72BC0F0CD00F1F798F4B5F50201ED21CC180BF`. Paket 281 dosya içeriyor; `plugins/std_array_intro.json`, `web/arena-ui.js` ve güncel `web/locales.json` pakette doğrulandı.
- Kurulum `.exe` dosyası oluşturuldu ancak mevcut Windows kurulumuna uygulanmadı. Başlatılan masaüstü uygulamasında eklenti sayfasını elle açıp dosya seçicisiyle eklenti yükleme GUI akışı ayrıca elle test edilmedi; kurulum/update/remove akışları API entegrasyon testleriyle doğrulandı.

### Bulunan ve giderilen hata / kalan sınırlar

- Eklenti kurulum API'si başarı sonucunu hata gibi ele alıyor, 400 yanıtı veriyordu. Başarı ve hata dönüş ayrımı düzeltildi; hedef ve tam test paketleri sonrasında başarılı.
- C++/Python/JavaScript kodu çalıştıran, OS erişimli üçüncü taraf plugin desteği bu aşamada yoktur; yalnızca güvenli JSON ders manifestleri vardır.
- İlk kısıtlı loopback test denemesi Windows izin hatası verdi; bu bir ürün hatası değil ortam kısıtıydı. Loopback'e izin verilerek yapılan tam test başarılıdır.

### Durum

**Aşama 26 tamamlandı ve test edildi.** Bu aşamanın ötesine geçilmedi. Geri dönüş kopyası `restore-points/stage26-before`; başlatıcı artık yeni paketi tercih eder. Güncel masaüstü çalıştırılabilir dosyası `dist-stage26/CppAdventure/CppAdventure.exe`, kurulum paketi `dist-stage26/C++Adventure-Setup.exe`.


## Aşama 27 — Türkçe/Rusça arayüz tutarlılığı, 2026-11-14

### Kapsam ve geri dönüş

- Stage 27 başlamadan önce proje kaynakları, web arayüzü, testler ve mevcut Stage 26 dağıtımı incelendi. `restore-points/stage27-before` altında değişiklik öncesi tam geri dönüş kopyası oluşturuldu (500 dosya, 99.645.513 bayt). Gerçek kullanıcı veritabanı değiştirilmedi. 28. aşamaya geçilmedi.
- Mevcut `web/i18n.js` katalog yükleme, anlık dil değiştirme ve TR/RU anahtar denetimi altyapısı korundu; yeni metinler aynı merkezi kataloğa eklendi. Ders ve görev içeriğinin ayrı iki dilli içerik modeline müdahale edilmedi.

### Yapılan değişiklikler

- `web/locales.json`: Proje atölyesinin varsayılan proje adı, iptal/silme onayı, aynı dosya ve son kaynak dosyayı silme uyarıları TR/RU eklendi. Splash erişilebilirlik etiketi ve dil düğmesinin erişilebilirlik adı iki dilde merkezi hale getirildi.
- `web/project-workshop.js`: Atölyedeki gömülü Türkçe/Rusça dallar katalog metinlerine bağlandı.
- `web/arena-ui.js`: Gizli test sayısı ve gerçek G++ açıklaması merkezi biçimlendirmeli katalog anahtarından gösteriliyor.
- `web/splash.js`, `web/index.html`, `web/app.js`: Başlangıç ekranı, progress bar ve tekrar düğmesi erişilebilirlik/metin bilgileri dil değişiminde güncelleniyor; dil değiştir düğmesinin aria etiketi de çevriliyor.
- `tests/test_i18n_catalog.py`: Atölye, Arena, splash ve dil düğmesi çevirileri için regresyon kontrolleri eklendi. `start-desktop.bat` artık Stage 27 dağıtımını önce açıyor. README ve bu kayıt güncellendi.

### Test sonuçları

- Değiştirilen dört JavaScript dosyası için `node --check`: başarılı.
- Hedefli i18n ve splash/PIN testleri: **10 geçti, 0 başarısız**.
- Tam regresyon (`python -m unittest discover -s tests`): **90 geçti, 0 başarısız (139,896 saniye)**. İlk kısıtlı koşuda Windows loopback erişimi engellendi; tekrar yerel test sunucusuna erişim verildiğinde bütün testler geçti. İlk hedefli splash denemesi sahte DOM nesnesinde `setAttribute` olmadığı için yakalandı; isteğe bağlı metot çağrısı ile düzeltildi.
- PyInstaller dağıtımı oluşturuldu: `dist-stage27/CppAdventure/CppAdventure.exe` (5.601.406 bayt; SHA-256 `A229D12B26EB68756E3F7913679F6901CBA1D9B1DCB211435B7C7FEB8579D728`). Pakette 281 dosya ve güncel `web/locales.json` (95.129 bayt) var.
- Kurulum paketi oluşturuldu: `dist-stage27/C++Adventure-Setup.exe` (25.004.201 bayt; SHA-256 `1AF36A435D362672899D16D23A8A793D4270062C11174863DF5844E679BC8616`).
- Paketlenmiş uygulama işlemi izole test veri yolu ile başlatıldı; süreç kısa kontrol aralığında çalışıyordu. CUA pencere envanteri uygulama penceresini göstermedi; dolayısıyla masaüstü penceresinin görsel açılışı ve dil değişimini paket içinde elle kontrol etmek doğrulanmadı. Setup exe oluşturuldu ancak kurulum yapılmadı.

### Kalan sınırlar

- TR/RU katalog yapısı ve yeni ekran etiketleri otomatik olarak doğrulandı; tüm uygulama ekranlarında uzun süreli görsel/manuel gezinme yapılmadı. Bazı sunucu tarafı doğrulama hataları hâlâ endpoint içinde sabit metin içeriyor; derleyici tanılamaları ve C++/Git/CMake/terminal komutları teknik çıktı olarak özgün dilinde bırakılıyor. Bunlar Stage 27'nin tam görsel/mesaj kapsamı için kalan yerelleştirme işidir.
- Ollama/OpenAI harici bağlantısı bu aşamada yeniden sınanmadı. Kullanıcı onayı ve API anahtarı olmadan harici servise veri gönderilmedi.
- CMake/Testing/Git modülleri, çoklu profil/XP/kayıt sistemleri ve G++ testleri tam regresyon içindeydi; yeni katalog değişiklikleri tarafından bozulmadı.

### Geri dönüş ve başlatma

- Değişiklik öncesi tam dönüş noktası: `restore-points/stage27-before`.
- Güncel başlatma: `start.bat` → `start-desktop.bat` → `dist-stage27/CppAdventure/CppAdventure.exe`.
- Stage 27 dağıtımı ve kurulum dosyası: `dist-stage27/`.
- **Durum:** Katalog, güncellenen arayüz metinleri ve otomatik regresyon tamamlandı. Kalan backend sabit hata metinleri ile masaüstü GUI'nin gözle görünür smoke doğrulaması nedeniyle bütün Stage 27 dil/GUI kapsamı tam tamamlandı olarak işaretlenmiyor; bir sonraki aşamaya geçilmedi.


## Aşama 28 — Görsel tasarım ve kedi karakterleri, 2026-11-14

### Ön inceleme ve geri dönüş

- `web/assets/` içindeki mevcut companion, coding-room ve C++ dünya haritası görselleri; bunların kullanım yerleri ve genel koyu RPG stili incelendi. Mevcut illüstrasyonlar korundu.
- Değişiklik öncesi `restore-points/stage28-before` altında **478 dosyalık / 99.514.788 baytlık** proje geri dönüş kopyası alındı. Kullanıcı veritabanı test çalıştırmasında izole kaldı.

### Yapılanlar

- C++ Adventure için birbirine uyumlu 6 özgün kedi karakterinden oluşan atlas hazırlandı: Profesör, AI Öğretmeni, Hacker, Debugger, Büyücü ve Boss. `web/assets/cat-crew-atlas.png` olarak yerel pakete eklendi; üçüncü taraf görsel kullanılmadı. Görsel kaynak kaydı `web/assets/SOURCES.md` içinde.
- Ana ekran hero bölümünün altına kedi ekibi kartları eklendi. Kartlar görsel varlığı atlas hücrelerinden kullanıyor; hafif idle/hover animasyonu ve küçük ekran kırılımları var. `prefers-reduced-motion` etkinse hareket kapatılıyor.
- Ekip başlığı ve karakter adları `web/locales.json` içindeki TR/RU merkezi katalogdan geliyor. Yeni `web/visual-upgrade.css` yerel stylesheet olarak bağlandı.
- PNG’yi WebP’ye küçültme denemeleri görsel kaliteyi düşürdüğü için kullanılmadı; 2.661.686 baytlık orijinal temiz çizim korundu.
- `tests/test_i18n_catalog.py` içine asset, yerel kullanım, TR/RU adları ve responsive stylesheet kontrolleri eklendi.

### Test ve paket sonuçları

- `node --check web/app.js`: başarılı.
- i18n/splash ve görsel hedef testleri: **11 geçti, 0 başarısız**.
- Tam regresyon: `python -m unittest discover -s tests` → **91 geçti, 0 başarısız (143,797 saniye)**. Gerçek API, G++, CMake, profil/XP/kayıt ve var olan modüller bu koşuya dahil.
- PyInstaller dağıtımı oluşturuldu: `dist-stage28/CppAdventure/CppAdventure.exe`, **5.601.406 bayt**, SHA-256 `F9056FF1064CE36AEC531FC8471AFA715D607F31B10A6EA17D7ACA13B39D64D7`.
- Setup oluşturuldu: `dist-stage28/C++Adventure-Setup.exe`, **27.655.718 bayt**, SHA-256 `261CA978A37044040393F888F1504026FBA193E248466DCC802082C6349056F9`. Kurulum arşivinde 300 dosya var; yeni PNG, stylesheet ve locale kataloğunun kaynakla aynı olduğu doğrulandı.
- Paket exe izole bir test `LOCALAPPDATA` klasöründe çalıştırıldı. Başlangıç kaydı SQLite başlatma, `127.0.0.1` yerel HTTP servisi ve `desktop window created` satırlarını gösterdi; process `C++ Adventure` pencere başlığıyla yanıt veriyordu. CUA pencere envanteri bu pencereden ekran görüntüsü alamadı; bu nedenle gerçek piksel yerleşimi için görsel GUI incelemesi yapılamadı. Setup çalıştırılarak kurulum yapılmadı.

### Durum ve devam noktası

- Aşama 28’in yerel görsel varlık, ana ekran entegrasyonu, iki dilli metin ve animasyon davranışı tamamlandı ve otomatik testlerle doğrulandı. Görsel GUI ekran görüntüsüyle elle incelenemedi; uygulamanın startup kaydı ve pencere başlığı doğrulandı.
- Güncel başlatıcı `start.bat` → `start-desktop.bat` → `dist-stage28/CppAdventure/CppAdventure.exe` yolunu önce seçer. Önceki paket klasörleri korunuyor.
- Geri dönüş kopyası: `restore-points/stage28-before`. Aşama kaydı: `DEVAM.md`. 29. aşamaya geçilmedi.

## Aşama 28 görsel entegrasyon düzeltmesi — altı kedi karakteri

- Önceki raporda atlasın bulunduğu ve otomatik testlerin geçtiği yazılmıştı; ancak gerçek pencere ekran görüntüsüyle görünürlük doğrulanmamıştı. Bu eksiklik bu düzeltmede giderildi; 29. aşamaya geçilmedi.
- `web/assets/cat-crew-atlas.png` görsel olarak incelendi: 1536×1024 atlas 3×2 hücre düzeninde ve her karakter ayrı bir hücrede. PNG RGBA şeffaflığı sayısal olarak doğrulandı; altı hücre kırpılarak `cat-professor.png`, `cat-teacher.png`, `cat-hacker.png`, `cat-debugger.png`, `cat-wizard.png`, `cat-boss.png` üretildi. Karakterler kartlarda birbirinden bağımsız, büyük görseller olarak görünür.
- Windows masaüstü uygulamasının `dist-stage28-cat-crew/CppAdventure/CppAdventure.exe` paketi açıldı. Türkçe ekranda ilk ve ikinci kart sıraları; Rusça ekranda da her iki sıra, karakter adları, roller, açıklamalar ve eylem düğmeleri gerçek pencerede gözle kontrol edildi.
- Rusça görünümde Hata Avcısı kartındaki “Лаборатория условий” düğmesine basıldı. Uygulama gerçekten Görsel Laboratuvarlar ekranına geçti ve Hata Avcısı çizimi, Rusça rol ve açıklama üst bölümde gösterildi. Kod bağlantıları Profesör→ilk ders, AI Öğretmeni→öğretmen ayarları, Hacker→arena, Büyücü→İleri C++, Boss→RPG olarak tanımlı.
- Ana sayfa kartlarında hafif hover/idle animasyonu ve hareket azaltma tercihi; uygun ekranlarda karakter kılavuz kartları etkin. `web/locales.json` tüm altı karakterin Türkçe/Rusça ad, rol, açıklama ve eylem metinlerini içeriyor.
- Test: önceki tam regresyon **91 geçti, 0 başarısız**; bu düzeltmede ayrıca gerçek masaüstü penceresi ve yönlendirme elle kontrol edildi. Düzeltmeden sonra Python/JS iş mantığı değişmedi; başlatıcı ve rapor dosyaları değişti. Yeni PyInstaller kurulumu tekrar oluşturulmadı; kontrol edilen çalışan paket `dist-stage28-cat-crew` konumundadır.
- `start-desktop.bat` artık bu düzeltilmiş paketi eski Stage 28 paketinden önce seçiyor. Geri dönüş noktaları ve eski paketler korunuyor.

## Ultimate Visual Learning & Cat Companion 2.0 — Ön inceleme

### Mevcut durum

- Önceki uygulama kaynakları değişiklik öncesi `restore-points/stage29-cat-visual-before` konumuna kopyalandı. `web` (161 dosya), `tests` (35 dosya) ve `plugins` (1 dosya) için dosya sayısı ve toplam bayt karşılaştırması eşleşti. Python kaynakları, başlatıcılar, paket tanımları, README/DEVAM ve gereksinim dosyaları da kopyalandı. Derleme/dağıtım klasörleri ve kullanıcı verisi yedeğe dahil edilmedi.
- `data/adventure.db` değişiklik öncesinde 69.632 bayt ve 2026-11-14 04:10 son değiştirilme zamanındaydı; bu inceleme sırasında açılmadı veya değiştirilmedi. Git deposu bulunmadığından geri dönüş noktası dosya kopyasıdır.
- Gerçek C++ izleme için G++ 16.2.0, GDB ve Clang 22.1.8 mevcut. GDB tabanlı çalışma zamanı gözlemleme teknik olarak denenebilir; izleme yalnızca doğrulanmış desteklenen C++ alt kümesi için kullanılmalı. Clang AST tek başına runtime değerlerini vermez.
- Mevcut görsel laboratuvarlar (`visual_labs.py`) girdiden deterministik ve güvenli sembolik adımlar üretir; kullanıcının editördeki gerçek C++ kodunu çalıştırıp izlemez. Adresler `0x1000`, `stack:...` gibi simülasyon adresleridir. Algoritma modülünde Bubble/Selection/Insertion, Linear/Binary Search ve factorial recursion vardır; Merge/Quick/Heap Sort ve istenen tüm veri yapısı işlemleri henüz yoktur.
- Kedi dükkânında 10 ürün bulunuyor; ürünler `web/app.js` içinde emoji ve tek slot etiketiyle temsil ediliyor. Önizleme/ana karakter görünümü tek `cat-companion.png` ve tek bir emoji katmanı kullanıyor. Profilde yalnızca `active_item` alanı var; aynı anda birden fazla takılı aksesuar ve kombinasyon kaydı yok. Mevcut alış/satın alma API’si sahiplik ve XP harcamasını profil bazında koruyor; bu XP/level hesaplaması değiştirilmeyecek.
- RPG `companion_stage` değerini mevcut XP üzerinden beş kademede hesaplıyor; istenen 1, 2–5, 6–10, 11–15, 16–20 ve 21+ level görünüm aralıklarına uymuyor. Level gerçekte mevcut görev/proje kazanımlarından türetildiği için yeni görsel kademe doğrudan mevcut `profile.level` ile hesaplanmalı; mağaza harcamaları ilerleme görünümünü geriletmemeli.
- Paket tanımı `web` ve `plugins` dizinlerini topluyor; yeni assetlerin Windows pakete girmesi mevcut paketleme akışıyla mümkün. Yeni bir masaüstü paket yine de ayrıca oluşturulup açılarak doğrulanmalı.

### Başlangıç testleri

- `test_algorithm_labs.py`: **4 geçti, 0 başarısız**.
- Profil/mağaza/RPG/görsel laboratuvar odaklı `test_core.py`: **6 geçti, 0 başarısız**.
- Bu aşamada tam regresyon koşulmadı. Gerçek kullanıcı veritabanına dokunulmadı.

### Önerilen geliştirme aşamaları

1. **Kedi donanım verisi ve uyumluluk:** Profil başına slot tabanlı ekipman ve kombinasyon için geriye uyumlu SQLite/API tasarımı; eski `active_item` ve mevcut sahiplik kayıtlarını kaybetmeden veri geçişi. Birim/API testleri.
2. **Giyilebilir katmanlar ve mağaza önizlemesi:** Yerel baş/ göz/ boyun/ gövde/ sırt aksesuar çizimleri; birlikte takma, deneme, satın alma, giydirme/çıkarma ve kombinasyon kaydı. TR/RU, profil izolasyonu ve gerçek masaüstü göz kontrolü.
3. **Seviye bazlı kedi gelişimi:** Altı ayrı yaş/gelişim modeli; kademe yalnızca mevcut level’dan türetilir. Level-up animasyonu, aksesuarların yeni modele hizalanması ve hareket azaltma tercihi.
4. **Gerçek kod izleme servisi:** GDB/MI ile `-g -O0` derlenmiş kullanıcı C++ kodundan sınırlı runtime olayları; değişken, pointer, call stack ve kaynak satırı. Zaman aşımı ve desteklenmeyen yapı bildirimi. Simülasyon adresleri açıkça temsili kalır; doğrulanmamış olay gösterilmez.
5. **Kod izleme arayüzü:** Editör satırı, değişkenler, stack/RAM diyagramı ve ileri/geri/oynat/duraklat/hız kontrolleri; kaynak değişince eski iz kaldırılır. Kod izinin değerleri G++ çalışma çıktısıyla karşılaştırılır.
6. **Algoritma ve veri yapısı laboratuvarları:** İstenen altı sıralama, iki arama, recursion ve veri yapısı adımlarını merkezi TR/RU açıklamalarla ekleme; kullanıcı dizisi, karşılaştırma/swap/indeks/işlem vurgusu ve animasyon kontrolleri. Önce saf algoritma doğruluk testleri, sonra masaüstü arayüz kontrolü.
7. **Entegrasyon ve Windows paket doğrulaması:** Profil/XP regresyonu, TR/RU anlık geçiş, tüm yeni varlıkların pakete girişi, gerçek masaüstü kullanımı ve son paket açılış testi. README/DEVAM son durumu.

Her geliştirme aşamasında rapor verilecek ve bir sonraki aşamaya geçmeden önce kullanıcı onayı beklenecek. Bu ön inceleme kaydında uygulama koduna henüz dokunulmadı; 1. geliştirme aşamasına geçiş için onay bekleniyor.

### Aşama 1 — Kedi ekipmanı verisi ve API geçişi

- `server.py` ürün kataloğuna doğrulanan slot bilgileri eklendi (`head`, `ears`, `neck`, `body`, `back`, `toy`). Yeni `companion_equipment` ve `companion_loadouts` tabloları profil kimliğine bağlı ve yuva başına tek ürünü saklıyor.
- Başlangıç veritabanı geçişi, satın alınmış eski `active_item` aksesuarını doğru yuvaya aktarır; eski sütun ve değer aynen kalır. Böylece mevcut ekranlarla geçici uyumluluk korunurken ilerleme/XP hesaplamasına dokunulmadı.
- Yeni API: `GET /api/companion`; aksesuarı yuvaya giydirme/çıkarma; profil başına kombinasyon kaydetme, uygulama ve silme. Yalnızca sahip olunan ürün takılabilir; kombinasyon uygulanırken profil sahipliği ve yuva eşleşmesi yeniden doğrulanır. En fazla 20 kombinasyon ve 32 karakterlik ad sınırı var.
- `/api/state` ekipman yuvalarını içerir. JSON dışa/içe aktarma ekipmanları ve kombinasyonları taşır; eski sürüm yedeklerinde mevcut tek `active_item` yeni yuvaya çevrilir. Alışverişte XP düşürme ve mevcut satın alma mantığı değişmedi.
- Testler: Aşama 1 yeni iki test (eski DB geçişi, çoklu slot/kombinasyon/profil ayrımı/JSON turu ve kombinasyon silme/sahiplik kontrolü) **2 geçti, 0 başarısız**; son hedefli tekrar da **2/2 geçti**. Tam regresyon ilk koşuda Windows geçici `.exe` dosyası kilidi nedeniyle 1 hata verdi; ilgili test tek başına tekrarlandı ve geçti. Tam regresyon tekrarında **93 geçti, 0 başarısız** (151,930 saniye). `py_compile` ve ilgili `node --check` doğrulamaları başarılı.
- Windows paketi `dist-stage29-phase1/CppAdventure/CppAdventure.exe` olarak yeniden oluşturuldu. Gerçek paket izole `%LOCALAPPDATA%` test alanında açıldı; başlangıç günlüğü veritabanı, yerel HTTP servisi ve masaüstü penceresinin hazır olduğunu doğruladı. Önceden hazırlanmış eski şemalı deneme verisinde `active_item=scarf` → `neck: scarf` geçişi oluştu; paket içindeki `/api/companion` gerçek HTTP isteğine bu durumu döndürdü. Test penceresi normal kapatıldı. Kullanıcı veritabanı kullanılmadı. PyInstaller iki kullanılmayan `pycparser` tablo modülü için uyarı verdi; masaüstü açılışını veya bu aşamanın API’sini etkilemedi.
- Güncel `start-desktop.bat`, yeni aşama paketini varsayılan olarak seçer. Önceki paketler korunuyor.
- Değişen kaynaklar: `server.py`, `tests/test_core.py`, `start-desktop.bat`, `DEVAM.md`. Geri dönüş noktası: `restore-points/stage29-cat-visual-before`.
- **Bu aşamada yapılmayanlar:** Görsel katmanlar, mağaza önizlemesi ve takma ekranı; fiziksel büyüme modelleri/animasyonları; GDB çalışma zamanı izleme; algoritma arayüzü. Bu nedenle kullanıcı henüz arayüzden birden çok aksesuarı giydiremez; yalnızca profil bazlı kayıt ve API altyapısı hazırdır.
- Sonraki aşama: **Aşama 2 — Giyilebilir katmanlar ve mağaza önizlemesi.** İlerleme/onay kuralı gereği başlamadan önce kullanıcı onayı beklenecek.

### Aşama 2 — Giyilebilir katmanlar ve mağaza önizlemesi (2026-11-14)

- Kullanıcı Aşama 2’ye başlamayı onayladı. Önceki Aşama 1 kayıtları, mevcut UI/assetler ve testler incelendi. Geri dönüş kopyası `restore-points/stage29-cat-visual-stage2-before` altında oluşturuldu; gerçek kullanıcı veritabanı bu aşamada açılmadı veya değiştirilmedi. Git metadata’sı bu çalışma kopyasında yok; geri dönüş noktası tam dosya kopyasıdır.
- `web/assets/cat-wearables.svg`, 10 mağaza eşyası için yerel ve çevrimdışı SVG çizim katmanları içerir. `web/cat-companion-ui.js` ve `.css`, kedinin mevcut illüstrasyonunun üzerine sırt/giysi, baş/aksesuar, boyun, gözlük/kulak ve oyuncak katmanlarını çizim sırasına göre bindirir. Fiyonk küçültülerek göz hattının üzerine hizalandı.
- Mağaza sayfasına profil seviyesi/XP ile kedi önizlemesi, aksesuara göre doğru slot etiketleri, her slotta bir deneme öğesi, aynı anda farklı slotlarda çoklu önizleme, önizlemeyi sıfırlama, satın alma, sahip olunan eşyayı giydirip çıkarma ve profil bazlı kombin kaydetme/uygulama/silme bağlantıları eklendi. Önizleme sunucuya yazılmaz ve XP harcatmaz; satın alma XP/ownership kontrolünü mevcut API yürütür. Ekipman ve kombinler Aşama 1’de kurulan profil bazlı SQLite/API altyapısını kullanır.
- Yeni ekran metinleri `web/locales.json` üzerinden Türkçe/Rusça sağlanır. Ekran açıkken dil geçişiyle aksesuar adları, slotlar, butonlar ve kombin metinleri değişir.
- Değişen/eklenen dosyalar: `web/assets/cat-wearables.svg`, `web/cat-companion-ui.js`, `web/cat-companion-ui.css`, `web/index.html`, `web/locales.json`, `tests/test_cat_companion_ui.py`, `start-desktop.bat`, `README.md`, `DEVAM.md`. Başlatıcı `dist-stage29-cat-visual-stage2/CppAdventure/CppAdventure.exe` paketini öncelikli seçer.
- Hedefli otomatik testler: **5 geçti, 0 başarısız**. Katman dosyaları, fiyonk ölçeği, profil bazlı kombin çizimi, XP harcamayan istemci önizlemesi, ekipman API bağlantısı ve TR/RU metin anahtarları doğrulandı. `node --check web/cat-companion-ui.js` başarılı. Tam regresyon test koşum çıktısı: **97 geçti, 0 başarısız** (yaklaşık 167 saniye).
- PyInstaller Windows masaüstü paketi `dist-stage29-cat-visual-stage2/CppAdventure/CppAdventure.exe` altında yeniden oluşturuldu. Paket içindeki `cat-companion-ui.js`, `cat-companion-ui.css`, `cat-wearables.svg` ve `locales.json` varlığı kontrol edildi; paket yaklaşık 5.6 MB’lık başlatılabilir EXE ve `_internal` kaynak klasöründen oluşur. İki kullanılmayan `pycparser` tablosu için PyInstaller uyarıları kaydedildi; paket üretimini engellemedi. Bu aşama için ayrıca kurulum `.exe`’si üretilmedi.
- Paketlenmiş uygulama Windows masaüstü penceresinde açıldı ve `Kedi dükkânı` ekranı gerçek kullanıcı verisinden ayrı `Stage2 QA` test profiliyle incelendi. Başlık aksesuarı ile boyun atkısı aynı anda kedinin üzerinde görünür oldu; fiyonk gözleri kapatmadı. Türkçe ve Rusça mağaza metinleri aynı açık ekranda kontrol edildi. Deneme boyunca profil **0 XP** kaldı; hiçbir eşya satın alınmadı. Test penceresi kapatıldı.
- Geri dönüş noktası: `restore-points/stage29-cat-visual-stage2-before`. Güncel masaüstü paketi: `dist-stage29-cat-visual-stage2/CppAdventure/CppAdventure.exe`; başlatma: `start.bat` → `start-desktop.bat`.
- **Aşama 2 tamamlandı ve test edildi.** Bu aşama yalnızca görsel giyilebilir katmanlar/mağaza deneyimini kapsar. Level 1/2–5/6–10/11–15/16–20/21+ için ayrı fiziksel kedi modelleri ve level-up animasyonu henüz yapılmadı. Gerçek C++ çalışma izi, algoritma görselleştiricisi ve diğer Aşama 3/sonraki modüller de başlamadı. Sonraki kapsam, onay gelirse Aşama 3 — seviye bazlı fiziksel kedi gelişimi ve level-up animasyonudur.
