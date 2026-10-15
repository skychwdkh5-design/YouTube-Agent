# EP003 - YouTube Studio upload checklist (the owner uploads; the agent never publishes)

Approved master: `media/ep003-gsl-final-v3`, join `cat final.mp4.part* > final.mp4`, check `sha256sum final.mp4` = b0b28c62d6f37c5e190418fa486e7e2be97f05965227dd195c6fb217f67456ce.
(Or upload `EP003_V3_review_1080p.mp4` only if the master cannot be joined - it is a smaller re-encode.)

1. Upload `final.mp4`. Visibility: Private or Unlisted first.
2. Title: `The Great Salt Lake Is Disappearing: 37 Years From Orbit`
3. Description: paste `release/description.txt` (chapters inside; first chapter 0:00).
4. Thumbnail: `release/thumbnail.jpg`.
5. Tags: paste `release/tags.txt`.
6. Subtitles: upload `captions/captions.srt` as English.
7. Audience: Not made for kids. Category: Education. Language: English.
8. Altered or synthetic content: the narration voice is AI-generated (ElevenLabs) - answer according to YouTube's current policy for synthetic voices.
9. Before going public: confirm your ElevenLabs plan allows commercial use of the narration (COPYRIGHT_CHECK.md).
10. Check the processed HD version plays (wait for 1080p processing), then set Public / schedule.
