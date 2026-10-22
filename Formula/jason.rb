# Rendered into Formula/jason.rb by .github/scripts/bump_formula.py. Edit this template, never the formula.
# The version must be stated: Homebrew reads a version from the archive's stem first, and
# from jason-osx-arm64.tar.gz it would read 64. Each url sits under an `if Hardware::CPU`
# test inside on_macos or on_linux, because brew style refuses a url directly in on_macos or
# on_linux.
class Jason < Formula
  desc "Local-first runtime for AI sales development work, driven by your own AI agent"
  homepage "https://jasonharness.ai"
  version "0.14.0"
  license :cannot_represent

  on_macos do
    depends_on arch: :arm64
    if Hardware::CPU.arm?
      url "https://jasonharness.ai/releases/download/v0.14.0/jason-osx-arm64.tar.gz"
      sha256 "1de4756adad8bb323501e814ea53cdb782cb5ba66f07182c785f29a45897b748"
    end
  end

  on_linux do
    depends_on arch: :x86_64
    if Hardware::CPU.intel?
      url "https://jasonharness.ai/releases/download/v0.14.0/jason-linux-x64.tar.gz"
      sha256 "c40a7a996a1979fa609909dec5290e67e9917f067a931c1dbe39026366d0e35e"
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
