# AGENTS.md

Shared instructions for Claude Code and Codex in this workspace.

## Contacts and phone calls ("call <name>")

- **Contact numbers live in Google Drive, not in this repo.** File: `CONTACTS.md` in MK's
  "My Projectless Folder" (Drive file id `1_eja74aWj7b62YnopA_oTElSes5d0G_E`,
  folder id `1xyyY-8-xboaZs42RD8HkwGGqfT2ehdBZ`). Look it up there first with the Google Drive
  connector (`search_files` with `title contains 'CONTACTS'`). Never ask MK for a number before checking it.
- Full calling setup and lessons learned: `PHONE-ME-SETUP.md` in the same Drive folder
  (file id `1izw5jAGRXxHHKh0xuyokDMHqKuT6RGdE`). It is `text/markdown`, so read it with
  `download_file_content` (base64), not `read_file_content`.
- In cloud sessions, `api.bland.ai` is connected through the proxy (no API key needed).
  `POST https://api.bland.ai/v1/calls` with `"from": "+18546664223"` works for UAE numbers
  (verified 2026-10-16).
- Call conventions: the assistant introduces itself as **Ashley** (voice id
  `b90310fb-3f1f-4c0b-a6ff-1a1a457d2da3`), never claims to be human, recording OFF (UAE consent law),
  leave a short voicemail if unanswered, and always show MK the full transcript afterwards.
- Lesson (2026-10-16): Bland's voicemail detection marked a live person (kids talking over each other)
  as voicemail, played the voicemail message twice and hung up. For family calls, leave out the
  `voicemail` block so the agent always talks to whoever answers, and put the request in the first sentence.
- Personal phone numbers stay in Drive CONTACTS.md, never in this repo.
- MK's time zone: Asia/Dubai (GST, UTC+4).
