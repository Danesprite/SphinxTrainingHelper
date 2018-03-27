#!/usr/bin/python3

"""
Script to create Sphinx training transcription and fileids files.

Note that input files can have empty lines, single line comments starting with '#' or
in-line comments at the end of sentence lines.
"""

import os
import sys
import argparse


def print_err(msg):
    # Write an error message to stderr
    with sys.stderr as f:
        f.write("%s\n" % msg)


def generate_files(in_file, out_dir):
    """
    Generate the transcription and fileids files from the in_file.
    :param in_file: file object open for reading the input file
    """
    # Get the transcription name - the name of the input file minus its extension
    name = os.path.splitext(os.path.basename(in_file.name))[0]

    open_files = [in_file]
    def close_files():
        while open_files:
            open_files.pop().close()

    def open_file(path, mode):
        try:
            result = open(path, mode)
            open_files.append(result)
            return result
        except IOError as e:
            print_err("Couldn't open '%s' with mode '%s': %s" % (path, mode, e))
            close_files()  # close any opened files
            exit(1)

    # Open the transcription and fileids files in writing mode.
    transcription_filename = "%s.transcription" % name
    fileids_filename = "%s.fileids" % name
    if out_dir:
        # If specified, use the output directory.
        f2 = open_file(os.path.join(out_dir, transcription_filename), "w")
        f3 = open_file(os.path.join(out_dir, fileids_filename), "w")
    else:
        # Otherwise open the files in the working directory.
        f2 = open_file(transcription_filename, "w")
        f3 = open_file(fileids_filename, "w")

    try:
        # Process each line in the input file
        count = 1
        for line in in_file.readlines():
            # Strip white space and any line comment or in-line comment
            line = line.strip().split("#")[0]

            # Skip empty or commented lines in the input file
            if not line:
                continue

            # Note: %04d will produce leading zeros, e.g. 0005, 0014
            transcription_id = "%s_%04d" % (name, count)
            count += 1
            try:
                # Write appropriate data to the transcription files
                f2.write("<s> %s </s> (%s)\n" % (line.strip(), transcription_id))
                f3.write("%s\n" % transcription_id)
            except IOError as e:
                print_err("Couldn't write to transcription file: %s" % e)
                close_files()
                exit(1)
    except IOError as e:
        print_err("Unable to read '%s': %s" % (in_file.name, e))
        close_files()
        exit(1)

    # Finished. Close any open files.
    close_files()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="make_transcript_files",
        description="Generate CMU Sphinx transcription and fileids files from a "
        "file of training sentences."
    )
    parser.add_argument("input_file", type=argparse.FileType("r"),
                        help="Input file containing a list training sentences. "
                        "Empty lines or commented lines beginning with '#' will be "
                        "ignored, as will inline comments.")

    def directory(path):
        """
        Pseudo-type function for validating the optional output directory path,
        creating the directory if it doesn't exist and displaying error messages
        appropriately.
        :param path: path string | None
        :returns: valid directory path | None
        """
        if not path:
            return
        exists = os.path.exists(path)

        # Check that the specified path is a directory.
        if exists and not os.path.isdir(path):
            parser.print_usage()
            print_err("Expected directory path '%s' is not a directory." % path)
            exit(1)

        # If it doesn't exist, then try to create it.
        if not exists:
            try:
                os.mkdir(path)
            except OSError as e:
                parser.print_usage()
                print_err("Failed to create output directory '%s': %s" % (path, e))
                exit(1)
        return path

    parser.add_argument("--out-dir", type=directory, default=None,
                        help="Output directory for generated transcription files. "
                        "By default, this is the current working directory. If the "
                        "specified directory does not exist, this program will "
                        "attempt to create it.")
    args = parser.parse_args()

    # Generate the transcription files
    generate_files(args.input_file, args.out_dir)

