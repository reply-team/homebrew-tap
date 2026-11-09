# Rendered into Formula/jason.rb by .github/scripts/bump_formula.py. Edit this template, never the formula.
# The version must be stated: Homebrew reads a version from the archive's stem first, and
# from jason-osx-arm64.tar.gz it would read 64. Each url sits under an `if Hardware::CPU`
# test inside on_macos or on_linux, because brew style refuses a url directly in on_macos or
# on_linux.
class Jason < Formula
  desc "Local-first runtime for AI sales development work, driven by your own AI agent"
  homepage "https://jasonharness.ai"
  version "0.33.0"
  license :cannot_represent

  on_macos do
    depends_on arch: :arm64
    if Hardware::CPU.arm?
      url "https://get.jasonharness.ai/releases/download/v0.33.0/jason-osx-arm64.tar.gz"
      sha256 "a45c3b697f8e3b301fe714e95e313ed1550f2e9bb3eb7c701f95129355c24eff"
    end
  end

  on_linux do
    depends_on arch: :x86_64
    if Hardware::CPU.intel?
      url "https://get.jasonharness.ai/releases/download/v0.33.0/jason-linux-x64.tar.gz"
      sha256 "d29ffedccb35f99106608bcd57d02fed2950c42126a0b25249f766347c1febb7"
    end
  end

  def install
    bin.install "jason"
    prefix.install "LICENSE" => "jason-LICENSE", "THIRD-PARTY-NOTICES" => "jason-THIRD-PARTY-NOTICES"
  end

  def caveats
    <<~EOS
      Jason is updated by Homebrew, with the runtime stopped first:
        jason runtime stop
        brew upgrade jason
        jason runtime start
      jason update apply refuses an installation Homebrew owns.
    EOS
  end

  test do
    assert_match(/\A#{Regexp.escape(version.to_s)}\+/, shell_output("#{bin}/jason --version"))
  end
end
