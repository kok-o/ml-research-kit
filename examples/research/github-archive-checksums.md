# Which ZIP should an offline installer verify?

On 23 November 2026 we tested `research` on a distribution question for this repository. A maintainer wants to publish a SHA-256 today. A user will download the ZIP again six months later and verify it offline against a trusted copy of that checksum.

**Decision.** Build a versioned ZIP once, record its filename, commit and SHA-256, and upload it as an asset to a draft release. Publish with immutable releases enabled. GitHub protects the uploaded bytes while that release exists. Keep a copy of the artifact if future availability is also a requirement. [GitHub's immutable release documentation](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)

## What the guarantees cover

| Download | What stays stable | Conditions that matter here |
| --- | --- | --- |
| GitHub-generated source ZIP | The extracted files at a pinned commit | The commit must remain available. The repository name determines the top-level directory. GitHub may regenerate the ZIP with different compression settings after giving notice. [Source archive stability](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives#stability-of-source-code-archives) |
| Maintainer-uploaded release ZIP | The file attached to the published immutable release | Immutability must be enabled and the asset attached before publication. The automatic “Source code (zip)” link on that same release page still serves a generated archive. [Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) · [Source downloads on release pages](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives#downloading-source-code-archives-from-a-release) |

GitHub promises at least six months' notice before a compression change. That notice runs from the announcement date. A user's download date does not start a fresh six-month window. [Source archive stability](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives#stability-of-source-code-archives)

## Check on this repository

Three downloads of the [ZIP for commit `5c6cc0e`](https://github.com/kok-o/ml-research-kit/archive/5c6cc0ecf7ef683c32d59408392538e6245768b7.zip) produced the same checksum during the test. We then repacked those entries in their original order with Python's `zipfile.ZIP_STORED`, preserving their paths and timestamps. We compared the filename-to-SHA-256 maps for all nine files.

| ZIP | Bytes | SHA-256 |
| --- | ---: | --- |
| Downloaded | 19,720 | `7711136f2c8d89afd73739e7c51f800b6f343f24156542ce03d76c6800301021` |
| Repacked locally | 40,281 | `8f5714bc6147f8df7c248ca64954c31c7cb5ec199a962086957393d8260fe201` |

All nine file hashes matched. The local repack demonstrates why the archive hash can change even when every extracted file is identical. The repeated downloads establish what GitHub served during the test.

**Decision Flip Trigger** — If the installer only needs to verify the extracted files, a source archive pinned to the full commit plus a trusted per-file hash manifest meets that requirement.
