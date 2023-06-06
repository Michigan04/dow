from __future__ import print_function

import hashlib
import os
import os.path as osp
import shutil
import sys
import tempfile

import filelock

from .custom_download import custom_download

custom_cache_root = osp.join(osp.expanduser("~"), ".custom_cache/gdown")
if not osp.exists(custom_cache_root):
    try:
        os.makedirs(custom_cache_root)
    except OSError:
        pass


def calculate_md5sum(file_path, block_size=None):
    if block_size is None:
        block_size = 65536

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(block_size), b""):
            hash_md5.update(block)
    return hash_md5.hexdigest()


def validate_md5sum(file_path, expected_md5, silent=False, block_size=None):
    if not (isinstance(expected_md5, str) and len(expected_md5) == 32):
        raise ValueError("Expected MD5 must be 32 characters long: {}".format(expected_md5))

    if not silent:
        print("Calculating MD5: {}".format(file_path))
    actual_md5 = calculate_md5sum(file_path, block_size)

    if actual_md5 == expected_md5:
        if not silent:
            print("MD5 matches: {}".format(file_path))
        return True

    raise AssertionError(
        "MD5 mismatch:\nActual: {}\nExpected: {}".format(actual_md5, expected_md5)
    )


def cached_custom_download(
    url=None, file_path=None, expected_md5=None, silent=False, postprocess=None, **kwargs
):
    """Cached download from a URL.

    Parameters
    ----------
    url: str
        URL. Supports Google Drive URLs.
    file_path: str, optional
        Output filename. By default, it uses the basename of the URL.
    expected_md5: str, optional
        Expected MD5 checksum for the file.
    silent: bool
        Suppress terminal output. Default is False.
    postprocess: callable
        Function called with the filename as postprocess.
    kwargs: dict
        Keyword arguments to be passed to `custom_download`.

    Returns
    -------
    file_path: str
        Output filename.
    """
    if file_path is None:
        file_path = (
            url.replace("/", "-SLASH-")
            .replace(":", "-COLON-")
            .replace("=", "-EQUAL-")
            .replace("?", "-QUESTION-")
        )
        file_path = osp.join(custom_cache_root, file_path)

    # Check if the file already exists
    if osp.exists(file_path) and not expected_md5:
        if not silent:
            print("File already exists: {}".format(file_path))
        return file_path
    elif osp.exists(file_path) and expected_md5:
        try:
            validate_md5sum(file_path, expected_md5, silent=silent)
            return file_path
        except AssertionError as e:
            # Display a warning and overwrite the file if the MD5 doesn't match
            print(e, file=sys.stderr)

    # Download the file
    lock_path = osp.join(custom_cache_root, "_dl_lock")
    try:
        os.makedirs(osp.dirname(file_path))
    except OSError:
        pass
    temp_root = tempfile.mkdtemp(dir=custom_cache_root)
    try:
        temp_file_path = osp.join(temp_root, "dl")

        if not silent:
            msg = "Cached Download in progress"
            if file_path:
                msg = "{}: {}".format(msg, file_path)
            else:
                msg = "{}...".format(msg)
            print(msg, file=sys.stderr)

        custom_download(url, temp_file_path, silent=silent, **kwargs)
        with filelock.FileLock(lock_path):
            shutil.move(temp_file_path, file_path)
    except Exception:
        shutil.rmtree(temp_root)
        raise

    if expected_md5:
        validate_md5sum(file_path, expected_md5, silent=silent)

    # Postprocess the file
    if postprocess is not None:
        postprocess(file_path)

    return file_path
