#!/usr/bin/env bash
# Build the free true-3D toolchain for orbitalatlas.pbrt3d in a cloud container without X11/OpenGL dev files:
#   pbrt-v4 (Apache-2.0, github.com/mmp/pbrt-v4), CPU build, interactive viewer stubbed out (headless);
#   Intel Open Image Denoise 2.3.3 (Apache-2.0, github.com/RenderKit/oidn) prebuilt Linux binaries.
# Only github.com is needed (download.blender.org / PyPI / Ubuntu mirrors may be blocked by the network policy).
# Usage: tools/pbrt3d/build_toolchain.sh [DIR]   -> DIR/pbrt-v4/build/{pbrt,imgtool}, DIR/oidn-2.3.3.x86_64.linux/bin/oidnDenoise
# Then: export PBRT_BIN=DIR/pbrt-v4/build OIDN_BIN=DIR/oidn-2.3.3.x86_64.linux/bin     (about 15 min on 4 cores)
set -euo pipefail
DIR="${1:-/tmp/claude-0/s3d}"; mkdir -p "$DIR"; cd "$DIR"
[ -d pbrt-v4 ] || git clone -q --recursive --depth 1 --shallow-submodules https://github.com/mmp/pbrt-v4.git
[ -d oidn-2.3.3.x86_64.linux ] || { curl -sL -o oidn.tgz https://github.com/RenderKit/oidn/releases/download/v2.3.3/oidn-2.3.3.x86_64.linux.tar.gz && tar xzf oidn.tgz && rm oidn.tgz; }
cd pbrt-v4
python3 - <<'PY'
import os
h = open("src/pbrt/util/gui.h").read()
if "#include <glad/glad.h>" in h:
    h = h.replace("#include <glad/glad.h>\n#include <GLFW/glfw3.h>\n", "// headless build: no OpenGL/GLFW\nstruct GLFWwindow;\n"); open("src/pbrt/util/gui.h", "w").write(h)
open("src/pbrt/util/gui.cpp", "w").write('''// Headless stub of pbrt's interactive viewer (no X11/OpenGL in the render container).
#include <pbrt/util/gui.h>
#include <pbrt/util/error.h>
namespace pbrt {
GUI::GUI(std::string title, Vector2i resolution, Bounds3f sceneBounds) { ErrorExit("pbrt built without the interactive viewer"); }
GUI::~GUI() {}
DisplayState GUI::RefreshDisplay() { return EXIT; }
void GUI::keyboardCallback(GLFWwindow *, int, int, int, int) {}
void GUI::cursorPosCallback(GLFWwindow *, double, double) {}
void GUI::mouseButtonCallback(GLFWwindow *, int, int, int) {}
void GUI::Initialize() { ErrorExit("pbrt built without the interactive viewer"); }
Point2i GUI::GetResolution() { return Point2i(0, 0); }
bool GUI::processKeys() { return false; }
bool GUI::processMouse() { return false; }
bool GUI::process() { return false; }
}  // namespace pbrt
''')
c = open("CMakeLists.txt").read()
c = c.replace("find_package(OpenGL REQUIRED)", "# find_package(OpenGL REQUIRED)  # headless build").replace("  utf8proc\n  glfw\n  glad\n  OpenGL::GL)", "  utf8proc)")
open("CMakeLists.txt", "w").write(c)
e = open("src/ext/CMakeLists.txt").read()
e = e.replace("add_subdirectory (glfw)\nadd_subdirectory (glad)", "# add_subdirectory (glfw)\n# add_subdirectory (glad)  # headless build")
e = e.replace('set_property (TARGET glfw PROPERTY FOLDER "ext")\nset_property (TARGET glad PROPERTY FOLDER "ext")', "")
open("src/ext/CMakeLists.txt", "w").write(e)
PY
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DPBRT_BUILD_NATIVE_EXECUTABLE=ON > cmake.log 2>&1
make -j"$(nproc)" pbrt_exe imgtool > make.log 2>&1
./pbrt --version 2>&1 | head -1 || true
echo "PBRT_BIN=$PWD  OIDN_BIN=$DIR/oidn-2.3.3.x86_64.linux/bin"
