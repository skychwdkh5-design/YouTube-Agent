# IceCube production materials — 2026-11-06

Complete media ZIP: OA_IceCube_Production_Pack_2026-11-06.zip, saved in the conversation. SHA and exact media rights are in the ZIP. Attach ZIP to assembly session; no paid vidIQ calls authorized.


---
# FILE: README_RU.md
# IceCube — пакет материалов Orbital Atlas
Подготовлен 5 ноября 2026 для сборки 6 ноября (Вьетнам).

## Что готово
- SCRIPT_EN.md: английский сценарий, 792 слова. VOICE_ONLY.txt: чистый текст для Adam.
- EDIT_PLAN.md: 57 монтажных событий на предварительной сетке 5:42; живое видео, движение и научные схемы, указания звука и камеры.
- media/: реальные скачанные видео и фото; 4 собственные анимации по 18 секунд, 1080p30.
- graphics/: исходник схем и ключевые кадры, черновик обложки.
- SOURCES_AND_FACTS.md: научные источники и фактчек.
- MEDIA_RIGHTS.md: точные источники и условия использования, исключённые материалы.
- PACKAGING.md: 3 концепции названия/обложки, выбранная подача и описание.
- CLAUDE_HANDOFF_RU.md: короткое задание для сборки без повторного исследования и расхода vidIQ.
- ASSET_MANIFEST.json: SHA-256, размеры, кодеки и длительности скачанных/отрендеренных материалов.
- research/: локальные копии источников, лицензий и контактный лист реальной съёмки.

## Реальная готовность
Это производственный пакет материалов, НЕ финальный смонтированный и озвученный выпуск. Adam не генерировался, SRT по аудио пока нет, публикация не запускалась. Дополнительные композиты из плана ещё нужно собрать. Четыре A-клипа отрендерены; простые схемы служат объяснению и не заменяют весь видеоряд.

V01 — 4:15 живой антарктической съёмки, не IceCube construction. V02–V04 — NASA scientific visualizations. P01 — настоящее фото IceCube, CC BY-SA 4.0. P02 — настоящий оптический модуль, CC BY 4.0. Сохранить условия лицензий. Если не выполнять ShareAlike для P01, использовать собственную схему A01 вместо неё; фильм от этого не блокируется.

Основная история: видимая лаборатория → массив подо льдом → редкая частица → как построили → как работает световой след → событие 2017 и совместный поиск → обратно к льду. Никаких обещаний просмотров. Конкурентный сигнал исторический, не прогноз. vidIQ на этот пакет: 0 новых вызовов.

## Быстрый старт
Распаковать всё, отдать Claude CLAUDE_HANDOFF_RU.md вместе с папкой. Сначала использовать готовые медиа; не покупать повторно данные или генерации. При переносе на другой компьютер пути относительные. Свежесть источников и лицензий зафиксирована на дату подготовки.

---
# FILE: CLAUDE_HANDOFF_RU.md
# Задание на сборку IceCube — Orbital Atlas

Собери один английский Long из приложенного пакета. Тема утверждена Егором: IceCube под Антарктидой. Не возвращайся к Artemis и не запускай выбор темы заново. Не трать ни одного кредита vidIQ. Не запускай новые research/thumbnail/script scoring вызовы. Все необходимые научные источники, метаданные и материал собраны. Старые бюджеты не разрешают расходы.

Прочитай README_RU.md, SCRIPT_EN.md, EDIT_PLAN.md, MEDIA_RIGHTS.md. Проверь ASSET_MANIFEST.json. Используй существующий монтажный стек репозитория. Никаких новых движков, R&D-веток и серии тестовых роликов. Номер эпизода определить по текущему состоянию репозитория; не назначать автоматически EP010, если он уже занят.

План: единая озвучка Adam из VOICE_ONLY.txt → выровнять сцены по голосу → собрать полный ролик → проверить и исправить финальный монтаж. Если в текущей сессии уже есть действующее разрешение на платную озвучку — используй его в пределах разрешения. Если такого разрешения нет, не покупай озвучку молча: подготовь полный монтаж и точный список оставшегося, не выдавай временный голос за Adam. Перед генерацией искать существующую озвучку этого текста по хэшу, повторно не покупать.

Анимации A01–A04 уже есть в media/. Это объяснительные схемы, не заставки для всего ролика. Чередуй их с живыми кадрами. Дополнительные композиты плана — монтаж существующих элементов, а не повод создавать новую библиотеку анимации. Сценарий 792 слова, ожидаемые ~5:42 с паузами; не раздувать хронометраж.

Научная точность: 5,160 и 86 — исходный глубинный массив, не новый общий итог 2026 года. Не добавлять Нобелевку, «быстрее света в вакууме», секретные базы и бункеры. NASA B-roll — 88-South Traverse, не бурение IceCube. Fermi видит gamma rays. У события есть угловая неопределённость; источник не вычисляется со стопроцентной точностью по одной вспышке.

Выполнить требования CC BY/CC BY-SA и NASA из MEDIA_RIGHTS.md. Если P01 нельзя использовать с соблюдением ShareAlike, заменить её собственным A01, а не останавливать сборку и не брать NC-галерею. Не переносить музыку из источников.

Критерии сдачи: полный 1080p30 ролик; понятный хук и раскрытие массива в первые 12с; ни одного плейсхолдера; минимум 30% живой съёмки и 45% действующей анимации/визуализации, максимум 25% фото; no slideshow; плавное воспроизведение; достоверные подписи; разборчивый голос; финальный MP4, thumbnail, SRT по реальному аудио, описание с источниками/атрибуцией, короткий честный QC. Измерить доли по таймлайну, не заявлять их на глаз.

Не публиковать и не менять расписание канала в рамках этого задания: задача — готовый ролик для просмотра. Не писать «готово», если осталась озвучка, отсутствует медиа или не проверены права. Сдать то, что реально собрано, с точными оставшимися блокерами.

---
# FILE: SCRIPT_EN.md
# IceCube — English narration master

Voice: Adam. Target delivery 140–150 words/minute, calm but urgent; pauses at reveals. Exact timing must follow recorded voice, not be forced to this draft grid. Read only the paragraphs below, not headings or source IDs. Pronunciation: IceCube = ice cube; neutrino = noo-TREE-no; Cherenkov = chuh-REN-koff; blazar = BLAY-zar; TXS 0506+056 = T X S, zero five zero six, plus zero five six.

## 01 — The surface is misleading [S01, S02]

At the South Pole, this building hides the scale of what is underneath it. Below the snow, thousands of light sensors are frozen into a cubic kilometer of Antarctic ice. Together, they form IceCube: an observatory built to catch particles from space.

But this telescope has no giant mirror. And the particles it is waiting for usually pass straight through matter. So why build it here? And how do you bury an instrument this large without excavating the ice?

## 02 — Reveal the instrument [S01, S02]

Start at the surface, then go down. The original deep array begins about fourteen hundred and fifty meters below the ice and extends to roughly twenty-four hundred and fifty meters. Eighty-six cables carry five thousand, one hundred and sixty optical modules.

That is the original detector, completed in twenty ten. The illustration shows its scale, not every sensor's exact position. The building above is only the visible part. The detector includes the ice itself.

## 03 — Why the target is so difficult [S03, S04]

Neutrinos are electrically neutral particles with extremely small masses. They interact so rarely that enormous numbers pass through us unnoticed. IceCube's own fact sheet puts that number at about a hundred trillion every second.

For a detector, that creates an unusual problem. A particle can cross your instrument and leave absolutely nothing to record. Making the target larger increases the opportunity for one of those rare interactions. Here, the target is an enormous volume of clear, stable ice.

So the challenge is not simply seeing deeper into space. It is catching a messenger that normally refuses to stop.

## 04 — How to build it [S04, S05]

To install the sensors, teams used hot water to melt deep holes into the ice. They lowered cables of optical modules into those holes, then let the water freeze around them.

Imagine the sequence in reverse. A buried sensor leads up to a cable. The cable leads to a hole. And that hole had to be made from the surface, through more than two kilometers of ice.

Construction took place over Antarctic summer seasons between twenty oh four and twenty ten. The original deep array ended up with eighty-six strings, each holding sixty modules. The multiplication is simple. Building the result at the South Pole was not.

There is no underground hall surrounding this instrument. The sensors are frozen into the material they use to detect particles.

## 05 — What a detection actually means [S06, S07]

Now follow one neutrino into the detector. Usually, nothing happens. Occasionally, it interacts and produces charged particles. Those secondary particles can emit a faint blue light called Cherenkov radiation as they travel through the ice.

They can move faster than light travels in ice. That does not mean they break the speed limit of light in a vacuum.

The sensors record the arriving light. Their timing and positions allow scientists to reconstruct the event. For a track-like event, the pattern helps estimate the direction of the incoming neutrino.

The glowing dots in this animation are a diagram of detector responses. They are not a camera watching a giant beam shine underground. The colors indicate the order in which light reaches sensors.

That distinction matters. IceCube does not take an ordinary photograph of a neutrino. It reconstructs an encounter from the light left behind.

## 06 — A message and a direction [S08, S09]

In twenty thirteen, IceCube announced evidence for a population of high-energy neutrinos from beyond our solar system. That established a new way to study the universe. But finding a population is different from identifying a particular source.

Then, on September twenty-second, twenty seventeen, IceCube detected a high-energy event and sent an alert to astronomers. Its reconstructed direction narrowed the search to a region of sky.

Other observatories checked that region. NASA's Fermi telescope found that a known blazar, called T X S zero five zero six, plus zero five six, was unusually active in gamma rays.

A blazar is an active galaxy with a powerful jet pointed roughly toward us. The neutrino direction and the light observations together provided evidence linking the event to that source. The finding was announced in twenty eighteen.

This was a coordinated investigation, not IceCube identifying a distant black hole from one flash alone. One instrument supplied the particle clue. Others supplied the light.

## 07 — Return to the ice [S10, S01]

That is why the location matters. At the surface, Antarctica looks like a place that hides things. Here, its clear ice becomes part of an instrument for revealing them.

The original array is also a baseline, not the end of the project. IceCube reported a major upgrade deployment in twenty twenty-six. That is separate from the original five thousand, one hundred and sixty modules shown earlier.

Return to that small building on the snow. Now picture the cables descending beneath it, and a volume of ice waiting for a rare interaction. Most particles pass without a trace. A few leave enough light to begin a search across the sky.

---
# FILE: SOURCES_AND_FACTS.md
# Sources and fact check — checked 2026-11-05, Vietnam

Primary sources only for science. Competitor titles are demand clues, not scientific sources. No Nobel claim, alien claim, parallel-universe claim, "largest telescope" superlative, or current world's-most-energetic-neutrino claim is in the script.

| ID | Primary source | Supports | Script section |
|---|---|---|---|
| S01 | https://icecube.wisc.edu/science/icecube/ | Original array: 5,160 DOMs, 86 strings, 1,450–2,450 m, cubic-km volume; secondary-particle light | 01,02,07 |
| S02 | https://gcn.nasa.gov/missions/icecube | Location, detector design, completed Dec 2010, reconstruction and real-time alerts | 01,02 |
| S03 | https://icecube.wisc.edu/about-us/faq/ | Neutral, nearly massless particles; source messengers, interactions | 03 |
| S04 | https://icecube.wisc.edu/about-us/facts/ | Approx 100 trillion neutrinos/body/second; clear ice; construction 2004–2010, hot-water drill | 03,04 |
| S05 | https://icecube.wisc.edu/about-us/icecube10/timeline/ | Hot-water drilling, deployment and completion history | 04 |
| S06 | https://masterclass.icecube.wisc.edu/en/icecube-and-neutrinos/detecting-neutrinos/ | Charged secondary, Cherenkov light, track/cascade distinction | 05 |
| S07 | https://icecube.wisc.edu/science/icecube/ | Timing, digitization and direction reconstruction | 05 |
| S08 | https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.113.101101 | 2013 astrophysical flux; distinguish population from point-source identification | 06 |
| S09 | https://gcn.nasa.gov/missions/icecube and https://www.nasa.gov/news-release/nasas-fermi-traces-source-of-cosmic-neutrino-to-monster-black-hole/ | 2017 event, Fermi followup, blazar association; 2018 announcement | 06 |
| S10 | https://icecube.wisc.edu/news/press-releases/2026/02/the-icecube-neutrino-observatory-gets-a-major-upgrade-beneath-the-ice/ | Upgrade deployed 2026; do not call original 5,160 modules current total | 07 |

86 × 60 = 5,160 applies to original deep array, not every sensor across IceTop and upgrades.
Cherenkov: secondary charged particle faster than light in ICE; never faster than c in vacuum.
Reconstruction: do not render a perfectly precise line to an object as if no directional uncertainty existed. Draw an uncertainty cone; an alert identifies a region, not a guaranteed source.
Detector animation: schematic geometry, not actual surveyed positions or genuine recorded event data. Visible particle paths and time are greatly enlarged/slowed for explanation.
Blazar clips are scientific visualizations, not live camera images of the 2017 event.
Antarctic traverse footage is real field footage near 88°S, not IceCube drilling or deployment. Keep this distinction visible when used.

## Historical competitive evidence, not current analytics
Saved NEXORA PR #13: https://github.com/skychwdkh5-design/NEXORA/pull/13
Chris Pattison IceCube example: screenshot ~250K views, vidIQ badge 13×. Offline channel-median calculation in saved report ~40.09× (250,273 / 6,243). Different definitions, not interchangeable. Does not predict OA views. No further paid lookup authorized.
