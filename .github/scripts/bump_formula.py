#!/usr/bin/env python3
"""Keeps Formula/jason.rb at Jason's latest release, from that release's own manifest.

  bump    Reads https://jasonharness.ai/releases/latest/download/manifest.json, downloads the archives the formula
          installs from https://jasonharness.ai/releases/download/v<version>/, checks each one's SHA-256 and size
          against the manifest, and renders Formula/jason.rb from .github/formula/jason.rb.template. The address is
          fixed here, and no option changes it.
  render  The same checks and rendering, from local files: --manifest, --archives (a folder holding the archives
          under their asset names), --formula (the formula there is now, if any), --template and --out. It is how
          the checks are tried without a network.

Every request follows at most three redirects, and prints how many it followed. Nothing is written unless every check
passes. A release before 0.9.0, or a formula that already is the template rendered for the release, is not a change: the
script says so and exits 0. A formula at the same version but with other text (the template corrected since) is rendered
again. Anything wrong exits 1 and says what. Under GitHub Actions it also writes `changed` and `version` to
$GITHUB_OUTPUT.
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

PRODUCT = "https://jasonharness.ai/releases"
MAX_REDIRECTS = 3
FLOOR = (0, 9, 0)
# Every platform a release's manifest may name, with its archive. Homebrew does not run on Windows: its archive is
# known and not used. A platform not named here is refused, so a new one reaches the formula only through a reviewed
# change to this table and to the template.
KNOWN = {
    "osx-arm64": "jason-osx-arm64.tar.gz",
    "linux-x64": "jason-linux-x64.tar.gz",
    "win-x64": "jason-win-x64.zip",
}
FORMULA = {"osx-arm64": "{{SHA256_OSX_ARM64}}", "linux-x64": "{{SHA256_LINUX_X64}}"}
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
    """Through a temporary file beside it, so the formula is either the old one or the new one, never half of each."""
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


def current_version(formula_path):
    """The version the formula states, or None when there is no formula yet or it states none. Its urls are the
    cross-check: they must all name one version, and the stated one where there is one."""
    if not formula_path or not os.path.isfile(formula_path):
        return None
    text = read_text(formula_path)
    stated = re.search(r'^\s*version "(\d+\.\d+\.\d+)"\s*$', text, re.M)
    urls = r'^\s*url "https://jasonharness\.ai/releases/download/v(\d+\.\d+\.\d+)/'
    found = set(re.findall(urls, text, re.M))
    if len(found) > 1:
        raise Refused("the formula's urls name more than one version (%s)" % ", ".join(sorted(found)))
    if stated and found and found != {stated.group(1)}:
        raise Refused("the formula states %s and its urls name %s" % (stated.group(1), found.pop()))
    return parse_version(stated.group(1)) if stated else None


def check_manifest(raw):
    """The manifest's version and artifacts, after every check the formula depends on."""
    try:
        manifest = json.loads(raw)
    except ValueError as e:
        raise Refused("the manifest is not JSON (%s)" % e)
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise Refused("the manifest's schema is not 1")
    version = parse_version(manifest.get("version"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise Refused("the manifest has no artifacts")
    unknown = sorted(set(artifacts) - set(KNOWN))
    if unknown:
        raise Refused("the manifest names a platform this formula does not know (%s); a new platform enters the "
                      "template through a reviewed change, never through this script" % ", ".join(unknown))
    for rid in FORMULA:
        entry = artifacts.get(rid)
        if not isinstance(entry, dict):
            raise Refused("the manifest has no %s archive" % rid)
        if entry.get("asset") != KNOWN[rid]:
            raise Refused("the manifest names %r for %s, not %s" % (entry.get("asset"), rid, KNOWN[rid]))
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise Refused("the manifest's SHA-256 for %s is not 64 lowercase hexadecimal digits" % rid)
        size = entry.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise Refused("the manifest's size for %s is not a positive whole number" % rid)
    return version, artifacts


def nothing_to_do(version, text, formula_path):
    """The reason there is nothing to do, or None when the formula should become `text`, the template rendered for
    this release. The version alone does not decide it: a formula the template has corrected since is rendered again."""
    if version < FLOOR:
        return "%s is before %s, the first release this tap carries: nothing to do" % (fmt(version), fmt(FLOOR))
    current = current_version(formula_path)
    print("the formula there now states %s" % (fmt(current) if current else "no version"))
    if formula_path and os.path.isfile(formula_path) and read_text(formula_path) == text:
        return "the formula already is the template rendered for %s: nothing to do" % fmt(version)
    return None


def verify(entry, data):
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry["sha256"] or len(data) != entry["size"]:
        raise Refused("%s does not match the manifest: the manifest says SHA-256 %s and %d bytes, the archive is "
                      "SHA-256 %s and %d bytes" % (entry["asset"], entry["sha256"], entry["size"], digest, len(data)))
    print("%s matches the manifest: SHA-256 %s, %d bytes" % (entry["asset"], digest, len(data)))


def render(template_text, version, artifacts):
    text = template_text.replace("{{VERSION}}", fmt(version))
    for rid, placeholder in FORMULA.items():
        text = text.replace(placeholder, artifacts[rid]["sha256"])
    if "{{" in text:
        raise Refused("the template holds a placeholder this script does not fill")
    return text


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Each redirect comes back to get(), which counts it, instead of being followed here."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_once(url):
    """One GET, following nothing: (status, Location or None, body)."""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "reply-team-homebrew-tap"})
    try:
        with opener.open(request, timeout=120) as response:
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


def bump(formula_path, template_path, transport=None):
    """The release's manifest and archives from the product address; the formula rendered if anything changed."""
    version, artifacts = check_manifest(get(PRODUCT + "/latest/download/manifest.json", transport))
    text = render(read_text(template_path), version, artifacts)
    reason = nothing_to_do(version, text, formula_path)
    if reason:
        print(reason)
        return None
    for rid in FORMULA:
        data = get("%s/download/v%s/%s" % (PRODUCT, fmt(version), KNOWN[rid]), transport)
        verify(artifacts[rid], data)
    write_text(formula_path, text)
    print("rendered %s for %s" % (formula_path, fmt(version)))
    return version


def render_local(manifest_path, archives, formula_path, template_path, out_path):
    """The same checks and rendering, from local files."""
    version, artifacts = check_manifest(read_bytes(manifest_path))
    text = render(read_text(template_path), version, artifacts)
    reason = nothing_to_do(version, text, formula_path)
    if reason:
        print(reason)
        return None
    for rid in FORMULA:
        verify(artifacts[rid], read_bytes(os.path.join(archives, KNOWN[rid])))
    write_text(out_path, text)
    print("rendered %s for %s" % (out_path, fmt(version)))
    return version


def report(version):
    """For the workflow: whether the formula changed, and to which version."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write("changed=%s\n" % ("true" if version else "false"))
            if version:
                f.write("version=%s\n" % fmt(version))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Keeps Formula/jason.rb at Jason's latest release.")
    commands = ap.add_subparsers(dest="command", required=True)
    b = commands.add_parser("bump", help="read the latest release from the product address and render the formula")
    b.add_argument("--formula", default="Formula/jason.rb")
    b.add_argument("--template", default=".github/formula/jason.rb.template")
    r = commands.add_parser("render", help="the same checks and rendering, from local files")
    for option in ("--manifest", "--archives", "--formula", "--template", "--out"):
        r.add_argument(option, required=True)
    args = ap.parse_args(argv)
    try:
        if args.command == "bump":
            version = bump(args.formula, args.template)
        else:
            version = render_local(args.manifest, args.archives, args.formula, args.template, args.out)
    except (Refused, OSError) as e:
        print("FAIL: %s. Nothing was written." % e, file=sys.stderr)
        return 1
    report(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
