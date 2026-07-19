# On-demand Spotify Connection Design

Date: 2026-07-20

## Goal

Let `research-music` recognize when Spotify catalog data would materially help
a music-research request, check whether access is already configured, and offer
a secure connection flow only at that point. Keep Spotify optional and continue
with other providers when the user declines or access fails.

## Decision

Keep `scripts/spotify_api.py` as the deterministic provider adapter. Do not make
users discover or operate it before using the skill. Teach the skill to invoke
the adapter as an internal implementation detail.

Rejected alternatives:

- Removing the adapter and generating ad-hoc HTTP requests would duplicate
  authentication, secret handling, API limits, and normalization across agents.
- Building a dedicated MCP server now would improve centralized distribution
  but adds installation and maintenance work before multiple providers need it.

## User experience

1. Build the smallest source stack that can answer the request.
2. Select Spotify only when its catalog identity or release metadata adds
   useful evidence; do not request access merely because Spotify is available.
3. Run the adapter's non-interactive connection check.
4. If access exists, use Spotify and combine its output with the other selected
   providers.
5. If access is missing, explain in one sentence what Spotify would add and ask
   whether the user wants to connect it.
6. After consent on macOS, launch native dialogs for Client ID and a hidden
   Client Secret, store them in macOS Keychain, and verify the connection. Never
   request or echo the Client Secret in chat.
7. If the user declines, cancels, uses an unsupported environment, or Spotify
   rejects access, continue with MusicBrainz, Apple Music, official pages, or
   web search and mark the Spotify branch unavailable or access-dependent.

## Components

### Skill orchestration

Add a concise optional-provider handshake to `SKILL.md`. Keep provider-specific
commands and platform details in `providers/spotify.md` so the main skill stays
small. The skill must not pause for credentials when Spotify would not change
the answer.

### Spotify adapter

Retain the existing `check` and `search` commands. Extend `configure` with an
explicit `--gui` mode for agents operating from a non-interactive conversation.
The native-dialog helper returns credentials only to the local Python process;
stdout contains only the safe verification result.

Terminal prompting remains the default for a person running `configure`
directly. Environment variables remain the portable non-macOS path.

### Credential storage

Preserve environment-variable precedence and the single macOS Keychain item.
Do not persist access tokens. Do not log Client ID, Client Secret, Authorization
headers, or Keychain payloads.

## Error handling

- Treat dialog cancellation as a normal, actionable configuration cancellation.
- Fail closed when only one environment variable is present.
- Distinguish missing access from Spotify HTTP/network failure without exposing
  response credentials.
- Never let optional Spotify access prevent completion with available fallback
  providers.

## Testing

- Add failing adapter tests before implementation for `configure --gui`, native
  dialog invocation, hidden-secret handling, cancellation, and safe output.
- Add a skill contract test requiring need-based selection, user consent,
  prohibition on chat secrets, GUI invocation, and fallback continuation.
- Run the Spotify-focused suite, full repository suite, CLI smoke tests, and
  Agent Skills validation.

## Non-goals

- User-account OAuth, playlists, private listening data, or playback control.
- Sales, streaming counts, historical popularity, or removed Spotify fields.
- Automatic Spotify app creation.
- A general provider registry or dedicated MCP server in this iteration.
