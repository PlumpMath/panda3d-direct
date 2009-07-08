// Filename: ppBrowserObject.cxx
// Created by:  drose (05Jul09)
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

#include "ppBrowserObject.h"
#include "ppInstance.h"
#include <sstream>
#include <string.h>  // strncpy

// The following functions are C-style wrappers around the above
// PPBrowserObject methods; they are defined to allow us to create the
// C-style P3D_class_definition method table to store in the
// P3D_object structure.
static void
object_finish(P3D_object *object) {
  delete ((PPBrowserObject *)object);
}

static P3D_object *
object_copy(const P3D_object *object) {
  return new PPBrowserObject(*(const PPBrowserObject *)object);
}

static int 
object_get_repr(const P3D_object *object, char *buffer, int buffer_length) {
  return ((const PPBrowserObject *)object)->get_repr(buffer, buffer_length);
}

static P3D_object *
object_get_property(const P3D_object *object, const char *property) {
  return ((const PPBrowserObject *)object)->get_property(property);
}

static bool
object_set_property(P3D_object *object, const char *property,
                    P3D_object *value) {
  return ((PPBrowserObject *)object)->set_property(property, value);
}

static P3D_object *
object_call(const P3D_object *object, const char *method_name,
            P3D_object *params[], int num_params) {
  if (method_name == NULL) {
    method_name = "";
  }
  return ((const PPBrowserObject *)object)->call(method_name, params, num_params);
}

static P3D_object *
object_eval(const P3D_object *object, const char *expression) {
  return ((const PPBrowserObject *)object)->eval(expression);
}

P3D_class_definition *PPBrowserObject::_browser_object_class;

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::Constructor
//       Access: Public
//  Description: 
////////////////////////////////////////////////////////////////////
PPBrowserObject::
PPBrowserObject(PPInstance *inst, NPObject *npobj) :
  _instance(inst),
  _npobj(npobj)
{
  _class = get_class_definition();
  browser->retainobject(_npobj);
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::Copy Constructor
//       Access: Public
//  Description: 
////////////////////////////////////////////////////////////////////
PPBrowserObject::
PPBrowserObject(const PPBrowserObject &copy) :
  _instance(copy._instance),
  _npobj(copy._npobj)
{
  _class = get_class_definition();
  browser->retainobject(_npobj);
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::Destructor
//       Access: Public
//  Description: 
////////////////////////////////////////////////////////////////////
PPBrowserObject::
~PPBrowserObject() {
  browser->releaseobject(_npobj);
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::get_repr
//       Access: Public
//  Description: Returns a user-friendly representation of the object,
//               similar to get_string(), above.
////////////////////////////////////////////////////////////////////
int PPBrowserObject::
get_repr(char *buffer, int buffer_length) const {
  ostringstream strm;
  strm << "NPObject " << _npobj;
  string result = strm.str();
  strncpy(buffer, result.c_str(), buffer_length);
  return (int)result.size();
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::get_property
//       Access: Public
//  Description: Returns the named property element in the object.  The
//               return value is a freshly-allocated PPBrowserObject object
//               that must be deleted by the caller, or NULL on error.
////////////////////////////////////////////////////////////////////
P3D_object *PPBrowserObject::
get_property(const string &property) const {
  NPIdentifier property_name = browser->getstringidentifier(property.c_str());
  if (!browser->hasproperty(_instance->get_npp_instance(), _npobj,
                            property_name)) {
    // No such property.
    return NULL;
  }

  NPVariant result;
  if (!browser->getproperty(_instance->get_npp_instance(), _npobj,
                            property_name, &result)) {
    // Failed to retrieve property.
    return NULL;
  }

  P3D_object *object = _instance->variant_to_p3dobj(&result);
  browser->releasevariantvalue(&result);
  return object;
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::set_property
//       Access: Public
//  Description: Modifies (or deletes, if value is NULL) the named
//               property element in the object.  Returns true on
//               success, false on failure.
////////////////////////////////////////////////////////////////////
bool PPBrowserObject::
set_property(const string &property, P3D_object *value) {
  NPIdentifier property_name = browser->getstringidentifier(property.c_str());
  bool result;
  if (value != NULL) {
    // Set the property.
    NPVariant npvalue;
    _instance->p3dobj_to_variant(&npvalue, value);
    result = browser->setproperty(_instance->get_npp_instance(), _npobj,
                                  property_name, &npvalue);
    browser->releasevariantvalue(&npvalue);
    P3D_OBJECT_FINISH(value);

  } else {
    // Delete the property.
    result = browser->removeproperty(_instance->get_npp_instance(), _npobj,
                                     property_name);
  }

  return result;
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::call
//       Access: Public
//  Description: Invokes the named method on the object, passing the
//               indicated parameters.  If the method name is empty,
//               invokes the object itself.  Returns the return value
//               on success, NULL on error.
////////////////////////////////////////////////////////////////////
P3D_object *PPBrowserObject::
call(const string &method_name, P3D_object *params[], int num_params) const {
  logfile << "call " << method_name << "(";
  // First, convert all of the parameters.
  NPVariant *npparams = new NPVariant[num_params];
  for (int i = 0; i < num_params; ++i) {
    _instance->p3dobj_to_variant(&npparams[i], params[i]);
    _instance->output_np_variant(logfile, npparams[i]);
    logfile << ", ";
  }
  logfile << ")\n";

  NPVariant result;
  if (method_name.empty()) {
    // Call the default method.
    if (!browser->invokeDefault(_instance->get_npp_instance(), _npobj,
                                npparams, num_params, &result)) {
      // Failed to invoke.
      logfile << "invokeDefault failed\n" << flush;
      delete[] npparams;
      return NULL;
    }
  } else {
    // Call the named method.

    NPIdentifier method_id = browser->getstringidentifier(method_name.c_str());
    if (!browser->invoke(_instance->get_npp_instance(), _npobj, method_id,
                         npparams, num_params, &result)) {
      // Failed to invoke.
      logfile << "invoke failed\n" << flush;
      delete[] npparams;
      return NULL;
    }
  }

  delete[] npparams;

  logfile << "invoke succeeded\n" << flush;

  P3D_object *object = _instance->variant_to_p3dobj(&result);
  browser->releasevariantvalue(&result);
  return object;
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::eval
//       Access: Public
//  Description: Evaluates the indicated JavaScript expression in the
//               context of the object.
////////////////////////////////////////////////////////////////////
P3D_object *PPBrowserObject::
eval(const string &expression) const {
  logfile << "eval " << expression << "\n";

  NPString npexpr;
  npexpr.utf8characters = expression.c_str();
  npexpr.utf8length = expression.length();

  NPVariant result;
  if (!browser->evaluate(_instance->get_npp_instance(), _npobj, 
                         &npexpr, &result)) {
    // Failed to eval.
    logfile << "eval failed\n" << flush;
    return NULL;
  }

  logfile << "eval succeeded\n" << flush;

  P3D_object *object = _instance->variant_to_p3dobj(&result);
  browser->releasevariantvalue(&result);
  return object;
}

////////////////////////////////////////////////////////////////////
//     Function: PPBrowserObject::get_class_definition
//       Access: Private, Static
//  Description: Returns a pointer to the P3D_class_definition object
//               that lists all of the C-style method pointers for
//               this class object.
////////////////////////////////////////////////////////////////////
P3D_class_definition *PPBrowserObject::
get_class_definition() {
  if (_browser_object_class == NULL) {
    // Create a default class_definition object, and fill in the
    // appropriate pointers.
    _browser_object_class = P3D_make_class_definition();
    _browser_object_class->_finish = &object_finish;
    _browser_object_class->_copy = &object_copy;

    _browser_object_class->_get_repr = &object_get_repr;
    _browser_object_class->_get_property = &object_get_property;
    _browser_object_class->_set_property = &object_set_property;
    _browser_object_class->_call = &object_call;
    _browser_object_class->_eval = &object_eval;
  }

  return _browser_object_class;
}
