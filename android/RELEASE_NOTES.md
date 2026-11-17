# SigmaNG 14.3 — Android Client Version (1.16.4)

نسخة **SigmaNG** المعدّلة لتعمل على أندرويد عبر **Fold Craft Launcher (FCL)** مع عارض **GL4ES** أو **Krypton Wrapper (NG-GL4ES)** المعدّل — بنظام **Client Version** مستقل على ماينكرافت **1.16.4**.

- الملفات: `SigmaNG-Android-14.3.jar` (العميل الكامل) + `SigmaNG-Android-14.3.json` (ملف الإصدار).
- المصدر: https://github.com/t86952356-eng/SigmaNG
- البناء يتم تلقائياً عبر GitHub Actions في هذا المستودع.

---

## ما الجديد في 14.3 (إصلاح كراش الإقلاع)

**إصلاح عاجل لكراش الإقلاع الذي ظهر في 14.2 على الأجهزة:**

```
java.lang.NoClassDefFoundError: org/yaml/snakeyaml/constructor/BaseConstructor
	at ...vialoadingbase.platform.ViaVersionPlatformImpl.<init>
	...
	at info.sigmaclient.sigma.SigmaNG.initClient
```

**السبب:** عند تخفيف الحجم في 14.2 استُبعد جار `snakeyaml` باعتباره "غير مستخدم" لأن لا شيء في سورس العميل يستورده — لكن **جارات ViaVersion نفسها** (نظام تعدد الإصدارات داخل العميل) تعتمد عليه داخلياً (تبعية مكتبة-لمكتبة لا تظهر في فحص السورس). وعلى الجهاز يعمل العميل بجار واحد فقط في الـ classpath، فأي مكتبة مفقودة = كراش فوري.

**الإصلاح:** أُعيد دمج `snakeyaml` كاملاً (+0.3 MB فقط). كذلك أُعيد تدقيق **كل** الجارات المستبعدة العشرة الأخرى بفحص أعماق الـ bytecode (constant-pool) لكل الكلاسات المدمجة — كلها مؤكدة الآمان:
- `jna`/`platform`: كل مستدعيها إما محمي بـ try-catch (ناريتور النظام، معلومات CPU) أو لا يُحمَّل أصلاً على أندرويد (مسارات oshi الويندوزية).
- `joda-time`: يُسجَّل في fastjson خلف `Class.forName` محمي.
- `junixsocket`: يُستخدم فقط في Discord RPC وهو معطَّل على أندرويد أصلاً.

الحجم بقي خفيفاً: **~79.7 MB** (مقابل 79.4 في 14.2 و 109.2 في 14.1). لا يزال **دون أي تعديل على الثيم أو الواجهة أو الرسم أو الموديولات** (`git diff` على `src/` فارغ تماماً).

ملاحظة ناتجة عن `-g:none` (موجودة منذ 14.2): آثار الأعطال (stack traces) تظهر بدون أرقام الأسطر — سلوك اللعب والواجه غير متأثر إطلاقاً.

---

## التثبيت على Fold Craft Launcher (FCL)

### 1) تجهيز FCL
1. حمّل FCL من المستودع الرسمي: https://github.com/FCL-Team/FoldCraftLauncher
2. شغّل FCL مرة واحدة واتركه ينزّل مكوّناته (Java Runtime).

### 2) تركيب النسخة
1. حمّل `SigmaNG-Android-14.3.json` و `SigmaNG-Android-14.3.jar` من هذا الـ Release.
2. اذهب إلى مجلد اللعبة في FCL (الإعدادات ← مسار اللعبة، غالباً `Android/data/com.fcl.konan/files/.minecraft` أو المجلد الذي اخترته).
3. أنشئ مجلداً: `versions/SigmaNG-Android-14.3/`
4. ضع داخل الملفين بالاسمين **تماماً كما هما**:
   - `versions/SigmaNG-Android-14.3/SigmaNG-Android-14.3.json`
   - `versions/SigmaNG-Android-14.3/SigmaNG-Android-14.3.jar`
   - (يكفي وضع ملف JSON وحده؛ سيقوم FCL بتنزيل الجار تلقائياً من هذا الـ Release عند أول تشغيل إذا وضعت الـ JSON فقط.)
   - من ثبت النسخة المعطوبة (14.2): احذف مجلد `versions/SigmaNG-Android-14.2/` القديم بعد التثبيت.
5. أعد فتح قائمة الإصدارات في FCL وستظهر النسخة باسم **SigmaNG-Android-14.3**.

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
اختر نسخة `SigmaNG-Android-14.3` ← سجّل دخولك بحسابك (تُدار الحسابات من FCL نفسه) ← اضغط تشغيل.

---

## ما الذي عُدّل من أجل أندرويد؟

هذه البنية ("Client Version") تجعل العميل نسخة ماينكرافت مستقلة كاملة، بدون الحاجة إلى Fabric أو Forge. التعديلات الجراحية فقط — **لم يتم تعديل أي موديول من موديولات العميل**:

| التعديل | السبب |
| --- | --- |
| تعطيل Discord RPC على أندرويد (`-Dsigma.android=true`) | مكتبة junixsocket تحمّل natives سطح مكتب فقط → `UnsatisfiedLinkError` (خطأ غير ملتقط) كان سيسبب كراش عند الإقلاع |
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

**v14.3 hotfix** — fixes the 14.2 startup crash `NoClassDefFoundError: org/yaml/snakeyaml/constructor/BaseConstructor` in `ViaVersionPlatformImpl.<init>`: snakeyaml was excluded from the fat jar in 14.2 because nothing in the client source imports it, but ViaVersion's own bundled jars reference it internally (lib-to-lib dependency invisible to a source-level audit). It is merged again (+0.3 MB only). All ten remaining excluded jars were re-audited with a constant-pool scan of every merged class (android/audit_exclusions.py): jna/platform (all callers try-catch-Throwable or never loaded on Android), joda-time (guarded `Class.forName` in fastjson), junixsocket (Discord RPC, disabled on Android) — all verified safe. Jar stays slim at ~79.7 MB (79.4 MB in 14.2, 109.2 MB in 14.1). Zero source changes — themes, UI, visuals and modules untouched.

Install: place `SigmaNG-Android-14.3.json` (+ optional `SigmaNG-Android-14.3.jar`) into `<game dir>/versions/SigmaNG-Android-14.3/`, pick **Java 17** runtime, pick a GL4ES-family renderer, launch. Android-specific hardening: Discord RPC disabled via `-Dsigma.android=true`, yt-dlp removed, minimap load and blur-shader failures made non-fatal, LWJGL excluded from the fat jar (launcher injects its own). No game modules were modified.
