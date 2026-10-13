# Upload as a PRIVATE draft (no integration available)
No YouTube upload connector is attached to this session (only Google Calendar and Google Drive), so nothing was uploaded.

1. Get the master (repo `skychwdkh5-design/YouTube-Agent`, branch `media/ep002-dubai-final`, folder `ep002/final_v41/`):
   `git clone --branch media/ep002-dubai-final --single-branch <repo-url> media && cd media/ep002/final_v41 && cat parts/ep002_final_v41.mp4.part* > ep002_final_v41.mp4 && sha256sum ep002_final_v41.mp4`
   expected: 504412b34925974517eea4b34462c616e86237996b5521fa24297cb53adfe7d8
2. YouTube Studio -> Create -> Upload videos -> choose `ep002_final_v41.mp4`.
3. Title: `How Dubai Built Islands Where There Was Only Sea` (48 characters).
4. Description: paste `description.txt` as is (the chapter block starts at 0:00, 16 chapters, each >= 15 s; YouTube builds chapters automatically).
5. Thumbnail: upload `thumbnail_1280x720.jpg`.
6. Audience: "No, it's not made for kids". Altered/synthetic content question: answer after reading the current wording (see COPYRIGHT_CHECK.md).
7. More options: Category = Education; Video language = English; Tags = `tags.txt`; Captions: Subtitles -> Add language English -> Upload file -> With timing -> `ep002_en.srt`.
8. Visibility: **Private**. Do not use Publish, Schedule or Premiere. Wait for the owner's command.
9. Before publishing: confirm the ElevenLabs plan allows commercial use (COPYRIGHT_CHECK.md).
