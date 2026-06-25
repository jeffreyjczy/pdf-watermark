from pdf_toolkit.app import main


if __name__ == "__main__":
    main()


# Windows build script:
# pyinstaller --onefile --windowed --add-data "fonts;fonts" main.py
#
# macOS build script:
# source venv/bin/activate
# pyinstaller --onefile --windowed --add-data "fonts:fonts" main.py
