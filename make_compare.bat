cd tests\syntax

call ..\..\venv-friendly3.6\scripts\activate
call python compile_data.py
call deactivate

call ..\..\venv-friendly3.7\scripts\activate
call python compile_data.py
call deactivate

call ..\..\venv-friendly3.8\scripts\activate
call python compile_data.py
call deactivate

call python compare_data.py > ..\..\..\friendly-traceback-docs\docs\source\compare_data.html

cd ..\..\..\friendly-traceback-docs\docs
call make html
cd ..\..\friendly-traceback
