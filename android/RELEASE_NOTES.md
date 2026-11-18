# SigmaNG 14.4 — Android Client Version (1.16.4)

نسخة **SigmaNG** المعدّلة لتعمل على أندرويد عبر **Fold Craft Launcher (FCL)** مع عارض **GL4ES** أو **Krypton Wrapper (NG-GL4ES)** المعدّل — بنظام **Client Version** مستقل على ماينكرافت **1.16.4**.

- الملفات: `SigmaNG-Android-14.4.jar` (العميل الكامل) + `SigmaNG-Android-14.4.json` (ملف الإصدار).
- المصدر: https://github.com/t86952356-eng/SigmaNG
- البناء يتم تلقائياً عبر GitHub Actions في هذا المستودع.

---

## ما الجديد في 14.4 (إصلاح كراش القائمة الرئيسية)

**إصلاح عاجل لكراش مرحلة "لوجو Mojang / القائمة الرئيسية" الذي ظهر في 14.3:**

```
java.lang.IllegalStateException: Shader (35632) failed to compile!
	at ...utils.render.ShaderUtil.createShader
	at ...utils.render.blurs.JelloBlur.<clinit>
	at ...gui.mainmenu.SelectAddonsGUI.draw   ← كراش عند أول إطار للقائمة
```

**السبب:** شيدرات البلبور/التدرجات في العميل مكتوبة بـ GLSL سطح-مكتب (110/120). عارض **Holy-GL4ES** يقدّم OpenGL 2.1/GLES2 فقط، فتفشل ترجمة الشيدر — والفشل كان يُرمى كاستثناء غير ملتقط من المُهيّئ الثابت للكلاس = `ExceptionInInitializerError` = كراش فوري. **الأخطر: نفس هذه الكلاسات يستخدمها الـ ClickGUI والـ HUD داخل اللعبة** — أي أن الكراش كان سيحدث ثانية داخل اللعبة على هذا العارض.

**الإصلاح (تدهور رشيد بدل الكراش):**
- `ShaderUtil` لم يعد يرمي أبداً: أي فشل (تجميع/ربط/غياب GL) يحوّله لوضع no-op ويطبع رسالة واحدة في اللوج.
- البلبور/البloom (JelloBlur/Bloom): يتخطى نفسه تلقائياً على العارضات التي لا تدعم الشيدرات.
- التدرجات والمستطيلات الدائرية (Gradient/RoundedRectShader): ترسم **بديلاً لونياً ثابتاً** (بدون تدرج/تدوير زوايا) بدل الانهيار.
- القائمة الرئيسية نفسها **لم تُحذف ولم تتغير** — كل عناصرها مرسومة بمستطيلات عادية تعمل على أي عارض؛ فقط تأثير البلبور يُعطَّل على العارضات الضعيفة.
- ClickGUI وHUD **لم يُلمس كودهما إطلاقاً** — الإصلاح في طبقة الشيدر المشتركة تحتهما، وهو ما يمنع نفس الكراش داخل اللعبة.

**نصيحة للحصول على التأثيرات كاملة (بلبور + تدرجات):** استخدم عارض **Krypton Wrapper (NG-GL4ES)** الذي يقدّم GL 3.1 — عليه تُجمَّع الشيدرات وتعمل كل التأثيرات. مع Holy-GL4ES (GL 2.1) سيعمل العميل الآن بثبات لكن بدون تأثيرات الشيدر.

الحجم كما هو: **~79.7 MB**. لا تغيير في أي موديول أو ثيم أو أصول واجهة.

---

## التثبيت على Fold Craft Launcher (FCL)

### 1) تجهيز FCL
1. حمّل FCL من المستودع الرسمي: https://github.com/FCL-Team/FoldCraftLauncher
2. شغّل FCL مرة واحدة واتركه ينزّل مكوّناته (Java Runtime).

### 2) تركيب النسخة
1. حمّل `SigmaNG-Android-14.4.json` و `SigmaNG-Android-14.4.jar` من هذا الـ Release.
2. اذهب إلى مجلد اللعبة في FCL (الإعدادات ← مسار اللعبة).
3. أنشئ مجلداً: `versions/SigmaNG-Android-14.4/`
4. ضع داخل الملفين بالاسمين **تماماً كما هما**:
   - `versions/SigmaNG-Android-14.4/SigmaNG-Android-14.4.json`
   - `versions/SigmaNG-Android-14.4/SigmaNG-Android-14.4.jar`
   - (يكفي وضع ملف JSON وحده؛ سيقوم FCL بتنزيل الجار تلقائياً من هذا الـ Release عند أول تشغيل.)
   - من ثبت النسخة السابقة (14.3): احذف مجلد `versions/SigmaNG-Android-14.3/` القديم بعد التثبيت.
5. أعد فتح قائمة الإصدارات في FCL وستظهر النسخة باسم **SigmaNG-Android-14.4**.

### 3) إعدادات التشغيل المهمة
- **Java Runtime**: اختر **Java 17** (أو أحدث — الكود مترجم بمستوى Java 17، لن يعمل على Java 8).
- **الذاكرة (RAM)**: 2–3 GB على الأقل (الجار ~76 MB).
- **العارض (Renderer)**:
  - الخيار الأول الموصى به: **Krypton Wrapper (NG-GL4ES)** — يقدّم GL 3.1 فتعمل كل تأثيرات الشيدر (بلبور/تدرجات):
    1. حمّل إضافة العارض: https://github.com/BZLZHH/NGG-FCLRendererPlugin
    2. ثبّتها في FCL (الإعدادات ← الإضافات/Plugins ← تثبيت من ملف APK).
    3. اختر العارض Krypton من قائمة العارضات قبل التشغيل.
  - الخيار الثاني: **Holy-GL4ES** أو **GL4ES** المدمج — يعمل الآن بثبات مع 14.4 لكن بدون تأثيرات الشيدر (ألوان ثابتة بدل البلبور/التدرجات).
- عند أول تشغيل سيقوم FCL بتنزيل الأصول (assets) الرسمية لـ 1.16.4 (~330 MB) من سيرفرات Mojang.

### 4) تشغيل
اختر نسخة `SigmaNG-Android-14.4` ← سجّل دخولك بحسابك (تُدار الحسابات من FCL نفسه) ← اضغط تشغيل.

---

## ما الذي عُدّل من أجل أندرويد؟

هذه البنية ("Client Version") تجعل العميل نسخة ماينكرافت مستقلة كاملة، بدون الحاجة إلى Fabric أو Forge. التعديلات الجراحية فقط — **لم يتم تعديل أي موديول من موديولات العميل**:

| التعديل | السبب |
| --- | --- |
| تعطيل Discord RPC على أندرويد (`-Dsigma.android=true`) | مكتبة junixsocket تحمّل natives سطح مكتب فقط → كانت ستسبب كراشاً عند الإقلاع |
| عدم إيقاف العميل عند فشل تحميل شاشة الخريطة المصغّرة | كان `RuntimeException` يوقف كل شيء إذا تعذّر قراءة ملفات Xaero |
| حذف تنزيل وتشغيل `yt-dlp.exe` (ميزة تنزيل الموسيقى) كاملاً من السورس | ملف تنفيذي خاص بويندوز لا يعمل على أندرويد |
| حذف نوافذ Swing لمشغل MP3 من السورس | نافذة سطح مكتب لا تُعرض على أندرويد أصلاً |
| تحمّل فشل تهيئة شيدرز البلور | درايفرات GL4ES قد تفشل في تجميع الشيدر → كان يسبب `RuntimeException` عند الإقلاع؛ الآن يتم تعطيل البلور فقط والاستمرار |
| دمج كل المكتبات داخل جار واحد بدون LWJGL | FCL/Pojav يحقنان نسخة LWJGL الخاصة بهما (3.3.x) أولاً في الـ classpath ويوفران الـ natives — يجب ألا تُحجب |
| (14.4) احتواء فشل ترجمة أي شيدر بدل رمي استثناء | عارضات GLES2 (Holy-GL4ES) لا تترجم GLSL 110/120 — الفشل أصبح تعطيلاً رشيقاً للتأثير مع بديل لوني، لا كراشاً في القائمة أو داخل اللعبة |

## ملاحظات
- إصدار ماينكرافت الأساسي: **1.16.4** (يظهر كإصدار مستقل).
- حسابات Microsoft/الإضافة تُدار من الـ Launcher (آلية المصادقة الرسمية) — لم يتم تجاوز أي نظام تحقق.
- شيدرز OptiFine: تعمل مع العارضات المتقدمة (Krypton Wrapper/Zink) بدرجات متفاوتة؛ الرسم الافتراضي يعمل مع GL4ES.
- آثار الأعطال تظهر بدون أرقام أسطر (نتيجة `-g:none` لتقليل الحجم) — لا يؤثر على اللعب.

---

## English summary

SigmaNG (Minecraft 1.16.4, full-source client) packaged as a standalone **Client Version** for **Fold Craft Launcher** on Android, with **GL4ES** (built-in) or the modified **Krypton Wrapper / NG-GL4ES** renderer (https://github.com/BZLZHH/NG-GL4ES, plugin: https://github.com/BZLZHH/NGG-FCLRendererPlugin).

**v14.4 hotfix** — fixes the 14.3 main-menu crash (`IllegalStateException: Shader (35632) failed to compile!` in `JelloBlur.<clinit>` via `SelectAddonsGUI.draw`): the client's blur/gradient shaders are desktop GLSL 110/120, which GLES2-class renderers (Holy-GL4ES advertising GL 2.1) cannot compile; the failure escaped a static initializer as `ExceptionInInitializerError` and killed the game at the first menu frame. Since the very same shader classes back the in-game ClickGUI and HUD, the identical crash would have re-appeared in-game. Fix: ShaderUtil constructors never throw anymore (compile/link/missing-GL failures switch the instance to a no-op mode with a single log line), JelloBlur/Bloom skip themselves when unusable, Gradient/RoundedRectShader fall back to flat color fills, and blur framebuffers are created lazily. The custom main menu is untouched (all its elements are plain rects that render on any GL) — only the shader effects degrade on weak renderers. ClickGUI/HUD code untouched. For full effects (blur/gradients) use the Krypton Wrapper renderer (GL 3.1); on Holy-GL4ES/GL2.1 the client now runs stable with flat fallbacks. Verified by CI smoke test `android/ProbeShader.java` reproducing the exact crash path: published 14.3 jar fails with the uncaught constructor error; 14.4 jar initializes all 7 shader classes cleanly and blurs are safe no-ops. Zero module/theme/asset changes; jar stays ~79.7 MB.

Install: place `SigmaNG-Android-14.4.json` (+ optional `SigmaNG-Android-14.4.jar`) into `<game dir>/versions/SigmaNG-Android-14.4/`, pick **Java 17** runtime, pick a GL4ES-family renderer, launch. No game modules were modified.
