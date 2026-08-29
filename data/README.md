# Competition Data

## `public_set.jsonl`

Contains 200 labeled development sessions: 80 Buying, 80 Browsing, 30 Intent Override, and 10 Boundary sessions.

Each session contains a safe aggregate `user_profile` and public labels for local development. Direct user identifiers, timestamps, free-text reviews, raw purchase history, hidden intent cards, and simulator-policy internals are not shipped in this participant file.

## `catalog.jsonl`

Download `catalog.jsonl.gz` from the GitHub Release and decompress it as `catalog.jsonl` in this directory. Expected row count: 50,000.

Expected SHA256 of `catalog.jsonl.gz`:

`07fd142631fd6b03e2b4d09988c3eb7d53720e9d57010c79db48eeaada50a8f8`

Never place API keys, private evaluation data, or participant outputs in this directory.
