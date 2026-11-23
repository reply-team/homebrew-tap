# reply-team/homebrew-tap

The Homebrew tap for Jason, the local-first runtime for AI sales development work that your own AI agent drives.

## Install on a Mac

```sh
brew install --cask reply-team/tap/jason
```

If Homebrew says the tap is not trusted, run `brew trust reply-team/tap` once, then the install line again.

This installs Jason Desktop, with the `jason` command in your terminal, on a Mac with Apple silicon. Open Jason once from
Applications: its first start sets up the `jason` command and the skills, as the disk image does. Jason then updates
itself, so `brew upgrade` leaves it alone; `brew upgrade --greedy` reinstalls it whenever Homebrew's version is behind the
one Jason updated itself to, quitting it and stopping the runtime first.

On Linux, and on a Mac without Homebrew, the one line at <https://get.jasonharness.ai/install> installs the same Jason
Desktop.

## Take it off

```sh
brew uninstall --zap --cask jason
```

takes off the application, its link, the `jason` command's wrapper, the start at logon and the application's own state
under `~/Library`. A plain `brew uninstall --cask jason` takes off the application and its link only, and leaves the
wrapper and the start at logon pointing at nothing. `jason uninstall`, run before either, takes off all Jason set up. Your
data in `~/.jason` and your work in `~/Jason` stay in both.

## The older formula

Jason 0.9.0 to 0.48.7 were published here as a formula, the command line alone. The formula is no longer in this tap;
where it is still installed it stays at 0.48.7. While it is linked, Homebrew does not link the cask's `jason`, so take it
off first:

```sh
jason runtime stop
brew uninstall --formula jason
brew install --cask reply-team/tap/jason
```

On Linux, the last line is the install script instead:
`curl -fsSL https://get.jasonharness.ai/releases/latest/download/install.sh | sh`. Your data in `~/.jason` and your work in
`~/Jason` stay where they are.

## Licence

Jason itself, and the files of this repository (the cask, the workflow and the script), are under the MIT
licence: Jason's in <https://github.com/reply-team/jason-ai/blob/main/LICENSE>, this repository's in [LICENSE](LICENSE).

## How the cask is kept current

A workflow, `.github/workflows/bump.yml`, runs every six hours and can also be started by hand, and Jason's release
workflow can ask it to run once a release is published and its macOS proof of the cask has passed. It reads the manifest of Jason's latest
release from `https://get.jasonharness.ai`.

It does nothing for a release before 0.49.2, the first whose `jason` leaves an application Homebrew placed to Homebrew, or
when `Casks/jason.rb` already is the template rendered for the latest release. Otherwise it:

1. reads the release's `checksums.txt` for the line of `jason-desktop-macos-arm64.zip`, downloads the zip, and stops
   without changing anything if its SHA-256 differs;
2. reads the cask's template, `.github/cask/jason.rb.template`, from Jason's repository at the release's tag, and renders
   `Casks/jason.rb` from it;
3. commits it as `jason <version>`;
4. trusts that one cask, then runs `brew style` on the cask's file, `brew audit --strict` and `brew install --cask` on
   it, failing where Homebrew says a tap is not trusted or ignored, checks that the `jason` it links answers the
   release's version, and that `reply-team/tap/jason` resolves to this cask at that version;
5. pushes that commit only when every one of those steps passes.

Every request follows at most three redirects. A longer chain stops the run, because it means something changed that
somebody should look at. A candidate is never rendered by the bump, which reads the latest release; `bump_cask.py render`
renders one by hand, from local files.
