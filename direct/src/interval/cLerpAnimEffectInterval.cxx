// Filename: cLerpAnimEffectInterval.cxx
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

#include "cLerpAnimEffectInterval.h"
#include "lerp_helpers.h"
#include "partBundle.h"

TypeHandle CLerpAnimEffectInterval::_type_handle;

////////////////////////////////////////////////////////////////////
//     Function: CLerpAnimEffectInterval::step
//       Access: Published, Virtual
//  Description: Advances the time on the interval.  The time may
//               either increase (the normal case) or decrease
//               (e.g. if the interval is being played by a slider).
////////////////////////////////////////////////////////////////////
void CLerpAnimEffectInterval::
priv_step(double t) {
  check_started(get_class_type(), "priv_step");
  _state = S_started;
  double d = compute_delta(t);

  Controls::iterator ci;
  for (ci = _controls.begin(); ci != _controls.end(); ++ci) {
    ControlDef &def = (*ci);
    float effect;
    lerp_value(effect, d, def._begin_effect, def._end_effect);
    def._control->get_part()->set_control_effect(def._control, effect);
  }

  _curr_t = t;
}

////////////////////////////////////////////////////////////////////
//     Function: CLerpAnimEffectInterval::output
//       Access: Published, Virtual
//  Description: 
////////////////////////////////////////////////////////////////////
void CLerpAnimEffectInterval::
output(ostream &out) const {
  out << get_name() << ": ";

  if (_controls.empty()) {
    out << "(no controls)";
  } else {
    Controls::const_iterator ci;
    ci = _controls.begin();
    out << (*ci)._name;
    ++ci;
    while (ci != _controls.end()) {
      out << ", " << (*ci)._name;
      ++ci;
    }
  }

  out << " dur " << get_duration();
}
