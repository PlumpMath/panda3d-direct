// Filename: showBase.h
// Created by:  shochet (02Feb00)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) 2001, Disney Enterprises, Inc.  All rights reserved
//
// All use of this software is subject to the terms of the Panda 3d
// Software license.  You should have received a copy of this license
// along with this source code; you will also find a current copy of
// the license at http://www.panda3d.org/license.txt .
//
// To contact the maintainers of this program write to
// panda3d@yahoogroups.com .
//
////////////////////////////////////////////////////////////////////

#ifndef SHOWBASE_H
#define SHOWBASE_H

#include "directbase.h"

#include "eventHandler.h"
#include "graphicsPipe.h"
#include "graphicsWindow.h"
#include "animControl.h"
#include "pointerTo.h"
#include "dconfig.h"
#include "dSearchPath.h"
#include "nodePath.h"
#include "chancfg.h"

ConfigureDecl(config_showbase, EXPCL_DIRECT, EXPTP_DIRECT);
typedef Config::Config<ConfigureGetConfig_config_showbase> ConfigShowbase;

class CollisionTraverser;
class Camera;
class GraphicsEngine;

BEGIN_PUBLISH

EXPCL_DIRECT DSearchPath &get_particle_path();

EXPCL_DIRECT PT(GraphicsPipe) make_graphics_pipe();
EXPCL_DIRECT ChanConfig
make_graphics_window(GraphicsEngine *engine, GraphicsPipe *pipe,
                     const NodePath &render);

EXPCL_DIRECT void throw_new_frame();

EXPCL_DIRECT void take_snapshot(GraphicsWindow *win, const string &name);

EXPCL_DIRECT ConfigShowbase &get_config_showbase();


// klunky interface since we cant pass array from python->C++
EXPCL_DIRECT void add_fullscreen_testsize(unsigned int xsize,unsigned int ysize);
EXPCL_DIRECT void runtest_fullscreen_sizes(GraphicsWindow *win);
EXPCL_DIRECT bool query_fullscreen_testresult(unsigned int xsize,unsigned int ysize);

END_PUBLISH

#endif
