TEMPLATE = app
QT = quick
DEFINES += QT_DEPRECATED_WARNINGS
CONFIG += warn_off c++11 release
dev {
    CONFIG += debug
}

BUILD_DIR = build
MOC_DIR = $$BUILD_DIR/moc
OBJECTS_DIR = $$BUILD_DIR/obj
RCC_DIR = $$BUILD_DIR/rcc

QRC_FILE = $$BUILD_DIR/resources.qrc
!no_embedded {
    RESOURCES += $$QRC_FILE
}

SOURCES += src/main.cpp
TARGET = harmonyqml


# Libraries includes

include(submodules/SortFilterProxyModel/SortFilterProxyModel.pri)


# Custom functions

defineReplace(glob_filenames) {
    for(pattern, ARGS) {
        results *= $$files(src/$${pattern}, true)
    }
    return($$results)
}


# Generate resource file

RESOURCE_FILES *= $$glob_filenames(qmldir, *.qml, *.js, *.py)
RESOURCE_FILES *= $$glob_filenames( *.jpg, *.jpeg, *.png, *.svg)

file_content += '<!-- vim: set ft=xml : -->'
file_content += '<!DOCTYPE RCC>'
file_content += '<RCC version="1.0">'
file_content += '<qresource prefix="/">'

for(file, RESOURCE_FILES) {
    alias = $$replace(file, src/, '')
    file_content += '    <file alias="$$alias">../$$file</file>'
}

file_content += '</qresource>'
file_content += '</RCC>'

write_file($$QRC_FILE, file_content)


# Add stuff to `make clean`

# Allow cleaning folders instead of just files
win32:QMAKE_DEL_FILE = rmdir /q /s
unix:QMAKE_DEL_FILE = rm -rf

for(file, $$list($$glob_filenames(*.py))) {
    PYCACHE_DIRS *= $$dirname(file)/__pycache__
}

QMAKE_CLEAN *= $$MOC_DIR $$OBJECTS_DIR $$RCC_DIR $$PYCACHE_DIRS $$QRC_FILE
QMAKE_CLEAN *= $$BUILD_DIR Makefile .qmake.stash
QMAKE_CLEAN *= $$glob_filenames(*.pyc, *.qmlc, *.jsc, *.egg-info)