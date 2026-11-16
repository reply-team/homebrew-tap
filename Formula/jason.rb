# Rendered into Formula/jason.rb by .github/scripts/bump_formula.py. Edit this template, never the formula.
# The version must be stated: Homebrew reads a version from the archive's stem first, and
# from jason-osx-arm64.tar.gz it would read 64. Each url sits under an `if Hardware::CPU`
# test inside on_macos or on_linux, because brew style refuses a url directly in on_macos or
# on_linux.
class Jason < Formula
  desc "Local-first runtime for AI sales development work, driven by your own AI agent"
  homepage "https://jasonharness.ai"
  version "0.47.1"
  license :cannot_represent

  on_macos do
    depends_on arch: :arm64
    if Hardware::CPU.arm?
      url "https://get.jasonharness.ai/releases/download/v0.47.1/jason-osx-arm64.tar.gz"
      sha256 "3fb068699433148be7c73f6f5db82dceeb88da4474a3d82c4074883e12274de3"
    end
  end

  on_linux do
    depends_on arch: :x86_64
    if Hardware::CPU.intel?
      url "https://get.jasonharness.ai/releases/download/v0.47.1/jason-linux-x64.tar.gz"
      sha256 "dba31c8dc7dd6f4f4ba6136e4d630744b3516178d375e8d95929d2f54e3ddda6"
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
