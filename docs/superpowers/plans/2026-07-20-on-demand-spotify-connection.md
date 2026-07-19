# On-demand Spotify Connection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `research-music` offer secure Spotify setup only when Spotify materially helps a request, then continue through fallbacks when access is declined or unavailable.

**Architecture:** Keep `spotify_api.py` as the deterministic provider boundary and add a macOS-native GUI credential input path for conversation-driven setup. Put the provider-selection handshake in `SKILL.md` and detailed commands in `providers/spotify.md` so other Agent Skills clients can follow the same flow without making Spotify mandatory.

**Tech Stack:** Python 3 standard library, macOS `osascript` and Keychain `security`, Agent Skills Markdown, pytest/unittest.

## Global Constraints

- Never request, echo, log, or commit a Spotify Client Secret in chat or command output.
- Keep Spotify optional; a declined, cancelled, unsupported, or failed connection must not block other providers.
- Preserve terminal `configure`, `check`, `search`, environment-variable precedence, and the existing Keychain service.
- Add no third-party runtime dependency and no user-account OAuth.
- Work directly on `main`; do not create a worktree.

---

### Task 1: macOS-native secure setup

**Files:**
- Modify: `tests/research_music/test_spotify_api.py`
- Modify: `skills/music/research-music/scripts/spotify_api.py`

**Interfaces:**
- Consumes: existing `Credentials`, `CredentialError`, `store_credentials()`, and `SpotifyApi.check()`.
- Produces: `prompt_gui_credentials(platform_name=None, runner=subprocess.run) -> Credentials`; `configure --gui` CLI option.

- [ ] **Step 1: Write failing GUI behavior tests**

Add a sequenced runner and tests equivalent to:

```python
class SequencedRunner:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        output = next(self.outputs)
        if isinstance(output, Exception):
            raise output
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")


def test_gui_prompt_uses_hidden_native_secret_dialog(self):
    runner = SequencedRunner(["gui-id\n", "gui-secret\n"])
    credentials = spotify.prompt_gui_credentials(
        platform_name="darwin", runner=runner
    )
    assert credentials == spotify.Credentials("gui-id", "gui-secret")
    assert "with hidden answer" in runner.calls[1][0][-1]
    assert all(call[1]["capture_output"] for call in runner.calls)


def test_gui_prompt_turns_dialog_cancellation_into_safe_error(self):
    cancelled = subprocess.CalledProcessError(1, ["osascript"])
    with pytest.raises(spotify.CredentialError, match="cancelled"):
        spotify.prompt_gui_credentials(
            platform_name="darwin", runner=SequencedRunner([cancelled])
        )


def test_configure_help_exposes_gui_mode(self):
    result = subprocess.run(
        [SCRIPT, "configure", "--help"], text=True, capture_output=True, check=True
    )
    assert "--gui" in result.stdout
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q tests/research_music/test_spotify_api.py
```

Expected: FAIL because `prompt_gui_credentials` and `configure --gui` do not exist.

- [ ] **Step 3: Implement native dialogs and CLI routing**

Implement the following behavior:

```python
def _native_dialog(script: str, runner: Runner) -> str:
    try:
        result = runner(
            ["osascript", "-e", script],
            text=True,
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise CredentialError("Spotify configuration was cancelled or unavailable.") from None
    return result.stdout.strip()


def prompt_gui_credentials(*, platform_name=None, runner=subprocess.run):
    if (platform_name or sys.platform) != "darwin":
        raise CredentialError("Spotify GUI configuration is available on macOS only.")
    client_id = _native_dialog(CLIENT_ID_DIALOG, runner)
    client_secret = _native_dialog(CLIENT_SECRET_DIALOG_WITH_HIDDEN_ANSWER, runner)
    return _validate_credentials(client_id, client_secret)
```

Add `--gui` to the `configure` subparser and route `_configure(gui=True)` through
`prompt_gui_credentials()`. Keep terminal input as the default.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest -q tests/research_music/test_spotify_api.py
```

Expected: all Spotify adapter and documentation tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add tests/research_music/test_spotify_api.py \
  skills/music/research-music/scripts/spotify_api.py
git commit -m "feat: add native Spotify setup dialog"
```

### Task 2: need-based provider handshake

**Files:**
- Modify: `tests/research_music/test_spotify_api.py`
- Modify: `skills/music/research-music/SKILL.md`
- Modify: `skills/music/research-music/providers/spotify.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: `spotify_api.py check`, `spotify_api.py configure --gui`, and existing provider fallbacks.
- Produces: a portable agent workflow that selects, checks, offers, configures, retries, or bypasses Spotify based on observed access and user consent.

- [ ] **Step 1: Establish the current-skill baseline**

Use the current skill against this pressure case without revealing the intended
wording: a user requests Spotify-backed album research, Spotify is not
configured, and the user wants setup in the conversation. Record whether the
agent asks for the secret in chat, merely hands off a terminal command, blocks
the research, or continues with a safe fallback.

- [ ] **Step 2: Write the failing skill contract test**

Require the skill and provider card to contain observable instructions for:

```python
for expected in (
    "only when Spotify",
    "spotify_api.py check",
    "ask whether",
    "spotify_api.py configure --gui",
    "Never ask the user to paste",
    "continue with",
):
    assert expected in combined_skill_text
```

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/research_music/test_skill_contract.py \
  tests/research_music/test_spotify_api.py
```

Expected: FAIL because the need-based consent handshake is not documented.

- [ ] **Step 3: Add the minimal orchestration guidance**

Add an imperative optional-provider section to `SKILL.md`:

```markdown
## Optional credentialed providers

Select a credentialed provider only when it materially helps close a requested
branch. Read its provider card, check access non-interactively, and use it when
available. When access is missing, explain what it would add and ask whether
the user wants to connect it. Never request secrets in chat. If the user
declines or setup fails, continue with the documented fallbacks.
```

In `providers/spotify.md`, specify `check` → consent → `configure --gui` → retry,
plus terminal and non-macOS alternatives. Update README examples without making
Spotify a prerequisite.

- [ ] **Step 4: Verify the revised skill behavior**

Run the same focused tests, then forward-test the approved skill on the same
scenario. Success means the agent proposes a native secure dialog only when
Spotify adds value, never asks for the secret in chat, and states a fallback.

- [ ] **Step 5: Validate and commit Task 2**

Run:

```bash
.venv/bin/python -m pytest -q
uvx --from skills-ref agentskills validate skills/music/research-music
python3 -m py_compile skills/music/research-music/scripts/spotify_api.py
git diff --check
```

Expected: full test suite passes, the skill is valid, compilation succeeds, and
the diff has no whitespace errors.

```bash
git add README.md skills/music/research-music/SKILL.md \
  skills/music/research-music/providers/spotify.md \
  tests/research_music/test_spotify_api.py
git commit -m "feat: guide on-demand Spotify connections"
git push origin main
```
