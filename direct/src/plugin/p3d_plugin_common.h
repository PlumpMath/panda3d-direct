// Filename: p3d_plugin_common.h
// Created by:  drose (29May09)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) Carnegie Mellon University.  All rights reserved.
//
// All use of this software is subject to the terms of the revised BSD
// license.  You should have received a copy of this license along
// with this source code in a file named "LICENSE."
//
////////////////////////////////////////////////////////////////////

#ifndef P3D_PLUGIN_COMMON
#define P3D_PLUGIN_COMMON

// This header file is included by all C++ files in this directory; it
// provides some common symbol declarations.

#define P3D_FUNCTION_PROTOTYPES
#define BUILDING_P3D_PLUGIN

#include "p3d_plugin.h"

#include <iostream>
#include <string>
#include <assert.h>

using namespace std;

#define INLINE inline

#ifdef _WIN32
#define LOCK CRITICAL_SECTION
#define INIT_LOCK(lock) InitializeCriticalSection(&(lock))
#define ACQUIRE_LOCK(lock) EnterCriticalSection(&(lock))
#define RELEASE_LOCK(lock) LeaveCriticalSection(&(lock))
#define DESTROY_LOCK(lock) DeleteCriticalSection(&(lock))
#endif

#endif

