# SigmaNG 14.2 — Android Client Version (1.16.4)

نسخة **SigmaNG** المعدّلة لتعمل على أندرويد عبر **Fold Craft Launcher (FCL)** مع عارض **GL4ES** أو **Krypton Wrapper (NG-GL4ES)** المعدّل — بنظام **Client Version** مستقل على ماينكرافت **1.16.4**.

- الملفات: `SigmaNG-Android-14.2.jar` (العميل الكامل) + `SigmaNG-Android-14.2.json` (ملف الإصدار).
- المصدر: https://github.com/t86952356-eng/SigmaNG
- البناء يتم تلقائياً عبر GitHub Actions في هذا المستودع.

---

## ما الجديد في 14.2 (تخفيف الحجم)

الجار أخفّ بنحو **27%** (من 109.2 MB إلى **79.4 MB**) — **دون أي تعديل على الثيم أو الواجهة أو الرسم أو الموديولات** (`git diff` على `src/` فارغ تماماً):

| التقنية | التأثير |
| --- | --- |
| حذف 11 جار مكتبات غير مستخدمة أو خاصة بسطح المكتب | ~10.4 MB |
| قصّ الكلاسات الميتة من fastutil/icu4j بتحليل الوصول (10,557 كلاساً محذوفاً؛ 1,691 مستخدَماً محفوظاً كاملاً) | ~18.5 MB |
| تجريد بيانات التصحيح من الكلاسات (`-g:none`) + ضغط أقصى (deflate 9) | الباقي |

الجارات المحذوفة (كلها بدون أي مرجع في السورس، أو ويندوزية خالصة): `jave` (غلاف ffmpeg — مات بعد إزالة yt-dlp)، `jna` + `platform`، `junixsocket` ×2، `joda-time`، `snakeyaml`، 3 جارات `google-api-services-*` غير المستخدمة، و`text2speech-natives-windows` (DLL ويندوز SAPI).

ملاحظة وحيدة ناتجة عن `-g:none`: آثار الأعطال (stack traces) ستظهر بدون أرقام الأسطر — سلوك اللعب والواجه غير متأثر إطلاقاً. الإصدار السابق `android-v14.1` يبقى متاحاً إن أردت التراجع.

---

## التثبيت على Fold Craft Launcher (FCL)

### 1) تجهيز FCL
1. حمّل FCL من المستودع الرسمي: https://github.com/FCL-Team/FoldCraftLauncher
2. شغّل FCL مرة واحدة واتركه ينزّل مكوّناته (Java Runtime).

### 2) تركيب النسخة
1. حمّل `SigmaNG-Android-14.2.json` و `SigmaNG-Android-14.2.jar` من هذا الـ Release.
2. اذهب إلى مجلد اللعبة في FCL (الإعدادات ← مسار اللعبة، غالباً `Android/data/com.fcl.konan/files/.minecraft` أو المجلد الذي اخترته).
3. أنشئ مجلداً: `versions/SigmaNG-Android-14.2/`
4. ضع داخل الملفين بالاسمين **تماماً كما هما**:
   - `versions/SigmaNG-Android-14.2/SigmaNG-Android-14.2.json`
   - `versions/SigmaNG-Android-14.2/SigmaNG-Android-14.2.jar`
   - (يكفي وضع ملف JSON وحده؛ سيقوم FCL بتنزيل الجار تلقائياً من هذا الـ Release عند أول تشغيل إذا وضعت الـ JSON فقط.)
   - من ثبت النسخة القديمة (14.1): احذف مجلد `versions/SigmaNG-Android/` القديم بعد التثبيت.
5. أعد فتح قائمة الإصدارات في FCL وستظهر النسخة باسم **SigmaNG-Android-14.2**.

### 3) إعدادات التشغيل المهمة
- **Java Runtime**: اختر **Java 17** (أو أحدث — الكود مترجم بمستوى Java 17، لن يعمل على Java 8).
- **الذاكرة (RAM)**: 2–3 GB على الأقل (الجار ~76 MB).
- **العارض (Renderer)**:
  - الخيار الأول: **GL4ES** (المدمج في FCL) — يعمل مع الرسم الافتراضي للعبة.
  - الخيار الثاني: **Krypton Wrapper (NG-GL4ES)** — عارض GL4ES معدّل يدعم شيدرز أحدث وأداء أفضل:
    1. حمّل إضافة العارض: https://github.com/BZLZHH/NGG-FCLRendererPlugin
    2. ثبّتها في FCL (الإعدادات ← الإضافات/Plugins ← تثبيت من ملف APK).
    3. اختر العارض Krypton من قائمة العارضات قبل التشغيل.
- عند أول تشغيل سيقوم FCL بتنزيل الأصول (assets) الرسمية لـ 1.16.4 (~330 MB) من سيرفرات Mojang.

### 4) تشغيل
اختر نسخة `SigmaNG-Android-14.2` ← سجّل دخولك بحسابك (تُدار الحسابات من FCL نفسه) ← اضغط تشغيل.

---

## ما الذي عُدّل من أجل أندرويد؟

هذه البنية ("Client Version") تجعل العميل نسخة ماينكرافت مستقلة كاملة، بدون الحاجة إلى Fabric أو Forge. التعديلات الجراحية فقط — **لم يتم تعديل أي موديول من موديولات العميل**:

| التعديل | السبب |
| --- | --- |
| تعطيل Discord RPC على أندرويد (`-Dsigma.android=true`) | مكتبة junixsocket تحمّل natives سطح مكتب فقط → `UnsupportedLinkError` (خطأ غير ملتقط) كان سيسبب كراش عند الإقلاع |
| عدم إيقاف العميل عند فشل تحميل شاشة الخريطة المصغّرة | كان `RuntimeException` يوقف كل شيء إذا تعذّر قراءة ملفات Xaero |
| حذف تنزيل وتشغيل `yt-dlp.exe` (ميزة تنزيل الموسيقى) كاملاً من السورس | ملف تنفيذي خاص بويندوز لا يعمل على أندرويد |
| حذف نوافذ Swing لمشغل MP3 من السورس | نافذة سطح مكتب لا تُعرض على أندرويد أصلاً |
| تحمّل فشل تهيئة شيدرز البلور (Jello/Sigma5 blur) | درايفرات GL4ES قد تفشل في تجميع الشيدر → كان يسبب `RuntimeException` عند الإقلاع؛ الآن يتم تعطيل البلور فقط والاستمرار |
| دمج كل المكتبات داخل جار واحد بدون LWJGL | FCL/Pojav يحقنان نسخة LWJGL الخاصة بهما (3.3.x) أولاً في الـ classpath ويوفران الـ natives — يجب ألا تُحجب |

## ملاحظات
- إصدار ماينكرافت الأساسي: **1.16.4** (يظهر كإصدار مستقل).
- حسابات Microsoft/الإضافة تُدار من الـ Launcher (آلية المصادقة الرسمية) — لم يتم تجاوز أي نظام تحقق.
- شيدرز OptiFine: تعمل مع العارضات المتقدمة (Krypton Wrapper/Zink) بدرجات متفاوتة؛ الرسم الافتراضي يعمل مع GL4ES.

---

## English summary

SigmaNG (Minecraft 1.16.4, full-source client) packaged as a standalone **Client Version** for **Fold Craft Launcher** on Android, with **GL4ES** (built-in) or the modified **Krypton Wrapper / NG-GL4ES** renderer (https://github.com/BZLZHH/NG-GL4ES, plugin: https://github.com/BZLZHH/NGG-FCLRendererPlugin).

**v14.2** slims the jar by **27%** (109.2 MB → 79.4 MB) with zero source changes: 11 unused/desktop-only library jars dropped (jave, jna+platform, junixsocket x2, joda-time, snakeyaml, 3 unused google-analytics jars, Windows SAPI DLLs), 10,557 never-referenced fastutil/icu4j classes removed via constant-pool reachability analysis (1,691 used classes fully preserved), `-g:none` and deflate level 9. Themes, UI, visuals and modules are untouched.

Install: place `SigmaNG-Android-14.2.json` (+ optional `SigmaNG-Android-14.2.jar`) into `<game dir>/versions/SigmaNG-Android-14.2/`, pick **Java 17** runtime, pick a GL4ES-family renderer, launch. Android-specific hardening: Discord RPC disabled via `-Dsigma.android=true`, yt-dlp removed, minimap load and blur-shader failures made non-fatal, LWJGL excluded from the fat jar (launcher injects its own). No game modules were modified.
