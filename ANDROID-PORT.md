# SigmaNG Android Port — Audit & Change Log

## الهدف

تحويل سورس SigmaNG 14.1 (ماينكرافت 1.16.4، سورس كامل MCP-style مع OptiFine وBaritone وViaMCP)
إلى **Client Version** مستقل يعمل على أندرويد عبر **Fold Craft Launcher (FCL)** مع عارض
**GL4ES** أو **Krypton Wrapper (NG-GL4ES)**، وبناؤه على GitHub Actions ورفعه كـ Release
مع ملف JSON.

## جرد المشروع (قبل التعديل)

| المكوّن | المسار | التصنيف | ملاحظات أندرويد |
| --- | --- | --- | --- |
| سورس ماينكرافت 1.16.4 كامل | `src/net/minecraft` (3618 ملف) | CORE | يعمل كما vanilla على FCL |
| OptiFine HD U G5 مدمج | `src/net/optifine` | CORE | الرسم الافتراضي يعمل على GL4ES |
| Baritone | `src/baritone` (295) | CORE | Java خالص |
| ViaMCP / ViaVersion | `src/com/viaversion` + libs | CORE | Java خالص |
| كود العميل (modules/gui/...) | `src/info/sigmaclient` (546) | CORE | لم تُلمس الموديولات |
| Discord RPC | `sigma/DiscordRPC.java` | DESKTOP_ONLY | junixsocket natives سطح مكتب → كراش (Error غير ملتقط) |
| تنزيل يوتيوب | `sigma5/youtubedl` | DESKTOP_ONLY | `yt-dlp.exe` تنفيذي ويندوز |
| شيدرز البلور | `sigma5/utils/BlurUtils.java`, `Sigma5BlurUtils.java` | CORE (هشّ) | فشل التجميع على GL4ES كان يرمي RuntimeException عند الإقلاع |
| مكتبة LWJGL 3.3.4 (كل المنصات) | `libs/lwjgl*.jar` (161 ملف) | DESKTOP_ONLY | FCL يحقن LWJGL 3.3.x الخاص به أولاً — يجب استبعادها |
| Lombok | `libs/lombok-1.18.32.jar` | BUILD_ONLY | معالج تعليقات |
| بقية المكتبات (54 جار) | `libs/*.jar` | CORE | تُدمج داخل جار العميل |
| `Start.java` | `src/Start.java` | BUILD_ONLY | مشغّل بيئة التطوير — لا يدخل الجار النهائي |

## سلسلة التشغيل

```
FCL (Amethyst backend)
  ├─ يجهّز JRE 17 + AWT (caciocavallo, headless=false)
  ├─ يضع LWJGL 3.3.3 الخاص به أولاً في classpath
  ├─ يقرأ versions/SigmaNG-Android/SigmaNG-Android.json
  │    └─ mainClass = net.minecraft.client.main.Main
  │    └─ libraries = [org.lwjgl:lwjgl:3.2.2]  (لكشف جيل LWJGL فقط)
  │    └─ downloads.client = جار العميل الكامل (fat jar)
  │    └─ assetIndex 1.16 (أصول Mojang الرسمية — تشمل الأصوات)
  └─ يشغّل اللعبة مع -Dsigma.android=true
        └─ Minecraft ctor → ResourceLoadProgressGui
              ├─ SigmaNG.staticInitTitle() → DiscordRPC.load() [معطّلة على أندرويد]
              └─ SigmaNG.staticInit() → initClient()
                    ├─ minimap.load() [فشلها لم يعد قاتلاً]
                    ├─ ViaLoader / FontUtil / JelloFontUtil (خطوط AWT — تعمل عبر cacio)
                    ├─ moduleManager.init() [بدون أي تعديل]
                    ├─ BlurUtils.reInit() / Sigma5BlurUtils.initAll() [فشلها يعطّل البلور فقط]
                    └─ ...
```

## التعديلات (5 ملفات — لا يشمل أي موديول)

1. **`src/info/sigmaclient/sigma/DiscordRPC.java`**
   - `load()`: خروج مباشر إذا `-Dsigma.android=true`.
   - `connect()`: التقاط `Throwable` بدل `Exception` (لأن junixsocket يرمي
     `UnsatisfiedLinkError` وهو `Error` وليس `Exception`).
2. **`src/info/sigmaclient/sigma/SigmaNG.java`**
   - فشل `minimap.load()` يسجّل تحذيراً بدل `RuntimeException` يقتل الإقلاع.
3. **`src/info/sigmaclient/sigma/sigma5/youtubedl/YoutubeDownloader.java`**
   - `download()`: خروج مباشر على أندرويد (yt-dlp.exe تنفيذي ويندوز).
4. **`src/info/sigmaclient/sigma/sigma5/utils/BlurUtils.java`**
   - `reInit()`: التقاط `Throwable` + تصفير الحالات بدل الرمي.
   - `updateFrame()`/`blur()`: حماية null قبل استخدام الشيدر/الفرمبفر.
5. **`src/info/sigmaclient/sigma/sigma5/utils/Sigma5BlurUtils.java`**
   - `initAll()`: التقاط `Throwable` بدل الرمي، `vblur()`/`init()`: حماية null.

## الحذف الفعلي للمميزات الويندوزية/سطح-المكتبيّة (commit 2)

> مسح آلي لـ 546 ملف Java الخاص بالعميل (os.name / loadLibrary / ProcessBuilder /
> JNA / Registry / APPDATA / Robot / SystemTray / exe-dll-bat / مسارات C:\ ...)
> — النتيجة: السورس نظيف، لا يوجد سوى البنود التالية.

### ملفات محذوفة (5 — غير موجودة أصلاً في المستودع الآن)

| الملف | السبب |
| --- | --- |
| `music/statics/player/MP3PlayerThemeDefault.java` | نافذة Swing سطح مكتب (JButton/JCheckBox/JSlider) لمشغل MP3 — لا تُعرض على أندرويد |
| `music/statics/player/MP3PlayerTheme.java` | واجهة النافذة أعلاه — بقي بلا مستخدم |
| `sigma5/jellomusic/player/MP3PlayerThemeDefault.java` | نسخة JelloMusic من نافذة Swing نفسها |
| `sigma5/jellomusic/player/MP3PlayerTheme.java` | واجهتها — بقي بلا مستخدم |
| `sigma5/youtubedl/YoutubeDownloader.java` | تنزيل وتشغيل `yt-dlp.exe` (ثنائي ويندوز) عبر `Runtime.exec` |

### ملفات معدَّلة (3 — سطور معدودة، خارج الموديولات)

1. **`music/statics/player/MP3Player.java`** و**`sigma5/jellomusic/player/JelloMusic.java`**
   - `init()`: حُذف استدعاء `new MP3PlayerThemeDefault().apply(this)` (أصبح no-op موثّقاً).
   - التشغيل الصوتي نفسه (JavaLayer/`javax.sound` — جافا خالص) لم يُمس.
2. **`music/youtubedl/YoutubeVideoHelper.java`**
   - `playMusicFromLink()`: أصبح no-op مع سجل واضح (كان يستدعي `yt-dlp.exe`).
   - `getMp4Duration()`: حُذفت كلياً (كانت تستخدم JAVE = غلاف ثنائي ffmpeg سطح مكتب).
   - أُزيلت استيرادات `YoutubeDownloader` / `ClickGUI` / `JelloMusicPlayer` / `jave.Encoder`.
   - **بقي**: `fetchContentWithRedirect` و`downloadToFile` و`search` (HTTP خالص — تستخدمها ميزة الحسابات البديلة وميزة البحث عن الموسيقى، وتعمل على أندرويد).

### ما بقي محصّناً لا محذوفاً

- `DiscordRPC.java`: معطّل على أندرويد عبر `-Dsigma.android=true` (نسخة سطح المكتب من نفس المستودع تحتاجه).
- 160 جار LWJGL + `jinput` + `Start.java`: مستبعدة من جار أندرويد فقط (سكربت التغليف)، وتبقى في المستودع لمن يبني نسخة سطح المكتب.

### إثبات الالتزام بعدم لمس الموديولات

- `git diff --stat -- src/info/sigmaclient/sigma/modules/` → **فارغ** تماماً.
- نفس الشيء لـ `sigma5/killaura` و`sigma5/jelloportal` و`baritone`.
- `Music.download()` تحقّقت: HTTP خالص (`Resources.downloadTexture`) — لا exe ولا ffmpeg.

### ملاحظات توافق أندرويد (ليست ويندوزية — لا تُحذف)

- مشغل الموسيقى الصوتي يعتمد `javax.sound.sampled` — قد لا يُخرج صوتاً على بعض أجهزة أندرويد (قيد JVM لا كود ويندوز).
- نظام السكربتات (`sigma/scripts/`) يحتاج محرك Nashorn على JRE 17 (متوفر كجار مستقل إن لزم).

## البناء (GitHub Actions)

`.github/workflows/build-android.yml`:

1. JDK 17 (Temurin).
2. `javac --release 17` لكل 5626 ملف Java (بدون `Start.java`) مع Lombok كمعالج تعليقات.
   - (المستوى 17 إلزامي: موديولات العميل تستخدم صيغ Java 16+ مثل switch expressions
     وpattern matching — ولهذا يجب اختيار JRE 17 في FCL.)
3. `android/package_client.py`: جار واحد كامل = كلاسات المشروع + `assets/` + `data/`
   + 54 مكتبة مدموجة، **بدون** أي ملف LWJGL/lombok/sources/javadoc، مع دمج
   `META-INF/services` وحذف توقيعات `META-INF/*.SF|RSA|DSA`.
4. `android/generate_version_json.py`: يولّد JSON انطلاقاً من ملف 1.16.4 الرسمي
   (arguments/assetIndex/logging) + إدخال LWJGL واحد + رابط جار العميل من الـ Release.
5. رفع Release بالملفات: `SigmaNG-Android.jar` + `SigmaNG-Android.json` + دليل التثبيت.

## قرارات معمارية

- **لماذا fat jar واحد؟** backend الفئة (Pojav/FCL) يبني classpath من ملفات
  المكتبات الموجودة فعلياً ويتخطى المفقود منها؛ جار واحد كامل يلغي أي نقطة فشل
  تنزيل، ويتطلب من JSON مكتبة واحدة فقط (LWJGL للكشف).
- **لماذا إبقاء إدخال `org.lwjgl:lwjgl:3.2.2` في JSON؟** كود
  `Tools.generateLibClasspath` يرمي "Unable to determine LWJGL version" إن غاب.
- **لماذا استبعاد LWJGL من الجار؟** ترتيب classpath في FCL يضع LWJGL الخاص
  بالمشغّل أولاً؛ احتواء الجار على LWJGL 3.3.4 قد يحجب جسر العارض.
- **الأصوات؟** جار vanilla لا يحتوي أصواتاً أصلاً — تأتي من assetIndex (1.16)
  الذي ينزّله FCL تلقائياً من Mojang.

## ما تم التحقق منه

- ترجمة كاملة: 5626 ملف، 0 أخطاء (`--release 17` + Lombok).
- اختبار تشغيل محلي (headless): العميل يصل حتى تهيئة GLFW/OpenGL — أي أن كل
  الكلاسات والموارد تُحمّل بنجاح، ويتوقف فقط عند المكوّن الذي يوفره المشغّل
  على الجهاز (نافذة العرض).
- بنية الجار: لا LWJGL، لا توقيعات، services مدموجة، manifest صحيح.
- التشغيل الفعلي على جهاز أندرويد يتطلب المستخدم (لا يوجد جهاز في بيئة البناء).

## ما لم يتم تعديله عمداً

- موديولات العميل كاملة (`src/info/sigmaclient/sigma/modules/**`).
- ميزة حسابات Microsoft داخل العميل (HttpServer محلي — تعمل على أندرويد؛
  فتح المتصفح قد لا يعمل لكنه لا يسبب كراشاً).
- OptiFine وشيدرزها (تعمل حسب العارض المختار).
