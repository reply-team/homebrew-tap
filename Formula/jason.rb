# Rendered into Formula/jason.rb by .github/scripts/bump_formula.py. Edit this template, never the formula.
# The version must be stated: Homebrew reads a version from the archive's stem first, and
# from jason-osx-arm64.tar.gz it would read 64. Each url sits under an `if Hardware::CPU`
# test inside on_macos or on_linux, because brew style refuses a url directly in on_macos or
# on_linux.
class Jason < Formula
  desc "Local-first runtime for AI sales development work, driven by your own AI agent"
  homepage "https://jasonharness.ai"
  version "0.48.7"
  license :cannot_represent
  deprecate! date:    "2026-11-21",
             because: "is replaced by Jason's own installer since 0.49 (https://jasonharness.ai) and stays at 0.48.7"

  on_macos do
    depends_on arch: :arm64
    if Hardware::CPU.arm?
      url "https://get.jasonharness.ai/releases/download/v0.48.7/jason-osx-arm64.tar.gz"
      sha256 "a8a3e30dcd4f43c1c8917bc01b7057576c022d38fe57ce7b9581dfee225ae474"
    end
  end

  on_linux do
    depends_on arch: :x86_64
    if Hardware::CPU.intel?
      url "https://get.jasonharness.ai/releases/download/v0.48.7/jason-linux-x64.tar.gz"
      sha256 "318bc2079eede1b7bea1b7db6b29f52b06ba835808bdc522d8eab9a219315055"
    end
  end

  def install
    bin.install "jason"
    prefix.install "LICENSE" => "jason-LICENSE", "THIRD-PARTY-NOTICES" => "jason-THIRD-PARTY-NOTICES"
  end

  def caveats
    <<~EOS
      Jason 0.49 and later are not installed by Homebrew: this formula stays at 0.48.7.
      To move to the current Jason, which is Jason Desktop with the jason command in your terminal:
        jason runtime stop
        brew uninstall jason
        curl -fsSL https://get.jasonharness.ai/releases/latest/download/install.sh | sh
      Your data in ~/.jason and your work in ~/Jason stay where they are.
    EOS
  end

  test do
    assert_match(/\A#{Regexp.escape(version.to_s)}\+/, shell_output("#{bin}/jason --version"))
  end
end
