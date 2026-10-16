# reply-team/homebrew-tap

The Homebrew tap for Jason, the local-first runtime for AI sales development work that your own AI agent drives.
Jason 0.9.0 and later are published here.

## Install

```sh
brew install reply-team/tap/jason
```

This works on a Mac with Apple silicon, and on Linux on x86-64. On Linux, the install script in Jason's
[installation guide](https://github.com/reply-team/jason-ai/blob/main/docs/INSTALL.md) remains the documented way;
the formula is a convenience there.

## Updates

Stop the runtime first, then upgrade, then start it again:

```sh
jason runtime stop
brew upgrade jason
jason runtime start
```

Jason reads Homebrew's own install receipt, sees that Homebrew installed it, and leaves updating to Homebrew:
`jason update apply` refuses an installation Homebrew owns.

## Licence

Jason itself is distributed under the Jason Runtime Licence,
<https://github.com/reply-team/jason-ai/blob/main/LICENSE-RUNTIME.md>. The formula installs that licence beside the
executable as `jason-LICENSE`, and the third-party notices as `jason-THIRD-PARTY-NOTICES`.

The files of this repository (the formula, its template, the workflow and the script) are under the MIT licence, in
[LICENSE](LICENSE).

## How the formula is kept current

A workflow, `.github/workflows/bump.yml`, runs every six hours and can also be started by hand. It reads the manifest
of Jason's latest release from `https://jasonharness.ai`.

It does nothing for a release before 0.9.0, or when `Formula/jason.rb` already is the template rendered for the
latest release. Otherwise (a new release, or a template corrected since) it:

1. downloads each archive the formula installs, checks its SHA-256 and size against the manifest, and stops without
   changing anything if either differs;
2. renders `Formula/jason.rb` from `.github/formula/jason.rb.template`;
3. commits it as `jason <version>`;
4. trusts that one formula (Homebrew 6 asks for it), then runs `brew style`, `brew audit`, `brew install` and
   `brew test` on it, prints what is trusted and what `brew info jason` says, and checks that `jason` resolves to
   `reply-team/tap/jason` and that the version Homebrew holds for it is the release's;
5. pushes that commit only when every one of those steps passes.

Every request follows at most three redirects. A longer chain stops the run, because it means something changed that
somebody should look at.

A platform that Jason's releases add later reaches the formula through a reviewed change to the template, never
through the workflow, which refuses a manifest naming a platform it does not know.
