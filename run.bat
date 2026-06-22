@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
python setup_fonts.py
python setup_backgrounds.py
python generate_banners.py
python setup_reciter_photos.py
python app.py
