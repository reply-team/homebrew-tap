# Rendered into Formula/jason.rb by .github/scripts/bump_formula.py. Edit this template, never the formula.
# The version must be stated: Homebrew reads a version from the archive's stem first, and
# from jason-osx-arm64.tar.gz it would read 64. Each url sits under an `if Hardware::CPU`
# test inside on_macos or on_linux, because brew style refuses a url directly in on_macos or
# on_linux.
class Jason < Formula
  desc "Local-first runtime for AI sales development work, driven by your own AI agent"
  homepage "https://jasonharness.ai"
  version "0.31.0"
  license :cannot_represent

  on_macos do
    depends_on arch: :arm64
    if Hardware::CPU.arm?
      url "https://get.jasonharness.ai/releases/download/v0.31.0/jason-osx-arm64.tar.gz"
      sha256 "4ca0dae4f22a02810e43ca402b4a0e0ed76701a481c4eb83d5d09217bc2e4423"
    end
  end

  on_linux do
    depends_on arch: :x86_64
    if Hardware::CPU.intel?
      url "https://get.jasonharness.ai/releases/download/v0.31.0/jason-linux-x64.tar.gz"
      sha256 "f873c2b9b8dd051aaff8c4384a5baafea1864a5f6a03a35d22452e0b94d55906"
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
