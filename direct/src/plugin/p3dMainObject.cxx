// Filename: p3dMainObject.cxx
// Created by:  drose (10Jul09)
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

#include "p3dMainObject.h"
#include "p3dInstance.h"
#include "p3dSession.h"
#include "p3dStringObject.h"
#include "p3dInstanceManager.h"

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::Constructor
//       Access: Public
//  Description: 
////////////////////////////////////////////////////////////////////
P3DMainObject::
P3DMainObject() :
  _pyobj(NULL)
{
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::Destructor
//       Access: Public, Virtual
//  Description: 
////////////////////////////////////////////////////////////////////
P3DMainObject::
~P3DMainObject() {
  set_pyobj(NULL);

  // Clear the local properties.
  Properties::const_iterator pi;
  for (pi = _properties.begin(); pi != _properties.end(); ++pi) {
    P3D_object *value = (*pi).second;
    P3D_OBJECT_DECREF(value);
  }
  _properties.clear();
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::get_type
//       Access: Public, Virtual
//  Description: Returns the fundamental type of this kind of object.
////////////////////////////////////////////////////////////////////
P3D_object_type P3DMainObject::
get_type() {
  return P3D_OT_object;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::get_bool
//       Access: Public, Virtual
//  Description: Returns the object value coerced to a boolean, if
//               possible.
////////////////////////////////////////////////////////////////////
bool P3DMainObject::
get_bool() {
  return true;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::get_int
//       Access: Public, Virtual
//  Description: Returns the object value coerced to an integer, if
//               possible.
////////////////////////////////////////////////////////////////////
int P3DMainObject::
get_int() {
  return 0;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::get_float
//       Access: Public, Virtual
//  Description: Returns the object value coerced to a floating-point
//               value, if possible.
////////////////////////////////////////////////////////////////////
double P3DMainObject::
get_float() {
  return 0.0;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::make_string
//       Access: Public, Virtual
//  Description: Fills the indicated C++ string object with the value
//               of this object coerced to a string.
////////////////////////////////////////////////////////////////////
void P3DMainObject::
make_string(string &value) {
  if (_pyobj == NULL) {
    value = "P3DMainObject";
  } else {
    int size = P3D_OBJECT_GET_STRING(_pyobj, NULL, 0);
    char *buffer = new char[size];
    P3D_OBJECT_GET_STRING(_pyobj, buffer, size);
    value = string(buffer, size);
    delete[] buffer;
  }    
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::get_property
//       Access: Public, Virtual
//  Description: Returns the named property element in the object.  The
//               return value is a new-reference P3D_object, or NULL
//               on error.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
get_property(const string &property) {
  if (_pyobj == NULL) {
    // Without a pyobj, we just report whatever's been stored locally.
    Properties::const_iterator pi;
    pi = _properties.find(property);
    if (pi != _properties.end()) {
      P3D_object *result = (*pi).second;
      P3D_OBJECT_INCREF(result);
      return result;
    }
    return NULL;
  }

  // With a pyobj, we pass the query down to it.
  return P3D_OBJECT_GET_PROPERTY(_pyobj, property.c_str());
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::set_property
//       Access: Public, Virtual
//  Description: Modifies (or deletes, if value is NULL) the named
//               property element in the object.  Returns true on
//               success, false on failure.
////////////////////////////////////////////////////////////////////
bool P3DMainObject::
set_property(const string &property, P3D_object *value) {
  // First, we set the property locally.
  if (value != NULL) {
    Properties::iterator pi;
    pi = _properties.insert(Properties::value_type(property, NULL)).first;
    assert(pi != _properties.end());
    P3D_object *orig_value = (*pi).second;
    if (orig_value != value) {
      P3D_OBJECT_XDECREF(orig_value);
      (*pi).second = value;
      P3D_OBJECT_INCREF(value);
    }
  } else {
    // (Or delete the property locally.)
    Properties::iterator pi;
    pi = _properties.find(property);
    if (pi != _properties.end()) {
      P3D_object *orig_value = (*pi).second;
      P3D_OBJECT_DECREF(orig_value);
      _properties.erase(pi);
    }
  }

  if (_pyobj == NULL) {
    // Without a pyobj, that's all we do.
    return true;
  }

  // With a pyobj, we also pass this request down.
  return P3D_OBJECT_SET_PROPERTY(_pyobj, property.c_str(), value);
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::has_method
//       Access: Public, Virtual
//  Description: Returns true if the named method exists on this
//               object, false otherwise.
////////////////////////////////////////////////////////////////////
bool P3DMainObject::
has_method(const string &method_name) {
  // Some special-case methods implemented in-place.
  if (method_name == "start") {
    return true;
  } else if (method_name == "read_game_log") {
    return true;
  } else if (method_name == "read_system_log") {
    return true;
  }

  if (_pyobj == NULL) {
    // No methods until we get our pyobj.
    return false;
  }

  return P3D_OBJECT_HAS_METHOD(_pyobj, method_name.c_str());
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::call
//       Access: Public, Virtual
//  Description: Invokes the named method on the object, passing the
//               indicated parameters.  If the method name is empty,
//               invokes the object itself.
//
//               If needs_response is true, the return value is a
//               new-reference P3D_object on success, or NULL on
//               failure.  If needs_response is false, the return
//               value is always NULL, and there is no way to
//               determine success or failure.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
call(const string &method_name, bool needs_response,
     P3D_object *params[], int num_params) {
  if (method_name == "start") {
    return call_start(params, num_params);
  } else if (method_name == "read_game_log") {
    return call_read_game_log(params, num_params);
  } else if (method_name == "read_system_log") {
    return call_read_system_log(params, num_params);
  }

  if (_pyobj == NULL) {
    // No methods until we get our pyobj.
    return NULL;
  }

  return P3D_OBJECT_CALL(_pyobj, method_name.c_str(), needs_response,
                         params, num_params);
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::output
//       Access: Public, Virtual
//  Description: Writes a formatted representation of the value to the
//               indicated string.  This is intended for developer
//               assistance.
////////////////////////////////////////////////////////////////////
void P3DMainObject::
output(ostream &out) {
  out << "P3DMainObject";
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::set_pyobj
//       Access: Public
//  Description: Changes the internal pyobj pointer.  This is the
//               P3D_object that references the actual PyObject held
//               within the child process, corresponding to the true
//               main object there.  The new object's reference
//               count is incremented, and the previous object's is
//               decremented.
////////////////////////////////////////////////////////////////////
void P3DMainObject::
set_pyobj(P3D_object *pyobj) {
  if (_pyobj != pyobj) {
    P3D_OBJECT_XDECREF(_pyobj);
    _pyobj = pyobj;
    if (_pyobj != NULL) {
      P3D_OBJECT_INCREF(_pyobj);

      // Now that we have a pyobj, we have to transfer down all of the
      // properties we'd set locally.
      Properties::const_iterator pi;
      for (pi = _properties.begin(); pi != _properties.end(); ++pi) {
        const string &property_name = (*pi).first;
        P3D_object *value = (*pi).second;
        P3D_OBJECT_SET_PROPERTY(_pyobj, property_name.c_str(), value);
      }
    }
  }
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::get_pyobj
//       Access: Public
//  Description: Returns the internal pyobj pointer, or NULL if it has
//               not yet been set.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
get_pyobj() const {
  return _pyobj;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::set_instance
//       Access: Public
//  Description: Sets a callback pointer to the instance that owns
//               this object.  When this instance destructs, it clears
//               this pointer to NULL.
////////////////////////////////////////////////////////////////////
void P3DMainObject::
set_instance(P3DInstance *inst) {
  _inst = inst;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::call_start
//       Access: Private
//  Description: Starts the process remotely, as if the start button
//               had been clicked.  Only applicable if the application
//               was in the ready state.  Returns true if the
//               application is now started, false otherwise.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
call_start(P3D_object *params[], int num_params) {
  P3DInstanceManager *inst_mgr = P3DInstanceManager::get_global_ptr();
  if (_inst == NULL) {
    return inst_mgr->new_bool_object(false);
  }

  if (!_inst->is_started()) {
    _inst->play_button_clicked();
  }
   
  return inst_mgr->new_bool_object(_inst->is_started());
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::call_read_game_log
//       Access: Private
//  Description: Reads the entire logfile as a string, and returns it
//               to the calling JavaScript process.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
call_read_game_log(P3D_object *params[], int num_params) {
  P3DInstanceManager *inst_mgr = P3DInstanceManager::get_global_ptr();
  if (_inst == NULL) {
    return inst_mgr->new_undefined_object();
  }

  P3DSession *session = _inst->get_session();
  if (session == NULL) {
    return inst_mgr->new_undefined_object();
  }

  string log_pathname = session->get_log_pathname();
  return read_log(log_pathname, params, num_params);
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::call_read_system_log
//       Access: Private
//  Description: As above, but reads the system log, the logfile for
//               the installation process.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
call_read_system_log(P3D_object *params[], int num_params) {
  P3DInstanceManager *inst_mgr = P3DInstanceManager::get_global_ptr();

  string log_pathname = inst_mgr->get_log_pathname();
  return read_log(log_pathname, params, num_params);
}

////////////////////////////////////////////////////////////////////
//     Function: P3DMainObject::call_read_log
//       Access: Private
//  Description: The generic log-reader function.
////////////////////////////////////////////////////////////////////
P3D_object *P3DMainObject::
read_log(const string &log_pathname, P3D_object *params[], int num_params) {
  ifstream log(log_pathname.c_str(), ios::in);

  // Check the parameter, if any--if specified, it specifies the last
  // n bytes to retrieve.
  int max_bytes = 0;
  if (num_params > 0) {
    max_bytes = P3D_OBJECT_GET_INT(params[0]);
  }

  // Get the size of the file.
  log.seekg(0, ios::end);
  size_t size = (size_t)log.tellg();

  if (max_bytes > 0 && max_bytes < (int)size) {
    // Apply the limit.
    log.seekg(size - max_bytes, ios::beg);
    size = (size_t)max_bytes;
  } else {
    // Read the entire file.
    log.seekg(0, ios::beg);
  }

  char *buffer = new char[size];
  if (buffer == NULL) {
    return NULL;
  }

  log.read(buffer, size);
  P3D_object *result = new P3DStringObject(buffer, size);
  delete[] buffer;
  
  return result;
}
