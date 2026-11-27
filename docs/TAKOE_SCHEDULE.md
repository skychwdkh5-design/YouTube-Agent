# «Такое бывает»: очередь публикаций по расписанию

Workflow `YouTube schedule — Такое бывает` (`.github/workflows/youtube-schedule-takoe.yml`), код
`.claude/skills/yt-publish/takoe_schedule.py` на базе общего `publish.py`.

- Источник: ANIMAVERSE, релиз или ветка (`media_ref`) с `youtube/takoe/youtube-queue.json` и MP4; читается секретом
  `ANIMAVERSE_RELEASE_READ_TOKEN`. SHA-256 каждого файла сверяется с очередью.
- Авторизация: `ANIMAVERSE_YT_CLIENT_ID/SECRET/REFRESH_TOKEN`. Перед записью `channels.list(mine=true)` должен вернуть ровно
  `UCOakEPBhSGwx-2RV0dKGdNA`. Токен и очередь Orbital Atlas (`YT_REFRESH_TOKEN`, `publish-data`) не используются.
- Режимы: `dry_run` (проверки и план слотов), `private_test` (одна приватная загрузка без publishAt, сверка канала,
  метаданных и статуса обработки), `schedule` (private + publishAt; тестовому видео ставится publishAt без повторной загрузки).
- Слоты: сетка 00:00, 02:00 … 22:00 по Asia/Ho_Chi_Minh; первый свободный слот не ближе 30 минут; дальше строго +2 ч.
  Уже запланированные на канале видео учитываются; если блок не помещается между ними, он идёт после последнего.
- Журнал: ветка `takoe-data`, `takoe/journal.jsonl` (id серии, sha256, videoId, publishAt, read-back). Повторный запуск
  не загружает файл, для которого в журнале уже есть videoId; незавершённая загрузка принимается только при единственном
  точном совпадении названия на канале, иначе серия пропускается.
- Выпуск считается запланированным только если API вернул privacyStatus=private, тот же publishAt и uploadStatus
  uploaded/processed. Ошибка API или неподтверждённое расписание останавливает пакет.
- Квота YouTube: videos.insert стоит 1600 единиц; при стандартной квоте 10 000/сутки за день проходит около 6 загрузок.
  При `quotaExceeded` пакет останавливается; повторный запуск после сброса (полночь по Тихоокеанскому времени) продолжит
  с очередного слота после последнего запланированного.
