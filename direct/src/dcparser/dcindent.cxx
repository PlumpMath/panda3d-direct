// Filename: dcindent.cxx
// Created by:  drose (05May00)
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

#include "dcindent.h"

#ifndef WITHIN_PANDA

////////////////////////////////////////////////////////////////////
//     Function: indent
//  Description:
////////////////////////////////////////////////////////////////////
ostream &
indent(ostream &out, int indent_level) {
  for (int i = 0; i < indent_level; i++) {
    out << ' ';
  }
  return out;
}

#endif
