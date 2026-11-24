#!/usr/bin/env bash
set -euo pipefail

repository=${ASCII_SAVER_REPOSITORY:-${KDE_ASCII_SAVER_REPOSITORY:-JustAdreamerFL/ascii-saver}}
requested_version=${ASCII_SAVER_VERSION:-latest}
release_base_url=${ASCII_SAVER_RELEASE_BASE_URL:-"https://github.com/$repository/releases"}
mode=package
check_only=0
installer_args=()
temporary_dir=

usage() {
    cat <<'EOF'
Usage: install-online.sh [OPTIONS] [-- INSTALL_OPTIONS]

Install ASCII Saver from the latest GitHub release. By default the installer
detects the current distribution and installs the matching native package
without creating a virtual environment or building Rust.

Options:
  --version VERSION   Install a specific release (for example 0.111.0 or v0.111.0)
  --source            Build the user-local installation from source instead
  --check             Verify the selected package (or source dependencies) only
  --yes               Non-interactive source dependency installation
  --no-install-deps   Source mode: only print dependency guidance
  --no-start          Source mode: leave session processes untouched
  --non-interactive   Source mode: disable installer prompts
  -h, --help          Show this help

Environment overrides:
  ASCII_SAVER_VERSION           Release version, or "latest"
  ASCII_SAVER_REPOSITORY        GitHub owner/repository
  ASCII_SAVER_RELEASE_BASE_URL  Release URL base (intended for testing)
  ASCII_SAVER_OS_RELEASE        Alternate os-release file (intended for testing)
  ASCII_SAVER_NO_SESSION=1      Prevent source installer service actions
EOF
}

while (($#)); do
    case "$1" in
        --version)
            if (($# < 2)); then
                printf '%s\n' '--version requires a value' >&2
                exit 2
            fi
            requested_version=$2
            shift
            ;;
        --source)
            mode=source
            ;;
        --check)
            check_only=1
            installer_args+=("$1")
            ;;
        --yes|--no-install-deps|--no-start|--non-interactive)
            installer_args+=("$1")
            ;;
        --)
            shift
            installer_args+=("$@")
            break
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

for command in curl; do
    if ! command -v "$command" >/dev/null; then
        printf 'Required download command not found: %s\n' "$command" >&2
        exit 1
    fi
done
if command -v sha256sum >/dev/null; then
    checksum_tool=sha256sum
elif command -v shasum >/dev/null; then
    checksum_tool=shasum
else
    printf 'A SHA-256 tool is required (sha256sum or shasum).\n' >&2
    exit 1
fi
if [[ "$mode" == source ]] && ! command -v python3 >/dev/null; then
    printf 'Source installation requires Python 3. Use the default package mode or install Python first.\n' >&2
    exit 1
fi

case "$release_base_url" in
    https://*) curl_protocol='=https' ;;
    file://*) curl_protocol='=file' ;;
    *)
        printf 'Release URL must use HTTPS (or file:// for local testing).\n' >&2
        exit 2
        ;;
esac

if [[ "$requested_version" == latest ]]; then
    download_base="$release_base_url/latest/download"
else
    version=${requested_version#v}
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
        printf 'Invalid release version: %s\n' "$requested_version" >&2
        exit 2
    fi
    download_base="$release_base_url/download/v$version"
fi

temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/ascii-saver-download.XXXXXX")
chmod 0700 "$temporary_dir"
cleanup() {
    local status=$?
    trap - EXIT INT TERM HUP
    if [[ -n "$temporary_dir" && -d "$temporary_dir" ]]; then
        rm -rf -- "$temporary_dir"
    fi
    exit "$status"
}
trap cleanup EXIT INT TERM HUP

download() {
    local url=$1 output=$2
    curl --fail --silent --show-error --location --proto "$curl_protocol" \
        --proto-redir "$curl_protocol" --tlsv1.2 "$url" --output "$output"
}

sha256_of() {
    if [[ "$checksum_tool" == sha256sum ]]; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

verify_from_manifest() {
    local name=$1 expected actual
    if [[ "$name" == */* || "$name" == *..* ]]; then
        printf 'Unsafe package name in release manifest: %s\n' "$name" >&2
        return 1
    fi
    expected=$(awk -v name="$name" '$2 == name {print $1; exit}' "$temporary_dir/SHA256SUMS")
    if [[ ! "$expected" =~ ^[[:xdigit:]]{64}$ ]]; then
        printf 'No checksum found for %s; refusing to install.\n' "$name" >&2
        return 1
    fi
    actual=$(sha256_of "$temporary_dir/$name")
    if [[ "${actual,,}" != "${expected,,}" ]]; then
        printf 'SHA-256 verification failed; refusing to install.\n' >&2
        return 1
    fi
}

install_package() {
    local os_release_file=${ASCII_SAVER_OS_RELEASE:-/etc/os-release}
    local os_id os_like os_version version_major machine
    local manager package_pattern package_name arch
    local -a privilege=()

    if [[ ! -r "$os_release_file" ]]; then
        printf 'Cannot read %s; use --source or install a release package manually.\n' "$os_release_file" >&2
        exit 1
    fi
    os_id=$(. "$os_release_file" >/dev/null 2>&1; printf '%s' "${ID:-}")
    os_like=$(. "$os_release_file" >/dev/null 2>&1; printf '%s' "${ID_LIKE:-}")
    os_version=$(. "$os_release_file" >/dev/null 2>&1; printf '%s' "${VERSION_ID:-}")
    os_id=${os_id,,}
    os_like=${os_like,,}
    version_major=${os_version%%.*}

    machine=$(uname -m)
    case "$machine" in
        x86_64) arch=x86_64; deb_arch=amd64 ;;
        aarch64|arm64) arch=aarch64; deb_arch=arm64 ;;
        *)
            printf 'No native package is available for architecture %s; use --source.\n' "$machine" >&2
            exit 1
            ;;
    esac

    if ! download "$download_base/SHA256SUMS" "$temporary_dir/SHA256SUMS"; then
        printf 'This release does not provide a package manifest. Use --source to build from source.\n' >&2
        exit 1
    fi

    if [[ "$os_id" == debian || "$os_id" == ubuntu || "$os_like" == *debian* || "$os_like" == *ubuntu* ]]; then
        if [[ "$os_id" == debian ]] && { [[ ! "$version_major" =~ ^[0-9]+$ ]] || ((version_major < 13)); }; then
            printf 'Native packages require Debian 13 or newer (detected %s). Use --source to build from source.\n' "${os_version:-unknown}" >&2
            exit 1
        fi
        if [[ "$os_id" == ubuntu ]] && { [[ ! "$version_major" =~ ^[0-9]+$ ]] || ((version_major < 26)); }; then
            printf 'Native packages require Ubuntu 26.04 or newer (detected %s). Use --source to build from source.\n' "${os_version:-unknown}" >&2
            exit 1
        fi
        manager=apt-get
        package_pattern="^ascii-saver_[0-9][^_]*_${deb_arch}\\.deb$"
    elif [[ "$os_id" == fedora ]]; then
        if [[ ! "$os_version" =~ ^[0-9]+$ ]]; then
            printf 'Cannot determine a supported Fedora release (detected %s). Use --source.\n' "${os_version:-unknown}" >&2
            exit 1
        fi
        manager=dnf
        package_pattern="^ascii-saver-[0-9.]+-[0-9]+\\.fc${os_version}\\.${arch}\\.rpm$"
    elif [[ "$os_id" == arch || "$os_like" == *arch* ]]; then
        manager=pacman
        package_pattern="^ascii-saver-[0-9.]+-[0-9]+-${arch}\\.pkg\\.tar\\.zst$"
    else
        printf 'No native package is available for %s %s. Use --source to build from source.\n' \
            "${os_id:-unknown distro}" "${os_version:-}" >&2
        exit 1
    fi

    package_name=
    while read -r _ name; do
        if [[ -n "$name" && "$name" =~ $package_pattern ]]; then
            package_name=$name
            break
        fi
    done <"$temporary_dir/SHA256SUMS"
    if [[ -z "$package_name" ]]; then
        printf 'No matching package for %s %s (%s) in this release.\n' \
            "${os_id:-unknown}" "${os_version:-unknown}" "$machine" >&2
        printf 'Available native packages:\n' >&2
        while read -r _ name; do
            case "$name" in
                *.deb|*.rpm|*.pkg.tar.zst) printf '  %s\n' "$name" >&2 ;;
            esac
        done <"$temporary_dir/SHA256SUMS"
        printf 'Use --source to build from source, or install a package from another release.\n' >&2
        exit 1
    fi

    printf 'Selected %s package: %s\n' "$os_id" "$package_name"
    download "$download_base/$package_name" "$temporary_dir/$package_name"
    verify_from_manifest "$package_name"
    printf 'SHA-256 verified.\n'

    if ((check_only)); then
        printf 'Package is available and verified.\n'
        return 0
    fi

    if ((EUID != 0)); then
        if command -v sudo >/dev/null; then
            privilege=(sudo)
        elif command -v pkexec >/dev/null; then
            privilege=(pkexec)
        else
            printf 'Root privileges are required. Install sudo or run as root.\n' >&2
            exit 1
        fi
    fi

    case "$manager" in
        apt-get)
            "${privilege[@]}" apt-get install -y "$temporary_dir/$package_name"
            ;;
        dnf)
            "${privilege[@]}" dnf install -y "$temporary_dir/$package_name"
            ;;
        pacman)
            "${privilege[@]}" pacman -U --needed --noconfirm "$temporary_dir/$package_name"
            ;;
    esac
    printf 'ASCII Saver installed. Remove it with the system package manager.\n'
}

install_source() {
    local archive_name checksum_name checksum_line expected_checksum actual_checksum
    local -a roots

    if [[ "$requested_version" == latest ]]; then
        archive_name=ascii-saver.tar.gz
    else
        archive_name="ascii-saver-$version.tar.gz"
    fi
    checksum_name="$archive_name.sha256"

    printf 'Downloading ASCII Saver %s source...\n' "$requested_version"
    download "$download_base/$archive_name" "$temporary_dir/$archive_name"
    download "$download_base/$checksum_name" "$temporary_dir/$checksum_name"

    checksum_line=$(head -n 1 "$temporary_dir/$checksum_name")
    if [[ ! "$checksum_line" =~ ^([[:xdigit:]]{64})[[:space:]][[:space:]\*]([^/]+)$ ]] || \
        [[ "${BASH_REMATCH[2]}" != "$archive_name" ]]; then
        printf 'Invalid checksum file received; refusing to install.\n' >&2
        exit 1
    fi
    expected_checksum=${BASH_REMATCH[1],,}
    actual_checksum=$(sha256_of "$temporary_dir/$archive_name")
    if [[ "$actual_checksum" != "$expected_checksum" ]]; then
        printf 'SHA-256 verification failed; refusing to install.\n' >&2
        exit 1
    fi
    printf 'SHA-256 verified.\n'

    mkdir "$temporary_dir/source"
    # Release archives contain only regular files and directories. Reject links,
    # device nodes, absolute names, and parent traversal before extracting.
    if ! python3 - "$temporary_dir/$archive_name" "$temporary_dir/source" <<'PY'
import pathlib
import shutil
import sys
import tarfile

archive, destination = sys.argv[1:]
destination_path = pathlib.Path(destination)
with tarfile.open(archive, "r:gz") as release:
    members = release.getmembers()
    if len(members) > 10_000 or sum(member.size for member in members) > 100 * 1024 * 1024:
        raise SystemExit("release archive exceeds safety limits")
    for member in members:
        path = pathlib.PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
            raise SystemExit(f"unsafe archive member: {member.name}")
        target = destination_path.joinpath(*path.parts)
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            target.chmod(0o755)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        source = release.extractfile(member)
        if source is None:
            raise SystemExit(f"could not read archive member: {member.name}")
        with source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
        target.chmod(0o755 if member.mode & 0o111 else 0o644)
PY
    then
        printf 'Release archive failed safety validation; refusing to install.\n' >&2
        exit 1
    fi
    mapfile -t roots < <(find "$temporary_dir/source" -mindepth 1 -maxdepth 1 -type d -print)
    if [[ ${#roots[@]} -ne 1 || ! -x "${roots[0]}/install.sh" ]]; then
        printf 'Release archive does not contain one installable source directory.\n' >&2
        exit 1
    fi

    "${roots[0]}/install.sh" "${installer_args[@]}"
}

if [[ "$mode" == source ]]; then
    install_source
else
    install_package
fi
