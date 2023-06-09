from __future__ import print_function

import argparse
import os.path
import re
import sys
import textwrap
import warnings

import requests
import six

from . import __version__
from ._indent import indent
from .custom_download import custom_download
from .custom_download_folder import MAX_NUMBER_FILES
from .exceptions import FileURLRetrievalError
from .exceptions import FolderContentsMaximumLimitError


class _ShowVersionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(
            "ExclusiveDownloader {ver} located at {pos}".format(
                ver=__version__, pos=os.path.dirname(os.path.dirname(__file__))
            )
        )
        parser.exit()


def calculate_file_size(argv):
    if argv is not None:
        m = re.match(r"([0-9]+)(GB|MB|KB|B)", argv)
        if not m:
            raise TypeError
        size, unit = m.groups()
        size = float(size)
        if unit == "KB":
            size *= 1024
        elif unit == "MB":
            size *= 1024**2
        elif unit == "GB":
            size *= 1024**3
        elif unit == "B":
            pass
        return size


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-V",
        "--version",
        action=_ShowVersionAction,
        help="display version",
        nargs=0,
    )
    parser.add_argument(
        "url_or_id", help="URL or file/folder ID (with --id) to download from"
    )
    parser.add_argument("-O", "--output", help="output file name / path")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress logging except errors",
    )
    parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="(file only) extract Google Drive's file ID",
    )
    parser.add_argument(
        "--id",
        action="store_true",
        help="[DEPRECATED] flag to specify file/folder ID instead of URL",
    )
    parser.add_argument(
        "--proxy",
        help="<protocol://host:port> download using the specified proxy",
    )
    parser.add_argument(
        "--speed",
        type=calculate_file_size,
        help="download speed limit in seconds (e.g., '10MB' -> 10MB/s)",
    )
    parser.add_argument(
        "--no-cookies",
        action="store_true",
        help="don't use cookies in ~/.cache/gdown/cookies.json",
    )
    parser.add_argument(
        "--no-check-certificate",
        action="store_true",
        help="don't check the server's TLS certificate",
    )
    parser.add_argument(
        "--continue",
        "-c",
        dest="continue_",
        action="store_true",
        help="(file only) resume getting a partially-downloaded file",
    )
    parser.add_argument(
        "--folder",
        action="store_true",
        help="download the entire folder instead of a single file "
        "(maximum {max} files per folder)".format(max=MAX_NUMBER_FILES),
    )
    parser.add_argument(
        "--remaining-ok",
        action="store_true",
        help="(folder only) assert that it's okay to download a maximum "
        "of {max} files per folder.".format(max=MAX_NUMBER_FILES),
    )
    parser.add_argument(
        "--format",
        help="Format of Google Docs, Spreadsheets, and Slides. "
        "Default is Google Docs: 'docx', Spreadsheet: 'xlsx', Slides: 'pptx'.",
    )

    args = parser.parse_args()

    if args.output == "-":
        if six.PY3:
            args.output = sys.stdout.buffer
        else:
            args.output = sys.stdout

    if args.id:
        warnings.warn(
            "Option",
            category=FutureWarning,
        )
        url = None
        file_id = args.url_or_id
    else:
        if re.match("^https?://.*", args.url_or_id):
            url = args.url_or_id
            file_id = None
        else:
            url = None
            file_id = args.url_or_id

    try:
        if args.folder:
            download_folder(
                url=url,
                file_id=file_id,
                output=args.output,
                quiet=args.quiet,
                proxy=args.proxy,
                speed=args.speed,
                use_cookies=not args.no_cookies,
                verify=not args.no_check_certificate,
                remaining_ok=args.remaining_ok,
            )
        else:
            custom_download(
                url=url,
                output=args.output,
                quiet=args.quiet,
                proxy=args.proxy,
                speed=args.speed,
                use_cookies=not args.no_cookies,
                verify=not args.no_check_certificate,
                file_id=file_id,
                fuzzy=args.fuzzy,
                resume=args.continue_,
                format=args.format,
            )
    except FileURLRetrievalError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except FolderContentsMaximumLimitError as e:
        print(
            "Failed to retrieve folder contents:\n\n{}\n\n"
            "You can use the `--remaining-ok` option to ignore this error.".format(
                indent("\n".join(textwrap.wrap(str(e))), prefix="\t")
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.ProxyError as e:
        print(
            "Failed to use proxy:\n\n{}\n\n"
            "Please check your proxy settings.".format(
                indent("\n".join(textwrap.wrap(str(e))), prefix="\t")
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(
            "Error",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
