// Filename: p3dSplashWindow.cxx
// Created by:  drose (17Jun09)
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

#include "p3dSplashWindow.h"

// Stuff to use libpng.
#include <png.h>

// Stuff to use libjpeg.
extern "C" {
#include <jpeglib.h>
#include <jerror.h>
}

#include <setjmp.h>

struct my_error_mgr {
  struct jpeg_error_mgr pub;
  jmp_buf setjmp_buffer;
};

typedef struct my_error_mgr *my_error_ptr;

METHODDEF(void) my_error_exit (j_common_ptr cinfo) {
  // cinfo->err really points to a my_error_mgr struct, so coerce pointer
  my_error_ptr myerr = (my_error_ptr) cinfo->err;
  // Return control to the setjmp point
  longjmp(myerr->setjmp_buffer, 1);
}



////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::Constructor
//       Access: Public
//  Description: By the time the SplashWindow is created, the instance
//               has received both its fparams and its wparams.  Copy
//               them both into this class for reference.
////////////////////////////////////////////////////////////////////
P3DSplashWindow::
P3DSplashWindow(P3DInstance *inst) : 
  _inst(inst),
  _fparams(inst->get_fparams()),
  _wparams(inst->get_wparams())
{
  _button_width = 0;
  _button_height = 0;
  _button_x = 0;
  _button_y = 0;
  _button_active = false;
  _mouse_x = -1;
  _mouse_y = -1;
  _mouse_down = false;
  _button_depressed = false;
  _bstate = BS_hidden;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::Destructor
//       Access: Public, Virtual
//  Description: 
////////////////////////////////////////////////////////////////////
P3DSplashWindow::
~P3DSplashWindow() {
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_wparams
//       Access: Public, Virtual
//  Description: Changes the window parameters, e.g. to resize or
//               reposition the window; or sets the parameters for the
//               first time, creating the initial window.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_wparams(const P3DWindowParams &wparams) {
  _wparams = wparams;
  _win_width = _wparams.get_win_width();
  _win_height = _wparams.get_win_height();
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_image_filename
//       Access: Public, Virtual
//  Description: Specifies the name of a JPEG or PNG image file that
//               is displayed in the center of the splash window.
//
//               image_placement defines the specific context in which
//               this particular image is displayed.  It is similar to
//               the P3DInstance's image_type, but it is a more
//               specific, lower-level usage.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_image_filename(const string &image_filename, ImagePlacement image_placement) {
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_install_label
//       Access: Public, Virtual
//  Description: Specifies the text that is displayed above the
//               install progress bar.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_install_label(const string &install_label) {
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_install_progress
//       Access: Public, Virtual
//  Description: Moves the install progress bar from 0.0 to 1.0.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_install_progress(double install_progress) {
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::handle_event
//       Access: Public, Virtual
//  Description: Deals with the event callback from the OS window
//               system.  Returns true if the event is handled, false
//               if ignored.
////////////////////////////////////////////////////////////////////
bool P3DSplashWindow::
handle_event(P3D_event_data event) {
  return false;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_button_active
//       Access: Public, Virtual
//  Description: Sets whether the button should be visible and active
//               (true) or invisible and inactive (false).  If active,
//               the button image will be displayed in the window, and
//               a click event will be generated when the user clicks
//               the button.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_button_active(bool flag) {
  _button_active = flag;

  // Now light up the button according to the current mouse position.
  set_mouse_data(_mouse_x, _mouse_y, _mouse_down);
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::read_image_data
//       Access: Protected
//  Description: Reads the image filename and sets image parameters
//               width, height, num_channels, and data.  Returns true
//               on success, false on failure.
////////////////////////////////////////////////////////////////////
bool P3DSplashWindow::
read_image_data(ImageData &image, string &data,
                const string &image_filename) {
  image._width = 0;
  image._height = 0;
  image._num_channels = 0;
  data.clear();

  // We only support JPEG or PNG images.
  FILE *fp = fopen(image_filename.c_str(), "rb");
  if (fp == NULL) {
    nout << "Couldn't open splash file image: " << image_filename << "\n";
    return false;
  }

  // Check the magic number to determine which image type we have.
  static const size_t magic_number_len = 2;
  char magic_number[magic_number_len];
  if (fread(magic_number, 1, magic_number_len, fp) != magic_number_len) {
    nout << "Empty file: " << image_filename << "\n";
    return false;
  }
  // Rewind to re-read the magic number below.
  fseek(fp, 0, SEEK_SET);

  bool result = false;
  if ((char)magic_number[0] == (char)0xff &&
      (char)magic_number[1] == (char)0xd8) {
    // It's a jpeg image.
    result = read_image_data_jpeg(image, data, fp, image_filename);

  } else if (png_sig_cmp((png_bytep)magic_number, 0, magic_number_len) == 0) {
    // It's a PNG image.
    result = read_image_data_png(image, data, fp, image_filename);

  } else {
    nout << "Neither a JPEG nor a PNG image: " << image_filename << "\n";
    result = false;
  }

  fclose(fp);
  return result;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::read_image_data_jpeg
//       Access: Protected
//  Description: Reads the image filename and sets image parameters
//               width, height, num_channels, and data.  Returns true
//               on success, false on failure.
////////////////////////////////////////////////////////////////////
bool P3DSplashWindow::
read_image_data_jpeg(ImageData &image, string &data,
                     FILE *fp, const string &image_filename) {
  // We set up the normal JPEG error routines, then override error_exit.
  struct jpeg_decompress_struct cinfo;

  struct my_error_mgr jerr;
  cinfo.err = jpeg_std_error(&jerr.pub);
  jerr.pub.error_exit = my_error_exit;

  JSAMPLE *buffer = NULL;
  
  // Establish the setjmp return context for my_error_exit to use
  if (setjmp(jerr.setjmp_buffer)) {
    // If we get here, the JPEG code has signaled an error.
    nout << "JPEG error decoding " << image_filename << "\n";

    // We need to clean up the JPEG object, close the input file, and return.
    jpeg_destroy_decompress(&cinfo);

    if (buffer != NULL) {
      delete[] buffer;
    }
    return false;
  }

  /* Now we can initialize the JPEG decompression object. */
  jpeg_create_decompress(&cinfo);
  jpeg_stdio_src(&cinfo, fp);

  jpeg_read_header(&cinfo, true);

  cinfo.scale_num = 1;
  cinfo.scale_denom = 1;

  jpeg_start_decompress(&cinfo);

  image._width = cinfo.output_width;
  image._height = cinfo.output_height;
  image._num_channels = cinfo.output_components;

  int row_stride = image._width * image._num_channels;

  size_t buffer_size = image._height * row_stride;
  buffer = new JSAMPLE[buffer_size];
  JSAMPLE *buffer_end = buffer + buffer_size;

  JSAMPLE *rowptr = buffer;
  while (cinfo.output_scanline < cinfo.output_height) {
    assert(rowptr + row_stride <= buffer_end);
    jpeg_read_scanlines(&cinfo, &rowptr, 1);
    rowptr += row_stride;
  }

  jpeg_finish_decompress(&cinfo);

  data.append((const char *)buffer, buffer_size);
  delete[] buffer;

  return true;
}


////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::read_image_data_png
//       Access: Protected
//  Description: Reads the image filename and sets image parameters
//               width, height, num_channels, and data.  Returns true
//               on success, false on failure.
////////////////////////////////////////////////////////////////////
bool P3DSplashWindow::
read_image_data_png(ImageData &image, string &data,
                    FILE *fp, const string &image_filename) {
  cerr << "read_image_data_png\n";
  png_structp png;
  png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL,
                                png_error, png_warning);
  if (png == NULL) {
    return false;
  }

  png_infop info;
  info = png_create_info_struct(png);
  if (info == NULL) {
    png_destroy_read_struct(&png, NULL, NULL);
    return false;
  }

  jmp_buf jmpbuf;
  if (setjmp(jmpbuf)) {
    // This is the ANSI C way to handle exceptions.  If setjmp(),
    // above, returns true, it means that libpng detected an exception
    // while executing the code that reads the header info, below.
    png_destroy_read_struct(&png, &info, NULL);
    return false;
  }

  png_init_io(png, fp);
  int transforms = PNG_TRANSFORM_STRIP_16 | PNG_TRANSFORM_PACKING | PNG_TRANSFORM_EXPAND | PNG_TRANSFORM_SHIFT;
  //  transforms |= PNG_TRANSFORM_STRIP_ALPHA;
  png_read_png(png, info, transforms, NULL);

  png_uint_32 width;
  png_uint_32 height;
  int bit_depth;
  int color_type;

  png_get_IHDR(png, info, &width, &height,
               &bit_depth, &color_type, NULL, NULL, NULL);

  cerr
    << "width = " << width << " height = " << height << " bit_depth = "
    << bit_depth << " color_type = " << color_type << "\n";

  image._width = width;
  image._height = height;

  switch (color_type) {
  case PNG_COLOR_TYPE_RGB:
    cerr
      << "PNG_COLOR_TYPE_RGB\n";
    image._num_channels = 3;
    break;

  case PNG_COLOR_TYPE_RGB_ALPHA:
    cerr
      << "PNG_COLOR_TYPE_RGB_ALPHA\n";
    image._num_channels = 4;
    break;

  default:
    cerr
      << "Unsupported color type: " << color_type << "\n";
    png_destroy_read_struct(&png, &info, NULL);
    return false;
  }

  int row_stride = image._width * image._num_channels;
  png_bytep *row_pointers = png_get_rows(png, info);
  for (int yi = 0; yi < image._height; ++yi) {
    data.append((const char *)row_pointers[yi], row_stride);
  }

  png_destroy_read_struct(&png, &info, NULL);

  cerr << "successfully read\n";
  return true;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::get_bar_placement
//       Access: Protected
//  Description: Given the window width and height, determine the
//               rectangle in which to place the progress bar.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
get_bar_placement(int &bar_x, int &bar_y,
                  int &bar_width, int &bar_height) {
  bar_width = min((int)(_win_width * 0.6), 400);
  bar_height = min((int)(_win_height * 0.1), 24);
  bar_x = (_win_width - bar_width) / 2;
  bar_y = (_win_height - bar_height * 2);
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_button_range
//       Access: Protected
//  Description: Specifies the image that contains the "ready" button
//               image, which in turn determines the clickable
//               dimensions of the button within the window.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_button_range(const ImageData &image) {
  // The clickable area has a certain minimum size, even if it's a
  // very small image.
  _button_width = max(image._width, 64);
  _button_height = max(image._height, 64);

  // But it can't be larger than the window itself.
  _button_width = min(_button_width, _win_width);
  _button_height = min(_button_height, _win_height);
      
  // Compute the top-left corner of the button image in window
  // coordinates.
  _button_x = (_win_width - _button_width) / 2;
  _button_y = (_win_height - _button_height) / 2;
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::set_mouse_data
//       Access: Protected
//  Description: Intended to be called by the subclasses as the mouse
//               is tracked through the window, whether the button is
//               currently active or not.  This updates the internal
//               state of the mouse pointer, and also (if the button
//               is active) updates the button state appropriately,
//               and generates the click event when the mouse button
//               transitions from down to up over the button area.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
set_mouse_data(int mouse_x, int mouse_y, bool mouse_down) {
  ButtonState orig_bstate = _bstate;

  _mouse_x = mouse_x;
  _mouse_y = mouse_y;
  _mouse_down = mouse_down;

  ButtonState bstate = BS_hidden;

  if (!_button_active) {
    // The button isn't active, so it's hidden, regardless of the
    // mouse position.
    bstate = BS_hidden;
  } else {
    // Is the mouse pointer within the button region?
    bool is_within = (_mouse_x >= _button_x && _mouse_x < _button_x + _button_width &&
                      _mouse_y >= _button_y && _mouse_y < _button_y + _button_height);
    if (is_within) {
      // The mouse is within the button region.  This means either
      // click or rollover state, according to the mouse button.
      if (_mouse_down) {
        // We only count it mouse-down if you've clicked down while
        // over the button (or you never released the button since the
        // last time you clicked down).  Clicking down somewhere else
        // and dragging over the button doesn't count.
        if (orig_bstate == BS_rollover || _button_depressed) {
          _button_depressed = true;
          bstate = BS_click;
        }
      } else {
        _button_depressed = false;
        if (orig_bstate == BS_click) {
          // If we just transitioned from mouse down to mouse up, this
          // means a click.  And the button automatically hides itself
          // after a successful click.
          bstate = BS_hidden;
          _button_active = false;
          button_click_detected();
        } else {
          bstate = BS_rollover;
        }
      }
    } else {
      // The mouse is not within the button region.  This means ready
      // state.
      bstate = BS_ready;
      if (!_mouse_down) {
        _button_depressed = false;
      }
    }
  }

  if (_bstate != bstate) {
    _bstate = bstate;
    // If we've changed button states, we need to refresh the window.
    refresh();
  }
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::button_click_detected
//       Access: Protected, Virtual
//  Description: Called when a button click by the user is detected in
//               set_mouse_data(), this method simply turns around and
//               notifies the instance.  It's a virtual method to give
//               subclasses a chance to redirect this message to the
//               main thread or process, as necessary.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
button_click_detected() {
  assert(_inst != NULL);
  _inst->splash_button_clicked();
}

////////////////////////////////////////////////////////////////////
//     Function: P3DSplashWindow::refresh
//       Access: Protected, Virtual
//  Description: Requests that the window will be repainted.  This may
//               or may not be implemented for a particular
//               specialization of P3DSplashWindow.
////////////////////////////////////////////////////////////////////
void P3DSplashWindow::
refresh() {
}
