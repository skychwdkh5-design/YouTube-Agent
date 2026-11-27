#!/usr/bin/env python3
"""second_channel.py - OAuth for the second channel "Такое бывает" (read-only checks, NO uploads).

    python3 second_channel.py auth     # device flow -> verify the channel ID -> store ANIMAVERSE_YT_REFRESH_TOKEN
    python3 second_channel.py check    # read ANIMAVERSE_YT_REFRESH_TOKEN, verify the same channel ID

Reuses the existing OAuth client (YT_CLIENT_ID / YT_CLIENT_SECRET) and google.com/device. The Orbital Atlas token
YT_REFRESH_TOKEN is never read or written here: the only secret this module may write is ANIMAVERSE_YT_REFRESH_TOKEN,
and it is written only after channels.list(mine=true) returns exactly EXPECTED_CHANNEL_ID. Secret values are never printed.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish as P  # noqa: E402

EXPECTED_CHANNEL_ID = "UCOakEPBhSGwx-2RV0dKGdNA"
SECRET_NAME = "ANIMAVERSE_YT_REFRESH_TOKEN"
PROTECTED = ("YT_REFRESH_TOKEN",)          # the Orbital Atlas token: this module must never write it


def store_second_secret(value, name=SECRET_NAME):
    """The only write path. Refuses any name except ANIMAVERSE_YT_REFRESH_TOKEN."""
    if name != SECRET_NAME or name in PROTECTED:
        raise P.PublishError(f"refusing to write secret {name}: the second channel may only write {SECRET_NAME}")
    P.store_secret(SECRET_NAME, value)


def access_token_from(refresh_token):
    s, _, j = P.jhttp("POST", P.TOKEN_URL, form={
        "client_id": P.need("YT_CLIENT_ID"), "client_secret": P.need("YT_CLIENT_SECRET"),
        "refresh_token": refresh_token, "grant_type": "refresh_token"})
    if s != 200:
        raise P.PublishError(f"token refresh failed: {j.get('error')} - re-run 'YouTube auth - Takoe byvaet'")
    return j["access_token"]


def verified_channel(access_token):
    """channels.list(mine=true) -> the channel, only if it is exactly EXPECTED_CHANNEL_ID; otherwise raise."""
    j = P.api("GET", "channels", {"part": "snippet,statistics", "mine": "true"}, token=access_token)
    items = j.get("items", [])
    ids = [c["id"] for c in items]
    if ids != [EXPECTED_CHANNEL_ID] or j.get("nextPageToken"):
        raise P.PublishError(f"channel mismatch: signed-in account has {ids or 'no channel'}, expected {EXPECTED_CHANNEL_ID}. Nothing was written.")
    c = items[0]
    return {"id": c["id"], "title": c["snippet"]["title"], "customUrl": c["snippet"].get("customUrl"),
            "videos": c["statistics"].get("videoCount"), "subscribers": c["statistics"].get("subscriberCount")}


def cmd_auth(_):
    t = P.device_flow("the 'Такое бывает' channel")
    ch = verified_channel(access_token_from(t["refresh_token"]))     # raises on mismatch BEFORE any write
    store_second_secret(t["refresh_token"])
    return {"status": "ok", "stored_secret": SECRET_NAME, "channel": ch}


def cmd_check(_):
    ch = verified_channel(access_token_from(P.need(SECRET_NAME)))
    return {"status": "ok", "secret": SECRET_NAME, "channel": ch}


def main(argv=None):
    import json
    cmd = (argv if argv is not None else sys.argv[1:]) or [""]
    fn = {"auth": cmd_auth, "check": cmd_check}.get(cmd[0])
    if not fn:
        print("usage: second_channel.py auth|check", file=sys.stderr)
        return 2
    try:
        print(json.dumps(fn(None), indent=2, ensure_ascii=False))
        return 0
    except P.PublishError as e:
        print(json.dumps({"status": "error", "error": P.redact(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
