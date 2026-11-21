#!/usr/bin/env python3
"""Keeps Casks/jason.rb at Jason's latest release, from that release's own manifest and checksums.

  bump    Reads https://get.jasonharness.ai/releases/latest/download/manifest.json for the version, that release's
          checksums.txt for the line of jason-desktop-macos-arm64.zip, downloads the zip and holds it to that line, reads
          the cask's template from Jason's repository at the release's tag
          (https://raw.githubusercontent.com/reply-team/jason-ai/v<version>/.github/cask/jason.rb.template), and renders
          Casks/jason.rb from it. The addresses are fixed here, and no option changes them.
  render  The same checks and rendering, from local files: --manifest, --checksums, --zip, --template, --cask (the cask
          there is now, if any) and --out. It is how the checks are tried without a network, and how a candidate, which
          the bump never renders, is rendered by hand.

Every request follows at most three redirects, and prints how many it followed. Nothing is written unless every check
passes. A release before 0.49.2, the first whose jason leaves an application Homebrew placed to Homebrew, or a cask that
already is the template rendered for the release, is not a change: the script says so and exits 0. Anything wrong exits 1
and says what. Under GitHub Actions it also writes `changed` and `version` to $GITHUB_OUTPUT.
Standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

PRODUCT = "https://get.jasonharness.ai/releases"
TEMPLATE = "https://raw.githubusercontent.com/reply-team/jason-ai/v%s/.github/cask/jason.rb.template"
MAX_REDIRECTS = 3
FLOOR = (0, 49, 2)
ZIP = "jason-desktop-macos-arm64.zip"
REDIRECTS = (301, 302, 303, 307, 308)


class Refused(Exception):
    """A check failed. The message says which one, and why."""


def fmt(version):
    return ".".join(str(p) for p in version)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_text(path, text):
    """Through a temporary file beside it, so the cask is either the old one or the new one, never half of each."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    temporary = path + ".new"
    with open(temporary, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(temporary, path)


def parse_version(text):
    if not isinstance(text, str) or not re.fullmatch(r"\d+\.\d+\.\d+", text):
        raise Refused("the manifest's version %r is not a plain x.y.z" % (text,))
    return tuple(int(p) for p in text.split("."))


def check_manifest(raw):
    """The manifest's version, after the checks the cask depends on: schema 1 and a plain x.y.z."""
    try:
        manifest = json.loads(raw)
    except ValueError as e:
        raise Refused("the manifest is not JSON (%s)" % e)
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise Refused("the manifest's schema is not 1")
    return parse_version(manifest.get("version"))


def listed_sha(checksums):
    """The SHA-256 checksums.txt lists for the zip: exactly one line, `<64 hex>  jason-desktop-macos-arm64.zip`."""
    try:
        text = checksums.decode("utf-8") if isinstance(checksums, bytes) else checksums
    except UnicodeDecodeError:
        raise Refused("checksums.txt is not UTF-8")
    lines = [line for line in text.splitlines() if line.endswith("  " + ZIP)]
    if len(lines) != 1:
        raise Refused("checksums.txt lists %s %d time(s), not once" % (ZIP, len(lines)))
    digest = lines[0][: -len("  " + ZIP)]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise Refused("checksums.txt's SHA-256 for %s is not 64 lowercase hexadecimal digits" % ZIP)
    return digest


def verify(digest, data):
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise Refused("%s does not match checksums.txt: it lists SHA-256 %s, the zip is SHA-256 %s" % (ZIP, digest, actual))
    print("%s matches checksums.txt: SHA-256 %s, %d bytes" % (ZIP, actual, len(data)))


def render(template_text, version, digest):
    text = template_text.replace("{{VERSION}}", fmt(version)).replace("{{SHA256_MACOS_ARM64_ZIP}}", digest)
    if "{{" in text:
        raise Refused("the template holds a placeholder this script does not fill")
    if not text.startswith('cask "jason" do'):
        raise Refused("the template is not the cask jason")
    return text


def nothing_to_do(version, text, cask_path):
    if version < FLOOR:
        return "%s is before %s, the first release this cask carries: nothing to do" % (fmt(version), fmt(FLOOR))
    if cask_path and os.path.isfile(cask_path) and read_text(cask_path) == text:
        return "the cask already is the template rendered for %s: nothing to do" % fmt(version)
    return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Each redirect comes back to get(), which counts it, instead of being followed here."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_once(url):
    """One GET, following nothing: (status, Location or None, body)."""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "reply-team-homebrew-tap"})
    try:
        with opener.open(request, timeout=300) as response:
            return response.status, None, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location") if e.code in REDIRECTS else None, b""


def get(url, transport=None):
    """The body at url, after at most MAX_REDIRECTS redirects, all of them https."""
    transport = transport or open_once
    first, hops = url, 0
    while True:
        if not url.startswith("https://"):
            raise Refused("%s led to %s, which is not https" % (first, url))
        status, location, body = transport(url)
        if status in REDIRECTS:
            if not location:
                raise Refused("%s: a redirect with no Location" % url)
            hops += 1
            if hops > MAX_REDIRECTS:
                raise Refused("%s takes more than %d redirects; a longer chain is a change somebody made, and it is "
                              "not followed" % (first, MAX_REDIRECTS))
            url = urllib.parse.urljoin(url, location)
            continue
        if status != 200:
            raise Refused("%s answered HTTP %s" % (url, status))
        print("GET %s: %d redirect(s) of at most %d, %d bytes" % (first, hops, MAX_REDIRECTS, len(body)))
        return body


def bump(cask_path, transport=None):
    """The release's manifest, checksums, zip and template; the cask rendered if anything changed."""
    version = check_manifest(get(PRODUCT + "/latest/download/manifest.json", transport))
    if version < FLOOR:
        print("%s is before %s, the first release this cask carries: nothing to do" % (fmt(version), fmt(FLOOR)))
        return None
    digest = listed_sha(get("%s/download/v%s/checksums.txt" % (PRODUCT, fmt(version)), transport))
    template = get(TEMPLATE % fmt(version), transport).decode("utf-8")
    text = render(template, version, digest)
    reason = nothing_to_do(version, text, cask_path)
    if reason:
        print(reason)
        return None
    verify(digest, get("%s/download/v%s/%s" % (PRODUCT, fmt(version), ZIP), transport))
    write_text(cask_path, text)
    print("rendered %s for %s" % (cask_path, fmt(version)))
    return version


def render_local(manifest_path, checksums_path, zip_path, template_path, cask_path, out_path):
    """The same checks and rendering, from local files. The manifest's version may be a candidate's here."""
    try:
        manifest = json.loads(read_bytes(manifest_path))
    except ValueError as e:
        raise Refused("the manifest is not JSON (%s)" % e)
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise Refused("the manifest's schema is not 1")
    text_version = manifest.get("version")
    if not isinstance(text_version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?", text_version):
        raise Refused("the manifest's version %r is not x.y.z or a candidate of it" % (text_version,))
    digest = listed_sha(read_bytes(checksums_path))
    verify(digest, read_bytes(zip_path))
    text = read_text(template_path).replace("{{VERSION}}", text_version).replace("{{SHA256_MACOS_ARM64_ZIP}}", digest)
    if "{{" in text:
        raise Refused("the template holds a placeholder this script does not fill")
    if cask_path and os.path.isfile(cask_path) and read_text(cask_path) == text:
        print("the cask already is the template rendered for %s: nothing to do" % text_version)
        return None
    write_text(out_path, text)
    print("rendered %s for %s" % (out_path, text_version))
    return text_version


def report(version):
    """For the workflow: whether the cask changed, and to which version."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write("changed=%s\n" % ("true" if version else "false"))
            if version:
                f.write("version=%s\n" % (fmt(version) if isinstance(version, tuple) else version))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Keeps Casks/jason.rb at Jason's latest release.")
    commands = ap.add_subparsers(dest="command", required=True)
    b = commands.add_parser("bump", help="read the latest release and render the cask")
    b.add_argument("--cask", default="Casks/jason.rb")
    r = commands.add_parser("render", help="the same checks and rendering, from local files")
    for option in ("--manifest", "--checksums", "--zip", "--template", "--cask", "--out"):
        r.add_argument(option, required=True)
    args = ap.parse_args(argv)
    try:
        if args.command == "bump":
            version = bump(args.cask)
        else:
            version = render_local(args.manifest, args.checksums, args.zip, args.template, args.cask, args.out)
    except (Refused, OSError) as e:
        print("FAIL: %s. Nothing was written." % e, file=sys.stderr)
        return 1
    report(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
