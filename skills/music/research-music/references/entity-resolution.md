# Entity Resolution

## Artist

Record a stable provider ID, canonical name, aliases, market or country when relevant, and the source used to resolve the artist.

## Release group and edition

Resolve the release group before an edition. Preserve regional, deluxe, reissue, physical, and digital editions under one group while retaining their distinct identifiers and dates.

## Participation role

Keep the researched artist's primary, featured, guest, composer, producer, and other participation roles explicit; do not infer primary ownership from appearance alone.

## Matching order

Prefer stable provider IDs. Only after those are unavailable, match canonical artist identity, then title and edition, then date, market, and role; use fuzzy title/date matching last.

## Unresolved identity

Do not attach evidence when candidate entities remain plausible. Explain the ambiguity, list the discriminating information needed, and close the branch as unavailable or access-dependent.
