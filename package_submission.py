"""
Packages the soft copy submission ZIP according to official guidelines:
RollNo_Name_ProjectCode.zip -> 23ESKCS822_SumanKumar_CSL-G53.zip
Contains:
1. Report PDF (23ESKCS822_SumanKumar_CSL-G53.pdf)
2. Complete Source Code (crypto, network, ui, tests, shared_files, report_assets, cli.py, etc.)
3. Documentation (README.md, REPORT.md, VIVA_QUESTIONS.md)
"""

import os
import zipfile

ZIP_NAME = "23ESKCS822_SumanKumar_CSL-G53.zip"

INCLUDE_FILES = [
    "23ESKCS822_SumanKumar_CSL-G53.pdf",
    "README.md",
    "REPORT.md",
    "VIVA_QUESTIONS.md",
    "cli.py",
    "generate_benchmarks.py",
    "generate_pdf_report.py",
]

INCLUDE_DIRS = [
    "crypto",
    "network",
    "ui",
    "tests",
    "shared_files",
    "report_assets"
]

EXCLUDE_EXTS = [".pyc", ".zip"]
EXCLUDE_DIRS = ["__pycache__", ".git", ".pytest_cache", "received_files", "received_demo"]


def make_zip():
    print(f"[*] Creating submission archive: {ZIP_NAME}...")
    with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add single files
        for fname in INCLUDE_FILES:
            if os.path.exists(fname):
                zipf.write(fname, arcname=fname)
                print(f"  + Added file: {fname}")

        # Add directories
        for dname in INCLUDE_DIRS:
            if os.path.exists(dname):
                for root, dirs, files in os.walk(dname):
                    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                    for file in files:
                        if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                            continue
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=rel_path)
                        print(f"  + Added file: {rel_path}")

    size_kb = os.path.getsize(ZIP_NAME) / 1024
    print(f"\n[+] Submission ZIP package created successfully!")
    print(f"    File: {os.path.abspath(ZIP_NAME)}")
    print(f"    Size: {size_kb:.2f} KB\n")


if __name__ == "__main__":
    make_zip()

