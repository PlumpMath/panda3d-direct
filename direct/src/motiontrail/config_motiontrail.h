// Filename: config_interval.h
// Created by:  drose (27Aug02)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) 2001 - 2004, Disney Enterprises, Inc.  All rights reserved
//
// All use of this software is subject to the terms of the Panda 3d
// Software license.  You should have received a copy of this license
// along with this source code; you will also find a current copy of
// the license at http://etc.cmu.edu/panda3d/docs/license/ .
//
// To contact the maintainers of this program write to
// panda3d-general@lists.sourceforge.net .
//
////////////////////////////////////////////////////////////////////

#ifndef CONFIG_MOTIONTRAIL_H
#define CONFIG_MOTIONTRAIL_H

#include "directbase.h"
#include "notifyCategoryProxy.h"
#include "dconfig.h"

#include "cMotionTrail.h"

NotifyCategoryDecl(motiontrail, EXPCL_DIRECT, EXPTP_DIRECT);

extern EXPCL_DIRECT void init_libmotiontrail();

#endif
